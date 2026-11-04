# Google Contacts — Tools Reference

MCP tools for searching and managing Google Contacts. All tools require `user_google_email` (string, required).

## Contents
- Search & List: search_contacts, list_contacts
- Get & Manage: get_contact, manage_contact, manage_contacts_batch
- Groups: list_contact_groups, get_contact_group, manage_contact_group
- Tips

---

## Search & List

### search_contacts
Search contacts by name, email, or phone number. Results are capped at 50 per call; paginate with `start_index` to retrieve larger result sets.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| query | string | yes | | Search query (name, email, phone) |
| start_index | integer | no | 0 | 0-based offset for pagination. Results are capped at 50 per call |

### list_contacts
List all contacts in the user's account.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| start_index | integer | no | 0 | 0-based offset for pagination. Results are capped at 50 per call |

---

## Get & Manage

### get_contact
Retrieve a single contact by resource name. Accepts a full resource name (`people/<resource_id>`), a raw resource ID, or a URL.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| person_name | string | yes | | Resource name, ID, or URL of the contact |
| read_mask | string | no | | Comma-separated fields to include (e.g. `names,emailAddresses,phoneNumbers`). Omit for standard fields |

### manage_contact
Create, update, or delete a contact.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| action | string | yes | | "create", "update", or "delete" |
| person_name | string | for update/delete | | Resource name, ID, or URL |
| contact_data | object | for create/update | | Contact fields (see below) |

**contact_data format:**
```json
{
  "names": [{"displayName": "Alice", "familyName": "Smith", "givenName": "Alice"}],
  "emailAddresses": [{"value": "alice@example.com", "type": "work"}],
  "phoneNumbers": [{"value": "+61412345678", "type": "mobile"}],
  "organizations": [{"name": "Acme Inc", "title": "Engineer", "department": "Engineering"}]
}
```

Phone `type` values: `mobile`, `home`, `work`, `main`, `fax`, `other`.

### manage_contacts_batch
Batch create, update, or delete multiple contacts in a single call. Uses `action: "create"`, `"update"`, or `"delete"`.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| action | string | yes | | "create", "update", or "delete" |
| contacts | array | yes | | Array of `person_name` + `contact_data` objects. For update/delete, each entry needs `person_name` |

---

## Groups

### list_contact_groups
List contact groups the user belongs to or owns.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |

### get_contact_group
Get a specific contact group by resource name.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| resource_name | string | yes | | Contact group resource name |

### manage_contact_group
Manage a contact group: rename it, or add and remove members.

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| user_google_email | string | yes | | |
| resource_name | string | yes | | Contact group resource name |
| new_name | string | no | | Rename the group |
| add_members | array | no | | Array of resource names to add as members |
| remove_members | array | no | | Array of resource names to remove from the group |

All of `new_name`, `add_members`, and `remove_members` are optional -- omit everything to get current group state. Members can be contact resource names or a special `"me"` value for the account's own contact entry.

---

## Tips

**Reading contacts**: Use `list_contacts` to get all contacts or `search_contacts` to find specific ones. Read `list_contacts` results first, then call `get_contact` to fetch full details for specific contacts.

**Contact resource names**: The People API uses resource names like `people/AbCd...`. When calling `get_contact` or `manage_contact`, you can pass the full resource name, just the ID, or a URL.

**Contact types**: In `contact_data`, `type` fields support values like `work`, `home`, `mobile`, `main`, `other`. Phone `type` values include `mobile`, `home`, `work`, `main`, `fax`, `other`.

**Group membership**: `manage_contact_group` uses `add_members` and `remove_members` as arrays of resource names. `"me"` refers to the account's own contact entry.
