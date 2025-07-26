# Genshin Story

这是一个用于浏览和检索游戏剧情数据的 Web 应用。项目采用前后端分离架构，并使用 Docker 进行了完全容器化，以实现一键部署和运行。

- **后端**: 使用 `FastAPI` 构建，负责提供数据 API。
- **前端**: 使用 `Vue.js` 构建，负责展示数据和用户交互。
- **数据层**: 由 `game_data_parser` 模块提供支持，该模块负责解析和管理游戏数据。

## 项目结构

```
.
├── game_data_parser/   # 核心数据解析模块 (Python)
├── web/
│   ├── backend/        # FastAPI 后端应用
│   └── frontend/       # Vue.js 前端应用
├── docker-compose.yml  # Docker 服务编排文件
├── game_data.cache     # 必需的游戏数据缓存文件
└── README.md           # 本文档
```

- `game_data_parser/`: 一个独立的 Python 库，负责从 `game_data.cache` 加载和解析所有游戏数据，并为后端提供结构化的数据服务。
- `web/backend/`: 基于 FastAPI 的后端服务。它利用 `game_data_parser` 模块，并通过 RESTful API 将数据暴露给前端。
- `web/frontend/`: 基于 Vue.js 的单页面应用 (SPA)。它通过调用后端的 API 来获取数据，并在浏览器中进行渲染。

## 快速开始 (使用 Docker)

本项目已经完全配置为通过 Docker 运行。您无需在本地安装 Python, Node.js 或任何相关的依赖。

### 先决条件

- [Docker](https://www.docker.com/get-started) 已安装并正在运行。
- 确保 `game_data.cache` 文件位于项目的根目录。

### 启动应用

1.  **克隆或下载项目到本地。**

2.  **打开终端，进入项目根目录。**

3.  **使用 `docker-compose` 构建并启动服务：**

    ```bash
    docker-compose up --build
    ```

    - `--build` 参数会强制 Docker 根据 `Dockerfile` 重新构建镜像。首次运行时是必需的。
    - 该命令会同时启动 `backend` 和 `frontend` 两个服务。
    - 您将在终端看到来自两个服务的日志输出。

4.  **访问应用**

    构建完成后，打开您的浏览器并访问：
    **[http://localhost](http://localhost)**

    您应该能看到应用的前端界面。

### 工作原理

- `docker-compose` 根据 `docker-compose.yml` 文件启动两个服务：`backend` 和 `frontend`。
- **后端服务 (`backend`)**:
    - 使用 `web/backend/Dockerfile` 构建。
    - 这是一个多阶段构建的 Python 镜像，包含了所有依赖和应用代码。
    - FastAPI 应用在容器的 `8666` 端口上运行。此端口不对外暴露，仅在 Docker 内部网络中可访问。
- **前端服务 (`frontend`)**:
    - 使用 `web/frontend/Dockerfile` 构建。
    - 这是一个多阶段构建的 Node.js/Nginx 镜像。
    - 第一阶段使用 `npm run build` 构建出静态文件。
    - 第二阶段将构建好的静态文件（HTML, CSS, JS）放入一个轻量级的 `Nginx` 服务器中。
    - Nginx 在容器的 `80` 端口上提供服务，该端口被映射到您主机的 `80` 端口。
- **服务通信**:
    - 当您在浏览器中与前端交互时，前端会向 `/api/...` 发出请求。
    - `Nginx` (在前端容器中) 根据 `web/frontend/nginx.conf` 的配置，将所有 `/api/` 的请求反向代理到 `http://backend:8666`。
    - Docker 的内部 DNS 会将服务名 `backend` 解析为后端容器的内部 IP 地址，从而实现前后端通信。

### 停止应用

在您启动 `docker-compose` 的终端中，按下 `Ctrl + C`。

要彻底移除容器和网络，可以运行：
```bash
docker-compose down
```