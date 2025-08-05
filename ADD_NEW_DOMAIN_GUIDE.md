# 新增领域说明书

本文档旨在说明如何在项目中添加一个新的“领域”（Domain）。领域是内容和功能隔离的基本单位，例如“Genshin Impact”和“Honkai: Star Rail”都是独立的领域。

## 领域文件结构

一个标准的领域包含以下文件和目录结构：

```
web/docs-site/public/domains/
├── <your_domain_id>/
│   ├── core/
│   │   ├── instructions/
│   │   │   └── (指令.md 文件)
│   │   ├── personas/
│   │   │   └── (人格.yaml 文件)
│   │   ├── roles/
│   │   │   └── (角色.yaml 文件)
│   │   └── roles.json
│   ├── docs/
│   │   └── (领域专属的Markdown文档)
│   └── metadata/
│       └── catalog.json
└── manifest.json
```

- **`<your_domain_id>`**: 领域的唯一标识符，将用作目录名和内部引用。请使用简短、小写的名称（例如 `gi`, `hsr`）。
- **`core/`**: 存放领域的核心定义文件。
  - **`instructions/`**: 包含供 AI 使用的特定指令，格式为 Markdown (`.md`)。
  - **`personas/`**: 定义了领域内可用的不同“人格”，格式为 YAML (`.yaml`)。
  - **`roles/`**: 定义了领域内可用的不同“角色”，格式为 YAML (`.yaml`)。
  - **`roles.json`**: 一个 JSON 文件，列出了该领域所有可用的角色 ID。
- **`docs/`**: (可选) 存放该领域专属的知识库文档，格式为 Markdown (`.md`)。
- **`metadata/`**: (可选) 存放由文档自动生成的元数据。
  - **`catalog.json`**: `docs/` 目录下所有文档的文件索引，用于实现快速搜索和路径解析。
- **`manifest.json`**: 位于 `domains` 根目录，是所有领域的清单文件。

## 新增步骤

以下是添加一个新领域的完整步骤：

### 1. 创建领域目录结构

1.  在 `web/docs-site/public/domains/` 目录下，创建一个以你的领域ID命名的新文件夹（例如 `my_new_domain`）。
2.  在新创建的 `<your_domain_id>` 文件夹内，创建 `core` 子文件夹。
3.  在 `core` 文件夹内，分别创建 `instructions`, `personas`, 和 `roles` 三个子文件夹。

### 2. 添加核心定义文件

1.  **定义角色 (Roles)**:
    - 在 `roles` 文件夹中，为每个角色创建一个 `.yaml` 文件 (例如 `my_character_role.yaml`)。
    - 文件内容应描述该角色的属性和能力。
2.  **定义人格 (Personas)**:
    - 在 `personas` 文件夹中，为每个人格创建一个 `.yaml` 文件 (例如 `my_character_persona.yaml`)。
    - 文件内容应描述该人格的性格、背景和说话风格。
3.  **创建角色清单 (`roles.json`)**:
    - 在 `core` 文件夹中，创建一个名为 `roles.json` 的文件。
    - 在此文件中，以 JSON 数组的形式列出所有可用角色的 ID（即 `roles` 目录下的文件名，不含 `.yaml` 后缀）。
    - 示例:
      ```json
      [
        { "id": "my_character_role" },
        { "id": "another_character_role" }
      ]
      ```

### 3. (可选) 添加领域专属文档

如果你的领域需要一个独立的知识库：

1.  在 `<your_domain_id>` 目录下创建一个 `docs` 文件夹。
2.  将所有相关的 Markdown (`.md`) 文档放入 `docs` 文件夹内，你可以根据需要创建子目录来组织它们。
3.  运行项目提供的脚本来生成 `metadata/catalog.json` 文件。这个文件是文档搜索引擎正常工作所必需的。（注意：请参考项目构建流程或联系维护者了解如何生成此文件）。

### 4. 在主清单中注册新领域

最后一步是让应用知道这个新领域的存在。

1.  打开位于 `web/docs-site/public/domains/` 根目录下的 `manifest.json` 文件。
2.  在 JSON 数组中，为你的新领域添加一个新的对象。该对象应包含：
    - `id`: 你的领域 ID（必须与文件夹名称一致）。
    - `name`: 一个易于阅读的显示名称。
3.  示例:
    ```json
    [
      {
        "id": "hsr",
        "name": "Honkai: Star Rail"
      },
      {
        "id": "gi",
        "name": "Genshin Impact"
      },
      {
        "id": "my_new_domain",
        "name": "My New Awesome Domain"
      }
    ]
    ```

完成以上步骤后，重新启动应用程序，新的领域就应该可用了。
