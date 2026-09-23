# FlowAgent

> Agent → Skill → Automation

FlowAgent 是一个以 **Goal、Run、Task 和 Artifact** 为核心的 AI 任务执行平台。

目标是把一次成功的 AI 任务逐步沉淀为可复用的 **Skill**，最终进一步变成可以调度、触发和审计的 **Automation**。

FlowAgent 采用：

* **Task-first**：核心是任务执行，而不是聊天记录。
* **Artifact-first**：任务应尽可能产生可验证的成果。
* **Explore once, reuse later**：第一次允许 Agent 探索，后续逐步沉淀为稳定能力。
* **Progressive complexity**：严格按照项目版本逐步引入 Agent、RAG、LangGraph、Skill 和 Automation。

## Milestone Status

已完成：

```text
v0.1 — Domain Foundation ✅
```

下一阶段：

```text
v0.2 — Goal → Structured Plan
```

v0.1 建立了 FlowAgent 的工程基础和领域模型。

当前已经覆盖：

* Goal
* Task
* Run
* Artifact
* Task / Run 状态转换
* Task dependency 验证
* 循环依赖检测
* Artifact ownership
* Artifact 路径约束
* UTC 时间约束
* Run 生命周期时间戳
* Terminal state protection
* 配置管理
* Domain exceptions
* pytest 单元测试
* Domain public API

v0.1 **不包含**：

* LLM Planner
* Tool Calling
* Agent Loop
* RAG
* LangGraph Runtime
* Skill Extraction
* Automation Runtime

这些能力将在后续版本逐步加入。

## Core Domain

### Goal

描述用户最终想得到的结果。

```python
from flow_agent.domain import Goal

goal = Goal(
    title="Research LangChain",
    description="Research important LangChain updates from the last 7 days",
    success_criteria=[
        "Important claims are backed by reliable sources",
    ],
    requested_outputs=[
        "markdown_report",
    ],
)
```

### Task

表示执行计划中的一个可跟踪工作单元。

```python
from flow_agent.domain import Task

task = Task(
    title="Search official sources",
    description="Search recent LangChain updates",
)
```

Task 具有显式生命周期，例如：

```text
PENDING
→ RUNNING
→ COMPLETED
```

非法状态转换会被 Domain 层拒绝。

### Run

表示一个 Goal 的实际执行实例。

```python
from flow_agent.domain import Run

run = Run(
    goal_id=goal.id,
)

run.add_task(task)
```

Run 负责维护跨 Task 的领域规则，包括：

* dependency 必须指向同一 Run 中的 Task
* 不允许自依赖
* 不允许循环依赖
* 非 `SKIPPED` Task 未完成时，Run 不能进入 `COMPLETED`
* terminal Run 不允许继续添加 Task / Artifact
* `started_at` / `finished_at` 使用 UTC 时间

### Artifact

表示 Run 产生的实际成果。

```python
from flow_agent.domain import Artifact, ArtifactKind

artifact = Artifact(
    run_id=run.id,
    producer_task_id=task.id,
    kind=ArtifactKind.MARKDOWN,
    path="output/report.md",
)
```

Artifact 路径必须是受管 workspace 内的相对路径。

例如以下路径会被拒绝：

```text
/etc/passwd
../../secret.txt
C:\Users\secret.txt
```

符号链接等真实文件系统边界检查将在后续 `write_file` Tool 中处理。

## Project Structure

```text
agent/
├── docs/
│   ├── FLOWAGENT_PROJECT.md
│   └── 学习路线.md
├── examples/
│   └── learning/
├── src/
│   └── flow_agent/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       └── domain/
│           ├── __init__.py
│           ├── goal.py
│           ├── task.py
│           ├── run.py
│           └── artifact.py
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Requirements

```text
Python >= 3.11
```

## Installation

Create and activate a virtual environment, then install FlowAgent in editable mode:

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install project and development dependencies:

```bash
pip install -e ".[dev]"
```

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

FlowAgent v0.1 currently supports:

```dotenv
FLOW_AGENT_ENVIRONMENT=development
FLOW_AGENT_WORKSPACE_ROOT=workspace
FLOW_AGENT_LOG_LEVEL=INFO
```

Real secrets must never be committed to the repository.

## Running Tests

Run the complete test suite:

```bash
pytest -v
```

Tests cover the core v0.1 domain invariants, including:

* Pydantic validation
* immutable IDs
* UTC datetime validation
* Task and Run state machines
* terminal states
* dependency validation
* dependency cycle detection
* Artifact ownership
* Artifact path validation
* configuration loading
* public Domain API

## Documentation

Detailed product design, architecture boundaries and version roadmap:

```text
docs/FLOWAGENT_PROJECT.md
```

Learning roadmap:

```text
docs/学习路线.md
```

## Roadmap

```text
v0.1  Domain Foundation
  ↓
v0.2  Goal → Structured Plan
  ↓
v0.3  Tool Executor
  ↓
v0.4  Bounded Autonomous Run
  ↓
v0.5  Policy / Approval Runtime
  ↓
v0.6  Workspace / Knowledge
  ↓
v0.7  Evaluated Experience Memory
  ↓
v0.8  Skill Extraction & Evaluation
  ↓
v0.9  Explicit LangGraph Durable Runtime
  ↓
v1.0  Skill Ecosystem + Automation
```

The first end-to-end scenario used throughout the project is:

```text
Research
→ Report
→ Skill
→ Automation
```

See `docs/FLOWAGENT_PROJECT.md` for the complete specification.
