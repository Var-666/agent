# FlowAgent 项目规范

> Agent → Skill → Automation 平台
>
> 文档用途：供项目开发者与 Codex 共同阅读，作为产品方向、架构边界、阶段计划和实现约束的统一基线。
>
> 当前里程碑：**v0.1 — Domain Foundation**
>
> 状态：Draft v1.1

---

## 1. 项目概述

FlowAgent 是一个“从一次性 AI 任务，到可复用 Skill，再到可自动运行 Workflow”的 Agent 执行平台。

它的核心不是聊天，也不是另一个通用问答助手。用户提供一个 **Goal（目标）**，系统负责规划、执行、观察、修正，并产出 **Artifact（成果物）**。当某次执行成功后，系统可以把有效执行路径抽象为 **Skill（可复用能力）**；Skill 再结合 Trigger / Schedule / Input Mapping，成为可重复运行的 **Automation（自动化）**。

核心闭环：

```text
Goal
  ↓
Agent Exploration
  ↓
Run / Execution Trace
  ↓
Human Correction / Approval
  ↓
Skill Extraction
  ↓
Reusable Skill
  ↓
Automation
```

一句话定位：

> **把一次成功的 AI 任务，变成下一次可以稳定复用、最终可以自动执行的工作流。**

---

## 2. 为什么做这个项目

现有 AI 应用常见两类：

1. **Chat / RAG 应用**：擅长回答问题，但通常停留在“用户问一句，AI 回一句”。
2. **传统 Workflow 平台**：执行稳定，但需要人提前知道并配置完整流程。

FlowAgent 试图连接二者：

```text
Agent
擅长探索未知任务，但成本高、执行路径可能不稳定

        ↓ 成功轨迹沉淀

Skill
把成功经验参数化、约束化、可复用化

        ↓ 触发条件固定

Automation
低成本、可重复、可调度、可审计地执行
```

项目关注的核心问题是：

- Agent 如何完成一个真实任务，而不是只输出答案？
- 如何记录一次 Run 中真正有效的执行路径？
- 如何从成功轨迹中提炼可复用 Skill？
- 如何让 Skill 随时间变得更稳定，而不是每次重新探索？
- 哪些动作可以自动执行，哪些必须 Human-in-the-loop？
- 如何让长任务具备持久状态、失败恢复、等待与继续执行能力？

---

## 3. 产品原则

### 3.1 Task-first，而不是 Chat-first

产品核心对象是 Goal、Run、Task、Skill、Automation、Artifact，而不是 Conversation。

聊天可以作为输入和干预手段，但不是产品的数据中心。

### 3.2 Artifact-first

任务结束必须尽可能产生可验证成果，例如：

- `report.md`
- `result.json`
- `data.csv`
- `analysis.xlsx`
- 文档、代码、表单草稿
- 外部系统中的已执行动作

不能把“生成一段看起来合理的文字”当作默认完成标准。

### 3.3 Explore once, reuse later

第一次允许 Agent 自主探索；后续同类任务优先复用历史经验或 Skill。

### 3.4 Human controls consequential actions

读取、搜索等低风险行为可以自动进行；对外写入、发送、提交、删除、支付等高风险动作必须经过策略检查，必要时等待人工审批。

### 3.5 Progressive complexity

严格按照学习路线和项目版本逐层增加能力。不得因为“未来会需要”而提前引入复杂架构。

---

## 4. 非目标（Non-goals）

当前项目**不**以以下内容为目标：

- 重新实现一个 LLM Provider 框架。
- 自研向量数据库。
- 自研 Embedding 模型。
- 自研浏览器自动化底层。
- 自研完整 MCP 协议栈。
- 自研复杂聊天前端。
- 一开始就实现 Multi-Agent。
- 一开始就实现“万能 Agent”。
- 一开始就接入几十个第三方 SaaS。

原则：**已有成熟基础设施时优先集成，不重复造轮子；我们重点实现 Agent orchestration、State、Skill、Policy、Memory、Workflow、Evaluation。**

---

## 5. 核心领域模型

### 5.1 Goal

用户想完成的结果。

示例：

```text
调查 LangChain 最近 7 天的重要更新，并生成 Markdown 报告。
```

