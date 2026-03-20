# AGENT.md

本文档为 AI 助手提供项目开发指导。

## 项目概述

这是一个前后端分离的 AI 对话平台：
- **前端**: Vue 3 + TypeScript + Vite + Pinia + TailwindCSS + DaisyUI，使用 Vercel AI SDK
- **后端**: FastAPI (Python)，提供搜索和文档服务 API

支持与原神、崩坏：星穹铁道、绝区零的游戏角色进行沉浸式互动。

## 构建与开发命令

### 前端

```bash
cd web/docs-site
pnpm install
pnpm dev
pnpm typecheck
pnpm build
```

### 后端

```bash
# 同步依赖（项目根目录）
uv sync

# 启动后端
cd web/backend
uv run uvicorn main:app --reload
```

### 搜索模式

前端支持两种搜索模式，通过环境变量切换：

| 环境变量 | 值 | 说明 |
|----------|-----|------|
| `VITE_SEARCH_MODE` | `local` (默认) | 前端本地搜索，无需后端 |
| `VITE_SEARCH_MODE` | `backend` | 调用后端 Tantivy API 搜索 |
| `VITE_BACKEND_URL` | URL | 后端地址，默认 `http://localhost:8000` |

配置文件：`web/docs-site/.env` 或 `.env.local`

示例：
```
VITE_SEARCH_MODE=backend
VITE_BACKEND_URL=http://localhost:8000
```

## 架构概览

### 前端目录结构

```
web/docs-site/src/
├── assets/          # 静态资源
├── components/      # 通用组件
├── composables/     # Vue 组合式函数
├── features/        # 功能模块
│   ├── agent/       # AI 对话核心
│   ├── app/         # 全局应用状态和服务
│   ├── docs/        # 文档浏览
│   ├── memory/      # 记忆系统
│   ├── navigation/  # 导航
│   ├── scout-agent/ # 侦察代理
│   ├── search/      # 搜索引擎
│   ├── settings/    # 配置设置
│   └── viewer/      # 文档查看器
├── layouts/         # 布局组件 (三面板)
├── lib/             # 核心库
│   ├── llm/         # LLM 提供商服务
│   ├── searchProvider/
│   ├── markdown/
│   ├── tokenizer/
│   ├── streaming/
│   └── linkProcessor/
├── router/          # 路由配置
├── views/           # 页面视图
└── workers/         # Web Workers
```

### 后端目录结构

```
web/backend/
├── main.py          # FastAPI 入口
├── config.py        # 配置
├── search_service.py # 搜索服务
├── doc_service.py   # 文档服务
├── indexer.py       # 索引构建
└── requirements.txt # Python 依赖
```

### 前后端通信

```
Vue 组件 → fetch() → FastAPI (/api/{domain}/*)
```

API 端点：
- `GET /api/{domain}/index` - 获取目录索引
- `GET /api/{domain}/search` - 搜索文档
- `GET /api/{domain}/doc` - 读取文档

### 核心模块

| 模块 | 功能 |
|------|------|
| `features/agent/` | AI 对话核心 |
| `features/search/` | 搜索引擎 |
| `features/settings/` | 用户设置 |
| `features/app/stores/` | 状态管理 |
| `lib/` | 核心工具库 |

### Agent 架构

```
AgentService (AI 引擎核心)
├── AgentFlowService (流程控制)
├── AgentApiService (API 通信)
│   └── AgentProtocolRuntime (协议运行时)
├── AgentResponseHandlerService (响应处理)
│   └── parsers/ (JSON 解析)
├── AgentContextService (上下文管理)
│   └── contextOptimizerService (上下文压缩)
└── localToolsService (工具实现)
    ├── search_docs (调用后端 API)
    └── read_doc (调用后端 API)
```

### 组件层级

```
MainLayout.vue (三面板布局)
├── Navbar
├── Sidebar
└── MainContent
      ├── AgentChatView
      │     ├── AgentNavbarContent
      │     ├── ChatHistoryPanel
      │     │     └── MessageBubble.vue
      │     │           └── QuestionSuggestions.vue
      │     ├── ChatInputPanel
      │     └── AgentChatModals
      ├── SearchView
      ├── ItemListView
      └── SettingsView
```

