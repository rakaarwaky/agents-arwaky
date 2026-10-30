"""Integration tests for modules/service — test component interactions."""
from __future__ import annotations


def test_service_manager_execution():
    """IT-SERVICE-001: ServiceControl/Inspect status routes through injected aggregate (mocked)."""
    from unittest.mock import MagicMock, patch

    from modules.service.src.capabilities_service_inspect import ServiceInspect
    from modules.service.src.capabilities_service_manager import ServiceControl
    from modules.shared.src.common import utility_service_daemon as usd
    from modules.shared.src.daemon.taxonomy_daemon_vo import (
        DaemonName,
        DaemonOp,
        DaemonOutcome,
        DaemonRequest,
        DaemonStatus,
    )

    _ = ServiceControl()
    inspect_cap = ServiceInspect()
    mock_agg = MagicMock()
    mock_agg.execute.return_value = DaemonOutcome(
        success=True,
        exit_code=0,
        status=DaemonStatus(
            container_state="running",
            service_state="running",
            api_ready=True,
            data_dir="/tmp",
            ok=True,
        ),
    )
    with patch.object(usd, "_DAEMON_AGGREGATE", mock_agg):
        result = inspect_cap.status()
        assert result is not None
        assert mock_agg.execute.call_count == 3
        mock_agg.execute.assert_any_call(
            DaemonRequest(DaemonOp("status"), name=DaemonName("omniroute"))
        )
        mock_agg.execute.assert_any_call(
            DaemonRequest(DaemonOp("status"), name=DaemonName("9router"))
        )
        mock_agg.execute.assert_any_call(
            DaemonRequest(DaemonOp("status"), name=DaemonName("anytype"))
        )


def test_service_drive_and_inspect_operations_fan_out_to_daemon_aggregate(capsys):
    """SVC-01: drive/status/logs/help exercise the aggregate seam, not systemd."""
    from unittest.mock import MagicMock

    from modules.service.src.capabilities_service_inspect import ServiceInspect
    from modules.service.src.capabilities_service_manager import ServiceControl
    from modules.shared.src.daemon.taxonomy_daemon_vo import (
        DaemonOutcome,
        DaemonRequest,
        DaemonStatus,
    )
    from modules.shared.src.service.taxonomy_service_vo import ServiceTarget

    aggregate = MagicMock()
    aggregate.execute.side_effect = lambda request: DaemonOutcome(
        success=True,
        exit_code=0,
        status=DaemonStatus("running", "active", True, "/tmp", True)
        if str(request.op) == "status"
        else None,
    )
    control = ServiceControl(aggregate)
    inspect_cap = ServiceInspect(aggregate)

    assert control.start(ServiceTarget("all")) == 0
    assert control.stop(ServiceTarget("all")) == 0
    assert control.restart(ServiceTarget("all")) == 0
    assert inspect_cap.status() == 0
    assert inspect_cap.logs(ServiceTarget("anytype")) == 0
    assert inspect_cap.help() == 0
    capsys.readouterr()

    requests = [call.args[0] for call in aggregate.execute.call_args_list]
    requested = {(str(request.op), str(request.name)) for request in requests}
    for op in ("start", "stop", "restart", "status"):
        assert (op, "omniroute") in requested
        assert (op, "9router") in requested
        assert (op, "anytype") in requested
    assert ("logs", "anytype") in requested
    assert all(isinstance(request, DaemonRequest) for request in requests)
    assert all(str(request.op) in {"start", "stop", "restart", "status", "logs"} for request in requests)
    assert all(isinstance(request.name, str) for request in requests)


def test_service_orchestrator_creation():
    """IT-SERVICE-002: ServiceOrchestrator can be created."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
    from modules.service.src.capabilities_service_inspect import ServiceInspect
    from modules.service.src.capabilities_service_manager import ServiceControl

    control = ServiceControl()
    inspect_cap = ServiceInspect()
    orch = ServiceOrchestrator(control, inspect_cap)
    assert orch is not None


def test_service_container_creation():
    """IT-SERVICE-003: ServiceContainer creates valid aggregate."""
    from modules.service.src.root_service_container import ServiceContainer

    container = ServiceContainer()
    aggregate = container.aggregate
    assert aggregate is not None
def test_service_container_wires_both_gateways():
    """IT-SERVICE-004: ServiceContainer routes 9router and omniroute units apart."""
    from unittest.mock import patch

    from modules.service.src.root_service_container import ServiceContainer
    from modules.shared.src.daemon.taxonomy_daemon_vo import (
        DaemonOp,
        DaemonRequest,
        DaemonUnit,
        ExitCode,
    )

    container = ServiceContainer()
    daemons = container._daemons
    with patch.object(daemons._managers["9router"], "unit_status", return_value=ExitCode(0)) as nine, \
            patch.object(daemons._managers["omniroute"], "unit_status", return_value=ExitCode(0)) as omni:
        daemons.execute(
            DaemonRequest(DaemonOp("unit_status"), unit=DaemonUnit("9router.service"))
        )
        daemons.execute(
            DaemonRequest(DaemonOp("unit_status"), unit=DaemonUnit("omniroute.service"))
        )
        nine.assert_called_once_with(DaemonUnit("9router.service"))
        omni.assert_called_once_with(DaemonUnit("omniroute.service"))

def test_service_target_9router_resolves_to_the_gateway():
    """IT-SERVICE-005: ServiceTarget('9router') drives only the 9router daemon."""
    from unittest.mock import MagicMock

    from modules.service.src.capabilities_service_manager import ServiceControl
    from modules.shared.src.daemon.taxonomy_daemon_vo import (
        DaemonOutcome,
        DaemonRequest,
    )
    from modules.shared.src.service.taxonomy_service_vo import (
        TARGET_9ROUTER,
        ServiceTarget,
    )

    aggregate = MagicMock()
    aggregate.execute.return_value = DaemonOutcome(success=True, exit_code=0)
    control = ServiceControl(aggregate)

    assert control.restart(ServiceTarget(str(TARGET_9ROUTER))) == 0

    requests = [call.args[0] for call in aggregate.execute.call_args_list]
    assert all(isinstance(request, DaemonRequest) for request in requests)
    assert [str(request.name) for request in requests] == ["9router"]
    assert [str(request.op) for request in requests] == ["restart"]
