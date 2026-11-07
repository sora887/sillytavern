# 脚本使用指引

> 本文档说明三个 Python 脚本的完整用法。所有参数、配置格式、常见错误和酒馆兼容性约束均在此列出。使用前必须通读。

## 本文内容

>本文指引 card-generator.py（角色卡 JSON 生成/解包/编辑/验证/列表）、query.py（独立世界书条目查询）、world-book-create.py（独立世界书命令行管理）的完整用法。覆盖全部 CLI 参数、config.json 字段与对应关系、MVU/状态栏自动生成机制、酒馆 v2 规范兼容要点、以及排错记录中的已知坑点。

---

## 工作流程

### 阶段一：判断用哪个脚本

| 场景 | 脚本 | 命令模式 |
|------|------|---------|
| 从 config.json 生成角色卡 JSON | card-generator.py | `--config` — **这是必须使用的标准流程** |
| 从已有角色卡解包出可编辑 config.json | card-generator.py | `--decompile` |
| 修改已有角色卡字段 | card-generator.py | `--edit` |
| 验证角色卡 JSON 结构和安全性 | card-generator.py | `--validate` |
| 查看角色卡概要（条目数/正则数/双递归） | card-generator.py | `--list` |
| 交互式创建 | card-generator.py | `--interactive` |
| 提取简化模板 | card-generator.py | `--extract` |
| 查看独立世界书条目 | query.py | 默认 / `--brief` / `--uid` / `--search` / `--resolve` |
| 创建/编辑/删除独立世界书条目 | world-book-create.py | `--add` / `--batch-edit` / `--delete` |

**铁律：禁止手写 JSON，必须通过 card-generator.py --config 生成。**

---

## card-generator.py — 角色卡生成器（核心）

### 全部 CLI 参数

```
python card-generator.py                                                    # 显示帮助
python card-generator.py --config config.json -o output.json               # 从配置生成（标准流程）
python card-generator.py --interactive                                     # 交互式创建
python card-generator.py --decompile card.json -o config.json              # 解包角色卡为可编辑配置
python card-generator.py --extract card.json -o template.json              # 提取简化模板（兼容旧参数）
python card-generator.py --validate card.json                              # 验证角色卡结构
python card-generator.py --list card.json                                  # 查看角色卡概要
python card-generator.py card.json --edit --name "新名"                     # 原位编辑
python card-generator.py card.json --edit --add-greeting "新开场"           # 追加可选开场
python card-generator.py card.json --edit --enable-mvu true                 # 启用MVU
```

### config.json 完整字段详解

```json
{
  "card": {
    "name": "角色卡名称（必填）",
    "description": "",
    "personality": "",
    "scenario": "",
    "first_mes": "默认开场白（含<StatusPlaceHolderImpl/>，如有MVU）",
    "creator_notes": "作者备注",
    "system_prompt": "",
    "post_history_instructions": "",
    "creator": "作者名",
    "character_version": "1.0",
    "alternate_greetings": ["开场2", "开场3"]
  },
  "extensions": { "talkativeness": "0.5" },
  "worldbook": {
    "name": "世界书名称",
    "entries": [
      {
        "comment": "条目标题",
        "keys": [],
        "secondary_keys": [],
        "content": "条目内容（XML包裹YAML格式）",
        "constant": true,
        "position": "before_char",
        "order": 1,
        "enabled": true,
        "depth": 4,
        "prevent_recursion": true,
        "exclude_recursion": true
      }
    ]
  },
  "regex_scripts": [
    {
      "name": "正则名称",
      "findRegex": "/<pattern>/flags",
      "replaceString": "",
      "markdownOnly": true,
      "promptOnly": false,
      "placement": [2],
      "minDepth": null,
      "maxDepth": null,
      "runOnEdit": false,
      "substituteRegex": 0
    }
  ],
  "tavern_helper": {
    "scripts": [
      {
        "name": "脚本名",
        "content": "JS代码",
        "enabled": true,
        "buttons": [{"name": "按钮名", "visible": true}]
      }
    ]
  },
  "mvu": {
    "enabled": true,
    "schema_script": "完整Zod Schema JS代码（含import registerMvuSchema + registerMvuSchema调用）",
    "initvar": "角色名:\n  好感度: 20\n  关系状态: 陌生人",
    "update_rules": "YAML格式的变量更新规则",
    "output_format": "可选，留空使用内置JSON Patch模板",
    "variable_list_path": "stat_data",
    "hide_regex": true,
    "beautify_regex": true
  },
  "statusbar": {
    "enabled": true,
    "html": "<!DOCTYPE html>...完整HTML状态栏代码...",
    "hide_regex": true
  }
}
```

