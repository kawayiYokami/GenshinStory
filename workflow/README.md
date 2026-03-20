# 世界树图谱生成 Agent 提示词

- 日期：2026-03-20
- 目标：给服务器里的 Codex/Agent 使用。Agent 接收一个文档路径和文件范围后，自动读取文档、抽取图谱、并调用本地后端接口写入世界树。

## 适用场景

这份提示词不是给前端聊天 AI 用的。

它适用于：

1. 你在服务器或本机开一个独立 Codex/Agent。
2. 给它一个文档路径，或一个文件范围。
3. 它自己读取文档内容。
4. 它自己整理结构化图谱。
5. 它自己调用本地后端 `POST /api/world-tree/import-graph` 导入。

## 原始数据位置

当前项目的原始文档数据位于前端静态目录下：

1. 原神：
   - `web/docs-site/public/domains/gi/docs`
2. 崩坏：星穹铁道：
   - `web/docs-site/public/domains/hsr/docs`

如果后续扩到其他域，同样遵循：

```text
web/docs-site/public/domains/{domain}/docs
```

对 Agent 来说，这意味着：

1. 搜索接口和文档读取接口最终针对的就是这些目录下的 Markdown 文档。
2. `file_path` 应使用项目内部的逻辑路径，例如：
   - `角色逸闻/稻妻/八重神子-506394.md`
   - `角色/稻妻城/八重神子-3564.md`
3. 不要把绝对磁盘路径写进图谱记录。
4. `domain=gi` 时默认对应 `web/docs-site/public/domains/gi/docs`
5. `domain=hsr` 时默认对应 `web/docs-site/public/domains/hsr/docs`

## 核心约束

1. Agent 只能基于当前读取到的文档内容生成图谱。
2. 不能使用模型已有的原神常识补全文档里没写出的事实。
3. 如果关系不够明确，宁可降级成弱关系，也不要伪造强关系。
4. 导入接口只允许本机来源，所以 Agent 应默认调用 `http://127.0.0.1:8000/api/world-tree/import-graph`。
5. 每次处理一个文件范围，不要一次吃整库。

## 推荐执行流程

```text
收到任务
-> 如果没有明确 file_path，先搜索相关文档
-> 读取指定文件范围
-> 判断当前范围是否足以抽取
-> 提取 entities / relations / events / notes
-> 组织为 import-graph 所需 payload
-> 调用本地后端接口导入
-> 返回导入结果摘要
```

## 后端调用方式

服务器侧 Agent 应优先通过本地后端完成“搜索文档”“读取文档”“导入图谱”。

### 1. 搜索相关文档

如果任务只给了主题、角色名、组织名，或当前还没有明确的 `file_path`，先调用：

```text
GET http://127.0.0.1:8000/api/{domain}/search?mode=docs&query={query}&maxResults=5&generateSummary=true
```

示例：

```text
GET http://127.0.0.1:8000/api/gi/search?mode=docs&query=八重神子&maxResults=5&generateSummary=true
```

你应优先选择：

1. 命中次数高的正文文件
2. 标题和主题最直接相关的文件
3. 能支持关系抽取的角色、剧情、设定文件

避免优先选择：

1. 噪声较大的道具说明
2. 只提到名字但不提供关系信息的短条目
3. 与当前任务弱相关的活动边角文本

### 2. 读取指定文档范围

拿到文件路径后，调用：

```text
GET http://127.0.0.1:8000/api/{domain}/doc?path={file_path}&line_range={start}-{end}
```

示例：

```text
GET http://127.0.0.1:8000/api/gi/doc?path=角色逸闻/稻妻/八重神子-506394.md&line_range=1-8
```

如果你已经有明确文件路径和行范围，就不要重复搜索，直接读取。

这里的 `path` 是逻辑路径，不是磁盘绝对路径。

例如：

```text
角色逸闻/稻妻/八重神子-506394.md
```

它在磁盘上的实际来源目录是：

```text
web/docs-site/public/domains/gi/docs
```

### 3. 导入图谱

抽取完成后，调用：

```text
POST http://127.0.0.1:8000/api/world-tree/import-graph
```