Goal 只描述“想要什么”，不要求用户提前知道“怎么做”。

建议字段：

```python
class Goal:
    id: str
    title: str
    description: str
    success_criteria: list[str]
    requested_outputs: list[str]
    created_at: datetime
```

### 5.2 Task

执行计划中的一个可跟踪单元。

```python
class Task:
    id: str
    title: str
    description: str
    status: str
    dependencies: list[str]
```

建议状态：

```text
PENDING
RUNNING
WAITING
COMPLETED
FAILED
SKIPPED
CANCELLED
```

### 5.3 Run

一次 Goal 的实际执行实例。

这是系统最重要的运行时对象之一。

```python
class Run:
    id: str
    goal_id: str
    status: str
    tasks: list[Task]
    artifacts: list[Artifact]
    started_at: datetime | None
    finished_at: datetime | None
```

建议状态：

```text
QUEUED
PLANNING
RUNNING
WAITING_USER
WAITING_APPROVAL
WAITING_EXTERNAL
BLOCKED
COMPLETED
FAILED
CANCELLED
```

### 5.4 Artifact

Run 产生的实际成果。

```python
class Artifact:
    id: str
    run_id: str
    producer_task_id: str | None
    kind: str
    path: str
    description: str | None
    created_at: datetime
```

初期支持：

```text
markdown
text
json
csv
```

后期再扩展 DOCX、XLSX、PDF 等。

### 5.5 Skill

从成功执行经验中沉淀出的可复用能力。

Skill 不是一段 Prompt，而应该包含：

```text
metadata
input_schema
output_schema
instructions
allowed_tools
required_permissions
workflow / steps
success_criteria
examples
version
execution_mode
provenance / evaluation requirements
```

概念模型：

```python
class Skill:
    id: str
    name: str
    description: str
    version: str
    execution_mode: str
    input_schema: dict
    output_schema: dict
    instructions: str
    allowed_tools: list[str]
    required_permissions: list[str]
    steps: list[dict]
    success_criteria: list[str]
    source_run_ids: list[str]
    extractor_version: str | None
    evaluation_requirements: dict
```

Skill 的执行语义逐步收敛为三类：

```text
agentic
固定指令、工具策略和验收标准，具体路径由 Agent 探索。

workflow
步骤、依赖和路由明确，优先确定性执行。

hybrid
总体流程固定，部分节点允许 Agent 自主决策。
```

v0.8 可以先实现 `agentic`，不要在 Schema 尚未稳定时同时实现三种运行时。

### 5.6 Automation

Automation = Skill + Trigger + Input Mapping + Runtime Policy。

```python
class Automation:
    id: str
    name: str
    skill_id: str
    skill_version: str
    trigger: dict
    input_mapping: dict
    runtime_policy: dict
    enabled: bool
```

触发类型后期支持：

```text
manual
schedule
webhook
event
condition
```

### 5.7 领域不变量

v0.1 不引入数据库或复杂 Repository，但必须先明确并测试以下规则：

- ID 在对象生命周期内不可变。
- 时间使用带时区的 UTC `datetime`。
- Task dependency 必须指向同一 Run 中已存在的 Task。
- Task dependency 不允许自引用或循环依赖。
- Task 与 Run 只能按显式状态转换矩阵变更。
- `COMPLETED`、`FAILED`、`CANCELLED` 是终态，不得被普通业务方法静默恢复。
- Run 进入 `COMPLETED` 前，所有非 `SKIPPED` Task 必须已成功结束。
- Artifact 必须属于对应 Run；如关联 Task，Task 也必须属于该 Run。
- Artifact 路径必须是受管 workspace 内的相对路径，不允许绝对路径或 `..` 越界。
- Domain Model 不依赖 LangChain、LangGraph 或具体 Model Provider。

后续引入持久化时，数据库和 API 层必须保持同样的不变量，不能绕过 Domain 规则直接改状态。

---

## 6. 产品主流程

### 6.1 第一次执行

```text
User Goal
   ↓
Understand Goal
   ↓
Create Plan
   ↓
Execute Tasks
   ↓
Observe Results
   ↓
Retry / Replan when needed
   ↓
Approval when needed
   ↓
Validate Result
   ↓
Produce Artifacts
   ↓
Complete Run
```

