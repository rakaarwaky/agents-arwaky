"""Golden fixtures for the 13 issue types.

One crafted tree per issue type: ``fixtures/<issue-type>/`` contains a
minimal skills root (one or two category directories, each a folder that
holds either a ``DESCRIPTION.md`` and/or a skill directory with a
``SKILL.md``).

The tree for each issue type is constructed so the target issue is the
ONLY one the validator reports — that is what makes each fixture
golden: a regression in any other check shows up as an extra or missing
issue, not just a wrong message.
"""

FIXTURES = {
    "name-mismatch": "cat-a/good-skill",
    "invalid-skill-name": "cat-a/bad--name",
    "missing-description": "cat-a/good-skill",
    "invalid-description-characters": "cat-a/good-skill",
    "description-too-long": "cat-a/good-skill",
    "nested-skill-md": "cat-a/good-skill",
    "invalid-placement": "cat-a/SKILL.md",
    "too-deep": "cat-a/deep/nest/SKILL.md",
    "duplicate-skill-name": "cat-a/good-skill, cat-b/good-skill",
    "duplicate-description": "cat-a/alpha-skill, cat-b/beta-skill",
    "missing-category-description": "cat-a (no DESCRIPTION.md)",
    "empty-category-description": "cat-a (DESCRIPTION.md with no description key)",
    "empty-category": "cat-a (no skills)",
}

Note on `empty-category-description`: the fixture's `DESCRIPTION.md` has
frontmatter with no `description` key at all — not a `description:` key
with an empty value. An empty value parses to `None` under PyYAML, which
`clean_one_line` renders as the truthy string `"None"`, suppressing the
issue. The key-absent form is load-bearing: it is the shape that actually
triggers the issue.
