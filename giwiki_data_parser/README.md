# 原神Wiki数据解析器 (GiWiki Data Parser)

一个专门用于解析原神Wiki数据并转换为Markdown格式的Python工具。专注于提取故事内容和世界观设定，忽略纯游戏机制数据。

## 功能特性

- 🎮 **专注故事内容**: 只解析包含故事价值的数据，自动过滤游戏机制数据
- 📝 **Markdown输出**: 将结构化数据转换为易读的Markdown格式
- 🔄 **并发处理**: 支持多线程并发解析，提高处理效率
- 🛠️ **模块化设计**: 采用解释器-格式化器模式，易于扩展和维护
- 📊 **详细报告**: 生成完整的解析统计报告
- 🐛 **调试工具**: 内置交互式调试工具，方便开发和测试

## 支持的数据类型

| 数据类型 | 描述 | 故事价值 |
|---------|------|---------|
| 261_角色逸闻 | 角色故事和对话 | ⭐⭐⭐⭐⭐ |
| 6_敌人 | 敌人背景故事 | ⭐⭐⭐⭐ |
| 5_武器 | 武器故事和世界观 | ⭐⭐⭐⭐ |
| 68_书籍 | 游戏内书籍内容 | ⭐⭐⭐⭐⭐ |
| 255_组织 | 组织背景和结构 | ⭐⭐⭐⭐ |
| 25_角色 | 角色详细信息和语音 | ⭐⭐⭐⭐⭐ |
| 43_任务 | 任务对话和故事 | ⭐⭐⭐⭐ |
| 218_圣遗物 | 圣遗物背景故事 | ⭐⭐⭐⭐ |
| 13_背包 | 物品背景故事 | ⭐⭐⭐ |
| 20_NPC&商店 | NPC对话和互动 | ⭐⭐⭐⭐ |
| 49_动物 | 生物背景和生态 | ⭐⭐⭐ |
| 251_地图文本 | 地区文化和历史 | ⭐⭐⭐⭐⭐ |

## 安装要求

- Python 3.8+
- 依赖包：
  - `pydantic` - 数据验证和序列化
  - `pathlib` - 路径处理
  - `concurrent.futures` - 并发处理

## 快速开始

### 1. 基本用法

```bash
# 解析所有数据
python scripts/giwiki_run_parser.py

# 只解析敌人数据
python scripts/giwiki_run_parser.py --type "6_敌人"

# 指定输出目录
python scripts/giwiki_run_parser.py --output-dir "my_output"

# 使用8个并发线程
python scripts/giwiki_run_parser.py --workers 8
```

### 2. 编程接口

```python
from giwiki_data_parser.main import GIWikiDataParser

# 创建解析器
parser = GIWikiDataParser(
    data_dir="gi_wiki_scraper/output/structured_data",
    output_dir="output/giwiki_markdown"
)

# 解析所有数据
results = parser.parse_all()

# 解析单个数据类型
result = parser.parse_single_type("6_敌人")
```

### 3. 调试工具

```bash
# 启动交互式调试工具
python giwiki_data_parser/tools/debug_tool.py
```

## 项目结构

```
giwiki_data_parser/
├── __init__.py                 # 包初始化
├── main.py                     # 主解析器类
├── README.md                   # 项目文档
├── models/                     # 数据模型
│   ├── _core.py               # 核心基类
│   ├── character_story_261.py # 角色逸闻模型
│   ├── enemy_6.py             # 敌人模型
│   └── ...                    # 其他数据模型
├── interpreters/              # 数据解释器
│   ├── character_story_261_interpreter.py
│   ├── enemy_6_interpreter.py
│   └── ...                    # 其他解释器
├── formatters/                # Markdown格式化器
│   ├── character_story_261_formatter.py
│   ├── enemy_6_formatter.py
│   └── ...                    # 其他格式化器
├── services/                  # 服务层
│   ├── dataloader.py         # 数据加载服务
│   └── cache_service.py      # 缓存服务
├── utils/                     # 工具模块
│   └── text_transformer.py   # 文本处理工具
└── tools/                     # 开发工具
    └── debug_tool.py         # 调试工具
```

## 架构设计

### 解释器-格式化器模式

每种数据类型都有对应的解释器和格式化器：

1. **解释器 (Interpreter)**: 将JSON数据转换为结构化的Python对象
2. **格式化器 (Formatter)**: 将Python对象转换为Markdown格式

### 数据流程

```
JSON数据 → 解释器 → Python对象 → 格式化器 → Markdown文件
```

### 核心组件

- **GIWikiDataParser**: 主解析器类，协调所有组件
- **DataLoader**: 数据加载服务，负责读取JSON文件
- **CacheService**: 缓存服务，提高重复解析的性能
- **TextTransformer**: 文本处理工具，清理和标准化文本

## 开发指南

### 添加新的数据类型

1. **创建数据模型** (`models/new_type.py`):
```python
from pydantic import BaseModel
from ._core import BaseWikiModel

class NewType(BaseWikiModel):
    name: str
    description: Optional[str] = None
```

2. **创建解释器** (`interpreters/new_type_interpreter.py`):
```python
class NewTypeInterpreter:
    def interpret(self, data: Dict[str, Any]) -> Optional[NewType]:
        # 解析逻辑
        pass
```

3. **创建格式化器** (`formatters/new_type_formatter.py`):
```python
class NewTypeFormatter:
    def format(self, item: NewType) -> str:
        # 格式化逻辑
        pass
```

4. **注册到主解析器** (`main.py`):
```python
self.parsers["new_type"] = {
    "interpreter": NewTypeInterpreter(self.data_loader),
    "formatter": NewTypeFormatter(),
    "enabled": True
}
```

### 代码规范

- 使用类型提示
- 遵循PEP 8编码规范
- 添加适当的文档字符串
- 使用Pydantic进行数据验证
- 处理异常并记录日志

## 故事内容过滤

解析器会自动过滤掉以下类型的数据：

- 纯游戏机制数据（如深境螺旋、秘境）
- 装饰性数据（如名片、头像）
- 建造系统数据（如洞天）
- 临时活动数据
- 教程数据

只保留具有故事价值和世界观设定的内容。

## 输出格式

生成的Markdown文件具有以下特点：

- 清晰的层级结构
- 表格形式的基本信息
- 引用格式的对话内容
- 适当的分段和格式化
- 保留原始的故事结构

## 性能优化

- 并发处理多个数据类型
- 缓存重复解析的结果
- 内存友好的流式处理
- 智能跳过无故事内容的数据

## 故障排除

### 常见问题

1. **数据目录不存在**
   - 确保已运行 `gi_wiki_scraper` 获取数据
   - 检查数据目录路径是否正确

2. **解析失败**
   - 查看生成的解析报告了解详细错误
   - 使用调试工具检查具体文件

3. **内存不足**
   - 减少并发线程数
   - 分批处理数据类型

### 调试技巧

- 使用内置调试工具进行交互式测试
- 查看日志文件了解详细错误信息
- 检查生成的解析报告

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目采用MIT许可证。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持12种数据类型的解析
- 完整的解释器-格式化器架构
- 并发处理和缓存支持
- 交互式调试工具