### 6.2 Skill 化

```text
Completed Run
   ↓
Analyze successful trace
   ↓
Remove accidental / redundant steps
   ↓
Generalize concrete values into parameters
   ↓
Extract tool policy
   ↓
Define success criteria
   ↓
Generate Skill candidate
   ↓
Evaluate
   ↓
Human review
   ↓
Publish Skill
```

### 6.3 自动化

```text
Trigger
   ↓
Create Run
   ↓
Load Skill
   ↓
Resolve Inputs
   ↓
Execute
   ↓
Approval if required
   ↓
Validate
   ↓
Artifact / External Action
   ↓
Complete
```

---

## 7. 首个贯穿全项目的端到端场景

固定测试案例：

> **Research → Report → Skill → Automation**

第一次输入：

```text
调查 LangChain 最近 7 天的重要更新，验证官方来源，并生成 Markdown 报告。
```

预期首次 Run：

```text
search
→ read
→ verify
→ summarize
→ write
```

预期 Artifact：

```text
output/langchain-weekly.md
```

用户确认执行结果有效后：

```text
Save as Skill
```

系统抽象为：

```text
Skill: research_recent_project_updates

Inputs:
- project_name
- days
- result_count

Output:
- Markdown report
```

再进一步生成 Automation：

```text
每周一 09:00
执行 research_recent_project_updates
project_name = LangChain
days = 7
result_count = 10
```

此场景必须尽量贯穿整个学习过程，避免每一课都换一个完全无关的 Demo。

### 7.1 固定测试与实时演示分离

“最近 7 天”是动态数据，不能单独作为可重现的回归测试。同一场景需要两种运行模式：

```text
Fixture Mode
- 固定 as_of_date
- 固定官方来源快照
- 固定预期事实和输出约束
- 用于单测、离线 Eval 和 CI

Live Mode
- 使用当前日期与实时搜索
- 允许来源集合变化
- 用于人工验收、Smoke Test 和产品演示
```

CI 不应依赖当天是否存在重要更新、外部搜索排名或网络的短期波动。

---

## 8. 版本路线与学习路线映射

### v0.1 — Domain Foundation

**学习内容**：Python 类型系统、Pydantic、dataclass、TypedDict、异常、`.env`、pytest。

**项目目标**：建立正式项目骨架和领域模型。

实现：

- Goal
- Task
- Run
- Artifact
- Task / Run 状态转换矩阵
- Task 依赖合法性与环检测
- Artifact 归属与路径约束
- 配置管理
- 基础异常
- 单元测试

此阶段**没有 Agent、没有 RAG、没有 Multi-Agent**。

完成标准：

- 可以创建 Goal。
- 可以创建 Run。
- 可以给 Run 添加 Task。
- Task 状态可以合法转换。
- 非法状态转换、无效依赖和循环依赖会被拒绝。
- 可以登记 Artifact。
- Artifact 不能指向 workspace 外部路径。
- Pydantic Validation 有测试。
- `pytest` 全部通过。

建议提交：

```text
feat: bootstrap FlowAgent domain model
```

---

### v0.2 — Goal → Structured Plan

**学习内容**：Model、Messages、Prompt、invoke、Model Structured Output、基础 LangSmith tracing。

目标：LLM 只负责把自然语言 Goal 转成结构化 ExecutionPlan，暂不执行。

```text
Goal
  ↓
Model
  ↓
ExecutionPlan
  ├── Task 1
  ├── Task 2
  └── Task 3
```

内部分成两个小步骤：

```text
v0.2a Structured Planner（主线）
- invoke
- Prompt
- with_structured_output
- ExecutionPlan Schema
- 错误与重试
- 基础 tracing

v0.2b Model Call Modes（独立学习实验）
- batch
- stream
- async
```

batch、stream、async 必须有独立练习，但不作为 Structured Planner 上线的前置条件。

完成标准：

- Plan 必须符合 Pydantic Schema。
- Task 结构稳定。
- 对无效输出有错误处理。
- 有最小 Prompt / Plan 测试集。
- 每次 Planner 调用可以在 trace 中查看延迟、token 和异常。

---

