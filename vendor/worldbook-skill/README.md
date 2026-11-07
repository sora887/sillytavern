# SillyTavern 角色卡/世界书管理助手 — Character & World Book Manager

一句话让 AI 读轻小说/设定集，自动生成结构化世界书 JSON 与角色卡。

**注意：本项目基本由 AI 生成，可能会出现意料之外的问题。作者并不很懂编程，但欢迎提出 issue。**

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## 致谢
本项目的角色卡编写方法论和提示词设计大量参考了 [sanmingyue](https://github.com/sanmingyue) 大佬的写卡教程与工作流理念，是本技能写作规范的基石。

## 立场声明
本项目致力服务于开源RolePlay社区，服务于非商业的角色扮演创作。
严禁用于任何收费 AI 平台、商业 API 服务、或盈利性角色卡代写业务。
违反上述条款的使用者，将拒绝提供任何技术支持。

---

## 这是什么

一个 **AI Skill + CLI 工具** 的组合包。给 AI 装上它，SAY：

> "帮我读这本轻小说，把所有角色、世界观做成世界书条目"
> "根据这个设定，帮我写一个带 MVU 状态栏和 HTML 美化的角色卡"
> "为我生成一个有关于赛车的世界书，并提取作者的文风"

AI 就会自动执行任务：
1. **识别** — 自动判断原创还是二创，角色卡还是世界书，是否需要 MVU/EJS/HTML 美化。
2. **编写** — 遵循"角色卡编写铁律"，XML 包裹 YAML 格式，description 空置、全部信息塞入世界书条目。
3. **自查** — 唤起 SubAgent 执行禁词扫描（含破折号、叙事禁词、比喻禁词、描写禁律），自查通过后才进入生成。
4. **生成** — 调用 CLI 脚本输出可直接导入 SillyTavern 的世界书或角色卡 JSON。

## 功能一览

| 功能 | 说明 |
|------|------|
| **轻小说→世界书** | 喂文本，AI 自动抽取角色/世界观，标注章节行号，生成标准世界书 JSON |
| **高颜值角色卡** | 生成支持 MVU ZOD 与前端美化的角色卡，含人物设定、性格、世界观、开场白 |
| **MVU & EJS 动态内容** | 集成 ZOD 变量系统 + EJS 多阶段人设/调色盘，支持状态栏渲染与全局正文美化 |
| **HTML 美化** | 全局美化 + 状态栏美化 + 开场选择器，响应式 CSS 变量体系，内联 SVG 图标 |
| **CLI 管理工具** | `world-book-create.py` (世界书) / `card-generator.py` (角色卡) / `query.py` (查询) |
| **SubAgent 质量自检** | 生成 JSON 前唤起 SubAgent，逐字扫描禁词、破折号、配置正确性，修正后才输出 |

## 支持场景

| 场景 | 使用的 reference |
|------|-----------------|
| **原创角色卡制作** | character-card-guide + character-guide + card-generator-guide |
| **二创/轻小说转化** | information-extraction-guide + character-card-guide + world-book-guide |
| **MVU 变量系统** | mvu-guide |
| **EJS 动态内容** | ejs-guide（须先有 MVU） |
| **HTML 前端美化** | html-beautify-guide |
| **原创世界观设计** | world-building-guide + world-book-guide + config-guide |
| **物品/能力/装备** | world-book-guide + config-guide |
| **文风/故事提取** | information-extraction-guide + writing-optimization-guide |
| **修改/查询已有内容** | query.py + card-generator.py --decompile |
| **禁词扫描与写作优化** | writing-optimization-guide |

---

## 目录结构

```
world-book-skill/
├── SKILL.md                          # 技能入口：v4.0 重构，二创/原创分流，SubAgent自查
├── plan.md                           # 施工蓝图：文件清单与参考来源映射
├── agents/openai.yaml                # 技能注册元数据
├── scripts/
│   ├── world-book-create.py         # 世界书增删改查 CLI (+position 0-7 校验)
│   ├── card-generator.py            # 角色卡 V3 JSON 生成/解包/编辑/验证/列表
│   └── query.py                     # 世界书轻量查询/导出工具
└── references/
    ├── guide.md                     # 场景路由器（11 种任务类型，AI 第一步读取）
    ├── character-card-guide.md      # 角色卡编写：世界书条目 + 开场白（description 空）
    ├── character-guide.md           # 角色条目结构模板（XML 包裹 YAML）
    ├── world-building-guide.md      # 世界观设计（概念层，A/B/C 类型判定）
    ├── world-book-guide.md          # 世界书条目化（落地层，蓝绿灯决策，物品规范）
    ├── information-extraction-guide.md # 二创信息提取（章节行号标注，outline.txt）
    ├── writing-optimization-guide.md   # 禁词扫描 + 写作优化（含破折号禁词）
    ├── card-generator-guide.md      # 三个脚本完整使用指引（含酒馆兼容要点）
    ├── config-guide.md              # 世界书配置规则（位置/蓝绿灯/递归）
    ├── position-guide.md            # ST 注入位置参考
    ├── mvu-guide.md                 # MVU ZOD 变量系统（五阶段集成流程）
    ├── ejs-guide.md                 # EJS 动态内容（多阶段人设、调色盘）
    └── html-beautify-guide.md       # HTML 前端美化（全局/状态栏/换行规则）
```

## 依赖

- Python 3.8+
- SillyTavern (用于导入生成的 JSON)

---

# 更新日志

## v4.0.2 — 2026-05-18 (Current)

### 提示词强化
- **`card-generator-guide.md` 必读强调**：在 `SKILL.md`（铁律/分支三/分支四/收尾）、`guide.md`（场景路由器/类型2/执行原则）、`world-book-guide.md`（头部/阶段四/自查清单）共 11 处位置新增/强化了必须阅读 `card-generator-guide.md` 的声明，防止 AI 凭记忆直接输出酒馆世界书/角色卡 JSON 格式。

## v4.0.1 — 2026-05-18

### 合并 PR 修复与增强

| 来源 | PR | 内容 |
|------|-----|------|
| **pisces1986** | [#1](https://github.com/echo-xianyu/worldbook-skill/pull/1) | `world-book-create.py`：新增 `_camel_to_snake()` 自动转换，`_Args` 支持 camelCase/snake_case 双属性。batch JSON 同时兼容 `preventRecursion` 和 `prevent_recursion` 两种字段名。 |
| **pisces1986** | [#3](https://github.com/echo-xianyu/worldbook-skill/pull/3) | `world-book-create.py`：`parse_key_list()` 同时支持数组和逗号分隔字符串输入。`card-generator.py`：新增 `card.name` 必填校验，新增 MVU 风格冲突检测（zod/beta 混用时报错），MVU 启用时检查开场白是否缺少 `<StatusPlaceHolderImpl/>` 占位符警告。 |
| **uiharuayako** | [#4](https://github.com/echo-xianyu/worldbook-skill/pull/4) | `agents/openai.yaml`：修复第14行角色卡任务引用文件名（`card-writing-guide.md` → `character-card-guide.md`），修复第23行禁词扫描引用文件名（→ `writing-optimization-guide.md`）。 |

## v4.0 — 2026-05-17

### 架构重构
- **工作流程彻底拆分**：原创与二创分流独立流程。原创走 Plan 模式交互式搜集，二创走 `information-extraction-guide.md` 提取管线。
- **description 空置**：角色卡 description 字段不再写入内容，所有角色信息（基本档案、外貌、背景、关系、性格）全部塞入世界书条目，杜绝 AI 提前读取 description 导致性格标签打架。
- **世界观与世界书分层**：世界观设计（`world-building-guide.md`）与世界书条目化（`world-book-guide.md`）拆为两个阶段，概念与落地互不混淆。
- **SubAgent 自查机制**：生成 JSON 前必须唤起 SubAgent 执行禁词自查，逐字扫描通过后才调用 card-generator.py 生成输出。

### 新增功能
- **EJS 动态内容支持**：新增 `ejs-guide.md`，覆盖多阶段人设（控制器 + 阶段条目 + getwi 加载）和多阶段调色盘（底色/衍生/二次解释按变量值切换）。EJS 依赖 MVU，两者独立但不绑定。
- **全脚本使用指引**：新增 `card-generator-guide.md`，覆盖三个 Python 脚本的全部 CLI 参数、config.json 逐字段说明、MVU/状态栏自动生成机制、酒馆 v2 规范兼容要点（position 0-7 范围校验、双递归强制开启）。
- **脚本数据保护**：`card-generator.py` 新增 position 范围检查、content 空值检查、keys 中文标点检查；`world-book-create.py` 新增 position 越界拒绝写入。

### 禁词与质量优化
- **破折号列入禁词**：`writing-optimization-guide.md` 禁词表新增"——"（因果/解释性破折号），skill 自身全部 11 个 reference 文件已清理破折号。
- **全局换行规则**：`html-beautify-guide.md` 新增 4 条全局美化规则（容器 white-space、占位符保留、CSS 作用域隔离、宏优先渲染），解决全局美化与状态栏互斥、文本挤作一团的问题。

### 指引修改
- 所有 reference 文件开头从"你的角色"改为"本文内容"，skill 不是让 AI 扮演角色，而是告诉 AI 这篇指引覆盖什么范围。
- `character-guide.md` 模板从纯 XML 改为 XML 包裹 YAML 格式。
- `world-book-guide.md` 物品/场景条目模板同步改为 XML 包裹 YAML。
- `guide.md` 场景路由器重新编号，恢复故事/章节提取为独立类型 6。
- `SKILL.md` 铁律、分支、收尾全部重写，自查前置于生成前。

## v3.0 — 2026-05-14

### 重大功能升级
- **角色卡系统上线**：新增 `card-generator.py`，支持生成/解包高标准 V3 角色卡 JSON。
- **美化支持**：新增 `html-beautify-guide` 与 `mvu-guide`，支持 ZOD 变量状态栏与全局美化布局。
- **质量检查体系**：引入 DoubleCheck 质量清单，包含逐字禁词扫描与一致性检查。
- **格式标准演进**：全面转向 XML 包裹 YAML 格式，提升 AI 编写的结构化程度。

### 细节优化
- `SKILL.md` 全面重写，增加任务路由逻辑。
- 细化场景路由器 `guide.md`，明确区分世界书、角色卡、美化任务。
- 更新所有提取指南，适配最新的 YAML 结构化输出。

## v2.1 — 2026-05-09
- `world-book-create.py` 新增 `excludeRecursion` 支持。
- 优化提示词结构，增加世界书禁词防止增殖。

## v2.0 — 2026-04-26
- 新增 `query.py` 查询工具。
- 新增场景路由器 `guide.md` 及提取/转化指南。
- 角色条目格式升级，由单一指南拆分为角色、世界观、配置三个专项指南。

## v1.0 — 2025
- 初始版本发布，支持基础世界书 JSON 生成。

---

## Contributors

感谢以下贡献者对项目的代码贡献：

| 贡献者 | GitHub | 贡献内容 |
|--------|--------|---------|
| **sanmingyue** | [@sanmingyue](https://github.com/sanmingyue) | 角色卡编写方法论与提示词设计 |
| **pisces1986** | [@pisces1986](https://github.com/pisces1986) | [#1](https://github.com/echo-xianyu/worldbook-skill/pull/1) `_Args` camelCase→snake_case 自动转换 / [#3](https://github.com/echo-xianyu/worldbook-skill/pull/3) 输入校验、MVU 风格冲突检测（部分合并） |
| **uiharuayako** | [@uiharuayako](https://github.com/uiharuayako) | [#4](https://github.com/echo-xianyu/worldbook-skill/pull/4) openai.yaml prompt 引用修复 |
