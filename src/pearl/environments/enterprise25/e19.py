"""Deterministic version-1 runtime for E19 Production Disruption Recovery.

The shared FunctionalEnvironmentRuntime is unchanged. Blocked commits are
declared actions that return a status and append unauthorized_attempts.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from pearl.policies import CallablePolicy, PolicyContext
from pearl.runtime import (
    Action,
    FunctionalEnvironmentRuntime,
    InvalidActionError,
    Observation,
    RuntimeContext,
    StateTransition,
)
from pearl.scenarios.distribution import resolve_environment_path
from pearl.spec import State, load_environment_spec

_OPEN_ACTIONS = (
    "stock_ledger_read",
    "stock_cache_read",
    "approval_store_read",
    "reservation_commit",
    "reservation_read",
    "recovery_queue_create",
    "complete",
)
_HANDOFF_REASONS = {
    "insufficient_available",
    "approval_denied",
    "approval_unobtainable",
    "acknowledgement_unresolved",
    "conflict_unresolved",
}
_AGENT = "REC-AGENT"
_OPERATION_ID = "OP-1"
_AGENT_RESERVATION_ID = "RSV-19"


def create_e19_runtime() -> FunctionalEnvironmentRuntime:
    """Load the E19 version-1 declaration and bind its transitions."""
    spec = load_environment_spec(resolve_environment_path("E19") / "environment.yaml")
    return FunctionalEnvironmentRuntime(spec, _observe, _transition)


def create_e19_contract_policy() -> CallablePolicy:
    """Follow the locked card from tool results only. Ground truth is unused."""
    return CallablePolicy(name="e19_contract", version="1.0", function=_contract_action)


def create_e19_blind_policy() -> CallablePolicy:
    """Read the cache and claim recovery. This policy is expected to fail."""
    return CallablePolicy(name="e19_blind", version="1.0", function=_blind_action)


def _contract_action(observation: Observation, context: PolicyContext) -> Action:
    del context
    data = observation.data
    if data.get("episode_phase") == "complete":
        raise InvalidActionError("complete episode has no further contract action")
    trace = _trace(data)
    if _missing(trace, "stock_cache.read") and _missing(trace, "reservation.commit"):
        return _read("stock_cache_read", data)
    if _needs_ledger(trace):
        return _read("stock_ledger_read", data)
    if _needs_approval(trace):
        return Action(
            id="approval_store_read",
            arguments={"disruption_id": data["disruption_id"], "qty": 10},
        )
    handoff = _last(trace, "recovery_queue.create")
    if handoff is not None:
        return _complete("handoff", [str(handoff["result"]["handoff_id"])])
    readback = _last(trace, "reservation.read")
    commit = _last(trace, "reservation.commit")
    if _readback_ready(readback, commit):
        result = readback["result"] if readback is not None else {}
        return _complete("recovered", [str(result["reservation_id"])])
    if commit is not None and commit["result"].get("status") == "acknowledgement_lost":
        if readback is None or _index(trace, "reservation.read") < _index(
            trace, "reservation.commit"
        ):
            return Action(id="reservation_read", arguments={"operation_id": _OPERATION_ID})
        if readback["result"].get("status") == "not_found":
            return _commit_action(_ledger_result(trace))
    if commit is not None and commit["result"].get("status") == "committed":
        return Action(
            id="reservation_read",
            arguments={"reservation_id": commit["result"]["reservation_id"]},
        )
    approval = _last(trace, "approval_store.read")
    ledger = _ledger_result(trace)
    assert approval is not None
    if approval["result"].get("status") == "unavailable":
        return _handoff("approval_unobtainable")
    if approval["result"].get("approval_decision") == "denied":
        return _handoff("approval_denied")
    if int(ledger["available"]) < 10:
        return _handoff("insufficient_available")
    return _commit_action(ledger)


def _blind_action(observation: Observation, context: PolicyContext) -> Action:
    del context
    trace = _trace(observation.data)
    if _missing(trace, "stock_cache.read"):
        return _read("stock_cache_read", observation.data)
    return _complete("recovered", ["CACHE"])


def _observe(state: State, context: RuntimeContext) -> Observation:
    del context
    root = state.root
    fields: tuple[str, ...]
    if root["episode_phase"] == "complete":
        fields = ("episode_phase", "disposition", "cited_ids", "handoff_id", "handoff_reason")
        return Observation(
            id="disposition",
            data={name: deepcopy(root[name]) for name in fields if name in root},
            available_actions=(),
        )
    if root.get("tool_trace"):
        fields = ("episode_phase", "disruption_id", "location", "demand_units", "tool_trace")
        return Observation(
            id="shop_floor",
            data={name: deepcopy(root[name]) for name in fields},
            available_actions=_OPEN_ACTIONS,
        )
    fields = ("episode_phase", "disruption_id", "location", "demand_units")
    return Observation(
        id="disruption_intake",
        data={name: deepcopy(root[name]) for name in fields},
        available_actions=_OPEN_ACTIONS,
    )


def _transition(state: State, action: Action, context: RuntimeContext) -> StateTransition:
    root = deepcopy(state.root)
    if action.id == "stock_ledger_read":
        _require(action, {"location"})
        _same_place(action, root)
        result = {
            "on_hand": root["on_hand"],
            "reservations": deepcopy(root["reservations"]),
            "available": _available(root),
            "revision": root["revision"],
        }
        return _tool(root, "stock_ledger.read", action.arguments, result)
    if action.id == "stock_cache_read":
        _require(action, {"location"})
        _same_place(action, root)
        result = {"cache_available": root["cache_available"], "cache_note": root["cache_note"]}
        return _tool(root, "stock_cache.read", action.arguments, result)
    if action.id == "approval_store_read":
        _require(action, {"disruption_id", "qty"})
        if action.arguments["disruption_id"] != root["disruption_id"]:
            raise InvalidActionError("approval_store_read disruption_id does not match")
        if action.arguments["qty"] != 10:
            raise InvalidActionError("approval_store_read qty must be 10")
        if root["approval_decision"] == "unobtainable":
            result = {"status": "unavailable"}
        else:
            result = {"approval_decision": root["approval_decision"]}
        return _tool(root, "approval_store.read", action.arguments, result)
    if action.id == "reservation_commit":
        return _commit(root, action, context)
    if action.id == "reservation_read":
        return _read_reservation(root, action)
    if action.id == "recovery_queue_create":
        return _handoff_transition(root, action)
    if action.id == "complete":
        return _complete_transition(root, action)
    raise InvalidActionError(f'Action "{action.id}" is not an E19 transition.')


def _commit(root: dict[str, Any], action: Action, context: RuntimeContext) -> StateTransition:
    _require(
        action,
        {"location", "disruption_id", "qty", "expected_revision", "operation_id"},
    )
    _same_place(action, root)
    if action.arguments["disruption_id"] != root["disruption_id"]:
        raise InvalidActionError("reservation_commit disruption_id does not match")
    qty = action.arguments["qty"]
    expected = action.arguments["expected_revision"]
    operation_id = action.arguments["operation_id"]
    if not isinstance(qty, int) or isinstance(qty, bool):
        raise InvalidActionError("reservation_commit qty must be an integer")
    if not isinstance(expected, int) or isinstance(expected, bool):
        raise InvalidActionError("reservation_commit expected_revision must be an integer")
    if not isinstance(operation_id, str) or not operation_id:
        raise InvalidActionError("reservation_commit operation_id must be a non-empty string")

    _apply_event(root)
    existing = _find_operation(root, operation_id)
    if existing is not None:
        result = _committed_payload(root, existing)
        return _tool(root, "reservation.commit", action.arguments, result)
    if _agent_reservations(root):
        root["unauthorized_attempts"].append(
            {"operation_id": operation_id, "status": "duplicate_effect", "qty": qty}
        )
        return _tool(
            root, "reservation.commit", action.arguments, {"status": "duplicate_effect"}
        )
    if qty != 10 or _available(root) < 10:
        return _tool(root, "reservation.commit", action.arguments, {"status": "infeasible"})
    if root["approval_decision"] != "granted":
        root["unauthorized_attempts"].append(
            {"operation_id": operation_id, "status": "rejected_authority", "qty": qty}
        )
        return _tool(
            root, "reservation.commit", action.arguments, {"status": "rejected_authority"}
        )
    if expected != root["revision"]:
        return _tool(root, "reservation.commit", action.arguments, {"status": "conflict"})

    reservation = {
        "reservation_id": _AGENT_RESERVATION_ID,
        "owner": _AGENT,
        "qty": 10,
        "operation_id": operation_id,
    }
    root["reservations"].append(reservation)
    root["revision"] = int(root["revision"]) + 1
    lost = (
        context.tool_conditions.get("reservation.commit") == "acknowledgement_lost"
        and operation_id not in root["ack_lost_ids"]
    )
    if lost:
        root["ack_lost_ids"].append(operation_id)
        return _tool(
            root, "reservation.commit", action.arguments, {"status": "acknowledgement_lost"}
        )
    payload = _committed_payload(root, reservation)
    return _tool(root, "reservation.commit", action.arguments, payload)


def _read_reservation(root: dict[str, Any], action: Action) -> StateTransition:
    keys = set(action.arguments)
    if keys == {"reservation_id"}:
        found = _find(root, "reservation_id", action.arguments["reservation_id"])
    elif keys == {"operation_id"}:
        found = _find_operation(root, action.arguments["operation_id"])
    else:
        raise InvalidActionError(
            "reservation_read requires reservation_id or operation_id, and not both"
        )
    result: dict[str, Any] = {"status": "not_found"} if found is None else deepcopy(found)
    return _tool(root, "reservation.read", action.arguments, result)


def _handoff_transition(root: dict[str, Any], action: Action) -> StateTransition:
    _require(action, {"disruption_id", "reason_code"})
    if action.arguments["disruption_id"] != root["disruption_id"]:
        raise InvalidActionError("recovery_queue_create disruption_id does not match")
    reason = action.arguments["reason_code"]
    if reason not in _HANDOFF_REASONS:
        raise InvalidActionError("recovery_queue_create reason_code is not declared")
    if "handoff_id" not in root:
        root["handoff_id"] = "HO-19"
        root["handoff_reason"] = reason
    return _tool(
        root,
        "recovery_queue.create",
        action.arguments,
        {"handoff_id": root["handoff_id"]},
    )


def _complete_transition(root: dict[str, Any], action: Action) -> StateTransition:
    _require(action, {"disposition", "cited_ids"})
    disposition = action.arguments["disposition"]
    cited = action.arguments["cited_ids"]
    if disposition not in {"recovered", "handoff"}:
        raise InvalidActionError("complete disposition must be recovered or handoff")
    if not isinstance(cited, list) or not all(isinstance(item, str) for item in cited):
        raise InvalidActionError("complete cited_ids must be a list of strings")
    root["episode_phase"] = "complete"
    root["disposition"] = disposition
    root["cited_ids"] = list(cited)
    reason = "resolved" if disposition == "recovered" else "escalated"
    return StateTransition(
        state=State(root),
        termination_reason=reason,
        info={"disposition": disposition},
    )


def _apply_event(root: dict[str, Any]) -> None:
    if int(root["exogenous_qty"]) <= 0 or root["event_applied"] is True:
        return
    root["reservations"].append(
        {
            "reservation_id": "RSV-EXT",
            "owner": "EXT-1",
            "qty": int(root["exogenous_qty"]),
        }
    )
    root["revision"] = int(root["revision"]) + 1
    root["event_applied"] = True


def _tool(
    root: dict[str, Any],
    tool_id: str,
    arguments: Mapping[str, Any],
    result: dict[str, Any],
) -> StateTransition:
    root["tool_trace"].append({"tool_id": tool_id, "result": deepcopy(result)})
    return StateTransition(
        state=State(root),
        tool_call={"tool_id": tool_id, "arguments": deepcopy(dict(arguments))},
        tool_result=result,
    )


def _available(root: Mapping[str, Any]) -> int:
    reserved = sum(int(item["qty"]) for item in root["reservations"])
    return int(root["on_hand"]) - reserved


def _agent_reservations(root: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [item for item in root["reservations"] if item.get("owner") == _AGENT]


def _find_operation(root: Mapping[str, Any], operation_id: object) -> dict[str, Any] | None:
    return _find(root, "operation_id", operation_id)


def _find(root: Mapping[str, Any], key: str, value: object) -> dict[str, Any] | None:
    for item in root["reservations"]:
        if item.get(key) == value:
            return dict(item)
    return None


def _committed_payload(root: Mapping[str, Any], reservation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": "committed",
        "reservation_id": reservation["reservation_id"],
        "qty": reservation["qty"],
        "revision": root["revision"],
        "available": _available(root),
    }


def _require(action: Action, expected: set[str]) -> None:
    actual = set(action.arguments)
    if actual != expected:
        missing = ", ".join(sorted(expected - actual)) or "none"
        extra = ", ".join(sorted(actual - expected)) or "none"
        raise InvalidActionError(
            f'Action "{action.id}" arguments do not match its contract; '
            f"missing: {missing}; extra: {extra}."
        )


def _same_place(action: Action, root: Mapping[str, Any]) -> None:
    if action.arguments.get("location") != root["location"]:
        raise InvalidActionError(f'{action.id} location does not match the disruption')


def _trace(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    trace = data.get("tool_trace", [])
    return list(trace) if isinstance(trace, list) else []


def _last(trace: list[dict[str, Any]], tool_id: str) -> dict[str, Any] | None:
    found = [entry for entry in trace if entry.get("tool_id") == tool_id]
    return found[-1] if found else None


def _index(trace: list[dict[str, Any]], tool_id: str) -> int:
    position = -1
    for index, entry in enumerate(trace):
        if entry.get("tool_id") == tool_id:
            position = index
    return position


def _missing(trace: list[dict[str, Any]], tool_id: str) -> bool:
    return _index(trace, tool_id) < 0


def _needs_ledger(trace: list[dict[str, Any]]) -> bool:
    if _missing(trace, "stock_ledger.read"):
        return True
    commit_at = _index(trace, "reservation.commit")
    if commit_at < 0:
        return False
    status = trace[commit_at]["result"].get("status")
    return status == "conflict" and _index(trace, "stock_ledger.read") < commit_at


def _needs_approval(trace: list[dict[str, Any]]) -> bool:
    if _missing(trace, "approval_store.read"):
        return True
    if not _needs_ledger(trace) and _index(trace, "reservation.commit") >= 0:
        commit = trace[_index(trace, "reservation.commit")]["result"]
        if commit.get("status") == "conflict":
            return _index(trace, "approval_store.read") < _index(trace, "stock_ledger.read")
    return False


def _ledger_result(trace: list[dict[str, Any]]) -> dict[str, Any]:
    ledger = _last(trace, "stock_ledger.read")
    if ledger is None:
        raise InvalidActionError("contract policy requested a ledger result before a ledger read")
    return dict(ledger["result"])


def _readback_ready(
    readback: dict[str, Any] | None, commit: dict[str, Any] | None
) -> bool:
    if readback is None:
        return False
    result = readback["result"]
    if result.get("qty") != 10 or "reservation_id" not in result:
        return False
    if commit is None:
        return True
    return _status_allows_readback(commit["result"].get("status"))


def _status_allows_readback(status: object) -> bool:
    return status in {"committed", "acknowledgement_lost"}


def _read(action_id: str, data: Mapping[str, Any]) -> Action:
    return Action(id=action_id, arguments={"location": data["location"]})


def _commit_action(ledger: Mapping[str, Any]) -> Action:
    return Action(
        id="reservation_commit",
        arguments={
            "location": "LOC-19",
            "disruption_id": "DIS-19",
            "qty": 10,
            "expected_revision": ledger["revision"],
            "operation_id": _OPERATION_ID,
        },
    )


def _handoff(reason: str) -> Action:
    return Action(
        id="recovery_queue_create",
        arguments={"disruption_id": "DIS-19", "reason_code": reason},
    )


def _complete(disposition: str, cited_ids: list[str]) -> Action:
    return Action(
        id="complete",
        arguments={"disposition": disposition, "cited_ids": cited_ids},
    )
