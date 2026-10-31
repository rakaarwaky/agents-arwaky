# Dogfood QA Report

**Target:** {target}
**Target Type:** {target_type}
**Date:** {date}
**Scope:** {scope_description}
**Tester:** Hermes Agent (automated exploratory QA)

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {critical_count} |
| 🟠 High | {high_count} |
| 🟡 Medium | {medium_count} |
| 🔵 Low | {low_count} |
| **Total** | **{total_count}** |

**Overall Assessment:** {one_sentence_assessment}

---

## Issues

<!-- Repeat for each issue found, sorted by severity (Critical first) -->

### Issue #{issue_number}: {issue_title}

| Field | Value |
|-------|-------|
| **Severity** | {severity} |
| **Category** | {category} |
| **Location** | {location} |
| **Target Type** | {target_type} |

**Description:**
{detailed_description_of_the_issue}

**Steps to Reproduce:**
1. {step_1}
2. {step_2}
3. {step_3}

**Expected Behavior:**
{what_should_happen}

**Actual Behavior:**
{what_actually_happens}

**Evidence:**
MEDIA:{screenshot_path}

**Runtime log lines** (if applicable):
```
{log_output}
```

---

<!-- End of per-issue section -->

## Issues Summary Table

| # | Title | Severity | Category | Location |
|---|-------|----------|----------|----------|
| {n} | {title} | {severity} | {category} | {url_or_cmd_or_app} |

## Testing Coverage

### Target Type: {target_type}

### Areas Tested
- {list_of_pages_visited_or_commands_run_or_screens_tested}

### Features Tested
- {list_of_features_exercised}

### Not Tested / Out of Scope
- {areas_not_covered_and_why}

### Blockers
- {any_issues_that_prevented_testing_certain_areas}

---

## Notes

{any_additional_observations_or_recommendations}
