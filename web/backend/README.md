# 后端运行手册（以项目根目录为准）

本文档所有命令都假设你当前目录是项目根目录：`E:\github\story`

## 1. 启动后端

```powershell
uv run uvicorn --app-dir web/backend main:app --host 127.0.0.1 --port 8000
```

说明：
- 启动后会自动检查并构建缺失索引。
- 健康检查：`GET http://127.0.0.1:8000/health`

## 2. 重启后端

后端没有单独“重启命令”，按下面两步：

1. 在运行窗口 `Ctrl + C` 停止服务  
2. 重新执行启动命令

```powershell
uv run uvicorn --app-dir web/backend main:app --host 127.0.0.1 --port 8000
```

## 3. 重建索引（更新搜索库）

### 3.1 全部域重建

```powershell
uv run python web/backend/indexer.py
```

### 3.2 指定域重建

```powershell
uv run python web/backend/indexer.py gi
uv run python web/backend/indexer.py hsr
uv run python web/backend/indexer.py zzz
```

说明：
- 如果你修改了 `indexer.py` 的 schema（例如新增字段），必须重建索引。
- 后端启动时若发现 schema 不匹配，也会尝试自动重建。

## 4. 本地调试搜索（不走 HTTP）

### 4.1 目录搜索

```powershell
uv run python web/backend/debug_search_cli.py --domain gi --mode catalog --query 北斗 --max-results 20
```

### 4.2 文档搜索

```powershell
uv run python web/backend/debug_search_cli.py --domain gi --mode docs --query 一千次 --max-results 20 --generate-summary
```

### 4.3 搜索前先重建索引

```powershell
uv run python web/backend/debug_search_cli.py --domain gi --mode catalog --query 北斗 --rebuild-index
```

### 4.4 查看原始 JSON

```powershell
uv run python web/backend/debug_search_cli.py --domain hsr --mode docs --query 阅读物 --raw-json
```

## 5. 关键 API 速查

### 5.1 搜索

- 目录搜索：
  `GET /api/{domain}/search?mode=catalog&query=...`
- 深度搜索：
  `GET /api/{domain}/search?mode=docs&query=...&maxResults=50&generateSummary=true`

### 5.2 读取文档

- 结构化读取：
  `GET /api/{domain}/doc?path=...`
- 读取原始 Markdown：
  `GET /api/{domain}/doc/raw?path=...`

### 5.3 信源链接解析（仅 `gi`/`hsr`）

`GET /api/{domain}/resolve-link?title=...&k=3&minScore=200`

示例：

```powershell
curl "http://127.0.0.1:8000/api/gi/resolve-link?title=%E8%A7%92%E8%89%B2/%E7%8E%9B%E6%8B%89%E5%A6%AE-508006.md&k=3&minScore=200"
```

### 5.4 本机调试命令（仅 localhost）

`POST /api/debug/local-command`

可用 action：
- `search_catalog`
- `search_docs`
- `rebuild_index`
- `invalidate_index`
- `resolve_link`

## 6. 常见问题

### Q1：改了搜索逻辑但结果没变化

先重建索引，再重启后端：

```powershell
uv run python web/backend/indexer.py gi hsr
uv run uvicorn --app-dir web/backend main:app --host 127.0.0.1 --port 8000
```

### Q2：某域提示索引不存在

说明该域索引目录为空或缺失，执行：

```powershell
uv run python web/backend/indexer.py <domain>
```

### Q3：`resolve-link` 不支持 `zzz`

这是设计如此，当前仅支持 `gi` 与 `hsr`。

