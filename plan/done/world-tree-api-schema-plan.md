# 世界树 API 与 Schema 实施方案

- 日期：2026-03-20
- 目标：为原神 AI 问答网站设计一套面向 LLM 调用的“世界树”知识图谱查询层，负责关系导航、实体消歧、事件扩展、文件推荐与证据回溯，不直接替代文档精读。

## 1. 设计目标

1. 用户只提自然语言问题，不直接操作图谱。
2. LLM 通过受控 API 自主查询世界树，完成实体识别、关系扩展与证据定位。
3. 世界树返回“实体 + 关系 + 事件 + 关联文件 + chunk + 理由”，帮助 LLM 决定下一步读哪些文档。
4. 最终答案仍由 LLM 基于文档证据生成，世界树只承担导航层职责。

## 2. 非目标

1. 不向 LLM 暴露 SQL、Cypher 或数据库访问权限。
2. 不要求世界树直接生成最终答案。
3. 不要求第一阶段提供复杂图可视化前端。
4. 不要求第一阶段覆盖全部游戏数据类型，可先聚焦剧情、角色、组织、地点、事件、任务。

## 3. 总体链路

```text
用户提问
-> LLM 判断意图
-> 调用 /api/world-tree/query
-> 返回实体/关系/事件/文件/chunk/理由
-> 视需要调用 /api/world-tree/expand 或 /api/world-tree/paths
-> 调用文档搜索/精读接口读取关键 chunk
-> LLM 基于证据生成答案
```

## 4. API 列表

### 4.1 `POST /api/world-tree/query`

主入口。接收自然语言查询，返回实体、关系、事件与推荐阅读文件。

#### 请求体

```json
{
  "query": "芙宁娜和那维莱特到底是什么关系？",
  "intent": "relationship",
  "entities": ["芙宁娜", "那维莱特"],
  "domain": "genshin",
  "max_entities": 8,
  "max_relations": 12,
  "max_events": 6,
  "max_files": 8,
  "max_chunks_per_file": 3,
  "include_quotes": true
}
```

#### 字段说明

1. `query`: 原始自然语言问题。
2. `intent`: 查询意图，建议枚举：
   - `entity`
   - `relationship`
   - `event`
   - `timeline`
   - `theme`
   - `analysis`
3. `entities`: 可选，LLM 预识别的实体名列表。
4. `domain`: 游戏域，当前固定支持 `genshin`，未来可扩 `hsr` / `zzz`。
5. `max_*`: 控制返回规模，防止上下文过大。
6. `include_quotes`: 是否返回简短证据摘录。

#### 返回体

```json
{
  "query_id": "wt_q_20260320_001",
  "resolved_entities": [
    {
      "id": "char_furina",
      "name": "芙宁娜",
      "type": "character",
      "aliases": ["Furina"],
      "score": 0.99
    },
    {
      "id": "char_neuvillette",
      "name": "那维莱特",
      "type": "character",
      "aliases": ["Neuvillette"],
      "score": 0.98
    }
  ],
  "relations": [
    {
      "id": "rel_1001",
      "subject_id": "char_furina",
      "predicate": "co_appears_with",
      "object_id": "char_neuvillette",
      "score": 0.84,
      "evidence_count": 4,
      "reason": "两者在枫丹主线关键段落中多次共同出现",
      "source_refs": [
        {
          "file_path": "docs/genshin/aq/fontaine/ch5.md",
          "chunk_id": "chunk_42",
          "score": 0.95,
          "quote": "......"
        }
      ]
    }
  ],
  "events": [
    {
      "id": "event_fontaine_trial",
      "name": "枫丹审判",
      "type": "event",
      "score": 0.91,
      "reason": "问题涉及二者职责与公开关系，审判事件是高相关场景"
    }
  ],
  "related_files": [
    {
      "file_path": "docs/genshin/aq/fontaine/ch5.md",
      "score": 0.96,
      "reasons": [
        "同时涉及芙宁娜与那维莱特",
        "包含职责和身份相关对话"
      ],
      "chunks": [
        {
          "chunk_id": "chunk_42",
          "score": 0.95,
          "reason": "共同出场"
        },
        {
          "chunk_id": "chunk_51",
          "score": 0.89,
          "reason": "关系判断关键片段"
        }
      ]
    }
  ],
  "reasoning_hints": [
    "优先区分公开身份关系与真实背景关系",
    "建议先阅读枫丹主线相关 chunk，再补角色语音"
  ]
}
```

