# AI-First 垂直架构重构方案

- 日期：2026-02-14
- 目标：把当前 Agent/Scout 相关代码重构为「面向 AI 查找与修改效率」的垂直结构，做到职责清晰、会话隔离、改动可控。

## 0. 执行进展（2026-02-14）

### 已完成
1. 子代理能力收敛：
   - 主会话移除 `report_findings` 工具定义；
   - 子会话保留 `search_docs/read_doc/report_findings` 并在 `scout-agent` 内部约束。
2. `scout-agent` 内部垂直拆分：
   - `contracts.ts`（契约）
   - `prompt.ts`（子代理系统提示词）
   - `sessionTools.ts`（子会话工具守卫与汇报规则）
   - `childSessionRunner.ts`（运行器）
3. `AgentApiService` 第二阶段拆分：
   - `provider/AgentProtocolRuntime.ts`（协议与 provider 调用）
   - `stream/toolEventNormalizer.ts`（事件归一）
   - `stream/AgentStreamProjector.ts`（UI 投影）
   - `AgentApiService.ts` 退化为编排层。
4. `AgentEvent` 契约化（第三阶段）：
   - `events/AgentEvent.ts` 定义统一事件类型；
   - `events/agentEventAdapter.ts` 统一转换 `fullStream part` 与 `steps backfill`；
   - `AgentStreamProjector` 只消费 `AgentEvent`，不再直接依赖 provider 原始事件结构。
5. 验证：
   - `npm run build` 通过；
   - `npm run test -- AgentApiService` 通过（已修复 vitest hoist mock 问题）。

## 1. 设计原则（面向 AI）

1. 垂直切片优先：一个能力在一个目录内闭环（入口、契约、编排、实现、测试）。
2. 契约先行：每个能力先定义 `contracts.ts`，再写实现，减少隐式耦合。
3. 会话硬隔离：主会话与子会话只通过结构化结果通信，不共享消息流。
4. 事件统一：Provider 差异先归一成 `AgentEvent`，再投影到 UI。
5. 规则代码化：顺序约束、调用预算、并发上限必须在运行时校验，不只依赖提示词。

## 2. 目标目录结构

```text
web/docs-site/src/features/
  main-session/
    index.ts
    contracts.ts
    runtime.ts
    orchestrator.ts
    tools/
      search_docs.ts
      read_doc.ts
      explore.ts
    projector/
      chatProjector.ts
    ui/
      MessageBubble.vue
      ToolResultCard.vue
    __tests__/
    README.md

  scout-agent/
    index.ts
    contracts.ts
    prompt.ts
    policy.ts
    runner.ts
    orchestrator.ts
    tools/
      search_docs.ts
      read_doc.ts
      report_findings.ts
    __tests__/
    README.md

  ai-kernel/
    providerAdapter.ts
    eventTypes.ts
    toolRuntime.ts
```

## 3. 职责边界

### main-session
1. 接收用户输入并发起回合。
2. 仅调用 `search_docs/read_doc/explore/ask_choice`。
3. 渲染主会话消息与工具卡片，不渲染子代理内部对话。

### scout-agent
1. 执行 `explore` 下发的子任务（1~5 并发）。
2. 子会话只允许 `search_docs/read_doc/report_findings`。
3. 输出 `ExploreReport[]`，主会话只消费最终报告。

### ai-kernel
1. 屏蔽 Provider 差异。
2. 输出统一事件流（tool-called/tool-resulted/text-delta/finish）。
3. 给上层提供稳定执行接口。

## 4. 硬约束（必须保留）

1. 子任务并发上限：5。
2. 子任务最大探索时长：10 分钟。
3. 子任务非 report 工具调用上限：100 次。
4. `report_findings` 必须在至少一次成功 `read_doc` 之后调用。
5. 未读先报必须返回可恢复错误，不得终止子会话。
6. 达到调用上限后拒绝继续工具调用，并强制立即汇报。

## 5. 导入规则（防止再次耦合）

1. Feature 间只允许从对方 `index.ts` 导入。
2. 禁止跨 Feature 深路径引用（例如直接引用 `../x/internal/*.ts`）。
3. 每个 Feature 必须维护 `README.md`（入口、状态机、可改点、禁区）。

## 6. 分阶段迁移（建议 4 步）

### Phase 1：契约与入口收敛
1. 新建 `main-session/contracts.ts` 与 `scout-agent/contracts.ts`。
2. 为两个 Feature 增加 `index.ts` 统一导出。
3. 把外部引用改为只走 `index.ts`。

### Phase 2：执行链路拆分
1. 将 `AgentApiService` 拆为：
   - Provider 适配层（ai-kernel）
   - 事件归一层（AgentEvent）
   - UI 投影层（chatProjector）
2. 保证任何 Provider 路径都能产出一致工具事件。

### Phase 3：Scout 能力闭环
1. 把子代理策略、提示词、运行器收敛到 `scout-agent/`。
2. 保留当前约束：并发 5、10 分钟、100 次、read-before-report。
3. `explore` 只负责任务派发与结果回传。

### Phase 4：UI 与可观测
1. 工具卡片仅展示主会话工具调用与结果（结果默认折叠，不展示参数）。
2. 补充探索任务数、已完成任务数、子代理工具调用统计。
3. 增加结构化事件日志，方便回放排障。

## 7. 完成定义（DoD）

1. AI 修改某一能力时，仅需进入一个目录即可完成大部分变更。
2. 主会话/子会话链路彻底独立，主会话仅见 `explore` 调用与回传。
3. 所有硬约束有代码守卫和测试，不依赖“提示词自觉”。
4. 新增 Provider 或 UI 形态时，不需要回改 Scout 业务规则。