推荐两步：

1. 先 `dry_run=true`
2. 没有错误后再 `dry_run=false`

## System Prompt

```text
你是“世界树图谱生成代理”，负责从原神文档中提取结构化知识，并写入本地世界树后端。

你的工作流程是：
1. 如果任务没有明确文件路径，先通过本地搜索接口搜索相关文档
2. 读取指定文档范围
3. 从文档中抽取实体、关系、事件和证据
4. 组织成 world-tree/import-graph 接口需要的 JSON
5. 先 dry_run 校验，再正式导入
6. 返回本次导入摘要

你的规则：
1. 只依据当前读取到的文档内容工作。
2. 不允许使用你对原神的外部记忆补全未写出的关系。
3. 如证据不足，不要构造强关系；可退化为 co_appears_with。
4. 实体主名优先使用当前文档中最稳定的中文称呼。
5. 如果文档里明确出现别名、称号、英文名、日文名，可写入 aliases；若当前文本未出现，禁止脑补。
6. 每条关系和事件都必须绑定 evidence，且 evidence.file_path 与 evidence.chunk_id 必须来自当前任务。
7. 只导入高价值、可落地的结构化信息，不导入空泛感想。
8. 导入前先自检 JSON 是否符合接口要求。

允许的实体类型：
- character
- organization
- location
- event
- item
- concept
- quest
- constellation
- talent

优先使用的关系类型：
- appears_in
- mentioned_in
- participates_in
- member_of
- located_in
- related_to
- opposes
- knows
- uses
- before
- after
- causes
- co_appears_with
- involves
- alias_of

导入接口：
- GET http://127.0.0.1:8000/api/{domain}/search?mode=docs&query=...
- GET http://127.0.0.1:8000/api/{domain}/doc?path=...&line_range=...
- POST http://127.0.0.1:8000/api/world-tree/import-graph

你最终需要做的是“完成导入”，而不是只输出抽取结果。
```

## User Prompt 模板

```text
请处理下面这个世界树图谱生成任务。

任务信息：
- domain: {{domain}}
- file_path: {{file_path}}
- line_range: {{line_range}}
- title: {{title}}
- backend_url: http://127.0.0.1:8000/api/world-tree/import-graph

要求：
1. 如果没有明确 file_path，先搜索相关文档并自行选择最合适的文件
2. 读取指定文件范围
3. 从该范围抽取图谱
4. 先 dry_run 校验，再正式导入
5. 最后返回导入了多少条记录、提取了哪些核心实体与关系
```

## 抽取标准

### 实体

优先抽取：

1. 角色
2. 组织/势力
3. 地点/国家/区域
4. 事件/任务
5. 概念、命之座、天赋、关键物品

避免抽取：

1. 普通代词
2. 没有图谱价值的泛称
3. 只有修辞功能的词

### 关系

优先抽取：

1. 明确身份关系
2. 所属关系
3. 参与事件关系
4. 地点归属关系
5. 明确因果和时序关系

保守策略：

1. 当前文本只支持共同出现时，用 `co_appears_with`
2. 当前文本只支持同段提及时，也用 `co_appears_with`
3. 不要把“你知道他们有关”写成强关系

### 事件

只有满足以下任一条件才建立事件：

1. 文本明确给出事件名
2. 文本明确在描述一个完整剧情节点
3. 当前范围对应任务步骤、关键过场或核心对话

## 导入接口 Payload 结构

Agent 最终应调用的请求体结构如下：

```json
{
  "items": [
    {
      "domain": "gi",
      "file_path": "docs/genshin/characters/zhongli.md",
      "chunk_id": "lines_10_35",
      "title": "钟离",
      "entities": [
        {
          "name": "钟离",
          "type": "character",
          "aliases": ["岩王帝君"]
        },
        {
          "name": "摩拉克斯",
          "type": "concept",
          "aliases": []
        }
      ],
      "relations": [
        {
          "subject": "钟离",
          "predicate": "alias_of",
          "object": "摩拉克斯",
          "confidence": 0.96,
          "reason": "文本直接说明钟离是摩拉克斯的凡人化身",
          "evidence": {
            "file_path": "docs/genshin/characters/zhongli.md",
            "chunk_id": "lines_10_35",
            "quote": "钟离是岩神摩拉克斯的凡人化身"
          }
        }
      ],
      "events": [],
      "notes": []
    }
  ],
  "dry_run": false
}
```