### card 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 角色卡名称（必填） |
| `description` | string | 为空字符串。角色信息全部在世界书条目中 |
| `first_mes` | string | 默认开场。如有MVU，末尾须含 `<StatusPlaceHolderImpl/>` |
| `alternate_greetings` | string[] | 可选开场数组 |
| `creator` | string | 作者名 |
| `character_version` | string | 版本号 |

### worldbook.entries 字段

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `comment` | string | — | 条目标题/备注 |
| `keys` | array | `[]` | 触发关键词（英文逗号分隔的列表） |
| `secondary_keys` | array | `[]` | 辅助触发关键词 |
| `content` | string | — | 条目内容（XML包裹YAML格式） |
| `constant` | boolean | `true` | true=蓝灯常驻, false=绿灯关键词触发 |
| `position` | string | `"after_char"` | `"before_char"` / `"after_char"` / `"at_depth"` |
| `order` | number | `100` | 插入顺序，数字越小越靠前 |
| `enabled` | boolean | `true` | 启用/禁用 |
| `depth` | number | `4` | 深度层级（position=at_depth 时生效） |
| `prevent_recursion` | boolean | `true` | 本条目不触发其他条目。**必须为true** |
| `exclude_recursion` | boolean | `true` | 其他条目不触发本条目。**必须为true** |

**酒馆兼容性警告（来自酒馆源码）：**
- 位置0-7在运行时 switch 中无 default 以外的分支 → 无效位置值的条目会被静默跳过，永不激活
- `getSortedEntries()` 在遇到任何异常时返回 `[]` → 一条错误条目可导致所有世界书条目被静默丢弃
- 缺失的字段会被 `addMissingWorldInfoFields()` 静默填充默认值（excludeRecursion=false 是默认值！）
- **结论：每个条目的 `prevent_recursion` 和 `exclude_recursion` 必须显式设为 true，不可依赖默认值**

### regex_scripts 字段

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `name` | string | — | 正则名称 |
| `findRegex` | string | — | slash风格正则 `/pattern/flags`。内部 `/` 会自动转义为 `\/` |
| `replaceString` | string | `""` | 替换内容。留空=隐藏 |
| `markdownOnly` | boolean | `true` | true=仅用户可见（显示美化），false=AI也可见 |
| `promptOnly` | boolean | `false` | true=仅提示词阶段生效（对AI隐藏内容） |
| `placement` | int[] | `[2]` | [1]=显示阶段, [2]=提示词阶段 |
| `minDepth` | int? | `null` | 最小楼层深度限制 |
| `maxDepth` | int? | `null` | 最大楼层深度限制 |
| `runOnEdit` | boolean | `false` | 编辑消息时也运行 |
| `substituteRegex` | int | `0` | 替换模式 |

**正则组合规则：**
- 显示美化：`markdownOnly=true, promptOnly=false` — 用户看到美化效果
- AI隐藏：`markdownOnly=false, promptOnly=true` — AI看不到该内容
- 楼层限制：`[不发送]去除变量更新` 用 `minDepth=4` — 只隐藏旧楼层，最新3楼AI可见

