# 世界树 LLM 工具调用与提示词策略

- 日期：2026-03-20
- 目标：让 LLM 在原神 AI 问答链路中自主调用“世界树”工具完成查询规划、关系导航和证据定位，并与文档接口协同生成高质量答案。

## 1. 角色分工

### 用户

1. 只提出自然语言问题。
2. 不需要理解知识图谱、查询语法或文件结构。

### 世界树

1. 返回相关实体、关系、事件。
2. 推荐应当阅读的文件和 chunk。
3. 给出下一步调查提示。

### 文档接口

1. 精读具体 chunk。
2. 返回可引用的证据文本。

### LLM

1. 判断问题类型。
2. 决定是否调用世界树。
3. 基于世界树结果决定读哪些文档。
4. 组织最终回答，区分事实与推测。

## 2. 核心原则

1. 涉及关系、剧情链路、人物关联、事件因果时，优先调用世界树。
2. 世界树结果不是最终证据，最终回答尽量落回原文。
3. 不让 LLM 自由生成数据库语句，只允许调用受控工具。
4. 问题越复杂，越应该“先世界树，后文档”。
5. 图谱导航是为了减少盲搜，不是为了替代阅读。

## 3. 何时调用世界树

### 必须调用

1. “A 和 B 是什么关系？”
2. “某角色为什么会参与某事件？”
3. “这段剧情和前面的哪条线有关？”
4. “某个事件前后发生了什么？”
5. “某条主线涉及哪些人、地点、组织？”

### 建议调用

1. 问题包含两个以上实体。
2. 问题明确涉及“联系、因果、线索、关系、前后、背景、影响”。
3. 问题看起来需要多跳检索才能回答。

### 可以不调用

1. 纯闲聊。
2. 纯改写、二创、仿写。
3. 已经准确知道目标文件且问题只需读单一段落。

## 4. 工具定义

### 4.1 `world_tree_query`

```json
{
  "name": "world_tree_query",
  "description": "查询世界树图谱，返回相关实体、关系、事件和推荐阅读文件",
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "intent": {
        "type": "string",
        "enum": ["entity", "relationship", "event", "timeline", "theme", "analysis"]
      },
      "entities": {
        "type": "array",
        "items": { "type": "string" }
      },
      "max_files": { "type": "integer" },
      "max_relations": { "type": "integer" }
    },
    "required": ["query"]
  }
}
```

### 4.2 `world_tree_expand`

```json
{
  "name": "world_tree_expand",
  "description": "扩展某个实体或事件的邻接节点与关系",
  "parameters": {
    "type": "object",
    "properties": {
      "entity_id": { "type": "string" },
      "relation_types": {
        "type": "array",
        "items": { "type": "string" }
      },
      "depth": { "type": "integer" }
    },
    "required": ["entity_id"]
  }
}
```

### 4.3 `world_tree_paths`

```json
{
  "name": "world_tree_paths",
  "description": "查询两个实体之间的关系路径",
  "parameters": {
    "type": "object",
    "properties": {
      "from_entity_id": { "type": "string" },
      "to_entity_id": { "type": "string" },
      "max_depth": { "type": "integer" }
    },
    "required": ["from_entity_id", "to_entity_id"]
  }
}
```

## 5. LLM 决策流程

```text
用户问题
-> 判断是事实 / 关系 / 剧情理解 / 时间线 / 索隐 / 二创
-> 若为关系或剧情链路问题，调用 world_tree_query
-> 检查返回的实体、关系、文件、chunk
-> 若仍不清楚，调用 world_tree_expand 或 world_tree_paths
-> 选择 1~3 个关键 chunk 去读
-> 基于文档证据作答
```

## 6. 推荐的系统提示词约束

可直接作为系统提示词中的一段规则：

```text
当用户问题涉及人物关系、事件联系、剧情因果、时间线或多实体关联时，你应优先调用世界树工具，而不是直接盲目搜索全文档。

世界树工具用于：
- 识别相关实体
- 查找关系与事件
- 推荐应阅读的文件与 chunk

使用原则：
- 不要把世界树返回的关系直接当作最终证据
- 涉及事实判断时，先根据世界树结果读取关键文档 chunk，再回答
- 若问题是“两个实体如何联系起来”，优先使用 world_tree_paths
- 若问题是“围绕某个实体继续追踪相关人物/事件”，优先使用 world_tree_expand
- 若当前问题只是轻聊天、感叹或创作，不必调用世界树
```

## 7. 不同问题类型的调用策略

### 7.1 关系问题

例子：

1. “散兵和博士什么关系？”
2. “芙宁娜和那维莱特到底什么关系？”

推荐流程：

1. 调 `world_tree_query(intent=relationship)`
2. 若返回多条关系且链路复杂，调 `world_tree_paths`
3. 读取 1 到 3 个关键 chunk
4. 输出：
   - 一句话结论
   - 文档里明确能确认的事实
   - 如有必要，再补推测

### 7.2 事件问题

例子：

1. “层岩巨渊事件和愚人众有什么关联？”
2. “枫丹审判前后发生了什么？”

推荐流程：

1. 调 `world_tree_query(intent=event)`
2. 如事件边界不清，调 `world_tree_expand` 扩展事件节点
3. 读取推荐 chunk
4. 组织时间顺序和因果顺序

