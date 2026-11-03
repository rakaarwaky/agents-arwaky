# Google Forms — Tools Reference

MCP tools for reading, creating, updating, and managing Google Forms. All tools require `user_google_email` (string, required). The `form_id` parameter accepts a form ID or a full Google Forms URL.

## Contents
- Reading & Responses: get_form, list_form_responses, get_form_response
- Create & Update: create_form, batch_update_form
- Publishing: set_publish_settings
- Tips

---

## Reading & Responses

### get_form
Get the full form structure, including all questions, sections, and settings.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| form_id | string | yes | | Form ID or URL |

### list_form_responses
List responses submitted to a form.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| form_id | string | yes | | Form ID or URL |

### get_form_response
Get a single response by its ID.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| form_id | string | yes | | Form ID or URL |
| response_id | string | yes | | Response ID |

---

## Create & Update

### create_form
Create a new Google Form and return its URL.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| title | string | yes | | Form title |

### batch_update_form
Batch update a Google Form with a list of update requests.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| form_id | string | yes | | Form ID or URL |
| update_requests | array or string | yes | | Update requests. Each element is a dict with a `request_type` key and type-specific fields. Accepts a JSON string or a list. See request types below |

**Update request types:**

| request_type | Required fields | Notes |
|--------------|-----------------|-------|
| `createSection` | `object` (with `sectionId`), `insertionIndex` | Add a new section |
| `deleteSection` | `sectionId` | Remove a section |
| `createQuestion` | `object` (with `questionId`), `insertionIndex`, optional `sectionId` | Add a question |
| `updateQuestion` | `questionId`, `object` | Replace question properties |
| `deleteQuestion` | `questionId` | Remove a question |
| `createParagraph` | `object` (with `paragraphId`), `insertionIndex`, optional `sectionId` | Add a text paragraph |
| `updateParagraph` | `paragraphId`, `object` | Replace paragraph properties |
| `deleteParagraph` | `paragraphId` | Remove a paragraph |
| `updateFormInfo` | `formInfo` | Update the form's title, description, or settings |

Colors can be passed as hex strings (e.g. `"#FF0000"`) or RGB objects (e.g. `{"color": {"rgb": {"red": 1, "green": 0, "blue": 0}}}`).

---

## Publishing

### set_publish_settings
Update the form's answer collection and viewing settings.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| form_id | string | yes | | Form ID or URL |
| allow_response_editing | boolean | no | | Whether respondents can edit their answers |
| collect_email | boolean | no | | Whether to collect respondent email addresses |
| enable_collect_email | boolean | no | | Legacy alias for collect_email |
| restrict_to_domain | boolean | no | | Restrict submission to a specific domain |
| response_window_mode | string | no | | `OPEN` (always accepting), `CLOSING` (accepting until a time), or `CLOSED` (no longer accepting) |
| response_window_start_time | string | no | | RFC 3339 start time |
| response_window_end_time | string | no | | RFC 3339 end time |

---

## Tips

**Reading workflow**: Use `get_form` to see the full question list, then `list_form_responses` and `get_form_response` for submitted data.

**Question types**: When creating questions via `batch_update_form`, set the `question` field's `question_type` to one of: `TEXT`, `SHORT_ANSWER`, `PARAGRAPH`, `MULTIPLE_CHOICE`, `CHECKBOX`, `LINEAR_SCALE`, `GRID`, `DATE`, `DROPDOWN`.

**Response windows**: Use `set_publish_settings` with `response_window_mode` to control when the form accepts submissions. Times are RFC 3339.

**Batch updates**: `batch_update_form` accepts multiple update requests in a single call -- use it for multi-step form edits instead of many separate calls.