### tavern_helper.scripts 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 脚本名称 |
| `content` | string | 完整JS代码 |
| `enabled` | boolean | 启用状态 |
| `buttons` | object[] | 按钮配置：`{"name": "按钮名", "visible": true/false}` |

### mvu 自动生成机制

当 `mvu.enabled = true` 时，card-generator.py 自动生成以下内容。**在 config.json 的 worldbook.entries 中不要手写这些条目：**

| 自动生成 | 内容 | 配置 |
|---------|------|------|
| MVU 核心脚本 | bundle.js import | tavern_helper: "MVU", 6个按钮 |
| Zod Schema 脚本 | 从 schema_script 字段 | tavern_helper: "变量结构" |
| [initvar]条目 | `<initvar>YAML</initvar>` 包裹 | position=0 (before_char), enabled=false, order=14720 |
| 变量列表条目 | `<status_current_variable>` + 宏 | position=4 (at_depth), depth=0, order=14720 |
| [mvu_update]变量更新规则 | 从 update_rules 字段 | position=4 (at_depth), depth=0, order=14720 |
| [mvu_update]变量输出格式 | JSON Patch 模板 | position=4 (at_depth), depth=0, order=14720 |
| [不发送]去除变量更新 正则 | 隐藏 UpdateVariable 块 | promptOnly, minDepth=4 |
| [美化]完整变量更新 正则 | details 折叠面板 | markdownOnly |
| [美化]变量更新中 正则 | 不完整标签提示 | markdownOnly |

**initvar 格式铁律（参照排错记录错误3）：**
- 条目位置：`before_char` (position=0)
- 条目 enabled=false（禁用状态）
- 内容格式：必须用 `<initvar>` 标签包裹纯 YAML，例如：
  ```
  <initvar>
  角色名:
    好感度: 20
    关系状态: 陌生人
  </initvar>
  ```
- 不得在开场消息中嵌入 initvar

**变量条目位置铁律（参照排错记录错误3）：**
- 变量更新规则：[mvu_update] 前缀，位置 at_depth D0
- 变量输出格式：[mvu_update] 前缀，位置 at_depth D0
- 变量列表：位置 at_depth D0
- 所有 MVU 条目 order 统一为 14720

### statusbar 自动生成机制

当 `statusbar.enabled = true` 时自动生成：

| 自动生成 | 配置 |
|---------|------|
| [界面]状态栏 正则 | findRegex=`<StatusPlaceHolderImpl/>`, markdownOnly, placement=[2] |
| [不发送]界面占位符 正则 | findRegex=`<StatusPlaceHolderImpl/>`, promptOnly, placement=[2] |

**statusbar.html 注意事项（参照排错记录错误4）：**
- 必须使用 `{{format_message_variable::stat_data.路径}}` 宏读取MVU变量值
- 不得使用 `${AFFECTION}` 等 Python 占位符
- 脚本不内置任何 HTML 模板，HTML 完全由配置文件的 statusbar.html 字段提供
- 如需要JS实时刷新，在正则的 replaceString 中包含完整HTML+JS（含 eventOn 监听 VARIABLE_UPDATE_ENDED）

### 模式详解

#### --config（标准生成流程，必须使用）

```bash
python card-generator.py --config config.json -o card.json
```

读取 config.json，构建完整的 chara_card_v3 JSON 并保存。这是唯一正确的生成方式。禁止跳过此步骤手写 JSON。

#### --validate（生成后必须执行）

```bash
python card-generator.py --validate card.json
```

检查项：
- spec 是否为 chara_card_v3
- 是否有 data 对象和 data.name
- 世界书条目是否缺少 content
- 世界书条目的 prevent_recursion 和 exclude_recursion 是否为 true（否则 WARN）
- 正则脚本的 findRegex 是否为空（否则 WARN）

#### --list（查看概要）

```bash
python card-generator.py --list card.json
```

