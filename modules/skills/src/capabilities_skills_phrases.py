"""Skills phrases capability (AES capabilities layer).

Ports the repeated-prompt / repeated-instruction-line mining logic out of
the retired ``skills/skill-authoring/_trace-pipeline/scripts/collect_sessions.py``
into the ``IPhrasesProtocol`` seam.

Reads the session records ``tracker`` wrote into ``run_dir`` (a *file*
dependency sequenced by the agent — ``phrases`` does NOT import
``capabilities_skills_tracker``). Mines:

* repeated exact prompts (distinct-session threshold)
* prompt stems (first 12 words)
* repeated instruction lines

Single-turn automation exclusion is kept (a session whose single normalized
turn repeats in 3+ sessions is skipped). Counts are distinct sessions.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict

from modules.shared.src.common.utility_skill_pack import SLASH_RE, WORD_RE
from modules.shared.src.skills.contract_skills_protocol import IPhrasesProtocol
from modules.shared.src.skills.taxonomy_skills_authoring_vo import PhrasesReport
from modules.shared.src.skills.taxonomy_skills_vo import PhraseRow

__all__ = ["SkillsPhrases", "normalize"]

_SLASH_ONLY = re.compile(r"/[a-z0-9-]+(\s+\S+){0,3}")


def normalize(s: str) -> str:
    return WORD_RE.sub(" ", s.strip().lower())


_EXACT_MIN_SESSIONS = 2
_STEM_MIN_SESSIONS = 3
_LINE_MIN_SESSIONS = 3
_TOP = 60
_MIN_PHRASE_LEN = 12
_MIN_LINE_WORDS = 5
_MIN_LINE_CHARS = 24


class SkillsPhrases(IPhrasesProtocol):
    """Mine repeated exact prompts, prompt stems, and instruction lines."""

    def build_phrases(self, grok_home: str, run_dir: str) -> PhrasesReport:
        """Read session records from ``run_dir`` and return repeated phrases.

        Counts are distinct sessions; single-turn sessions repeated 3+ times
        are excluded as likely automation.
        """
        sessions_dir = os.path.join(run_dir, "sessions")
        exact: dict[str, list[str]] = defaultdict(list)
        stems: dict[str, list[str]] = defaultdict(list)
        lines: dict[str, set[str]] = defaultdict(set)

        if os.path.isdir(sessions_dir):
            for name in sorted(os.listdir(sessions_dir)):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(sessions_dir, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        rec = json.load(f)
                except (OSError, ValueError):
                    continue
                rid = rec.get("id") or ""
                # sessions flagged repeated_single_turn are automation — excluded
                if rec.get("repeated_single_turn"):
                    continue
                for t in rec.get("turns") or []:
                    n = normalize(t)
                    if len(n) < _MIN_PHRASE_LEN:
                        continue
                    stripped = t.strip()
                    if SLASH_RE.fullmatch(stripped) or _SLASH_ONLY.fullmatch(n):
                        continue
                    exact[n].append(rid)
                    words = n.split(" ")
                    if len(words) >= 6:
                        stems[" ".join(words[:12])].append(rid)
                    for ln in t.splitlines():
                        ln_n = normalize(ln)
                        if (
                            len(ln_n.split(" ")) >= _MIN_LINE_WORDS
                            and len(ln_n) >= _MIN_LINE_CHARS
                        ):
                            lines[ln_n].add(rid)

        exact_prompts = self._top(exact, _EXACT_MIN_SESSIONS, "phrase")
        prompt_stems = self._top(stems, _STEM_MIN_SESSIONS, "stem")
        instruction_lines = self._top(lines, _LINE_MIN_SESSIONS, "line")

        return PhrasesReport(
            exact_prompts=tuple(exact_prompts),
            stems=tuple(prompt_stems),
            repeated_instruction_lines=tuple(instruction_lines),
        )

    @staticmethod
    def _top(data: dict, min_count: int, key_name: str) -> tuple[PhraseRow, ...]:
        rows: list[PhraseRow] = []
        for k, ids in data.items():
            id_list = list(ids)
            sessions = len(set(id_list))
            if sessions >= min_count:
                rows.append(
                    PhraseRow(
                        phrase=k[:400],
                        sessions=sessions,
                        occurrences=len(id_list),
                        session_ids=tuple(sorted(set(id_list))[:8]),
                    )
                )
        rows.sort(key=lambda x: (-x.sessions, -x.occurrences, x.phrase))
        return tuple(rows[:_TOP])
