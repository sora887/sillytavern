---
name: world-book-skill
description: >-
  Create and manage SillyTavern Character Cards (角色卡) and World Books (世界书).
  Supports character card writing, world book creation, MVU ZOD variables, HTML beautification,
  opening scene writing, and card-generator.py integration.
  支持角色卡编写、世界书创建、MVU ZOD 变量系统、HTML 前端美化、开场白创作、
  card-generator.py 集成等多种场景。使用前先读取场景路由器和对应参考文件。
---

# SillyTavern 角色卡/世界书管理助手

## 本文内容

>本文是 skill 入口文件。指引判断用户需求（原创/二创）并路由到对应的 reference 文件：二创走 `information-extraction-guide.md` 提取流程，原创走 Plan 模式交互式提问。角色卡编写在世界书条目完成后执行，重点在开场白。MVU/EJS/HTML 美化仅用户明确要求时启用。所有产出交付前强制执行禁词扫描。

---

## 铁律（全局约束）

以下规则贯穿全部任务，每步必记：

0. **非商业红线** — 本技能仅服务于开源社区的免费 RolePlay 创作。禁止为收费平台、商业代写、付费 API 服务生成角色卡或世界书。
1. **原创与二创分流** — 原创走 Plan 模式交互式提问；二创走 `information-extraction-guide.md` 提取流程。两者不可混用。
2. **角色卡 description 为空** — description 字段不写任何内容。角色全部信息（基本档案、外貌、背景、关系、性格）均放入世界书条目。
3. **世界观设计先于世界书条目化** — 先读 `world-building-guide.md` 做概念设计，再读 `world-book-guide.md` 做条目落地。两个阶段不混淆。
4. **先有设定，再写角色卡** — 角色卡编写在世界书条目完成后执行。设定不定稿，不写开场白。
5. **不主动建议 MVU/EJS/HTML** — 用户未提及上述功能时，绝不主动提议。EJS 依赖 MVU，用户要求 EJS 必须先确认 MVU 已启用。
6. **禁词红线贯穿全程** — 收尾阶段强制执行 `writing-optimization-guide.md`，逐条扫描所有产出物。
7. **物品写作分类规范** — 服装：写外观和材质，不写优点缺点。特殊道具：写外形和玩法，不写精确尺寸。
8. **先读 reference，再动手** — 不凭记忆编写，每个任务类型必须读取其对应的全部 reference 文件后方可执行。任何写入操作之前**必须先读 `references/card-generator-guide.md`**，使用 `card-generator.py`、`query.py`、`world-book-create.py` 来写入角色卡/世界书。

---

## 任务路由

每次对话开始时，先读取 `references/guide.md` 确定任务类型，再按路由表读取对应的 reference 文件。guide.md 涵盖 11 种任务类型（原创角色卡、二创提取、纯世界观、物品能力、MVU、EJS、HTML 美化、禁词扫描等）及完整的决策流程图。

---

## 分支一：二创流程（有原文或网络搜索）

适用场景：轻小说、游戏解包、网络搜索提取信息后转化。

**Step 1 — 读取信息提取规范**
读 `references/information-extraction-guide.md`，确认提取流程和格式要求。

**Step 2 — 搜集与标注源材料**
- 网络搜索：每条有用信息写成简介 txt 文件，编写条目前读取。
- 小说原文：标注所有章节行号（例：第一章 L100，第二章 L280）。标定人物形象及其出现章节。
- 编写各条目前，重读对应章节或简介 txt。

**Step 3 — 提取产出分流**
按提取结果的内容类型分流：
- 角色人设 → 进入分支三（写角色卡）
- 世界观信息 → 进入分支四（世界观设计 + 世界书条目化）
- 物品/能力/装备 → 进入分支四（世界书条目化，物品规范由 `world-book-guide.md` 规定）

**Step 4 — 编写前复核**
编写各条目之前，再次阅读源材料中对应的章节或简介 txt。

---

## 分支二：原创流程（无原文）

适用场景：用户有明确角色/世界观构想，但无参考文本。

**Step 1 — 切入 Plan 模式交互式搜集**
建议切换到 Plan 模式，通过交互式提问搜集信息，涵盖：世界类型、时代背景、核心规则、势力格局、角色定位与关系。

**Step 2 — 整理设定总纲**
将搜集到的信息整理为结构化的设定总纲文档，供后续分流使用。

