# agent-runtime-lite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight agent runtime: tool registry with fail-safe execution, pluggable step planners, and ReAct-style loops with full run traces — the execution spine for local AI agents.

## 🚀 Overview

Agents die in production from unhandled tool failures and runaway loops. `agent-runtime-lite` separates those concerns: a **ToolRegistry** executes tools and captures every exception as a structured `ToolResult` (success flag + duration), a **StepPlanner** decides the next `(tool, arguments)` pair from goal + history — LLM-driven or scripted for tests — and the **ReActAgent** loop enforces `max_steps`, aborts cleanly on unknown tools, and returns a complete `AgentRunTrace`.

## ✨ Features

- **Tool protocol:** any object with `name` + `run(arguments)` plugs in; duplicates rejected
- **Fail-safe execution:** tool exceptions become failed results, never agent crashes
- **Planner protocol:** `ScriptedPlanner` (deterministic tests) or an LLM-backed planner in production
- **Step budget:** `MaxStepsExceededError` guards infinite planner loops
- **Full traces:** per-step results/durations plus final answer and total wall time
- **Reference tools:** calculator and key-value memory included
- **Zero dependencies**

## 🚧 Structure

```
agent-runtime-lite/
├── src/agent_runtime/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/agent-runtime-lite.git
cd agent-runtime-lite
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from agent_runtime import (
    CalculatorTool, MemoryStoreTool, ReActAgent,
    ScriptedPlanner, ToolRegistry,
)

registry = ToolRegistry([CalculatorTool(), MemoryStoreTool()])
planner = ScriptedPlanner([
    ("calculator", {"op": "multiply", "a": 6, "b": 7}),
    ("memory", {"action": "put", "key": "answer", "value": "42"}),
])

trace = ReActAgent(registry, planner).run("store the answer")
print(trace.final_answer)
for step in trace.steps:
    print(step.as_observation)
```

## 🔧 Error Handling

```text
AgentError
├── UnknownToolError        # planner requested an unregistered tool → trace aborts
└── MaxStepsExceededError   # planner never returned None within budget
```

Tool-level failures are data on the trace, not exceptions.

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen results/traces
- Zero comments — names carry the meaning
- Planner protocol keeps LLM coupling out of the loop logic

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi** - [kooroushmasoumi@gmail.com](mailto:kooroushmasoumi@gmail.com)

---

⭐ Star this repo if you find it useful!
