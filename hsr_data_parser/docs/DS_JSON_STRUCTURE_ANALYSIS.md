# DS/Story JSON 嵌套结构分析报告

**分析对象**: `turnbasedgamedata/Story/Discussion/Mission/1040606/DS104060601.json`

本文档旨在深入剖析《崩坏：星穹铁道》中 `Discussion` 和 `Story` 类型任务的 JSON 文件结构，揭示其内在的事件驱动和递归嵌套逻辑。

---

## 核心机制：事件驱动的流程图

与线性的 `Act` 类型任务不同，`DS/Story` 任务并非按顺序执行，而是构成了一个由信号触发和监听组成的网络。其核心是 `OnStartSequece` 数组，其中包含的 `TaskList` 块共同定义了一个完整的对话流程图。

关键组件：
-   `PlayTimeline`: 播放一段线性的对话或演出。
-   `PlayOptionTalk`: 呈现一个或多个对话选项，这是**分支点**。
-   `TriggerCustomString`: 触发一个自定义的字符串信号，用于广播一个事件。
-   `WaitCustomString`: 暂停执行，直到监听到匹配的自定义字符串信号。

---

## `DS104060601.json` 流程解析

### 1. 初始入口点 (Lines 4-69)
-   **动作**:
    -   `LevelPerformanceInitialize`: 初始化场景。
    -   `PlayTimeline`: 播放开场对话 (`...01.playable`)。
    -   `PlayOptionTalk`: **第一个分支点**，呈现三个选项，每个选项通过 `TriggerCustomString` 触发一个唯一信号 (e.g., `TalkSentence_146060109`)。

### 2. 分支路径定义 (Lines 70-131)
-   定义了三个独立的 `TaskList` 块，分别等待入口点的三个信号。
-   每个块的逻辑相同：
    1.  `WaitCustomString`: 监听到对应信号后激活。
    2.  `PlayTimeline`: 播放该分支独有的对话内容 (e.g., `...02.playable`)。
    3.  `TriggerCustomString`: 播放完毕后，触发一个**共同的汇合信号** (`TalkSentence_146060114`)。

### 3. 路径汇合与第二个分支点 (Lines 133-169)
-   **动作**:
    -   `WaitCustomString`: 等待 `TalkSentence_146060114` 信号，至此，无论玩家选择哪个分支，流程都会**汇合**于此。
    -   `PlayTimeline`: 播放汇合后的主线对话 (`...05.playable`)。
    -   `PlayOptionTalk`: **第二个分支点**，再次呈现新的选项，触发新的信号。

### 4. 嵌套分支 (Lines 171-221)
-   此部分清晰地展示了**递归/嵌套结构**。
-   其中两个分支路径 (`...118` 和 `...121`) 内部，在播放完各自的 `PlayTimeline` 后，紧接着又出现了一个新的 `PlayOptionTalk` 块。
-   这意味着一个选项触发的对话流内部，可以包含**新的、更深层级的选项**。
-   这些嵌套选项触发的信号，最终又指向了下一个汇合点 (`TalkSentence_146060123`)。

### 5. 多路汇合与最终分支 (Lines 223-253)
-   **动作**:
    -   `WaitCustomString`: 等待 `TalkSentence_146060123` 信号。这是一个**多路汇合点**，接收来自第二个分支点的直接选项和嵌套分支中的选项信号。
    -   `PlayTimeline`: 播放汇合后的对话。
    -   `PlayOptionTalk`: 呈现最终的选项。

### 6. 结局 (Lines 255-282)
-   **动作**:
    -   `WaitCustomString`: 等待最终的汇合信号。
    -   `PlayTimeline`: 播放结局对话。
    -   `EndPerformance`: 演出结束。

---

## 结论与结构树

该 JSON 文件的结构是一个有向无环图 (DAG)，其中节点是 `TaskList`，边是 `Trigger/Wait` 信号。

**伪代码结构树:**
```
START
  - Play(Dialogue_1)
  - Options [
      - Option_A -> trigger(Signal_A)
      - Option_B -> trigger(Signal_B)
      - Option_C -> trigger(Signal_C)
    ]
WAIT FOR (Signal_A, Signal_B, Signal_C)
  - Path A: Play(Dialogue_A) -> trigger(Signal_ABC_Merge)
  - Path B: Play(Dialogue_B) -> trigger(Signal_ABC_Merge)
  - Path C: Play(Dialogue_C) -> trigger(Signal_ABC_Merge)
WAIT FOR (Signal_ABC_Merge)
  - Play(Dialogue_ABC)
  - Options [
      - Option_X -> trigger(Signal_X)
      - Option_Y -> trigger(Signal_Y)
      - Option_Z -> trigger(Signal_Z)
    ]
WAIT FOR (Signal_X, Signal_Y, Signal_Z)
  - Path X: -> trigger(Signal_XYZ_Merge)  // 直接汇合
  - Path Y:
    - Play(Dialogue_Y)
    - Options [ // 嵌套选项
        - Option_Y1 -> trigger(Signal_XYZ_Merge)
      ]
  - Path Z:
    - Play(Dialogue_Z)
    - Options [ // 嵌套选项
        - Option_Z1 -> trigger(Signal_XYZ_Merge)
      ]
WAIT FOR (Signal_XYZ_Merge)
  - Play(Dialogue_XYZ)
  - Options [
      - Option_Final1 -> trigger(Signal_End)
      - Option_Final2 -> trigger(Signal_End)
    ]
WAIT FOR (Signal_End)
  - Play(Dialogue_End)
END
```

**对解析器的启示:**
1.  **必须使用递归数据模型**来表示这种潜在的无限嵌套结构。
2.  **必须使用递归下降的解析算法**来遍历这个流程图。
3.  解析器的核心是构建一个 `TriggerString` 到其对应 `TaskList` 的映射表，以便在遇到选项时能够快速找到并递归解析后续的对话流。