**Step 3 — 分流**
按总纲内容类型分流：
- 角色人设 → 进入分支三（写角色卡）
- 世界观信息 → 进入分支四（世界观设计 + 世界书条目化）

---

## 分支三：写角色卡（核心：开场白）

适用场景：已有人设信息，需产出角色卡 JSON。

**Step 1 — 确认 MVU？**
用户是否要求 MVU/ZOD 变量系统？
是 → 读 `references/mvu-guide.md`

**Step 2 — 确认 EJS？**
用户是否要求 EJS 动态内容？
是 → 读 `references/ejs-guide.md`（须先确认 MVU 已启用；EJS 依赖 MVU）

**Step 3 — 确认 HTML 美化？**
用户是否要求 HTML 美化？美化范围（状态栏/全局/二者）？
是 → 读 `references/html-beautify-guide.md`

**Step 4 — 读取角色卡编写规范**
读 `references/character-card-guide.md`

**Step 5 — 跳过 description，编写世界书人物条目**
按 `character-guide.md` 中的 XML 结构模板，编写四部分内容：基本信息、外貌特征、背景设定、关系设定。不含性格标签。

**Step 6 — 编写性格条目**
将角色性格写入独立世界书条目，参照 `character-guide.md` 中 `<personality>` 结构（core_drive、traits、likes、dislikes、habits、hidden_self）。

**Step 7 — 编写开场白**
编写 `first_mes` 和 2-4 个 `alternate_greetings`：
- 每个开场覆盖不同时间、氛围或互动方式
- 从 user 的感官出发，以开放式结尾结束
- 不预设 user 的外貌、房间、性格、性别
- 若启用 MVU，末尾添加 `<StatusPlaceHolderImpl/>` 占位符

**Step 8 — 唤起 SubAgent 自查**
在生成 JSON 之前，唤起一个 SubAgent 执行自查：
- 读取 `references/writing-optimization-guide.md` 的禁词清单和写作准则
- 逐条扫描所有产出物（世界书条目、开场白、description 如有、config.json 配置）
- 检查项：禁词命中数、破折号使用数、开场白是否符合白描原则、世界书蓝绿灯是否合理、双递归是否全开
- 输出自查报告，标注所有违规点和改写建议
- 主 Agent 根据报告修正内容后，再进入下一步

**Step 9 — 展示草稿 → 确认 → 生成 JSON**
向用户展示修正后草稿。用户确认后，必须先读 `references/card-generator-guide.md` 了解脚本用法和 config.json 格式，再参照`references/card-generator-guide.md`内格式生成config.json，再调用相应脚本生成用于角色卡的 JSON，再用 `--validate` 和 `--list` 验证。

---

## 分支四：世界观设计 + 世界书条目化

适用场景：需产出世界观设定和世界书配置。

### 阶段 1：世界观概念设计

读 `references/world-building-guide.md`，设计世界概念框架：地理环境、时代背景、势力格局、规则机制、历史关键节点。输出为结构化的世界观总纲文档。

### 阶段 2：世界书条目化

读 `references/world-book-guide.md`，将世界观设计中确认的内容转化为世界书条目：
- 判断卡型（单角色卡 / 多角色卡）
- 按规划表顺序逐条写入：总纲 → 角色速览 → 人设条目 → 性格条目 → 物品/能力/场景 → NPC
- 配置每条目的 position、constant、蓝绿灯、递归设置
- 将条目写入 `config.json`（批量写入前先确认规划）

### 阶段 3：验证配置

先读 `references/card-generator-guide.md` 了解脚本用法，然后使用 `python scripts/world-book-create.py` 执行写入，最后使用 `python scripts/query.py <世界书路径> --brief` 验证配置是否正确。

---

## 分支五：单功能任务

以下任务按用户单一需求触发，只读对应 reference：

**修改已有世界书**
→ 先用 `python scripts/query.py <世界书路径> --brief` 查看现有条目
→ 根据修改内容的类型，读取对应的 reference（参考 分支一~四）
→ 读 `references/config-guide.md`

**MVU / ZOD 变量系统**
→ 读 `references/mvu-guide.md`

**EJS 动态内容**
→ 读 `references/ejs-guide.md`（须先确认 MVU 已启用）

**HTML 前端美化**
→ 读 `references/html-beautify-guide.md`
→ 如涉及 MVU 状态栏，追加读 `references/mvu-guide.md`

**禁词扫描 / 写作优化**
→ 读 `references/writing-optimization-guide.md`