### 4.2 `POST /api/world-tree/expand`

对某个实体或事件做邻接扩展。

#### 请求体

```json
{
  "entity_id": "char_furina",
  "relation_types": ["participates_in", "related_to", "member_of"],
  "depth": 2,
  "max_nodes": 20,
  "max_edges": 30,
  "include_related_files": true
}
```

#### 返回体

```json
{
  "center_entity": {
    "id": "char_furina",
    "name": "芙宁娜",
    "type": "character"
  },
  "nodes": [],
  "edges": [],
  "related_files": []
}
```

#### 适用场景

1. 用户问题已经定位到角色，但关系网还不够清楚。
2. 需要从角色追到事件、组织、地点。
3. 需要补全“这个人最近在这条线里和谁强相关”。

### 4.3 `POST /api/world-tree/paths`

查询两个实体之间的关系路径。

#### 请求体

```json
{
  "from_entity_id": "char_furina",
  "to_entity_id": "char_neuvillette",
  "max_depth": 3,
  "max_paths": 5
}
```

#### 返回体

```json
{
  "paths": [
    {
      "score": 0.87,
      "steps": [
        {
          "from": "char_furina",
          "predicate": "participates_in",
          "to": "event_fontaine_trial"
        },
        {
          "from": "event_fontaine_trial",
          "predicate": "involves",
          "to": "char_neuvillette"
        }
      ],
      "source_refs": [
        {
          "file_path": "docs/genshin/aq/fontaine/ch5.md",
          "chunk_id": "chunk_42",
          "score": 0.93
        }
      ]
    }
  ]
}
```

#### 适用场景

1. “A 和 B 怎么联系起来？”
2. “为什么这个角色和这个事件有关？”
3. 需要解释中间桥接关系，而不是只列出命中结果。

### 4.4 `GET /api/world-tree/entity/:id`

返回单实体详情。

#### 作用

1. 给未来前端实体卡片使用。
2. 给 LLM 在已知实体 ID 时补摘要。
3. 给后台运营或调试页面核对实体数据。

## 5. 统一响应对象

### 5.1 `Entity`

```ts
interface Entity {
  id: string;
  name: string;
  type: 'character' | 'organization' | 'location' | 'event' | 'item' | 'concept' | 'quest';
  aliases: string[];
  summary?: string;
  tags?: string[];
  score?: number;
}
```

### 5.2 `SourceRef`

```ts
interface SourceRef {
  file_path: string;
  chunk_id: string;
  score: number;
  quote?: string;
}
```

### 5.3 `Relation`

```ts
interface Relation {
  id: string;
  subject_id: string;
  predicate: string;
  object_id: string;
  score: number;
  confidence?: number;
  evidence_count?: number;
  reason?: string;
  source_refs: SourceRef[];
}
```

### 5.4 `RelatedFile`

```ts
interface RelatedFile {
  file_path: string;
  score: number;
  reasons: string[];
  chunks: Array<{
    chunk_id: string;
    score: number;
    reason: string;
  }>;
}
```

### 5.5 `WorldTreeQueryResponse`

```ts
interface WorldTreeQueryResponse {
  query_id: string;
  resolved_entities: Entity[];
  relations: Relation[];
  events: Entity[];
  related_files: RelatedFile[];
  reasoning_hints: string[];
}
```

## 6. 底层存储模型

### 6.1 实体层

建议至少包含：

1. `characters`
2. `organizations`
3. `locations`
4. `events`
5. `items`
6. `concepts`
7. `quests`

统一抽象到 `entities` 视图中，避免上层查询分表拼接。

### 6.2 关系层

建议第一阶段支持：

1. `appears_in`
2. `mentioned_in`
3. `participates_in`
4. `member_of`
5. `located_in`
6. `related_to`
7. `opposes`
8. `knows`
9. `uses`
10. `before`
11. `after`
12. `causes`
13. `co_appears_with`
14. `involves`

### 6.3 证据层

每条关系必须绑定证据，至少包含：

1. `file_path`
2. `chunk_id`
3. `score`
4. `quote` 或 `summary`
5. `source_type`

### 6.4 提及层

记录实体在文档中的出现位置，用于召回和排序：

```ts
interface Mention {
  id: string;
  entity_id: string;
  file_path: string;
  chunk_id: string;
  surface_form: string;
  score: number;
}
```

## 7. 查询执行策略

### 7.1 `query` 接口执行步骤