### v0.3 — Tool Executor

**学习内容**：Tool Schema、`@tool`、`bind_tools`、Tool Calling Protocol、并行/串行调用、错误处理。

首批只实现四类能力：

```text
search_web
read_url
read_file
write_file
```

说明：可以使用成熟外部库实现工具底层；不要自研搜索引擎或浏览器内核。

这一阶段手动实现 Model → Tool → ToolMessage → Model 循环，以真正理解 Tool Calling。

完成标准：

- Model 能请求 Tool。
- Python 执行 Tool。
- Tool 结果正确回填。
- Tool timeout / failure 有可观察错误。
- 写文件操作限制在 Run Workspace 中。
- `write_file` 在路径规范化后再检查 workspace 边界，并拒绝 `..`、绝对路径和符号链接越界。
- `read_url` 仅允许指定 scheme，具有超时、响应大小和内容类型限制，并阻止本地/内网目标的 SSRF。
- 每次 Tool 调用记录 `run_id`、`task_id`、`tool_call_id`、latency 和 error。

---

### v0.4 — Bounded Autonomous Run

**学习内容**：`create_agent`、Agent Loop、State、Checkpointer、thread_id、Streaming。

目标：先执行固定 Plan，再在明确边界内允许 retry 和 replan：

```text
Fixed Plan Execution
  ↓
Bounded Agent Loop
  ↓
Retry recoverable failure
  ↓
Replan only when policy allows
```

Run 与 Agent thread 建立映射。

此阶段必须定义执行预算：

```text
max_steps
max_run_seconds
max_task_retries
max_tool_calls
max_tokens / max_cost
```

必须区分：

- 瞬时网络/限流错误：可按策略 retry。
- Tool 参数或计划错误：可能需要 replan。
- 缺少用户输入：进入 `WAITING_USER`。
- 策略禁止或无法继续：进入 `BLOCKED`。
- 超出预算：明确失败，不得无限循环。

引入最小 `RunEvent`，用于记录而不是反推执行历史：

```python
class RunEvent:
    id: str
    run_id: str
    task_id: str | None
    kind: str
    payload: dict
    created_at: datetime
```

完成标准：

- Run 可跨多个模型调用持续执行。
- 可查看执行事件流。
- 只有允许的错误会重试或触发重新规划。
- 可保存短期执行状态。
- 所有结束路径都能解释为什么完成、失败、阻塞或等待。
- 测试能证明 Agent 不会超过步数、时间和重试上限。

---

### v0.5 — Policy / Approval Runtime

**学习内容**：Middleware、Runtime Context、ToolRuntime、Guardrails、Human-in-the-loop。

Tool 风险等级：

```text
READ
WRITE_LOCAL
WRITE_EXTERNAL
HIGH_RISK
```

默认策略：

```text
READ          → 自动执行
WRITE_LOCAL   → 自动执行（受 workspace 限制）
WRITE_EXTERNAL→ 默认审批
HIGH_RISK     → 强制审批
```

完成标准：

- 高风险 Tool 无法绕过审批。
- Approval 支持 approve / edit / reject。
- Runtime Context 可携带 user / workspace / permissions。
- 此阶段只要求进程存活期间的审批暂停；跨进程重启恢复由 v0.9 的持久化 LangGraph Runtime 完成。

---

### v0.6 — Workspace / Knowledge

**学习内容**：RAG、Retrieval、Context Engineering、Context Compression。

每个 Run 拥有独立 Workspace：

```text
workspace/
└── runs/
    └── <run_id>/
        ├── input/
        ├── working/
        ├── sources/
        └── output/
```

RAG 的用途不是“做 PDF 问答”，而是为当前执行任务提供证据、历史材料和大规模上下文检索能力。

完成标准：

- 大量资料不需要全部塞进 Model Context。
- Retriever 能找到与当前 Task 相关内容。
- Artifact 与来源可以追溯。
- Fixture Mode 有固定来源快照、查询和预期事实。
- 建立最小离线评测集，至少检查检索相关性、引用完整性和关键事实。

---

### v0.7 — Evaluated Experience Memory

**学习内容**：Long-term Memory / Store。

重点不是只记录“用户喜欢中文”，而是记录执行经验：

