"""Rules renderer capability (AES capabilities layer).

``aa skills rules --markdown`` prints the human-readable rendering of the
rule SSOT: one section per ``Rule``, whose body is the verbatim message
template the validator emits, plus the loader citation when one exists.
The rendering reads the taxonomy — it contains no rule text of its own —
so the generated ``_rules/skill-rules.md`` cannot disagree with the
executable rules.

Regenerate the committed artifact with::

    python3 -m modules.root_cli_entry skills rules --markdown \
        > modules/skills/_rules/skill-rules.md
"""

from __future__ import annotations

import re

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsRulesRendererProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import RulesDocument
from modules.shared.src.skills.taxonomy_skills_constant import (
    _DOCS_HEADER,
    _FIELD_HELP,
)
from modules.shared.src.skills.taxonomy_skills_rule_vo import (
    RULES,
    Rule,
)
from modules.shared.src.skills.taxonomy_skills_vo import RulesSummary

__all__ = ["SkillsRulesRenderer"]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsRulesRenderer(ISkillsRulesRendererProtocol):
    """Renders the rule SSOT as markdown and as a one-line-per-rule summary."""

    # ─── Block 2: Protocol Method Implementation ──────────────
    def render_markdown(self) -> RulesDocument:
        """The full rules document, byte-stable across runs."""
        lines = [_DOCS_HEADER.format(rule_count=len(RULES)), "## Rules", ""]

        for rule_obj in RULES:
            lines.extend(self._rule_section(rule_obj))

        # Byte-stable tail: exactly one trailing newline, so a shell redirect
        # reproduces the committed file exactly.
        markdown = "\n".join(lines).rstrip("\n") + "\n"
        return RulesDocument(
            markdown=markdown,
            summary=self.render_summary(),
            rule_count=len(RULES),
        )

    def render_summary(self) -> RulesSummary:
        """The compact one-line-per-rule form ``aa skills rules`` prints."""
        lines = [f"{len(RULES)} rules from taxonomy_skills_constant.py:", ""]
        for rule_obj in RULES:
            lines.append(
                f"- [{rule_obj.level.value}] {rule_obj.id} — {rule_obj.summary}"
            )
        return RulesSummary("\n".join(lines))

    # ─── Block 3: Dunder Methods, Factories & Helpers ──────────
    def _format_fields(self, detail: str) -> str:
        """The template's ``{}`` placeholders, as the doc's readers see them."""
        fields = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", detail)
        if not fields:
            return "constant message"
        ordered = sorted(set(fields))
        return ", ".join(f"`{name}` ({_FIELD_HELP[name]})" for name in ordered)

    def _rule_section(self, rule_obj: Rule) -> list[str]:
        """One rule = one ``###`` section; the detail is the verbatim message."""
        lines = [
            f"### `{rule_obj.id}` — {rule_obj.summary}",
            "",
            f"- **Rule ID:** `{rule_obj.id}`",
            f"- **Level:** `{rule_obj.level.value}`",
            f"- **Issue type:** `{rule_obj.issue.value}` (the string `validate` prints)",
            f"- **Fields:** {self._format_fields(rule_obj.detail_md)}",
            "",
            "**Message (verbatim from `ISSUE_MESSAGES`):**",
            "",
            f"> {rule_obj.detail_md}",
        ]

        if rule_obj.why:
            lines.extend(["", f"**Provenance:** {rule_obj.why}"])

        lines.append("")
        return lines