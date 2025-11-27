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