```text
某类任务过去采用了什么步骤？
哪些搜索策略有效？
哪些 Tool 经常失败？
用户通常修改哪些结果？
```

目标：新 Run 可以检索过去相似且已验证的成功经验。

写入规则：

```text
Run COMPLETED
  ↓
Artifact validation passed
  ↓
Offline evaluation passed
  ↓
Human confirmed（初期必须）
  ↓
Eligible for Experience Memory
```

“执行完成”不等于“值得记忆”。失败、低质量或未审核轨迹可以保留在审计日志中，但不能被默认检索为成功经验。

---

### v0.8 — Skill Extraction & Evaluation

**学习内容**：LangSmith Tracing、Datasets、Evaluators、Experiments。

目标：从已评估的 Completed Run 提炼 Skill Candidate，并验证它是否比自由 Agent 更稳定。

第一版不做全自动发布：

```text
Completed + Evaluated Run
  ↓
Generate Skill Candidate
  ↓
Human edit / approve
  ↓
Offline evaluation
  ↓
Publish immutable Skill Version
```

实现自动提取前，先支持人工编写 Skill 并使用同一评测集执行，以便建立可比较基线。

Skill Builder 应至少处理：

- 成功步骤识别
- 冗余步骤删除
- 参数泛化
- Tool 白名单
- Success Criteria
- 示例输入输出
- 版本号
- 来源 Run 与提取器版本
- 执行模式与输出 Schema
- 发布所需的 Eval 阈值

关键指标：

- Task success rate
- Tool failure rate
- 重试次数
- Token cost
- Latency
- Human correction count
- Artifact correctness

---

### v0.9 — Explicit LangGraph Durable Runtime

**学习内容**：State、Reducer、Node、Edge、Conditional Edge、Command、Send、Interrupt、Persistence、Subgraph、Retry。

目标：把 Run 生命周期从 LangChain `create_agent` 提供的标准 Agent Graph，升级为显式 `StateGraph` Durable Workflow。这不是第一次使用 LangGraph Runtime，而是为了自定义路由、并行、持久化和恢复语义而下沉到显式图编排。

概念图：

```text
START
  ↓
load_skill_or_plan
  ↓
plan
  ↓
execute
  ↓
evaluate
  ├── retry
  ├── replan
  ├── wait approval
  ├── wait external
  └── done
       ↓
create_artifacts
       ↓
extract_skill_candidate
       ↓
END
```

完成标准：

- 进程重启后 Run 可恢复。
- WAITING_APPROVAL 可暂停并继续。
- 节点失败具备可控 Retry。
- 并行 Task 可以安全合并 State。

---

### v1.0 — Skill Ecosystem + Automation

**学习内容**：MCP、Multi-Agent 判断、部署与生产化。

目标：

- Skill Registry
- Automation Trigger
- Schedule / Event Trigger
- MCP Tool integration
- 必要时引入 Sub-agent / Multi-Agent
- API / deployment / observability

Automation Runtime 至少需要明确：

- timezone 与 daylight-saving 语义。
- 错过调度后是否 catch up。
- 同一 Automation 的并发策略。
- trigger event 的去重与幂等 key。
- 失败重试、死信与手动重放。
- 禁用 Automation 后已排队 Run 的处理方式。

注意：Multi-Agent 必须由真实需求驱动，例如上下文隔离、权限隔离、独立专业能力或并行任务，不允许为了“看起来高级”而拆 Agent。

---

## 9. Skill 文件格式草案

初版可以使用 YAML / JSON 表达，后续根据实现调整。

```yaml
name: research_recent_project_updates
version: 0.1.0
description: Research recent important updates for a software project and produce a sourced Markdown report.
execution_mode: agentic
source_run_ids:
  - run_example_001
extractor_version: manual-v1

inputs:
  project_name:
    type: string
  days:
    type: integer
    minimum: 1
  result_count:
    type: integer
    default: 10

allowed_tools:
  - search_web
  - read_url
  - write_file

required_permissions:
  - network.read
  - workspace.write

steps:
  - search official and primary sources
  - filter sources to requested time window
  - extract significant changes
  - verify claims against primary sources
  - deduplicate overlapping changes
  - rank by importance
  - generate Markdown report

success_criteria:
  - every reported change has at least one source
  - all changes fall inside requested time window
  - output file exists
  - report contains no duplicate items

outputs:
  - type: markdown
    path: output/report.md

evaluation:
  dataset: research_recent_project_updates_v1
  minimum_score: 0.85
```

