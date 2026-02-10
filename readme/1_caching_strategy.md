# 文档 1: 缓存构建机制

本文档阐述了项目中用于处理游戏数据的缓存构建策略，主要涉及 `scripts/gi_create_cache.py` 和 `scripts/hsr_create_cache.py` 两个核心脚本。

## 核心目标

缓存系统的主要目标是：

1.  **提升性能**：避免在每次请求时都从原始数据文件（如 Excel、JSON）进行解析，通过一次性加载和处理，将数据存入一个快速访问的二进制缓存文件中。
2.  **数据预处理**：在缓存构建阶段，对原始数据进行清洗、关联和结构化，形成易于使用的 Python 对象。
3.  **构建内存搜索索引**：在缓存数据的同时，创建一个用于全文搜索的倒排索引，并将其一并存入缓存文件，供后续步骤使用。

## 构建流程 (`gi_create_cache.py`)

`gi_create_cache.py` 脚本是为《原神》数据设计的，其流程如下：

### 1. 初始化

-   脚本首先初始化 `GameDataAPI`，但**不加载任何缓存** (`cache_path=None`)。这强制 API 从位于 `AnimeGameData` 目录下的原始数据文件开始工作。

### 2. 强制数据预热 (`force_load_all`)

-   这是缓存构建的核心步骤。脚本会系统地调用 `GameDataAPI` 中几乎所有的服务 (`QuestService`, `CharacterService`, `WeaponService` 等) 的数据获取方法。
-   当调用这些服务时，内部的 `DataLoader` 会被触发。如果 `DataLoader` 发现内存中没有所需数据，它会：
    -   从原始数据文件加载数据。
    -   调用相应的 `Interpreter` (解释器) 对原始数据进行解析和转换，生成结构化的 Python 对象。
    -   将这些对象存储在自身的内存缓存 (`_cache` 字典) 中。
-   通过遍历游戏中的每一个任务、角色、武器等，脚本确保了所有相关数据都被加载、解析并存入 `DataLoader` 的内存中。

### 3. 构建搜索索引

-   在所有数据都加载到内存后，脚本开始构建搜索索引。
-   它会遍历所有已加载的数据项（角色、武器、书籍等）。
-   对于每一个数据项：
    -   调用其对应的 `..._as_markdown` 方法，生成该项的 Markdown 格式文本。
    -   使用 `clean_markdown_for_search` 函数移除 Markdown 语法，提取纯文本内容。
    -   将纯文本内容（包括标题和正文）进行分词。
    -   将分词后的词条（token）作为键，数据项的元数据（如 ID, 名称, 类型）作为值，存入 `DataLoader` 的 `_search_index` 字典中。这是一个典型的**倒排索引**结构。

### 4. 保存缓存

-   最后，`DataLoader` 的 `save_cache` 方法被调用。
-   此方法使用 `gzip` 压缩，将包含所有结构化数据对象和完整搜索索引的 `DataLoader` 实例序列化，并保存到 `game_data_parser/cache/gi_data.cache.gz` 文件中。

## HSR 缓存构建 (`hsr_create_cache.py`)

`hsr_create_cache.py` 脚本为《崩坏：星穹铁道》服务，其逻辑与 GI 版本类似但实现上更模块化：

1.  **初始化服务**：分别初始化 `DataLoader`, `TextMapService` 和 `CacheService`。
2.  **统一处理**：脚本定义了一个 `processing_map`，将数据类型、解释器 (`Interpreter`) 和格式化器 (`Formatter`) 映射在一起。
3.  **迭代处理**：
    -   脚本遍历 `processing_map`，对每种数据类型（角色、光锥、遗器等）执行 `interpret_all` 方法来解析全部数据。
    -   解析后的对象列表被存入 `CacheService` 的对应属性中。
    -   同时，对每个解析出的对象，调用其格式化器生成 Markdown 内容。
    -   使用 `_index_item_with_ngrams` 函数对对象的名称和内容进行 **N-gram (二元组) 分词**，并构建搜索索引，索引信息同样存放在 `CacheService` 中。
4.  **保存缓存**：调用 `CacheService` 的 `save` 方法，将整个 `CacheService` 实例（包含所有数据和索引）序列化并保存到 `hsr_data_parser/cache/hsr_data.cache.gz`。

## 结论

缓存构建是一个**预处理**步骤，它将分散、原始的游戏数据转化为一个集中的、高性能的、包含搜索功能的数据包。这个数据包是后续所有数据驱动功能（如 Markdown 生成、API 查询）的基础，极大地提升了应用的运行效率。