输出：名称、版本、作者、描述/开场长度、可选开场数、世界书条目列表（位置/蓝绿灯/启用/双递归）、正则脚本列表、酒馆助手脚本列表、验证结果。

#### --decompile（解包）

```bash
python card-generator.py --decompile card.json -o config.json
```

从已有角色卡 JSON 反向提取完整配置。自动检测 MVU 和状态栏配置，输出格式与 --config 输入格式完全兼容。

#### --edit（原位编辑）

```bash
python card-generator.py card.json --edit --name "新名字"
python card-generator.py card.json --edit --add-greeting "新开场"
python card-generator.py card.json --edit --enable-mvu true
```

支持的编辑参数：--name, --description, --personality, --scenario, --first-mes, --creator-notes, --creator, --talkativeness, --add-greeting, --enable-mvu, --enable-statusbar

---

## query.py — 独立世界书查询

仅用于独立的 `.json` 世界书文件。角色卡内嵌世界书由 card-generator.py --list 查看。

### 全部 CLI 参数

```bash
query.py <世界书.json>                   # 列出所有条目摘要
query.py <世界书.json> --brief            # 极简模式（含双递归字段）
query.py <世界书.json> --uid <UID>        # 查看指定条目完整内容
query.py <世界书.json> --search "关键词"   # 搜索匹配条目（标题/内容/触发词）
query.py <世界书.json> --resolve           # 解析条目的 @UID/@名称 嵌套引用
```

### 输出字段（--brief 模式）

uid, comment, content_length, content_preview, keys, position, constant, order, depth, scanDepth, preventRecursion, excludeRecursion

---

## world-book-create.py — 独立世界书管理

仅用于创建不嵌入角色卡的独立世界书文件。

### 全部 CLI 参数

```bash
# 初始化空世界书
python world-book-create.py <世界书.json> --init --name "世界书名称"

# 添加条目
python world-book-create.py <世界书.json> --add \
  --comment "条目名称" \
  --content "条目内容（或 @文件路径 从文件读取）" \
  --keys "触发词1,触发词2" \
  --position 0 --order 1 --constant \
  --prevent-recursion --exclude-recursion

# 批量编辑条目
python world-book-create.py <世界书.json> --batch-edit --uid 0 --comment "新名称"

# 删除条目
python world-book-create.py <世界书.json> --delete --uid 0
```

### 全部 flag

| flag | 说明 |
|------|------|
| `--init` | 初始化空世界书文件 |
| `--add` | 添加新条目 |
| `--batch-edit` | 批量编辑（需配合 --uid） |
| `--delete` | 删除条目（需配合 --uid） |
| `--name "名称"` | 世界书名称 |
| `--comment "名称"` | 条目标题 |
| `--content "内容"` | 条目内容。支持 `@文件路径` 从文件读取 |
| `--keys "k1,k2"` | 触发关键词，英文逗号分隔 |
| `--keys2 "k1,k2"` | 辅助触发关键词 |
| `--position N` | 插入位置（0-7整数） |
| `--order N` | 插入顺序 |
| `--constant` | 蓝灯常驻 |
| `--no-constant` | 取消蓝灯 |
| `--prevent-recursion` | 阻止进一步递归。**必须** |
| `--exclude-recursion` | 排除被递归。**必须** |
| `--depth N` | 深度层级（position=4时生效，默认1） |
| `--disable` | 禁用条目 |
| `--enable` | 启用条目 |
| `--selective` | 选择性激活 |
| `--selective-logic N` | 选择性逻辑（0=AND_ANY, 1=NOT_ALL, 2=NOT_ANY, 3=AND_ALL） |
| `--scan-depth N` | 扫描深度限制 |
| `--role N` | 角色（0=system, 1=user, 2=assistant） |
| `--outlet-name "端口名"` | 预设端口名（position=7 时必需） |

---

## 酒馆 v2 规范兼容要点