Skill 的目标是**约束和复用 Agent 的成功行为**，不是要求所有 Skill 一开始都变成完全确定性的 Workflow。

---

## 10. Automation 文件格式草案

```yaml
name: weekly_langchain_report
enabled: true

trigger:
  type: schedule
  cron: "0 9 * * MON"
  timezone: "Asia/Shanghai"

skill:
  name: research_recent_project_updates
  version: "0.1.0"

inputs:
  project_name: LangChain
  days: 7
  result_count: 10

policy:
  require_approval_for:
    - WRITE_EXTERNAL
    - HIGH_RISK
  concurrency: skip_if_running
  catch_up_missed_runs: false
```

---

## 11. 建议目录结构

### v0.1

```text
agent/
├── src/
│   └── flow_agent/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── goal.py
│       │   ├── task.py
│       │   ├── run.py
│       │   └── artifact.py
│       └── main.py
│
├── tests/
│   ├── test_goal.py
│   ├── test_task.py
│   ├── test_run.py
│   └── test_artifact.py
│
├── examples/
│   └── learning/
│       └── agent_memory_demo.py
│
├── .env.example
├── pyproject.toml
├── README.md
└── FLOWAGENT_PROJECT.md
```

后续模块在对应版本真正需要时再创建，例如：

```text
planning/
tools/
agent/
workspace/
memory/
skills/
automations/
graph/
evals/
```

不要在 v0.1 预先创建全部空目录。

当前根目录的 `main.py` 是学习 `create_agent`、Tool Calling 和 `InMemorySaver` 的历史示例，与 v0.1 Domain Foundation 的产品边界不一致。开始 v0.1 实现时，应将它保留并移入 `examples/learning/agent_memory_demo.py`，而不是删除学习证据或把示例逻辑混入 `src/flow_agent`。

---

## 12. 工程约束

### 12.1 Python

- 推荐 Python 3.11+。
- 充分使用类型注解。
- Pydantic 用于跨边界数据验证与 Schema。
- dataclass / TypedDict 只在有明确理由时使用。

### 12.2 配置

- Secret 不提交 Git。
- `.env.example` 只包含变量名和说明，不包含真实密钥。
- 配置读取集中管理。

### 12.3 测试

每个阶段必须有对应测试，不能等到 v1.0 再补。

最低要求：

- Domain unit tests
- Tool unit tests
- Agent integration tests
- Workflow state transition tests
- Skill evaluation dataset
- Fixture Mode deterministic regression tests
- Live Mode smoke tests（不作为必须稳定通过的 CI 门禁）

测试必须分离稳定回归与外部环境验证，不得将实时搜索结果当作唯一预期值。

### 12.4 错误处理

禁止：

```python
except Exception:
    pass
```

失败必须变成可观察事件或明确异常。

### 12.5 可观察性

从早期开始保留：

```text
run_id
task_id
tool_call_id
status transition
error
latency
```

v0.2 开始接入基础 LangSmith tracing，但不让 Domain Model 依赖 LangSmith SDK。v0.8 再建立完整 dataset、experiment、evaluator 和回归门禁。

---

## 13. Tool 安全策略

所有 Tool 后期都应该有元数据：

```python
name
description
risk_level
side_effects
required_permissions
idempotent
```

风险等级：

| Level | 示例 | 默认行为 |
|---|---|---|
| READ | 搜索、读取网页、读取文件 | 自动 |
| WRITE_LOCAL | 写 Run Workspace 文件 | 自动，限制路径 |
| WRITE_EXTERNAL | 发邮件、创建日程、写 SaaS | 审批 |
| HIGH_RISK | 删除、提交、购买、支付 | 强制审批 |

任何外部写操作都不能仅因为“模型认为应该做”就直接执行。

安全检查必须发生在真实执行边界，不能只依赖 System Prompt。最低要求：