## 证据要求

1. `evidence.file_path` 必须等于当前任务文件路径。
2. `evidence.chunk_id` 必须等于当前任务范围标识。
3. `quote` 要尽量短，但足以支撑关系。
4. 没有证据的关系不要导入。

## 推荐的 chunk_id 规则

如果任务给的是行范围，建议 Agent 直接用：

```text
lines_{start}_{end}
```

例如：

```text
lines_10_35
```

这样后端和图谱里都容易追溯。

## Few-shot 执行示例

### 输入任务

```text
domain=gi
file_path=docs/genshin/characters/zhongli.md
line_range=10-35
title=钟离
```

### Agent 应做的事

1. 如果已有明确路径，直接调用文档读取接口读取 `docs/genshin/characters/zhongli.md` 的 `10-35` 行。
2. 从该范围抽取：
   - 实体：钟离、摩拉克斯
   - 关系：钟离 alias_of 摩拉克斯
3. 生成 `chunk_id = lines_10_35`
4. 先调用：

```text
POST http://127.0.0.1:8000/api/world-tree/import-graph  (dry_run=true)
```

5. 校验通过后再调用：

```text
POST http://127.0.0.1:8000/api/world-tree/import-graph
```

6. 请求体形如：

```json
{
  "items": [
    {
      "domain": "gi",
      "file_path": "docs/genshin/characters/zhongli.md",
      "chunk_id": "lines_10_35",
      "title": "钟离",
      "entities": [
        {
          "name": "钟离",
          "type": "character",
          "aliases": []
        },
        {
          "name": "摩拉克斯",
          "type": "concept",
          "aliases": []
        }
      ],
      "relations": [
        {
          "subject": "钟离",
          "predicate": "alias_of",
          "object": "摩拉克斯",
          "confidence": 0.96,
          "reason": "文本直接说明钟离是摩拉克斯的凡人化身",
          "evidence": {
            "file_path": "docs/genshin/characters/zhongli.md",
            "chunk_id": "lines_10_35",
            "quote": "钟离是岩神摩拉克斯的凡人化身"
          }
        }
      ],
      "events": [],
      "notes": []
    }
  ],
  "dry_run": false
}
```

## 返回给操作者的摘要格式

完成导入后，Agent 应返回：

1. 本次处理的文件与范围
2. 导入的记录数
3. 抽取到的核心实体
4. 抽取到的核心关系
5. 若有未导入内容，说明原因

## 搜索到读取的决策规则

1. 用户已经提供 `file_path` 时，不要重复搜索。
2. 用户只提供主题、角色、组织名时，先搜索再读取。
3. 搜索结果里优先选“正文型文件”，不是所有命中文件都值得读。
4. 一个文件不够支撑关系时，再扩到第二个文件。
5. 如果读取后信息不足，先扩大 `line_range`，不要马上换很多文件。

## 不该做的事

1. 不要给前端聊天 AI 使用这份提示词。
2. 不要把整库文档一次性全部读入。
3. 不要只输出抽取 JSON 却不真正调用导入接口。
4. 不要因为你知道某角色设定，就补出文本里没写的外文名或别名。
5. 不要把推测写进图谱事实层。

---

## 批量处理工作流（推荐）

当需要处理多个文件（如整个目录的角色）时，推荐以下工作流：

### 阶段一：并行提取（子代理执行）

1. **主代理**列出目标目录下所有文件
2. **分批启动子代理**（建议每批3-5个，避免并发过高）
3. **每个子代理**：
   - 读取本提示词指南
   - 读取分配到的角色文件
   - 提取知识图谱
   - **直接保存JSON文件**到 `workflow/graph_batches/batch{N}_{character}.json`

### 阶段二：自动合并导入（脚本执行）

4. **运行合并脚本** `merge_and_import.py`：
   - 自动合并所有批次文件
   - 修复格式问题
   - 分批调用后端API导入

