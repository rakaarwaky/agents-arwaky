package github

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/github/github-mcp-server/pkg/inventory"
	"github.com/github/github-mcp-server/pkg/scopes"
	"github.com/github/github-mcp-server/pkg/translations"
	"github.com/github/github-mcp-server/pkg/utils"
	"github.com/google/go-github/v82/github"
	"github.com/google/jsonschema-go/jsonschema"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// github_list_activity provides a high-level summary of the user's recent activity and tasks.
func GithubListActivity(t translations.TranslationHelperFunc) inventory.ServerTool {
	return NewTool(
		ToolsetMetadataHydra,
		mcp.Tool{
			Name:        "github_list_activity",
			Description: t("TOOL_HYDRA_LIST_ACTIVITY_DESCRIPTION", "Get a high-level summary of your recent GitHub activity, including notifications, assigned issues, and open pull requests."),
			Annotations: &mcp.ToolAnnotations{
				Title:        t("TOOL_HYDRA_LIST_ACTIVITY_USER_TITLE", "List recent activity"),
				ReadOnlyHint: true,
			},
			InputSchema: &jsonschema.Schema{
				Type: "object",
				Properties: map[string]*jsonschema.Schema{
					"all": {
						Type:        "boolean",
						Description: "If true, show all notifications (not just unread)",
					},
				},
			},
		},
		[]scopes.Scope{scopes.Notifications, scopes.Repo},
		func(ctx context.Context, deps ToolDependencies, _ *mcp.CallToolRequest, args map[string]any) (*mcp.CallToolResult, any, error) {
			client, err := deps.GetClient(ctx)
			if err != nil {
				return nil, nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			all, _ := args["all"].(bool)

			// 1. Get Notifications
			notifOpts := &github.NotificationListOptions{All: all}
			notifications, _, _ := client.Activity.ListNotifications(ctx, notifOpts)

			// 2. Get Assigned Issues
			issueOpts := &github.IssueListOptions{
				Filter: "assigned",
				State:  "open",
			}
			issues, _, _ := client.Issues.List(ctx, true, issueOpts)

			// 3. Get Pull Requests (Created by user)
			searchQuery := "is:pr is:open author:@me"
			prResults, _, _ := client.Search.Issues(ctx, searchQuery, nil)

			// Consolidate activity
			activity := struct {
				Notifications []any `json:"notifications,omitempty"`
				AssignedIssues []any `json:"assigned_issues,omitempty"`
				OpenPRs       []any `json:"open_pull_requests,omitempty"`
			}{
				Notifications:  make([]any, 0),
				AssignedIssues: make([]any, 0),
				OpenPRs:       make([]any, 0),
			}

			for _, n := range notifications {
				activity.Notifications = append(activity.Notifications, map[string]any{
					"id":      n.GetID(),
					"subject": n.GetSubject().GetTitle(),
					"type":    n.GetSubject().GetType(),
					"repo":    n.GetRepository().GetFullName(),
					"reason":  n.GetReason(),
				})
			}

			for _, i := range issues {
				activity.AssignedIssues = append(activity.AssignedIssues, map[string]any{
					"number": i.GetNumber(),
					"title":  i.GetTitle(),
					"repo":   i.GetRepository().GetFullName(),
					"url":    i.GetHTMLURL(),
				})
			}

			if prResults != nil {
				for _, pr := range prResults.Issues {
					activity.OpenPRs = append(activity.OpenPRs, map[string]any{
						"number": pr.GetNumber(),
						"title":  pr.GetTitle(),
						"url":    pr.GetHTMLURL(),
					})
				}
			}

			r, err := json.Marshal(activity)
			if err != nil {
				return nil, nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return utils.NewToolResultText(string(r)), nil, nil
		},
	)
}

// github_understand_codebase helps map the repository structure and find relevant entry points.
func GithubUnderstandCodebase(t translations.TranslationHelperFunc) inventory.ServerTool {
	return NewTool(
		ToolsetMetadataHydra,
		mcp.Tool{
			Name:        "github_understand_codebase",
			Description: t("TOOL_HYDRA_UNDERSTAND_CODEBASE_DESCRIPTION", "Recursively explore the repository structure and search for key configuration and entry point files in one call."),
			Annotations: &mcp.ToolAnnotations{
				Title:        t("TOOL_HYDRA_UNDERSTAND_CODEBASE_USER_TITLE", "Understand codebase"),
				ReadOnlyHint: true,
			},
			InputSchema: &jsonschema.Schema{
				Type: "object",
				Properties: map[string]*jsonschema.Schema{
					"owner": {
						Type:        "string",
						Description: "Repository owner",
					},
					"repo": {
						Type:        "string",
						Description: "Repository name",
					},
					"branch": {
						Type:        "string",
						Description: "Branch to explore (default is repo default branch)",
					},
					"query": {
						Type:        "string",
						Description: "Optional code search query (e.g., 'interface' or 'main')",
					},
				},
				Required: []string{"owner", "repo"},
			},
		},
		[]scopes.Scope{scopes.Repo},
		func(ctx context.Context, deps ToolDependencies, _ *mcp.CallToolRequest, args map[string]any) (*mcp.CallToolResult, any, error) {
			owner, _ := args["owner"].(string)
			repo, _ := args["repo"].(string)
			branch, _ := args["branch"].(string)
			query, _ := args["query"].(string)

			client, err := deps.GetClient(ctx)
			if err != nil {
				return nil, nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			if branch == "" {
				r, _, err := client.Repositories.Get(ctx, owner, repo)
				if err == nil {
					branch = r.GetDefaultBranch()
				} else {
					branch = "main" // fallback
				}
			}

			// 1. Get Recursive Tree
			tree, _, err := client.Git.GetTree(ctx, owner, repo, branch, true)
			if err != nil {
				return utils.NewToolResultError(fmt.Sprintf("failed to get repository tree: %v", err)), nil, nil
			}

			// 2. Search for common entry points (package.json, go.mod, README.md, etc.)
			// We can filter the tree locally for efficiency
			keyFiles := make([]string, 0)
			for _, entry := range tree.Entries {
				name := entry.GetPath()
				if entry.GetType() == "blob" {
					if strings.HasSuffix(name, "package.json") ||
						strings.HasSuffix(name, "go.mod") ||
						strings.HasSuffix(name, "README.md") ||
						strings.HasSuffix(name, "Dockerfile") ||
						strings.HasSuffix(name, "index.js") ||
						strings.HasSuffix(name, "main.go") {
						keyFiles = append(keyFiles, name)
					}
				}
			}

			result := map[string]any{
				"tree_summary": fmt.Sprintf("Found %d entries in branch %s", len(tree.Entries), branch),
				"key_files":    keyFiles,
				"tree_link":    fmt.Sprintf("https://github.com/%s/%s/tree/%s", owner, repo, branch),
			}

			// 3. Search code if query is provided
			if query != "" {
				searchQuery := fmt.Sprintf("repo:%s/%s %s", owner, repo, query)
				searchResult, _, err := client.Search.Code(ctx, searchQuery, nil)
				if err == nil && searchResult != nil {
					matches := make([]map[string]any, 0)
					for i, m := range searchResult.CodeResults {
						if i >= 10 {
							break
						}
						matches = append(matches, map[string]any{
							"path": m.GetPath(),
							"url":  m.GetHTMLURL(),
						})
					}
					result["search_results"] = matches
				}
			}

			// Limit the number of tree entries in the output to avoid context overflow
			shortTree := make([]string, 0)
			for i, entry := range tree.Entries {
				if i > 100 {
					shortTree = append(shortTree, "... and more")
					break
				}
				shortTree = append(shortTree, entry.GetPath())
			}
			result["tree_preview"] = shortTree

			r, err := json.Marshal(result)
			if err != nil {
				return nil, nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return utils.NewToolResultText(string(r)), nil, nil
		},
	)
}

// github_execute_workflow executes a preset multi-step operation like "hotfix" or "feature-start".
func GithubExecuteWorkflow(t translations.TranslationHelperFunc) inventory.ServerTool {
	return NewTool(
		ToolsetMetadataHydra,
		mcp.Tool{
			Name:        "github_execute_workflow",
			Description: t("TOOL_HYDRA_EXECUTE_WORKFLOW_DESCRIPTION", "Perform a multi-step operation in a single call, such as starting a feature (branch + initial commit + PR)."),
			Annotations: &mcp.ToolAnnotations{
				Title:        t("TOOL_HYDRA_EXECUTE_WORKFLOW_USER_TITLE", "Execute workflow"),
				ReadOnlyHint: false,
			},
			InputSchema: &jsonschema.Schema{
				Type: "object",
				Properties: map[string]*jsonschema.Schema{
					"owner": {
						Type:        "string",
						Description: "Repository owner",
					},
					"repo": {
						Type:        "string",
						Description: "Repository name",
					},
					"workflow": {
						Type:        "string",
						Description: "Workflow type: 'feature_start'",
						Enum:        []any{"feature_start"},
					},
					"branch_name": {
						Type:        "string",
						Description: "Name of the new branch",
					},
					"file_path": {
						Type:        "string",
						Description: "Path for the initial file",
					},
					"file_content": {
						Type:        "string",
						Description: "Content for the initial file",
					},
					"commit_message": {
						Type:        "string",
						Description: "Commit message",
					},
					"pr_title": {
						Type:        "string",
						Description: "Pull Request title",
					},
					"pr_body": {
						Type:        "string",
						Description: "Pull Request description",
					},
				},
				Required: []string{"owner", "repo", "workflow", "branch_name"},
			},
		},
		[]scopes.Scope{scopes.Repo},
		func(ctx context.Context, deps ToolDependencies, _ *mcp.CallToolRequest, args map[string]any) (*mcp.CallToolResult, any, error) {
			owner, _ := args["owner"].(string)
			repo, _ := args["repo"].(string)
			workflow, _ := args["workflow"].(string)

			client, err := deps.GetClient(ctx)
			if err != nil {
				return nil, nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			if workflow == "feature_start" {
				branchName, _ := args["branch_name"].(string)
				filePath, _ := args["file_path"].(string)
				fileContent, _ := args["file_content"].(string)
				commitMessage, _ := args["commit_message"].(string)
				prTitle, _ := args["pr_title"].(string)
				prBody, _ := args["pr_body"].(string)

				// 1. Get default branch SHA
				r, _, err := client.Repositories.Get(ctx, owner, repo)
				if err != nil {
					return utils.NewToolResultError(fmt.Sprintf("failed to get repo: %v", err)), nil, nil
				}
				baseBranch := r.GetDefaultBranch()
				ref, _, err := client.Git.GetRef(ctx, owner, repo, "refs/heads/"+baseBranch)
				if err != nil {
					return utils.NewToolResultError(fmt.Sprintf("failed to get base ref: %v", err)), nil, nil
				}

				newBranchRef := github.CreateRef{
					Ref: "refs/heads/" + branchName,
					SHA: ref.Object.GetSHA(),
				}
				_, _, err = client.Git.CreateRef(ctx, owner, repo, newBranchRef)
				if err != nil {
					return utils.NewToolResultError(fmt.Sprintf("failed to create branch: %v", err)), nil, nil
				}

				resultSteps := []string{"Branch created: " + branchName}

				// 3. Create File (if provided)
				if filePath != "" {
					opts := &github.RepositoryContentFileOptions{
						Message: github.Ptr(commitMessage),
						Content: []byte(fileContent),
						Branch:  github.Ptr(branchName),
					}
					_, _, err = client.Repositories.CreateFile(ctx, owner, repo, filePath, opts)
					if err != nil {
						resultSteps = append(resultSteps, "Failed to create file: "+err.Error())
					} else {
						resultSteps = append(resultSteps, "File created: "+filePath)
					}
				}

				// 4. Create PR (if title provided)
				var prURL string
				if prTitle != "" {
					newPR := &github.NewPullRequest{
						Title: github.Ptr(prTitle),
						Head:  github.Ptr(branchName),
						Base:  github.Ptr(baseBranch),
						Body:  github.Ptr(prBody),
					}
					pr, _, err := client.PullRequests.Create(ctx, owner, repo, newPR)
					if err != nil {
						resultSteps = append(resultSteps, "Failed to create PR: "+err.Error())
					} else {
						prURL = pr.GetHTMLURL()
						resultSteps = append(resultSteps, "PR created: "+prURL)
					}
				}

				finalResult := map[string]any{
					"workflow": "feature_start",
					"steps":    resultSteps,
					"pr_url":   prURL,
				}
				rjson, _ := json.Marshal(finalResult)
				return utils.NewToolResultText(string(rjson)), nil, nil
			}

			return utils.NewToolResultError("Unknown workflow type"), nil, nil
		},
	)
}

// github_manage_thread provides full conversational context for an issue or pull request.
func GithubManageThread(t translations.TranslationHelperFunc) inventory.ServerTool {
	return NewTool(
		ToolsetMetadataHydra,
		mcp.Tool{
			Name:        "github_manage_thread",
			Description: t("TOOL_HYDRA_MANAGE_THREAD_DESCRIPTION", "Read an issue or pull request along with all its comments in a single call to get full context."),
			Annotations: &mcp.ToolAnnotations{
				Title:        t("TOOL_HYDRA_MANAGE_THREAD_USER_TITLE", "Manage conversation thread"),
				ReadOnlyHint: true,
			},
			InputSchema: &jsonschema.Schema{
				Type: "object",
				Properties: map[string]*jsonschema.Schema{
					"owner": {
						Type:        "string",
						Description: "Repository owner",
					},
					"repo": {
						Type:        "string",
						Description: "Repository name",
					},
					"number": {
						Type:        "integer",
						Description: "Issue or Pull Request number",
					},
					"is_pr": {
						Type:        "boolean",
						Description: "Set to true if this is a Pull Request",
					},
				},
				Required: []string{"owner", "repo", "number"},
			},
		},
		[]scopes.Scope{scopes.Repo},
		func(ctx context.Context, deps ToolDependencies, _ *mcp.CallToolRequest, args map[string]any) (*mcp.CallToolResult, any, error) {
			owner, _ := args["owner"].(string)
			repo, _ := args["repo"].(string)
			numberFloat, _ := args["number"].(float64)
			number := int(numberFloat)
			isPR, _ := args["is_pr"].(bool)

			client, err := deps.GetClient(ctx)
			if err != nil {
				return nil, nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			var threadData map[string]any

			if isPR {
				pr, _, err := client.PullRequests.Get(ctx, owner, repo, number)
				if err != nil {
					return utils.NewToolResultError(fmt.Sprintf("failed to get PR: %v", err)), nil, nil
				}
				comments, _, _ := client.PullRequests.ListComments(ctx, owner, repo, number, nil)
				issueComments, _, _ := client.Issues.ListComments(ctx, owner, repo, number, nil)

				combinedComments := make([]any, 0)
				for _, c := range issueComments {
					combinedComments = append(combinedComments, map[string]any{
						"user": c.GetUser().GetLogin(),
						"body": c.GetBody(),
						"type": "issue_comment",
					})
				}
				for _, c := range comments {
					combinedComments = append(combinedComments, map[string]any{
						"user": c.GetUser().GetLogin(),
						"body": c.GetBody(),
						"type": "review_comment",
						"path": c.GetPath(),
					})
				}

				threadData = map[string]any{
					"type":     "pull_request",
					"title":    pr.GetTitle(),
					"body":     pr.GetBody(),
					"state":    pr.GetState(),
					"comments": combinedComments,
				}
			} else {
				issue, _, err := client.Issues.Get(ctx, owner, repo, number)
				if err != nil {
					return utils.NewToolResultError(fmt.Sprintf("failed to get issue: %v", err)), nil, nil
				}
				comments, _, _ := client.Issues.ListComments(ctx, owner, repo, number, nil)

				commentList := make([]any, 0)
				for _, c := range comments {
					commentList = append(commentList, map[string]any{
						"user": c.GetUser().GetLogin(),
						"body": c.GetBody(),
					})
				}

				threadData = map[string]any{
					"type":     "issue",
					"title":    issue.GetTitle(),
					"body":     issue.GetBody(),
					"state":    issue.GetState(),
					"comments": commentList,
				}
			}

			r, _ := json.Marshal(threadData)
			return utils.NewToolResultText(string(r)), nil, nil
		},
	)
}