- 文件 Tool 在 path resolve 后检查 workspace 边界，防止 path traversal 和 symlink escape。
- URL Tool 检查 scheme、DNS/IP、redirect 后目标、响应大小与超时，防止 SSRF。
- 外部写 Tool 使用幂等 key，并在重试前查询原操作状态。
- Approval 必须绑定经过展开和规范化的实际操作参数，审批后不允许模型静默替换。

---

## 14. Skill 生命周期

Skill 不应该一次生成后永久不变。

```text
DRAFT
  ↓
EVALUATING
  ↓
ACTIVE
  ↓
DEPRECATED
```

版本使用语义化版本思想：

```text
0.1.0
0.2.0
1.0.0
```

每次 Skill 修改需要保留：

- 原版本
- 新版本
- Eval 结果
- 变更原因

Automation 应固定引用 Skill Version，避免 Skill 更新后静默改变生产行为。

---

## 15. 什么时候才引入 Multi-Agent

只有出现以下情况之一时才考虑拆 Agent：

- 单 Agent Tool 数量和 Context 过大。
- 不同任务需要明确权限隔离。
- 不同领域需要完全不同的 System Prompt / Knowledge。
- 可以明显并行执行且结果可独立验证。
- Sub-agent 可以减少主 Agent 的 Context 压力。

否则优先：

```text
Single Agent + Tools + Skills + Middleware + LangGraph
```

---

## 16. 什么时候使用 MCP

学习 Tool Calling 阶段会自己实现少量 Tool，以理解机制。

当机制已经掌握后，对成熟外部服务优先考虑 MCP / 官方 SDK / 已有 Connector，不继续维护大量重复 API wrapper。

原则：

> **教学阶段适度自己实现；产品阶段优先复用成熟基础设施。**

---

## 17. Codex 开发规则

Codex 在修改项目代码前必须遵循以下规则：

1. 先阅读本文件和当前 `学习路线.md`。
2. 明确当前项目版本 / milestone。
3. 只实现当前 milestone 需要的能力。
4. 不提前引入未来模块，除非当前实现确实无法继续且有明确理由。
5. 不把示例代码直接升级成复杂框架。
6. 每次功能改动必须补测试或更新已有测试。
7. 优先修改已有模块，不无必要创建重复 abstraction。
8. 不为了“通用性”提前设计插件系统。
9. 不为了“Agent 化”把确定性逻辑交给 LLM。
10. 对有副作用的 Tool 必须显式考虑风险等级与审批。
11. 保持 Domain Model 与 LangChain / LangGraph runtime 解耦；领域对象不应依赖具体模型 Provider。
12. 如果发现项目需求与本文冲突，先指出冲突，再提出最小修改方案，不要静默改变项目方向。

---

## 18. 当前里程碑：v0.1

### 目标

建立 FlowAgent 最小、清晰、可测试的 Domain Foundation。

### 当前必须实现

- [ ] `Goal`
- [ ] `Task`
- [ ] `Run`
- [ ] `Artifact`
- [ ] Status Enum / validation
- [ ] Task dependency validation / cycle detection
- [ ] Task / Run transition methods
- [ ] Artifact ownership / safe relative path validation
- [ ] 配置模块
- [ ] 基础异常类型
- [ ] pytest 测试
- [ ] `.env.example`
- [ ] README 最小运行说明
- [ ] 将现有 Agent 学习代码归档到 `examples/learning/`

### 当前明确不要实现

- [ ] `create_agent`
- [ ] LangGraph
- [ ] RAG
- [ ] Vector Store
- [ ] MCP
- [ ] Multi-Agent
- [ ] Browser Automation
- [ ] Skill Extraction
- [ ] Scheduler
- [ ] Web UI

### v0.1 Definition of Done

1. `pip install -e .` 或项目选定的等价安装方式成功。
2. Domain models 可被独立 import。
3. 非法状态或非法字段会触发 Validation Error。
4. 非法 Task / Run 状态转换被拒绝。
5. 无效、自引用或循环 Task 依赖被拒绝。
6. Run 能保存多个 Task 和 Artifact。
7. Artifact 归属正确，且不能使用越界路径。
8. 每个不变量都有正常和失败测试。
9. `pytest` 全绿。
10. README 能让另一个开发者在本地安装项目并运行测试。

