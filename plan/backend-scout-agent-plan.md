# 后端子代理侦查模块实施计划

- 日期：2026-02-14
- 目标：让主会话（Main Session）通过工具调用按需启动子任务代理（Scout Agent）执行受限侦查任务，支持最多同时 5 个子任务，并将结构化结果回传主会话用于后续推理与回答。

## 1. 范围定义

### In Scope

1. 主会话触发子代理侦查（同步等待 + 可取消）。
2. 子代理独立上下文、独立工具白名单、独立预算控制。
3. 子代理结果标准化回传（summary + evidence + confidence + error）。
4. 侦查执行链路可观测（trace/event/log）。
5. 失败可降级（子代理失败不导致主会话整体崩溃）。
6. 子任务由工具调用触发，且并发上限为 5。

### Out of Scope

1. 超过 5 的大规模子任务编排与分布式队列。
2. 子代理长期记忆系统重构。
3. UI 大改（仅透传必要状态与结果）。
4. 跨进程/分布式调度（先在现有进程内实现）。

## 2. 核心能力设计

### 2.1 角色模型

1. Main Session：负责用户对话、决策是否发起侦查。
2. Scout Agent：只执行“侦查提示词”+“受限工具调用”，不直接面向用户发言。
3. Orchestrator：统一管理生命周期、预算、超时、回传和并发槽位。

### 2.2 子代理输入/输出契约

- 输入 `ScoutTaskInput`
  - `scoutId: string`
  - `sessionId: string`
  - `task: string`（侦查目标）
  - `constraints: { maxSteps, timeoutMs, tokenBudget }`
  - `allowedTools: ['search_docs', 'read_doc', 'report_findings']`
  - `contextSnapshot: Message[]`（主会话截断快照）

- 输出 `ScoutTaskResult`
  - `status: 'success' | 'partial' | 'failed' | 'timeout' | 'aborted'`
  - `summary: string`
  - `evidence: Array<{ source: string; quote?: string; note: string }>`
  - `confidence: number`（0~1）
  - `toolRuns: Array<{ name: string; ok: boolean; durationMs: number }>`
  - `error?: { code: string; message: string }`
  - `scoutId: string`

### 2.3 状态机

`QUEUED -> PREPARE -> RUNNING -> AGGREGATING -> COMPLETED`

异常分支：

- `RUNNING -> TIMEOUT`
- `RUNNING -> ABORTED`
- `RUNNING/AGGREGATING -> FAILED`

要求：每次状态迁移都写 trace event，且可回放。

并发约束：

- 同一主会话最多 5 个 `RUNNING` 子任务。
- 超出上限的新任务进入 `QUEUED`，按 FIFO 等待可用槽位。

## 3. 后端模块落位（垂直结构）

建议采用垂直结构，把子代理能力收敛在单一 feature 目录：

- `src/features/scout-agent/index.ts`
- `src/features/scout-agent/contracts.ts`
- `src/features/scout-agent/scout-orchestrator.ts`
- `src/features/scout-agent/scout-state-machine.ts`
- `src/features/scout-agent/scout-runner.ts`
- `src/features/scout-agent/scout-trigger-policy.ts`
- `src/features/scout-agent/scout-concurrency-manager.ts`
- `src/features/scout-agent/scout-trace-recorder.ts`
- `src/features/scout-agent/__tests__/...`

主会话通过工具调用进入该 feature：

- 新增工具 `explore`
- 功能：一次下发 1~5 个侦查子任务，返回 `scoutIds`
- 约束：参数 schema 限制 `tasks.length <= 5`

与现有模块关系：

1. 主流程由 `TurnOrchestrator` 触发工具 `explore`，再由 `ScoutOrchestrator.runMany()` 执行。
2. 工具执行复用 `AgentToolService`，但通过 `allowedTools` 和预算策略做二次约束。
3. 模型调用复用 provider adapter，新增 `mode='scout'` 的 system prompt/profile。

## 4. 调度策略（何时启动子代理）

新增 `ScoutTriggerPolicy`：

1. 用户问题包含“需要检索/比对/核验”的高不确定性信号。
2. 主代理连续两轮低置信度或工具失败后，允许一次侦查补救。
3. 明确禁止条件：
   - 已达到会话预算上限。
   - 用户显式要求“不要检索/不要额外调用”。
   - 上一轮刚执行过 scout 且冷却未结束。

策略输出：

- `shouldRun: boolean`
- `reason: string`
- `suggestedTask: string`
- `budgetProfile: 'light' | 'normal' | 'deep'`
- `tasks: Array<{ task: string; priority: number }>`（最多 5 条）

## 5. 安全与边界控制

1. 工具白名单：子代理只允许 `search_docs`、`read_doc`、`report_findings` 三个工具。
2. 主会话工具集不暴露 `report_findings`；该工具仅供子代理内部汇报链路使用。
3. 提示词隔离：子代理不可继承主代理全部隐式指令，仅注入必要上下文。
4. 预算硬限制：`maxSteps/maxToolCalls/timeoutMs/tokenBudget` 四重限制。
5. 输出净化：回传前做结构校验与长度裁剪，避免污染主上下文。
6. 并发守卫：同会话内 `maxConcurrentScouts = 5`，不可被请求覆盖。
7. 工具顺序守卫：`report_findings` 必须在至少一次 `read_doc` 成功后才能调用。
8. 软失败原则：顺序违规仅返回可恢复错误与引导提示，不得触发 `FAILED/ABORTED` 终态。
9. 工具上限守卫：达到 `maxToolCalls` 后，拒绝一切新工具调用并强制进入 `report_findings` 汇报阶段。

