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