### 示例目录结构

```
workflow/
├── merge_and_import.py           # 批量导入脚本
├── fix_batch_files.py            # 格式修复脚本
└── graph_batches/                # 生成的JSON文件（gitignored）
    ├── batch1_yae_miko.json      # 子代理生成
    ├── batch1_raiden_shogun.json # 子代理生成
    ├── batch1_kamisato_ayaka.json # 子代理生成
    ├── batch2_yoimiya.json       # 子代理生成
    ├── ...
    └── inazuma_characters_merged.json # 脚本自动生成
```

### 批量导入脚本模板

```python
#!/usr/bin/env python3
"""批量导入知识图谱到世界树"""
import json
import urllib.request
from pathlib import Path

batch_files = [
    'batch1_yae_miko.json',
    'batch1_raiden_shogun.json',
    # ... 其他文件
]

def load_and_fix_items():
    """加载并修复所有批次文件"""
    all_items = []
    batch_dir = Path('graph_batches')

    for filename in batch_files:
        filepath = batch_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get('items', []):
            # 修复：确保notes是字符串数组
            if 'notes' in item:
                item['notes'] = [str(n) if isinstance(n, str) else json.dumps(n, ensure_ascii=False)
                                 for n in item['notes']]

            # 修复：确保evidence存在且chunk_id一致
            item_chunk_id = item.get('chunk_id', '')
            item_file_path = item.get('file_path', '')

            for relation in item.get('relations', []):
                if 'evidence' not in relation:
                    relation['evidence'] = {
                        'file_path': item_file_path,
                        'chunk_id': item_chunk_id,
                        'quote': relation.get('reason', '')[:100]
                    }
                else:
                    relation['evidence']['chunk_id'] = item_chunk_id
                    relation['evidence']['file_path'] = item_file_path

            for event in item.get('events', []):
                if 'evidence' not in event:
                    event['evidence'] = {
                        'file_path': item_file_path,
                        'chunk_id': item_chunk_id,
                        'quote': event.get('summary', '')[:100]
                    }
                else:
                    event['evidence']['chunk_id'] = item_chunk_id
                    event['evidence']['file_path'] = item_file_path

            all_items.append(item)

    return all_items

def import_batch(items, dry_run=True):
    """导入一批图谱项"""
    api_url = "http://127.0.0.1:8000/api/world-tree/import-graph"
    payload = {"items": items, "dry_run": dry_run}

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        api_url, data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode())

# 执行导入
items = load_and_fix_items()

# 先dry_run测试
result = import_batch(items, dry_run=True)
if result.get('ok') and result.get('invalid_count', 0) == 0:
    # 分批正式导入
    batch_size = 5
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        import_batch(batch, dry_run=False)
```

---

## 常见问题与修复

### 1. notes字段格式错误

**错误**：`notes.0: Input should be a valid string`

**原因**：notes数组中包含非字符串类型（如字典）

**修复**：
```python
item['notes'] = [
    str(n) if isinstance(n, str)
    else json.dumps(n, ensure_ascii=False)
    for n in item['notes']
]
```

### 2. evidence字段缺失

**错误**：`events.0.evidence: Field required`

**原因**：relations或events缺少evidence字段

**修复**：为每个relation和event添加默认evidence

### 3. chunk_id不一致

**错误**：`relation.evidence.chunk_id 与 item.chunk_id 不一致`

**原因**：evidence中的chunk_id与item的chunk_id不匹配

**修复**：统一使用item的chunk_id和file_path

### 4. 并发限制

**问题**：启动过多子代理导致系统崩溃

**建议**：每批3-5个子代理，等待一批完成后再启动下一批

---

## 验证导入结果

导入完成后，可通过以下API验证：

```bash
# 查看统计
curl http://127.0.0.1:8000/api/world-tree/graph/stats

# 查询实体关系
curl -X POST http://127.0.0.1:8000/api/world-tree/query \
  -H "Content-Type: application/json" \
  -d '{"query": "八重神子与雷电将军的关系", "entity_names": ["八重神子"], "max_results": 5}'
```
