"""Agentic Orchestration Layer for BlenderMCP - AES Compliant.

All expert (router) classes live in src/agent/.
They depend on capabilities via constructor injection from the DI container.
"""

from typing import cast

from .agent_di_container import AgentDiContainer as AgentContainer
from .agent_di_container import get_container
from .generation_expert_orchestrator import GenerationExpertOrchestrator as GenerationExpert
from .refinement_expert_orchestrator import RefinementExpertOrchestrator as RefinementExpert
from .search_expert_orchestrator import SearchExpertOrchestrator as AssetExpert
from .setup_expert_orchestrator import SetupExpertOrchestrator as SceneExpert
from .workflow_agent_orchestrator import WorkflowAgentOrchestrator as TextToSceneOrchestrator


def get_scene_expert() -> SceneExpert:
    """Get SceneExpert from the global DI container."""
    return cast(SceneExpert, get_container().scene_expert)


def get_asset_expert() -> AssetExpert:
    """Get AssetExpert from the global DI container."""
    return cast(AssetExpert, get_container().asset_expert)


def get_generation_expert() -> GenerationExpert:
    """Get GenerationExpert from the global DI container."""
    return cast(GenerationExpert, get_container().generation_expert)


def get_refinement_expert() -> RefinementExpert:
    """Get RefinementExpert from the global DI container."""
    return cast(RefinementExpert, get_container().refinement_expert)


def get_orchestrator() -> TextToSceneOrchestrator:
    """Get the main TextToSceneOrchestrator from the global DI container."""
    return cast(TextToSceneOrchestrator, get_container().workflow_orchestrator)


def get_all_experts() -> dict:
    """Return dict of all experts (routers) from the container."""
    container = get_container()
    return {
        "tool_scene_ops": container.scene_expert,
        "asset": container.asset_expert,
        "generation": container.generation_expert,
        "refinement": container.refinement_expert,
    }


__all__ = [
    "SceneExpert",
    "AssetExpert",
    "GenerationExpert",
    "RefinementExpert",
    "TextToSceneOrchestrator",
    "AgentContainer",
    "get_container",
    "get_scene_expert",
    "get_asset_expert",
    "get_generation_expert",
    "get_refinement_expert",
    "get_orchestrator",
    "get_all_experts",
]
