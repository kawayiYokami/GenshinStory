# Game Data Parser API 文档

本文档详细介绍了 `game_data_parser` 库的 API 使用方法。

## 快速入门

所有功能都通过 `GameDataAPI` 这个统一的入口类来提供。首先，你需要初始化它，并提供包含 `AnimeGameData` 等文件夹的数据源根目录。

```python
from game_data_parser import GameDataAPI

# 你的数据目录路径
DATA_ROOT = "/path/to/your/data"

# 初始化 API
api = GameDataAPI(data_root_path=DATA_ROOT)
```

## 全局搜索

- **`search(keyword: str) -> List[SearchResult]`**
  - **作用**: 在所有数据中执行全局关键字搜索。
  - **返回**: `SearchResult` 对象的列表。每个对象包含:
    - `id`: 匹配项的ID
    - `name`: 匹配项的名称
    - `type`: 匹配项的类型 (e.g., 'Quest', 'Material', 'Weapon')
    - `match_source`: 关键字匹配的字段 (e.g., 'name', 'description')

---

## API 服务概览

`api` 对象下包含了多个按领域划分的子服务，你可以通过属性访问它们：

*   `api.quest`: 任务相关服务
*   `api.character`: 角色相关服务
*   `api.relic`: 圣遗物相关服务
*   `api.weapon`: 武器相关服务
*   `api.material`: 物料相关服务
*   `api.book`: 书籍相关服务

---

## `api.quest` - 任务服务
提供与任务、章节和对话相关的查询。

- **`list_quest_chapters(type: Optional[str] = None) -> List[Chapter]`**
  - **作用**: 获取所有或特定类型的章节列表。
  - **返回**: `Chapter` 对象的列表。
- **`get_quest_by_id(item_id: int) -> Optional[Quest]`**
  - **作用**: 获取单个任务的完整信息。
  - **返回**: 一个 `Quest` 对象。
- **`get_quest_as_markdown(item_id: int) -> Optional[str]`**
  - **作用**: 获取单个任务的格式化Markdown文档。
  - **返回**: Markdown 格式的字符串。
- **`get_chapter_as_markdown(chapter_id: int) -> Optional[str]`**
  - **作用**: 获取单个章节的格式化Markdown文档。
  - **返回**: Markdown 格式的字符串。
- **`get_tree() -> List[Dict]`**
  - **作用**: 获取用于前端展示的任务树状结构 `(Category -> Chapter -> Quest)`。
  - **返回**: 树状结构的字典列表。

---

## `api.character` - 角色服务
提供角色信息查询。

- **`list_characters() -> List[Avatar]`**
  - **作用**: 获取所有可玩角色的列表。
  - **返回**: `Avatar` 对象的列表。
- **`get_character_by_id(avatar_id: int) -> Optional[Avatar]`**
  - **作用**: 获取单个角色的完整信息。
  - **返回**: 一个 `Avatar` 对象。
- **`get_character_as_markdown(avatar_id: int) -> str`**
  - **作用**: 获取单个角色的格式化Markdown文档。
  - **返回**: Markdown 格式的字符串。
- **`get_tree() -> List[Dict]`**
  - **作用**: 获取用于前端展示的角色树状结构 `(Nation -> Character)`。
  - **返回**: 树状结构的字典列表。

---

## `api.relic` - 圣遗物服务
提供圣遗物套装和部件的查询。

- **`list_relic_sets() -> List[Dict]`**
  - **作用**: 获取所有圣遗物套装的简明列表。
  - **返回**: 包含 `id` 和 `name` 的字典列表。
- **`get_relic_set_by_id(set_id: int) -> Optional[ReliquarySet]`**
  - **作用**: 获取一个完整的圣遗物套装，包含所有部件。
  - **返回**: 一个 `ReliquarySet` 对象。
- **`get_relic_set_as_markdown(set_id: int) -> Optional[str]`**
  - **作用**: 获取圣遗物套装的格式化Markdown文档。
  - **返回**: Markdown 格式的字符串。
- **`get_tree() -> List[Dict]`**
  - **作用**: 获取用于前端展示的圣遗物套装树状结构（扁平列表）。
  - **返回**: 包含 `id` 和 `title` 的字典列表。

---

## `api.weapon` - 武器服务
提供武器信息查询。

- **`search_weapons(type: Optional[str] = None, rarity: Optional[int] = None) -> List[Dict]`**
  - **作用**: 获取所有武器的简明列表，支持按类型和稀有度筛选。
  - **返回**: 包含 `id` 和 `name` 的字典列表。
- **`get_weapon_by_id(item_id: int) -> Optional[Weapon]`**
  - **作用**: 获取单个武器的完整信息。
  - **返回**: 一个 `Weapon` 对象。
- **`get_weapon_as_markdown(item_id: int) -> Optional[str]`**
  - **作用**: 获取单个武器的格式化Markdown文档。
  - **返回**: Markdown 格式的字符串。
- **`get_tree() -> List[Dict]`**
  - **作用**: 获取用于前端展示的武器树状结构 `(Type -> Weapon)`。
  - **返回**: 树状结构的字典列表。

---

## `api.material` - 物料服务
提供通用材料和道具的查询。

- **`get_all() -> List[Material]`**
  - **作用**: 获取所有材料和道具的列表。
  - **返回**: `Material` 对象的列表。
- **`get_by_id(material_id: int) -> Optional[Material]`**
  - **作用**: 根据 ID 获取单个材料或道具。
  - **返回**: 一个 `Material` 对象。
- **`get_tree() -> List[Dict]`**
  - **作用**: 获取用于前端展示的物料树状结构 `(Category -> Material)`。
  - **返回**: 树状结构的字典列表。

---

## `api.book` - 书籍服务
统一提供与书籍物料、书籍系列及分卷内容相关的查询。

- **`list_books() -> List[Dict]`**
  - **作用**: 获取所有被识别为“书籍”的物料的简明列表。
  - **返回**: 包含 `id` 和 `name` 的字典列表。
- **`get_book_by_id(item_id: int) -> Optional[Material]`**
  - **作用**: 获取单个书籍物料的完整信息。
  - **返回**: 一个 `is_book=True` 的 `Material` 对象。
- **`get_book_as_markdown(item_id: int) -> Optional[str]`**
  - **作用**: 获取单本书籍物料的格式化Markdown文档。
  - **返回**: Markdown 格式的字符串。
- **`list_book_series() -> List[BookSuit]`**
  - **作用**: 获取所有书籍系列。
  - **返回**: `BookSuit` 对象的列表。
- **`get_book_series_by_id(series_id: int) -> Optional[BookSuit]`**
  - **作用**: 获取单个书籍系列的详细信息，包含所有分卷。
  - **返回**: 一个 `BookSuit` 对象。
- **`get_book_series_as_markdown(series_id: int) -> Optional[str]`**
  - **作用**: 获取单个书籍系列的完整Markdown文档，包括所有分卷内容。
  - **返回**: Markdown 格式的字符串。
- **`get_tree() -> List[Dict]`**
  - **作用**: 获取用于前端展示的书籍树状结构 `(Series -> Book)`。
  - **返回**: 树状结构的字典列表。