## 6. 错误处理与降级

1. 子代理超时：主会话收到 `partial` 结果并继续回答。
2. 子代理失败：主会话记录事件并回退到“直接回答 + 不确定性声明”。
3. 工具异常：在子代理内部最多重试 1 次，超限即失败。
4. 任何失败不应中断主会话回合提交。
5. 部分成功：5 个任务中任意失败，主会话聚合成功项并附失败说明。
6. 顺序违规：若在未成功 `read_doc` 前调用 `report_findings`，返回可恢复错误 `TOOL_ORDER_VIOLATION`，并在工具响应中提示 LLM 先执行 `read_doc`，不得终止子任务。
7. 调用超限：若达到 `maxToolCalls` 仍尝试调用工具，返回可恢复错误 `TOOL_CALL_LIMIT_REACHED`，并在响应中强制提示 LLM 立刻执行 `report_findings`。

## 7. 可观测性

新增事件：

1. `SCOUT_TRIGGERED`
2. `SCOUT_STARTED`
3. `SCOUT_TOOL_CALLED`
4. `SCOUT_COMPLETED`
5. `SCOUT_FAILED`
6. `SCOUT_TIMEOUT`
7. `SCOUT_ABORTED`
8. `SCOUT_QUEUED`
9. `SCOUT_SLOT_ACQUIRED`
10. `SCOUT_SLOT_RELEASED`
11. `SCOUT_TOOL_ORDER_VIOLATION`（recoverable）
12. `SCOUT_TOOL_LIMIT_REACHED`
13. `SCOUT_FORCE_REPORT_REQUIRED`

每个事件至少包含：`sessionId, turnId, scoutId, timestamp, mode, reason`。

## 8. 分阶段实施（4 个 PR）

### PR-1：契约与骨架

1. 定义 `ScoutTaskInput/Result` 与状态机。
2. 创建 `ScoutOrchestrator`、`ScoutConcurrencyManager` 空实现与 trace 事件。
3. 打通主会话工具 `explore` 到 `runMany()` 的编译链路（先返回 mock 结果）。

验收：能看到队列与槽位事件，且 `tasks.length > 5` 被 schema 拒绝。

### PR-2：最小可用侦查链路

1. 接入真实模型调用（受限 prompt/profile）。
2. 接入工具白名单、预算控制和工具调用顺序校验（read before report）。
3. 完成并发执行、工具上限强制汇报逻辑与结果聚合器（summary/evidence/confidence）。

验收：单轮可并发执行最多 5 个子任务并回传主会话。

### PR-3：触发策略与降级

1. 实现 `ScoutTriggerPolicy`。
2. 添加超时、失败、取消分支。
3. 在主回合流程集成“部分成功”聚合、降级文案与 fallback 行为。

验收：异常场景主会话仍可稳定完成响应。

### PR-4：测试与文档

1. 单元测试：状态机、策略、结果校验。
2. 集成测试：成功/超时/失败/取消主链路。
3. 文档补齐：配置项、事件、故障排查。

验收：关键路径测试通过，文档可支撑后续迭代。

## 9. 测试清单

1. 正常侦查：返回 `success`，含 evidence。
2. 工具不可用：返回 `failed`，主会话继续。
3. 预算耗尽：返回 `partial`。
4. 超时：返回 `timeout`。
5. 用户中止：返回 `aborted`。
6. 非法结果结构：被 schema 拦截并记错误事件。
7. 并发边界：同时 6 个任务时，1 个排队或直接拒绝（按策略）。
8. 工具入口边界：非工具路径不可直接拉起子任务。
9. 工具顺序边界：未执行成功 `read_doc` 时调用 `report_findings` 必须返回可恢复错误，并附“请先使用 read_doc”的提示。
10. 工具顺序正向：至少一次 `read_doc` 成功后，`report_findings` 可成功执行。
11. 工具调用上限：达到 `maxToolCalls` 后再次调用工具，必须返回 `TOOL_CALL_LIMIT_REACHED`。
12. 强制汇报：触发上限后，下一步必须是 `report_findings`，且不再允许其他工具。

## 10. 配置项建议

- `agent.scout.enabled: boolean = true`
- `agent.scout.defaultTimeoutMs: number = 12000`
- `agent.scout.maxSteps: number = 4`
- `agent.scout.maxToolCalls: number = 3`
- `agent.scout.cooldownTurns: number = 2`
- `agent.scout.allowedTools: string[] = ['search_docs', 'read_doc', 'report_findings']`
- `agent.scout.maxConcurrentScouts: number = 5`（硬上限，不允许 >5）
- `agent.scout.dispatchToolName: string = 'explore'`
- `agent.scout.requireReadBeforeReport: boolean = true`
- `agent.scout.forceReportOnToolLimit: boolean = true`

## 11. 完成定义（DoD）

1. 主会话可通过工具调用触发 1~5 个子任务侦查并拿到结构化结果。
2. 子代理运行受预算与工具白名单约束。
3. 并发上限严格生效（同会话最多 5 个 RUNNING）。
4. `report_findings` 在 `read_doc` 成功前不可调用，违规时返回可恢复错误并提示 LLM 改用 `read_doc`，且不终止子任务。
5. 达到 `maxToolCalls` 后不再允许任何非 `report_findings` 工具调用，并强制立即汇报。
6. 失败、超时、取消均可降级，不阻断主回答。
7. 事件可追踪、可定位问题。
8. 单元与集成测试覆盖核心路径。
