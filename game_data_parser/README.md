# Game Data Parser

这是一个用于解析、处理和结构化特定游戏数据的 Python 库。它旨在将分散、原始的游戏数据文件（主要是 JSON 格式）转换成易于使用、面向对象的 Python 模型，并提供统一的 API 进行访问。

## 核心特性

- **结构化数据模型**: 将原始数据映射到清晰、强类型的 Python `dataclasses`，便于开发和维护。
- **统一的 API 入口**: 通过 `GameDataAPI` 类提供一个简单的门面（Facade），隐藏了内部的复杂性。
- **分层架构**: 模块采用分层设计，将数据加载、业务逻辑解释和输出格式化明确分离。
- **缓存机制**: 内置高效的缓存系统（使用 `lzma` 和 `pickle`），在首次加载后能显著加快后续的初始化速度。

## 模块结构

本模块遵循清晰的目录结构，每个部分各司其职：

- **`api.py`**:
  - 定义了 `GameDataAPI` 类，是整个库的唯一公共入口。它本身不包含业务逻辑，而是将请求分发到相应的服务。

- **`dataloader.py`**:
  - 核心的数据加载器。负责从文件系统读取原始 JSON 和文本文件，并管理一个内存缓存和一个二进制文件缓存 (`game_data.cache`)，以避免重复的 I/O 操作。

- **`models.py`**:
  - 定义了所有的数据模型（例如 `Quest`, `Avatar`, `Weapon` 等）。这些是整个系统数据交互的基础。

- **`services/`**:
  - 领域服务层。每个服务（如 `QuestService`, `CharacterService`）负责处理一个特定领域的数据，协调解释器和格式化器来响应 `GameDataAPI` 的请求。

- **`interpreters/`**:
  - 解释器层。这是数据转换的核心，负责将 `DataLoader` 加载的原始、无序的字典数据，转换成 `models.py` 中定义的结构化对象。

- **`formatters/`**:
  - 格式化器层。负责将结构化的模型对象转换成人类可读的格式，例如 Markdown 文本。

- **`utils/`**:
  - 存放通用的辅助函数或工具类。

## 快速入门

所有功能都通过 `GameDataAPI` 访问。该库依赖于一个预先生成的缓存文件 (`game_data.cache`) 来运作。

```python
from game_data_parser import GameDataAPI

# 初始化 API
# 确保 'game_data.cache' 文件位于工作目录下
# cache_path 参数是可选的，默认为 'game_data.cache'
api = GameDataAPI(data_root_path=None, cache_path="game_data.cache")

# --- 使用服务 ---

# 获取所有角色的列表
all_characters = api.character.list_characters()
print(f"找到了 {len(all_characters)} 个角色。")

# 获取单个任务并将其格式化为 Markdown
quest_markdown = api.quest.get_quest_as_markdown(72105)
if quest_markdown:
    print(quest_markdown)

# 获取一个圣遗物套装的详细信息
relic_set = api.relic.get_relic_set_by_id(15006)
if relic_set:
    print(f"圣遗物套装: {relic_set.name}")
    print(f"2件套效果: {relic_set.effect_2_piece}")
```

## 缓存机制

该库依赖于一个名为 `game_data.cache` 的压缩缓存文件来提供数据。在初始化 `GameDataAPI` 时，它会自动从此缓存文件中加载所有必需的数据。

请确保 `game_data.cache` 文件存在于您的项目工作目录中。如果需要从新的原始数据生成缓存，请使用配套的缓存生成脚本。

## 详细文档

本文档只提供概览。更深入的技术细节、完整的 API 列表和数据结构定义，请参阅以下文档：

- **[API 文档 (`API_DOCUMENTATION.md`)](./API_DOCUMENTATION.md)**:
  详细介绍了 `GameDataAPI` 提供的所有公开方法、参数和返回值。如果你想知道如何使用这个库，请从这里开始。

- **[数据模型文档 (`DATA_MODEL_DOCUMENTATION.md`)](./DATA_MODEL_DOCUMENTATION.md)**:
  详细描述了 `models.py` 中定义的所有数据模型的字段、类型和含义。如果你需要理解数据的具体结构，请阅读此文档。