import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from agent_runtime import (
    AgentError,
    CalculatorTool,
    MaxStepsExceededError,
    MemoryStoreTool,
    ReActAgent,
    ScriptedPlanner,
    ToolRegistry,
    UnknownToolError,
)


@pytest.fixture
def registry():
    return ToolRegistry([CalculatorTool(), MemoryStoreTool()])


def test_registry_executes_calculator(registry):
    result = registry.execute("calculator", {"op": "add", "a": 2, "b": 3})
    assert result.success
    assert result.output == 5.0


def test_unknown_tool_raises(registry):
    with pytest.raises(UnknownToolError):
        registry.execute("teleport", {})


def test_tool_failure_captured_not_raised(registry):
    result = registry.execute("calculator", {"op": "divide", "a": 1, "b": 0})
    assert not result.success
    assert "unsupported op" in str(result.output)


def test_duplicate_tool_registration_rejected():
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    with pytest.raises(AgentError):
        registry.register(CalculatorTool())


def test_memory_put_then_get(registry):
    registry.execute("memory", {"action": "put", "key": "name", "value": "koor"})
    recall = registry.execute("memory", {"action": "get", "key": "name"})
    assert recall.output == "koor"


def test_scripted_agent_runs_to_completion(registry):
    planner = ScriptedPlanner([
        ("calculator", {"op": "multiply", "a": 6, "b": 7}),
        ("memory", {"action": "put", "key": "answer", "value": "42"}),
    ])
    agent = ReActAgent(registry, planner)
    trace = agent.run("store the answer")
    assert len(trace.steps) == 2
    assert all(step.success for step in trace.steps)
