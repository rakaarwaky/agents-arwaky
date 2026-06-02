"""
Core Agent Orchestrator - Low-level action dispatch route.
Handles basic code execution and action routing.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from contract import AgentDiContainerAggregate, CoreAgentOrchestratorAggregate, GenerationProtocol
from taxonomy import (
    ActionName,
    Details,
    DomainRef,
    FormatRef,
    JobId,
    ObjectName,
    Prompt,
    ProviderName,
    SectionRef,
    SkillName,
    SuccessFlag,
)

logger = logging.getLogger("BlenderMCPServer.CoreAgent")


class CoreAgentOrchestrator(CoreAgentOrchestratorAggregate):
    """Core agent orchestrator (Palais) coordinating capabilities and infrastructure."""

    _success_ref: SuccessFlag = SuccessFlag(True)
    _contract_name: ObjectName = ObjectName("CoreAgentOrchestrator")

    def __init__(self, container: AgentDiContainerAggregate) -> None:
        self._initialized = SuccessFlag(True)
        self._container = container

    async def execute_code(self, request: object) -> dict[str, object]:
        """Execute arbitrary Python code in Blender (low-level primitive)."""
        code = request.code if hasattr(request, "code") else str(request)
        executor = cast(Any, self._container).code_executor
        result = await executor.execute_blender_code(code)
        return {"success": True, "result": result}

    async def execute_action(self, action: ActionName, args: Details | None = None) -> Prompt:
        """Execute an action via the capabilities layer."""
        result = await self._container.action_execute_capability.execute(action, args)
        return Prompt(result)

    def list_commands(self, domain: DomainRef | None = None, format: FormatRef | None = None) -> Prompt:
        """List available actions from the catalog."""
        import json

        catalog_port = self._container.command_catalog
        raw_format = str(format) if format is not None else "detailed"

        # Normalize: None, empty string, and "all" all mean "list everything"
        raw_domain = str(domain) if domain is not None else ""
        use_filter = domain is not None and raw_domain not in ("", "all")

        if use_filter and domain is not None:
            catalog = catalog_port.filter_by_domain(domain)
        else:
            actions = catalog_port.list_actions()
            catalog = {}
            for a in actions:
                spec = catalog_port.get_command_spec(a)
                if spec is not None:
                    catalog[a] = spec

        if raw_format == "summary":
            summary = {
                k: {"description": v.get("description", ""), "domain": v.get("domain", "")} for k, v in catalog.items()
            }
            return Prompt(json.dumps(summary, indent=2))

        return Prompt(json.dumps(catalog, indent=2))

    async def check_status(self, provider: ProviderName, job_id: JobId) -> Prompt:
        """Check status of a background generation job."""
        import json

        raw_provider = str(provider)
        raw_job_id = str(job_id)

        gen_cap = cast(GenerationProtocol, cast(Any, self._container).generate_ai_capability)
        status = await gen_cap.check_status(provider, job_id)

        result_dict = {
            "success": True,
            "provider": raw_provider,
            "job_id": raw_job_id,
            "status": status.status,
            "message": "Status retrieved successfully",
        }
        return Prompt(json.dumps(result_dict, indent=2))

    def health_check(self) -> Prompt:
        """Check system health status."""
        import json

        from .system_utils_coordinator import health_check as _health_check

        return Prompt(json.dumps(_health_check(), indent=2))

    def read_skill_context(self, _skill_name: SkillName, section: SectionRef | None = None) -> Prompt:
        """Read system skill documentation (SKILL.md) directly from project root."""
        import json
        import os

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        skill_path = os.path.join(project_root, "SKILL.md")

        if not os.path.isfile(skill_path):
            return Prompt(json.dumps({"error": f"SKILL.md not found in project root: {project_root}"}, indent=2))

        with open(skill_path) as f:
            content = f.read()

        raw_section = str(section) if section is not None else ""
        if raw_section:
            import re

            pattern = rf"##\s+(?:Section:\s*)?{re.escape(raw_section)}\n.*?(?=\n## |\Z)"
            match = re.search(pattern, content, re.DOTALL)
            content = match.group(0).strip() if match else f"Section '{raw_section}' not found in SKILL.md"

        return Prompt(content)