1. 从 `query` 和 `entities` 中提取候选实体名。
2. 做别名归一和歧义消解。
3. 召回相关实体节点。
4. 召回相关关系边和高相关事件。
5. 根据实体、关系、mentions、chunk 检索结果混合打分。
6. 产出推荐文件与 chunk。
7. 生成 `reasoning_hints`，引导 LLM 的下一步动作。

### 7.2 排序建议

总分建议混合：

```text
final_score =
0.30 * entity_match +
0.20 * alias_match +
0.20 * relation_score +
0.20 * chunk_relevance +
0.10 * source_quality
```

可进一步加入：

1. 主线文档权重高于边角资料。
2. 直接共同出现高于远距离推断。
3. 最近已读 chunk 可适度降权，减少重复返回。

## 8. 与文档接口的职责边界

### 世界树负责

1. 找相关实体。
2. 找关系与路径。
3. 推荐要读的文件和 chunk。
4. 提供证据索引入口。

### 文档接口负责

1. 读取原文 chunk。
2. 精准搜索文档内容。
3. 返回足够可引用的证据文本。

### 约束

1. 世界树不能替代原文证据层。
2. LLM 作答前，涉及事实判断时应至少读取 1 到 3 个关键 chunk。

## 9. 数据构建流水线

### Phase 1：文档切块

1. 按任务步骤、剧情片段、对话段切 chunk。
2. 为每个 chunk 生成稳定 ID。
3. 建立 `file_path -> chunk_id` 映射。

### Phase 2：实体识别

1. 先词典匹配。
2. 再别名归一。
3. 用歧义表解决同名或称号混淆。

### Phase 3：关系抽取

1. 规则抽简单关系。
2. LLM 抽复杂关系。
3. 每条关系必须挂证据 chunk。

### Phase 4：事件归并

1. 把多个 chunk 归并到事件节点。
2. 建事件与角色、地点、组织、任务的关系边。

### Phase 5：索引构建

1. 实体索引。
2. 别名索引。
3. 关系邻接索引。
4. mentions 反查索引。
5. 文件与 chunk 推荐索引。

## 10. 错误处理

### 查询类错误

1. `INVALID_ARGUMENT`: 参数格式不合法。
2. `ENTITY_NOT_FOUND`: 未解析出可信实体。
3. `QUERY_TOO_BROAD`: 问题过宽，无法给出高质量导航。
4. `INTERNAL_ERROR`: 内部异常。

### 返回原则

1. 即使无法给出强关系，也尽量返回候选实体和建议阅读文件。
2. 不要因为单条边缺失而让整个接口失败。
3. 对于低置信度关系，要么过滤，要么明确降低分数并标注理由。

## 11. 可观测性

每次查询至少记录：

1. `query_id`
2. `intent`
3. `resolved_entity_ids`
4. `returned_relation_count`
5. `returned_file_count`
6. `latency_ms`
7. `cache_hit`
8. `degraded`

建议事件：

1. `WORLD_TREE_QUERY_RECEIVED`
2. `WORLD_TREE_ENTITY_RESOLVED`
3. `WORLD_TREE_RELATIONS_RANKED`
4. `WORLD_TREE_FILES_RANKED`
5. `WORLD_TREE_QUERY_COMPLETED`
6. `WORLD_TREE_QUERY_DEGRADED`

## 12. 实施顺序

### PR-1：接口契约与 mock

1. 定义 DTO、schema、错误码。
2. 打通 `query/expand/paths/entity` 四个路由。
3. 先返回 mock 数据，确保 LLM 工具链可接。

### PR-2：实体与文件召回

1. 接入实体索引和 alias 归一。
2. 接入 related files 与 chunk 推荐。
3. 支持最小可用 `query` 能力。

### PR-3：关系与路径

1. 接入关系边存储。
2. 支持 `expand` 与 `paths`。
3. 增加 evidence/source_refs。

### PR-4：排序、日志、回退

1. 接入混合打分。
2. 增加缓存与 tracing。
3. 补齐 degraded 返回与观测事件。

## 13. 完成定义（DoD）

1. LLM 能通过 `query` 拿到可靠的实体、关系和推荐文件。
2. `expand` 和 `paths` 能支持多跳剧情问题。
3. 每条高价值关系都可回溯到文件与 chunk。
4. 世界树返回结果足以引导 LLM 去读正确文档，而不是盲搜全库。
5. 接口有统一 schema、错误码、日志和退化策略。
