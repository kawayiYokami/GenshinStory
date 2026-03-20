# Genshin Story V2 - 与您最喜爱的角色进行 AI 对话

Genshin Story 已经进化为一个先进的 AI 对话平台，您可以选择并扮演游戏中的角色，通过自然语言与庞大的游戏知识库进行智能交互和探索。

## 功能特性

- **沉浸式多角色 AI 对话**:
    - 支持原神、崩坏：星穹铁道、绝区零三大游戏内容
    - 数百个预设角色，每个角色拥有独特的性格、知识体系与语音风格
    - 让您喜爱的角色成为您的专属 AI 助手

- **智能工具生态系统**:
    - **文档搜索**: 毫秒级精准定位游戏攻略、数据手册
    - **文档阅读**: 直接读取并理解 Markdown 内容
    - **智能探索**: 并行子代理深度挖掘，5 路同时检索，10 分钟超长续航
    - **持久记忆**: 跨会话保存重要信息，AI 越用越懂你
    - **交互式提问**: 支持多选项分支对话，用户选择更轻松
    - **结构化工具调用 + 思维链推理**，释放模型全部能力

- **对话管理**:
    - 上下文自动压缩，突破 Token 限制，长对话无忧
    - 会话历史持久化，随时回顾、继续或删除
    - 完整数据导出/导入，备份迁移零负担

- **极致交互体验**:
    - 流式打字机效果，还原真实对话感
    - 游戏内建表情包系统，角色更有"灵魂"
    - 三面板布局，文档阅读与对话两不误
    - 暗黑模式，护眼舒适

## 架构与运行模式

当前项目是前后端分离架构：

- 前端：`web/docs-site`（Vue 3 + Vite）
- 后端：`web/backend`（FastAPI + Tantivy，提供搜索与文档 API）

搜索模式支持：

- `local`（默认）：前端本地搜索，不依赖后端。
- `backend`：前端调用 FastAPI 后端接口。

前端通过环境变量切换：

- `VITE_SEARCH_MODE=local|backend`
- `VITE_BACKEND_URL=http://127.0.0.1:8000`

## 部署模式说明

### 纯前端部署（推荐默认）

- 只部署 `web/docs-site` 静态站点。
- 使用 `VITE_SEARCH_MODE=local`。
- 不需要启动/部署 `web/backend`。

适用场景：
- Netlify / Vercel / GitHub Pages 这类纯静态托管。
- 希望构建链路更简单、发布更稳定。

### 前后端一体方案（可选）

- 前端仍然部署 `web/docs-site`。
- 另行部署 `web/backend`（FastAPI）。
- 前端环境变量改为：
  - `VITE_SEARCH_MODE=backend`
  - `VITE_BACKEND_URL=<你的后端地址>`

## 最简部署（从克隆开始）

仓库地址：`https://github.com/kawayiYokami/GenshinStory/tree/feature/backend-tantivy`

```bash
git clone -b feature/backend-tantivy --single-branch https://github.com/kawayiYokami/GenshinStory.git
cd GenshinStory
corepack enable
corepack prepare pnpm@latest --activate
pnpm --dir web/docs-site install
pnpm --dir web/docs-site build
```

### build 完之后怎么启动？

推荐一键脚本（同时启动前后端，并挂在 `screen`）：

```bash
# Ubuntu/Debian 先安装 screen
sudo apt-get update && sudo apt-get install -y screen

# 赋予执行权限（只需一次）
chmod +x scripts/start_with_screen.sh

# 一键启动前端 + 后端
./scripts/start_with_screen.sh start
```

默认启动配置：

- 前端：`pnpm preview --host 0.0.0.0 --port 5713`
- 后端：`uv run uvicorn main:app --host 127.0.0.1 --port 8000 --app-dir web/backend`

常用命令：

```bash
# 查看运行状态
./scripts/start_with_screen.sh status

# 重启前后端
./scripts/start_with_screen.sh restart

# 停止前后端
./scripts/start_with_screen.sh stop

# 进入 screen 看日志
screen -r genshinstory_frontend
screen -r genshinstory_backend
```

可选端口覆盖：

```bash
FRONT_PORT=8080 BACK_PORT=9000 ./scripts/start_with_screen.sh restart
```

## 快速开始

请遵循以下步骤在您的本地计算机上运行本项目。

### 先决条件

- **Python**: 版本需 >= 3.10
- **uv**: 用于安装 Python 依赖。如果您的系统中还没有 `uv`，请先通过以下命令安装：
    ```shell
    pip install uv
    ```
- **Node.js**: 版本需 >= 20，用于运行和构建前端应用。
- **AI 模型访问权限**: 您需要拥有一个兼容 OpenAI API 的服务提供商的 API Key。

### 步骤 1: 安装项目依赖

确保你已在项目根目录（`GenshinStory` 文件夹）下：

1. **安装 Python 依赖**:
    ```bash
    uv sync
    ```

2. **安装前端依赖**:
    ```bash
    cd web/docs-site
    pnpm install
    ```

### 步骤 2: 生成数据内容

返回项目根目录，执行统一生成脚本：

```bash
uv run python scripts/generate_all_content.py
```

### 步骤 3: 启动前端开发服务器

推荐使用开发服务器以获得最佳体验。

```bash
cd web/docs-site
pnpm dev
```

默认地址为 `http://127.0.0.1:5713`。

### 步骤 4: （可选）启动后端搜索服务

如果你要使用 `backend` 搜索模式，请启动 FastAPI 后端：

```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000 --app-dir web/backend
```

并在 `web/docs-site/.env` 中配置：

```env
VITE_SEARCH_MODE=backend
VITE_BACKEND_URL=http://127.0.0.1:8000
```

修改 `.env.local` 后请重启 `pnpm dev`。

### 步骤 5: （可选）世界树记忆导入/导出

后端启动后会自动创建 `web/backend/world_tree.db` 数据库。如需批量导入或导出世界树记忆，使用 `scripts/world_tree_csv.py`：

**导出记忆到 CSV：**
```bash
uv run python scripts/world_tree_csv.py export --file data/world_tree_export.csv
```

**从 CSV 导入记忆：**
```bash
uv run python scripts/world_tree_csv.py import --file data/world_tree_import.csv
```

CSV 文件格式要求：
| 列名 | 说明 |
|------|------|
| id | 唯一标识符 |
| judgment | 记忆内容（必填） |
| reasoning | 推理/理由 |
| keywords | 关键词，用 `\|` 分隔 |
| metadata | JSON 格式元数据 |
| createdAt | 创建时间（ISO 格式） |
| updatedAt | 更新时间（ISO 格式） |

注意：导入时会自动跳过 `id` 或 `judgment` 为空的行。

### 步骤 6: 配置 AI Agent

应用启动后，您需要进行初次配置：

1. 在界面中，点击模型选择区域，展开配置面板。
2. 创建一个新配置。
3. 填入您的 **API URL** 和 **API Key**。
4. 点击"刷新"按钮获取并选择一个可用的模型。
5. 现在，您可以开始与您选择的 AI 角色进行对话了！

## 部署说明

当前仓库默认按“纯前端静态站点”部署（`web/docs-site/dist`），文档内容已包含在仓库内，构建时无需再执行内容生成脚本。

后端（FastAPI）始终是独立服务，只有在你启用 `backend` 搜索模式时才需要部署。
