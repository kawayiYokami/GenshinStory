# Meme 资源使用说明

本目录用于管理 Agent 聊天内的表情资源与角色专属表情包。

## 目录结构

```text
public/meme/
├─ memes/                      # 旧版公共表情包（按情绪分类）
├─ memes_data.json             # 表情文案说明（可选）
├─ meme_index.json             # 自动生成的表情索引（程序直接读取）
└─ agents/                     # 角色专属表情包根目录
   ├─ gi_furina_role/
   ├─ gi_mona_role/
   ├─ gi_nahida_role/
   ├─ gi_zhongli_role/
   ├─ hsr_herta_role/
   ├─ hsr_march7th_role/
   ├─ hsr_sparkle_role/
   └─ hsr_ruanmei_role/
```

## 角色配置（在 role.yaml 中）

每个内置角色在 `public/domains/*/core/roles/*.yaml` 中配置：

```yaml
ui:
  icon: /avatars/gi/gi_furina_role.png
  memePack: /meme/agents/gi_furina_role
```

- `ui.icon`：角色头像路径（可先占位，后续补图）
- `ui.memePack`：该角色专属表情包根路径

## 资源放置规则

当模型输出 `:happy:`、`:sad:` 等表情语法时，系统会按下面路径查找：

```text
{memePack}/{emoteName}/表情{group}_{index}.png
```

示例：

```text
/meme/agents/gi_furina_role/happy/表情1_1.png
/meme/agents/gi_furina_role/sad/表情2_45.png
```

其中：
- `emoteName` 为表情名（如 `happy`、`sad`、`angry`）
- 文件命名兼容现有规则 `表情{组号}_{序号}.png`

## 索引生成

前端不再扫描目录，也不再硬编码文件名。  
请在资源更新后执行：

```bash
python scripts/generate_meme_index.py
```

该脚本会：
- 读取 `memes_data.json` 的表情名
- 扫描 `meme/memes` 公共目录
- 扫描 8 个预设角色目录（`meme/agents/*`）
- 生成 `meme/meme_index.json`

## 回退逻辑

若角色专属目录下未找到可用图片，会自动回退到公共表情包：

```text
/meme/memes/{emoteName}/...
```

这样可以先完成配置，再逐步补齐每个角色的专属表情素材。

## 新增角色时的步骤

1. 在对应 `role.yaml` 增加 `ui.icon` 与 `ui.memePack`
2. 在 `public/meme/agents/` 下创建同名目录
3. 按情绪创建子目录并放入图片（如 `happy/`, `sad/`）
4. （可选）在 `public/avatars/{domain}/` 放入头像文件
