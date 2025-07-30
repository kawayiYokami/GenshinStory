# Genshin Story

这是一个用于浏览和检索游戏剧情数据的静态 Web 应用。

## 核心思想

项目的核心思想是**数据与展示分离**：
- **数据处理**: 使用纯 Python 脚本，将原始的游戏数据解析、转换并生成为一系列 Markdown 文件。
- **内容展示**: 使用一个独立的 Vue.js 应用，负责读取这些生成的 Markdown 文件，并提供一个美观、可交互的界面进行展示和搜索。

## 项目结构

```
.
├── scripts/              # 用于生成数据的 Python 脚本
├── web/
│   └── docs-site/        # Vue.js 前端应用
├── start_web.bat         # 一键启动 Web 服务器的批处理文件
└── README.md             # 本文档
```

## 快速开始

请遵循以下步骤在您的本地计算机上运行本项目。

### 先决条件

- **Python**: 版本需 >= 3.10
- **uv**: 用于安装 Python 依赖。如果您的系统中还没有 `uv`，请先通过以下命令安装：
  ```shell
  pip install uv
  ```
- **Node.js**: 用于运行和构建前端应用。

### 步骤 1: 安装项目依赖

项目分为 Python 数据处理部分和 Node.js 前端部分，需要分别安装依赖。

1.  **安装 Python 依赖**:
    在项目根目录下打开终端，运行：
    ```bash
    uv install
    ```

2.  **安装前端依赖**:
    进入前端应用目录并安装依赖。
    ```bash
    cd web/docs-site
    npm install
    ```

### 步骤 2: 生成数据内容

返回项目根目录。`scripts` 目录下的脚本负责将游戏数据转换为前端可以展示的 Markdown 文件。

请按顺序执行以下脚本：
```bash
python scripts/hsr_create_cache.py
python scripts/hsr_generate_markdown.py
python scripts/gi_create_cache.py
python scripts/gi_generate_markdown.py
```
执行完毕后，所需的数据和 Markdown 文件会生成在前端项目的指定目录中。

### 步骤 3: 构建前端应用

数据生成后，我们需要构建生产环境下的静态前端文件。

确保您当前位于 `web/docs-site` 目录下，然后运行：
```bash
npm run build
```
此命令会将 Vue.js 应用打包成优化后的 HTML, CSS 和 JavaScript 文件，存放在 `web/docs-site/dist` 目录中。

### 步骤 4: 启动并浏览网站

回到项目的根目录，您会找到一个名为 `start_web.bat` 的文件。

**双击运行 `start_web.bat`**。

它会自动为您启动一个本地的 HTTP 服务器，并打开您的默认浏览器访问 `http://localhost:8000`。现在您可以看到运行中的网站了。