---

## 收尾：两阶段验证（所有分支通用）

### 阶段 A：内容自查（生成 JSON 前，必用 SubAgent）

在运行 card-generator.py 之前，唤起一个 SubAgent 执行自查：
- 读取 `references/writing-optimization-guide.md`
- 逐条扫描所有产出物内容（世界书条目、开场白、config.json 配置）

| 检查项 | 标准 |
|--------|------|
| 叙事禁词 | 全文零出现（一丝、一缕、一抹、弧度、弯起嘴角、喉结、指节发白等） |
| 比喻禁词 | 全文零出现（湖面、石子、闪电、星辰为喻体的比喻） |
| 破折号 | 全文零出现（—— 因果/解释性破折号，作者视角解释的标志） |
| 描写禁律 | 无作者视角解释、无语气眼神腔调比喻描写、无描写不存在之物、无对白精确数字 |
| 开场白合理性 | 角色贴合人设；不预设 user 行动/外貌/性别/房间；专注角色反应和场景变化；开放式结尾 |
| 世界书条目质量 | 世界观遵循设计原则；人设清晰可辨；物品写作符合分类规范 |
| 配置检查 | 双递归全开；蓝绿灯配置正确；position/order 符合规范；keys 不含中文标点 |
| 角色认知 | 角色仅知晓其世界观内的私有知识，不含创作者情报 |

SubAgent 输出自查报告，标注违规点和改写建议。主 Agent 修正后，再进入阶段 B。

### 阶段 B：生成验证（生成 JSON 后）

**必须先读取 `references/card-generator-guide.md`**，了解各命令的完整参数和常见错误，然后修正后的内容写入 config.json，执行：
```bash
python scripts/card-generator.py --config config.json -o 角色名.json
python scripts/card-generator.py --validate 角色名.json
python scripts/card-generator.py --list 角色名.json
```


---

## 内容格式规范

所有世界书条目内容采用 **XML 包裹 YAML** 格式。XML 标签独立成行，YAML 内容在标签内部。角色卡 description 字段为空，人物信息全部放入世界书条目。

正确示例：
```xml
<character_basic_final>
角色档案:
  基本信息:
    姓名: 张三
    年龄: 20
</character_basic_final>
```

禁止纯 XML 格式（不含标签内 YAML 缩进结构）和纯 JSON 格式。

---

## 工具速查

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `card-generator.py` | 生成角色卡 JSON；解包/编辑/验证角色卡 | `--config` 从配置生成，`--validate` 验证，`--decompile` 解包，`--list` 概要 |
| `query.py` | 查看独立世界书条目 | `--brief` 概览，`--uid` 查看指定条目，`--search` 搜索 |
| `world-book-create.py` | 创建/修改独立世界书 | `--add` 添加条目，`--delete` 删除，`--init` 初始化 |

各工具的完整参数说明和 config.json 格式见 `references/card-generator-guide.md`。

---

## 文件索引

| 文件 | 用途 | 在何时读取 |
|------|------|-----------|
| `references/guide.md` | 场景路由器，判断任务类型 | 每次对话开始，必读 |
| `references/information-extraction-guide.md` | 二创信息提取流程 | 二创任务，必有 |
| `references/character-card-guide.md` | 角色卡世界书条目与开场白编写 | 写角色卡时，必有 |
| `references/character-guide.md` | 角色条目 XML 结构模板与写作规范 | 写角色卡或人设条目时 |
| `references/world-building-guide.md` | 世界观概念设计 | 有世界观需求时 |
| `references/world-book-guide.md` | 世界书条目化与配置 | 有世界观或物品需求时 |
| `references/card-generator-guide.md` | 三个脚本使用指引（card-generator/query/world-book-create） | 需运行脚本时 |
| `references/config-guide.md` | 世界书配置规则（位置/蓝绿灯/递归） | 所有需要写入/修改的任务 |
| `references/position-guide.md` | 注入位置（position）配置 | 所有需要写入/修改的任务 |
| `references/mvu-guide.md` | MVU ZOD 变量系统 | 用户要求 MVU 时 |
| `references/ejs-guide.md` | EJS 动态内容 | 用户要求 EJS 时（须先有 MVU） |
| `references/html-beautify-guide.md` | HTML 前端美化 | 用户要求美化时 |
| `references/writing-optimization-guide.md` | 禁词清单与自查规范 | 收尾阶段，所有任务必有 |