### 7.3 时间线问题

例子：

1. “这件事是在主线哪一段发生的？”
2. “这个角色什么时候第一次出现？”

推荐流程：

1. 调 `world_tree_query(intent=timeline)`
2. 必要时结合 `before/after` 边或 `paths`
3. 回到文档验证时间顺序

### 7.4 剧情理解问题

例子：

1. “为什么那维莱特会这样做？”
2. “这段剧情和前面的伏笔怎么连上？”

推荐流程：

1. 调 `world_tree_query(intent=analysis)`
2. 看是否需要 `expand`
3. 读取相关 chunk
4. 回答时分清：
   - 明确写出的事实
   - 基于结构的解释
   - 谨慎推测

## 8. 返回结果消费规则

LLM 使用世界树返回结果时，必须遵守：

1. 优先信任高分实体与高分文件。
2. 看到 `reasoning_hints` 时，优先按提示进行下一步阅读。
3. 如果 `related_files` 已经给出明确 chunk，优先定点读取，不再全文盲搜。
4. 如果 `relations` 分数低或证据少，不要直接下结论。
5. 如果世界树结果分散、没有强关系，答案里要显式说明证据边界。

## 9. 输出答案的结构约束

建议 LLM 对世界树增强问题按下面顺序输出：

1. 先回答用户真正要的结论。
2. 再说明文档里明确能确认的内容。
3. 若存在图谱帮助定位出的线索，可简短说明“相关线索主要集中在某事件/某主线”。
4. 若有推测，必须显式标注“推测”或“倾向于”。

## 10. 失败与降级策略

### 世界树未命中实体

LLM 应：

1. 降级到文档搜索。
2. 或先澄清用户说的是哪个实体。

### 世界树命中了实体但关系很弱

LLM 应：

1. 把世界树结果视为导航线索。
2. 去读推荐文件后再判断。
3. 不直接说“就是这种关系”。

### 世界树返回过宽

LLM 应：

1. 选最相关的 1 到 2 条线先读。
2. 避免一次性展开全部返回结果。

## 11. Few-shot 示例

### 示例 1：关系问题

用户：

```text
芙宁娜和那维莱特到底是什么关系？
```

推荐工具调用：

```json
{
  "tool": "world_tree_query",
  "arguments": {
    "query": "芙宁娜和那维莱特到底是什么关系？",
    "intent": "relationship",
    "entities": ["芙宁娜", "那维莱特"],
    "max_files": 5,
    "max_relations": 8
  }
}
```

若返回显示关系链路复杂，再调用：

```json
{
  "tool": "world_tree_paths",
  "arguments": {
    "from_entity_id": "char_furina",
    "to_entity_id": "char_neuvillette",
    "max_depth": 3
  }
}
```

### 示例 2：事件问题

用户：

```text
层岩巨渊那段和愚人众到底有什么关系？
```

推荐工具调用：

```json
{
  "tool": "world_tree_query",
  "arguments": {
    "query": "层岩巨渊那段和愚人众到底有什么关系？",
    "intent": "event",
    "entities": ["层岩巨渊", "愚人众"],
    "max_files": 6
  }
}
```

### 示例 3：时间线问题

用户：

```text
散兵第一次正式出现是在什么时候？
```

推荐工具调用：

```json
{
  "tool": "world_tree_query",
  "arguments": {
    "query": "散兵第一次正式出现是在什么时候？",
    "intent": "timeline",
    "entities": ["散兵"],
    "max_files": 4
  }
}
```

## 12. 运行时守卫

建议在工具层加这些守卫：

1. 单轮最多 3 次世界树调用，防止循环探索。
2. `query -> expand/paths -> read_doc` 是推荐路径，不鼓励无意义往返。
3. 若 `query` 已返回明确 chunk，不要再重复同义查询。
4. 若用户明确要求“不要查资料”，不要调用世界树。

## 13. 与行为模式的结合

结合你们现有行为模式，建议：

1. `chat`:
   - 默认不调世界树。
   - 问题转向事实/关系时再切换。
2. `search`:
   - 允许优先调世界树做导航，再查文档。
3. `story_archive`:
   - 世界树是主入口之一，适合追剧情链路和人物关系。
4. `subtext`:
   - 先少量用世界树补上下文，再回到文本阐释。
5. `fanwork`:
   - 默认不需要世界树，除非设定存疑。

## 14. 可观测性与评估

建议记录：

1. 哪类问题触发了世界树。
2. 世界树返回的文件是否最终被读取。
3. LLM 最终答案是否引用了世界树推荐文件。
4. 首次回答命中率是否提升。
5. 每轮平均调用次数是否可控。

重点指标：

1. `world_tree_query_call_rate`
2. `world_tree_to_doc_read_rate`
3. `answer_with_evidence_rate`
4. `avg_world_tree_calls_per_turn`
5. `relationship_question_success_rate`

## 15. 完成定义（DoD）

1. LLM 能在关系和剧情类问题中稳定优先调用世界树。
2. 工具调用路径清晰，不暴露底层数据库能力。
3. 世界树结果能有效引导 LLM 阅读更少但更准的 chunk。
4. 回答质量提升体现在关系题、时间线题、剧情链路题上。
5. 提示词、Few-shot、工具守卫和观测指标形成闭环。
