#!/bin/bash
export GITHUB_PERSONAL_ACCESS_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
exec /home/raka/mcp-servers/github-mcp-server/github-mcp-server "$@"
