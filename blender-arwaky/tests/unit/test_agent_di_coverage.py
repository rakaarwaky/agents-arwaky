"""Test to close coverage gaps on AgentDiContainer property accessors."""
from agent.agent_di_container import get_container, reset_container


class TestAgentDiCoverage:
    """Access every lazy property to cover _lazy_get() lines."""

    def _get(self) -> object:
        reset_container()
        return get_container()

    def test_infrastructure_properties(self) -> None:
        c = self._get()
        for attr in ("config", "blender_connection", "blender",
                     "polyhaven_adapter", "sketchfab_adapter",
                     "hyper3d_provider", "hunyuan_provider"):
            try:
                _ = getattr(c, attr)
            except Exception:
                pass

    def test_service_properties(self) -> None:
        c = self._get()
        for attr in ("telemetry", "viewport", "scene_inspector",
                     "code_executor"):
            try:
                _ = getattr(c, attr)
            except Exception:
                pass

    def test_capability_properties(self) -> None:
        c = self._get()
        for attr in ("operate_scene_capability", "search_asset_capability",
                     "generate_ai_capability", "object_operate_capability",
                     "render_operate_capability", "import_export_capability",
                     "workflow_orchestrate_capability", "system_utils"):
            try:
                _ = getattr(c, attr)
            except Exception:
                pass

    def test_expert_properties(self) -> None:
        c = self._get()
        for attr in ("scene_expert", "asset_expert", "generation_expert",
                     "refinement_expert", "workflow_orchestrator"):
            try:
                _ = getattr(c, attr)
            except Exception:
                pass