摘自酒馆源码 `world-info.js` 和 `characters.js`，直接决定角色卡能否在酒馆正常加载：

### 位置（position）

- 酒馆内部使用 0-7 的整数，不是字符串
- card-generator.py 接受 `"before_char"` / `"after_char"` / `"at_depth"` 字符串并在生成 JSON 时正确映射
- 不要在 config.json 中手写数字 position
- 服务端在保存 v2 卡时仅区分 position==0 和 position!=0 → 位置 2-7 在往返后靠 extensions.position 保留

### 双递归（prevent_recursion / exclude_recursion）

- 酒馆默认值均为 false
- card-generator.py 生成时默认设为 true
- **但手动修改 config.json 后再生成时，如果条目对象未显式含这两个字段，会按代码默认值 true 处理**
- 在 world-book-create.py 中，这两个 flag 默认 false，必须显式传入

### 条目 ID 与 keys

- 条目 ID 自动分配为 0, 1, 2... 递增整数
- keys/trigger 关键词之间用英文逗号分隔
- 缺失 key 字段会被酒馆静默修复为 `[]`

### 静默失败场景

- 无效 position 值 → 条目永不激活，无任何错误提示
- getSortedEntries() 异常 → 返回 []，所有世界书条目被丢弃
- 条目渲染异常 → 单条目静默跳过
- loadWorldInfo() HTTP 错误 → 静默返回 null
- **结论：生成后用 --validate 检查，用 --list 确认条目数正确**

---

## 常见错误

| # | 错误 | 原因 | 正确做法 |
|---|------|------|---------|
| 1 | 手写 JSON 而非脚本生成 | 跳过 card-generator.py 流程 | 必须用 `--config config.json -o card.json` 生成 |
| 2 | initvar 未用 `<initvar>` 标签包裹 | 纯 YAML 无标签 | 内容格式 `<initvar>\nYAML\n</initvar>` |
| 3 | initvar 条目位置错误 | 放在 after_char (position 1) | 必须 before_char (position 0) |
| 4 | 变量更新规则位置错误 | 放在 after_char | 必须 at_depth, depth=0 |
| 5 | 缺少 `<StatusPlaceHolderImpl/>` | 开场白末尾无占位符 | 每个开场白末尾附加 `<StatusPlaceHolderImpl/>` |
| 6 | 正则双重转义 | 脚本旧版 escape_regex_body bug | 当前版本已修复：先 normalize 再 escape |
| 7 | exclude_recursion 或 prevent_recursion 为 false | 酒馆默认 false | 所有条目必须显式设为 true |
| 8 | keys 用中文逗号/空格分隔 | 酒馆不识别 | 只用英文逗号分隔 |
| 9 | initvar 被嵌入开场消息 | 旧版代码残留 | initvar 只放在世界书 [initvar] 条目中 |
| 10 | HTML 中使用 `${VARIABLE}` 占位符 | 不是 MVU 宏 | 使用 `{{format_message_variable::stat_data.路径}}` |

---

## 自查清单

- [ ] 使用 `--config` 生成，非手写 JSON
- [ ] 生成后运行 `--validate` 通过
- [ ] 运行 `--list` 确认世界书条目数量正确
- [ ] 所有世界书条目 `prevent_recursion=true` 且 `exclude_recursion=true`
- [ ] initvar 条目 position=before_char, enabled=false, 内容 `<initvar>` 标签包裹
- [ ] 变量更新规则/输出格式/列表：position=at_depth, depth=0
- [ ] 开场白末尾含 `<StatusPlaceHolderImpl/>`（有MVU时）
- [ ] 正则 findRegex 使用 slash 风格 `/pattern/flags`
- [ ] statusbar.html 使用 `{{format_message_variable::stat_data.路径}}` 宏
- [ ] worldbook.entries 中不含 initvar/变量列表/更新规则条目。这些由 mvu.enabled 自动生成
