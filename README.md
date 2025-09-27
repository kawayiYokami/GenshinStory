# Genshin Story V2 - 与您最喜爱的角色进行 AI 对话

Genshin Story 已经进化为一个先进的 AI 对话平台，您可以选择并扮演游戏中的角色，通过自然语言与庞大的游戏知识库进行智能交互和探索。

## 功能特性

-   **多角色 AI Agent 对话**:
    -   您可以从多个预设的游戏角色（如钟离、阮•梅、芙宁娜等）中选择一个作为您的 AI Agent。
    -   每个角色都拥有独特的“个性”和知识，为您提供沉浸式的对话体验。

-   **强大的上下文感知与工具使用**:
    -   AI Agent 能够“阅读”整个项目的 Markdown 文件结构，精准定位信息。
    -   Agent 具备执行本地工具的能力，例如，当需要时，它可以主动搜索文件内容来回答您提出的复杂问题。

-   **高度可配置的 LLM 连接**:
    -   您可以轻松连接到任何兼容 OpenAI API 标准的大语言模型服务（如 OpenAI, Groq, Kimi, Zhipu AI 等）。
    -   支持自定义模型的参数，包括上下文长度（Max Tokens）和温度（Temperature），以满足不同的需求。

-   **流畅的现代化交互体验**:
    -   对话内容采用流式响应（Streaming），打字机效果让等待不再枯燥。
    -   完整的会话历史记录管理，您可以随时回顾、继续或删除之前的对话。
    -   支持在对话中直接打开和预览相关的游戏文档。

## 快速开始

请遵循以下步骤在您的本地计算机上运行本项目。

### 先决条件

-   **Python**: 版本需 >= 3.10
-   **uv**: 用于安装 Python 依赖。如果您的系统中还没有 `uv`，请先通过以下命令安装：
    ```shell
    pip install uv
    ```
-   **Node.js**: 版本需 >= 20，用于运行和构建前端应用。
-   **AI 模型访问权限**: 您需要拥有一个兼容 OpenAI API 的服务提供商的 API Key。

### 步骤 1: 安装项目依赖

1.  **安装 Python 依赖**:
    ```bash
    uv sync
    ```

2.  **安装前端依赖**:
    ```bash
    cd web/docs-site
    npm install
    ```

### 步骤 2: 生成数据内容

返回项目根目录。请依次执行以下脚本：

1.  **生成 Markdown 内容**:
    ```bash
    python scripts/hsrwiki_generate_markdown.py
    python scripts/giwiki_generate_markdown.py
    python scripts/zzz_generate_markdown.py
    ```

2.  **生成 AI 感知目录树**:
    ```bash
    python scripts/hsrwiki_generate_catalog_tree.py
    python scripts/giwiki_generate_catalog_tree.py
    python scripts/zzz_generate_catalog_tree.py
    ```

### 步骤 3: 启动前端开发服务器

推荐使用开发服务器以获得最佳体验。

**进入前端目录并启动服务器**:
```bash
cd web/docs-site
npm run dev
```
此命令会启动一个本地开发服务器，通常位于 `http://localhost:5173`。

### 步骤 4: 配置 AI Agent

应用启动后，您需要进行初次配置：

1.  在界面中，点击模型选择区域，展开配置面板。
2.  创建一个新配置。
3.  填入您的 **API URL** 和 **API Key**。
4.  点击“刷新”按钮获取并选择一个可用的模型。
5.  现在，您可以开始与您选择的 AI 角色进行对话了！

---

*注意：旧的 `start_web.bat` 和 `npm run build` 流程依然可用，但主要用于生产环境的静态部署。对于开发和本地使用，我们强烈推荐 `npm run dev`。*