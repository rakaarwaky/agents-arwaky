# Google Slides — Tools Reference

MCP tools for reading and managing Google Slides presentations. All tools require `user_google_email` (string, required). The `presentation_id` parameter accepts a presentation ID or a full Google Slides URL.

## Contents
- Reading & Thumbnails: get_presentation, get_page, get_page_thumbnail
- Create & Update: create_presentation, batch_update_presentation
- Comments: list_presentation_comments, manage_presentation_comment
- Tips

---

## Reading & Thumbnails

### get_presentation
Get the full slide list of a presentation.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| presentation_id | string | yes | | Slides ID or URL |
| include_speaker_notes | boolean | no | false | Fetch and list the speaker notes text for every slide |

### get_page
Get the contents of a specific slide page (shape inventory, text, layout).

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| presentation_id | string | yes | | Slides ID or URL |
| page_id | string | yes | | Page ID |

### get_page_thumbnail
Get the thumbnail image of a specific slide.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| presentation_id | string | yes | | Slides ID or URL |
| page_id | string | yes | | Page ID |

---

## Create & Update

### create_presentation
Create a new Google Slides presentation. Creates an empty presentation with a single blank slide and returns its ID.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| title | string | yes | | Presentation title |

### batch_update_presentation
Batch update a Google Slides presentation with a list of update requests.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| presentation_id | string | yes | | Slides ID or URL |
| update_requests | array or string | yes | | Update requests. Each element is a dict with a `request_type` key and type-specific fields. Accepts a JSON string or a list. See request types below |

**Update request types:**

| request_type | Required fields | Notes |
|--------------|-----------------|-------|
| `createSlide` | `insertionIndex`, `object` | Create a slide. `object` must contain `objectId` and `pageType` (`BLANK`, `TITLE`, `TITLE_AND_BODY`) |
| `deleteObject` | `objectId` | Delete a shape or slide by object ID |
| `updateSlide` | `objectId`, `object` | Replace a slide's properties (e.g. page type, layout) |
| `updateTextStyle` | `objectId`, `style` | Update text style for an object or sub-range. `style` supports `size` (float, points), `fontFamily`, `foregroundColor`/`backgroundColor` (hex or RGB dicts), `bold`/`italic`/`underline`/`strikethrough` (bool) |
| `replaceAllText` | `replacementTextElement`, `textToFind` | Find and replace text throughout the presentation. `replacementTextElement` supports `textRun` with `content`, or `shape` with `shapeId` and `textElement` |
| `duplicateSlide` | `objectId` | Duplicate an existing slide |

Colors can be passed as hex strings (e.g. `"#FF0000"`) or RGB objects (e.g. `{"color": {"rgb": {"red": 1, "green": 0, "blue": 0}}}`).

---

## Comments

### list_presentation_comments
List all comments on a presentation.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| presentation_id | string | yes | | Slides ID or URL |

### manage_presentation_comment
Create, reply to, or resolve a comment on a presentation.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| presentation_id | string | yes | | Slides ID or URL |
| action | string | yes | | `create`, `reply`, or `resolve` |
| comment_content | string | no | | Required for `create` and `reply` |
| comment_id | string | no | | Required for `reply` and `resolve` |

---

## Tips

**Reading workflow**: Use `get_presentation` to list all slides, then `get_page` for specific slide content and `get_page_thumbnail` for visual inspection.

**Batch updates**: `batch_update_presentation` accepts multiple update requests in a single call -- use it for multi-step edits instead of many separate calls.

**Speaker notes**: Set `include_speaker_notes=true` in `get_presentation` to retrieve speaker notes text for all slides in one response.

**Object IDs**: Most update requests target objects by `objectId` (shape, slide, text run). Discover these by first calling `get_presentation` or `get_page`.