---

## 19. 开发节奏

每一小节遵循：

```text
理解机制
→ 最小实现
→ 测试
→ 实验 / 修改
→ 小结
→ Commit
```

禁止：

```text
一次性让 Codex 写完 v1.0
```

推荐一个 milestone 一个 milestone 推进。

建议 Commit 风格：

```text
feat: add goal domain model
feat: add run lifecycle
feat: add structured execution planner
feat: add manual tool executor
feat: add bounded autonomous run loop
feat: add tool approval policy
feat: add run workspace retrieval
feat: add evaluated execution memory
feat: add skill extraction pipeline
feat: add explicit langgraph runtime
feat: add automation triggers
```

---

## 20. 项目长期成功标准

FlowAgent v1.0 不以“支持多少模型/多少 Tools”为核心指标。

更重要的是：

1. 用户能提交真实 Goal，而不是必须自己拆步骤。
2. Run 能完成多步骤任务并产生 Artifact。
3. Run 可中断、等待、恢复。
4. 高风险动作不会绕过人工控制。
5. 成功 Run 能被提炼成 Skill。
6. Skill 对同类任务比自由探索 Agent 更稳定、成本更低或更快。
7. Skill 可以被 Automation 可靠触发。
8. 全过程可追踪、可测试、可评估。

最终闭环必须成立：

```text
Agent explores
      ↓
System learns the successful procedure
      ↓
Skill captures it
      ↓
Evaluation verifies it
      ↓
Automation reuses it
```

---

## 21. 参考项目与借鉴方向

以下项目仅作为产品/架构灵感，不要求复制实现：

- n8n — Workflow / Automation / Integrations
- Browser Use — Browser as an execution environment
- ByteDance DeerFlow — Long-horizon agent, skills, memory, sandbox
- LangChain Deep Agents — Skills, filesystem, subagents, HITL
- LangGraph — Durable stateful workflows
- LangSmith — Tracing and evaluation

FlowAgent 的差异点不是“把这些项目重新实现一遍”，而是聚焦：

> **Agent → successful trace → reusable Skill → reliable Automation。**

---

## 22. 决策记录

### Decision 001 — 不以 Chat 为产品中心

**决定**：Conversation 只是交互入口之一，Run 是核心产品对象。

### Decision 002 — Skill 不等于 Prompt

**决定**：Skill 至少包含 Schema、Tool Policy、Steps / Instructions、Success Criteria 和 Version。

### Decision 003 — 不提前使用 Multi-Agent

**决定**：先用 Single Agent + Tools + Skills + Middleware + LangGraph，出现真实隔离需求时再拆。

### Decision 004 — 学习路线和开发路线绑定

**决定**：学到哪，实现到哪。不得跳过机制学习直接调用高级封装完成最终功能。

### Decision 005 — 首个固定 Demo

**决定**：长期保留 `Research → Report → Skill → Automation` 作为贯穿版本的回归场景。

### Decision 006 — 先评估，再写入经验记忆

**决定**：Run 成功只是候选条件。初期只有 Artifact 验证、离线评估和人工确认均通过的轨迹才能进入 Experience Memory。

### Decision 007 — Fixture 回归与 Live 演示分离

**决定**：CI 和离线 Eval 使用固定日期与来源快照；实时搜索仅用于 Smoke Test、人工验收和演示。

### Decision 008 — Skill Candidate 必须经过发布门禁

**决定**：轨迹提取的结果默认是 DRAFT Candidate，不能直接成为 ACTIVE Skill。初期发布必须通过人工审核和离线 Eval。

---

## 23. 给开发者 / Codex 的启动提示

每次开始一个新开发会话时，可以使用：

```text
Read FLOWAGENT_PROJECT.md and 学习路线.md first.
Identify the current milestone and its Definition of Done.
Do not implement features from later milestones.
Explain the smallest implementation step for the current milestone,
then modify the code and tests accordingly.
Keep domain logic independent from LangChain/LangGraph unless the current milestone explicitly introduces them.
```

当前应回答：

```text
Current milestone: v0.1 — Domain Foundation
Next objective: bootstrap project structure and implement Goal / Task / Run / Artifact with tests.
```
