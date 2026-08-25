from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol, Sequence


class AgentError(Exception):
    pass


class UnknownToolError(AgentError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"unknown tool: {tool_name!r}")


class MaxStepsExceededError(AgentError):
    def __init__(self, max_steps: int) -> None:
        super().__init__(f"agent exceeded {max_steps} steps")


@dataclass(frozen=True)
class ToolResult:
    tool: str
    output: Any
    success: bool
    duration_ms: float

    @property
    def as_observation(self) -> str:
        status = "ok" if self.success else "error"
        return f"[{self.tool}/{status}] {self.output}"


class Tool(Protocol):
    name: str

    def run(self, arguments: dict[str, Any]) -> Any: ...


class CalculatorTool:
    name = "calculator"

    _OPERATIONS: dict[str, Callable[[float, float], float]] = {
        "add": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
    }

    def run(self, arguments: dict[str, Any]) -> float:
        operation = arguments.get("op")
        left = float(arguments.get("a", 0))
        right = float(arguments.get("b", 0))
        if operation not in self._OPERATIONS:
            raise ValueError(f"unsupported op: {operation!r}")
        return self._OPERATIONS[operation](left, right)


class MemoryStoreTool:
    name = "memory"

    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def run(self, arguments: dict[str, Any]) -> str:
        action = arguments.get("action", "get")
        key = arguments.get("key", "")
        if action == "put":
            self._entries[key] = str(arguments.get("value", ""))
            return f"stored:{key}"
        return self._entries.get(key, "")


class ToolRegistry:
    def __init__(self, tools: Sequence[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool) -> "ToolRegistry":
        if getattr(tool, "name", "") in self._tools:
            raise AgentError(f"tool already registered: {tool.name!r}")
        self._tools[tool.name] = tool
        return self

    @property
    def tool_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise UnknownToolError(tool_name)
        started = time.perf_counter()
        try:
            output = tool.run(arguments)
            success = True
        except Exception as exc:
            output = str(exc)
            success = False
        duration = (time.perf_counter() - started) * 1000
        return ToolResult(tool=tool_name, output=output, success=success,
                          duration_ms=round(duration, 3))


class StepPlanner(Protocol):
    def next_step(self, goal: str, history: Sequence[ToolResult]) -> tuple[str, dict[str, Any]] | None: ...


class ScriptedPlanner:
    def __init__(self, script: Sequence[tuple[str, dict[str, Any]]]) -> None:
        self._script = list(script)

    def next_step(self, goal: str,
                  history: Sequence[ToolResult]) -> tuple[str, dict[str, Any]] | None:
        executed = sum(1 for result in history if result.success)
        if executed >= len(self._script):
            return None
        return self._script[executed]


@dataclass
class AgentRunTrace:
    goal: str
    steps: list[ToolResult] = field(default_factory=list)
    final_answer: str = ""
    total_duration_ms: float = 0.0


class ReActAgent:
    def __init__(self, registry: ToolRegistry, planner: StepPlanner,
                 max_steps: int = 10) -> None:
        if max_steps < 1:
            raise AgentError("max_steps must be >= 1")
        self._registry = registry
        self._planner = planner
        self._max_steps = max_steps

    def run(self, goal: str) -> AgentRunTrace:
        trace = AgentRunTrace(goal=goal)
        started = time.perf_counter()
        observations: list[ToolResult] = []
        for _ in range(self._max_steps):
            step = self._planner.next_step(goal, observations)
            if step is None:
                break
            tool_name, arguments = step
            try:
                result = self._registry.execute(tool_name, arguments)
            except UnknownToolError as exc:
                trace.steps.append(ToolResult(
                    tool=tool_name, output=str(exc), success=False, duration_ms=0.0,
                ))
                trace.final_answer = f"aborted: {exc}"
                break
            observations.append(result)
            trace.steps.append(result)
            if not result.success:
                trace.final_answer = f"failed at tool {tool_name!r}"
                break
        else:
            raise MaxStepsExceededError(self._max_steps)

        if not trace.final_answer:
            successful = [r.output for r in observations if r.success]
            trace.final_answer = successful[-1] if successful else "no steps executed"
        trace.total_duration_ms = round((time.perf_counter() - started) * 1000, 3)
        return trace