### 状态管理 (Pinia)

| Store | 用途 |
|-------|------|
| `useAgentStore` | AI 状态、会话、消息 |
| `useAppStore` | 应用全局状态 |
| `useConfigStore` | 配置管理 |
| `useDataStore` | 数据状态 |
| `useThemeStore` | 主题管理 |

### 数据存储

| 数据类型 | 存储位置 |
|----------|----------|
| 预设角色 | `public/domains/{domain}/core/roles/*.yaml` |
| Persona | `public/domains/{domain}/core/personas/*.yaml` |
| 自定义角色 | LocalStorage (`customPersonas`) |
| 自定义指令 | LocalStorage (`customInstructions`) |
| 会话历史 | IndexedDB (via localforage) |
| 搜索索引 | `data/{domain}/metadata/` |

### 路由

- `/domain/:domain/agent` - AI 聊天
- `/domain/:domain/category/:categoryName/:pathMatch(.*)*` - 内容浏览
- `/domain/:domain/search` - 搜索
- `/domain/:domain/settings` - 设置

### LLM 支持

- OpenAI
- Google Gemini
- DeepSeek

### 表情系统

- 格式: `:表情名:` 在提示词中使用
- 配置: `public/meme/memes_data.json`
- 索引: `public/meme/meme_index.json`
- 角色专属: YAML 中的 `memePack` 字段

## 开发约定

### 前端规则

- DaisyUI 组件优先
- 使用 Pinia 进行状态管理
- 配置文件"有改动才允许保存"
- 对话窗口保持极简

### 后端规则

- 使用 FastAPI 异步框架
- 统一使用 Pydantic 进行数据校验
- 异常使用 HTTPException 处理

### 代码组织

- 保持模块拆分，避免超大单文件
- 组件层保持轻薄，核心逻辑封装在 services 或 composables
- 注释说明意图而非实现

#### 紧凑优先 vs 按功能组织

- **紧凑优先**: 功能集中在一个场景、强耦合且变更总在同一处，使用注释分区（如 `// ==================== 配置管理 ====================`）可快速定位。
- **按功能组织**: 出现清晰职责边界，或多人并行开发导致同文件冲突频繁，应按 `features/chat/`、`features/archive/` 等目录分组。

判断标准：
- 规模：单文件接近 500-800 行，或公开函数数量接近 20
- 耦合：同文件内出现多个低相关子域
- 协作：多人经常改同文件、冲突率高
- 可测试性：难以对局部逻辑做独立单测
- 变更成本：每次重构/编译/回归都要牵动大范围代码

迁移步骤：
1. 先抽"纯数据与类型"（如 `types.ts`、`models.ts`）
2. 再抽"稳定服务逻辑"（如 `service.ts`、`use-*.ts`）
3. 最后抽"入口协调层"（如 `view glue`），保证外部调用面不变

#### 适度重复的边界

- 可接受重复：同一模块内短小重复（约 <= 20 逻辑行，且重复片段 <= 2 处）可保留
- 触发抽取条件：
  - 相同处理步骤出现 >= 3 次
  - 相同错误处理/回滚逻辑出现 >= 3 次
  - 单段重复超过约 8-10 行且后续仍在增长
  - 因重复导致一致性问题或测试成本明显上升
- 平衡准则：先保留短小直接实现；当共享逻辑超过阈值再抽取成公用函数

### 提交信息规范

- 格式: `type(scope): 简要中文描述`
- 类型: `feat`、`fix`、`perf`、`refactor`、`docs`、`chore`

### 计划与归档

- 新功能先写计划文档 (`plan/`)
- 计划获确认后才实现
- 功能完成需用户测试通过后才能归档
- 归档文件带日期: `20260314_xxx计划.md`
- 归档文件必须基于最终实现状态更新，禁止仅按中间实现归档
- 每个归档文件必须包含两部分:
  - 实现总结 (implementation summary)
  - 归档报告 (archival report)
- 归档报告必须至少包含: 变更点、验证/测试结论、负责人签名与时间戳
