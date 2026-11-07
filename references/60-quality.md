# 60 · 质量闸门：硬伤清单 / 反 AI 味 / 审查流程

> 什么时候读：卡「写完了」但还没交付；用户说「像 AI 写的 / 太平均 / 没味道」；改完存量卡要回归；要评审别人的卡。
>
> 什么时候不读：还在选题、定路线 —— 回 `00-routes.md`。硬伤还没清就开始谈文笔，是在给废稿化妆。
>
> 引用纪律：本文每条规则都来自 `vendor/` 里的原文。标 `[错误]` 的项会让成品不可用，标 `[警告]` 的项会让成品变差。不确定的结论标 `[待核]`，不拿记忆补。

---

## 一、三道闸门的顺序

质量不是一个分数，是三层互不放水的检查：

| 层 | 判什么 | 手段 | 通过之后能说什么 |
|---|---|---|---|
| 结构闸门 | 字段、JSON、正则、脚本、变量条目 | `scripts/check_card.py`（0 依赖） | `CHECK-PASSED`：能打包 |
| 内容闸门 | 事实一致、泄底、因果、文风、AI 味 | 十维审查（§四）＋人工读 | 内容自洽，**不等于模型能稳定执行** |
| 体验闸门 | 触发、状态、长聊、导入 | 场景回归＋平台试跑 | 只有真的跑过才敢说长聊稳定 |

`vendor/foreverse-card-skills/skills/campus-card-skill/references/validation-guide.md:5-12` 把这件事写成四层（静态结构 / 内容审读 / 场景回归 / 平台实测），并明确「内容审读 = 设计是否自洽；不等于模型能稳定执行」。`vendor/chunshui-fengyue/skills/chunshui-card-studio/references/qa.md:5-12` 是同一意思的四层（文件有效 / 本地模拟 / 平台有效 / 模型体验）。

**跨层不许合并成一句「已通过」。** 静态通过不能声称导入通过，导入通过不能声称长聊通过。

---

## 二、硬伤清单

判定方法一栏优先给**机器可判的语句**（跑 `check_card.py` 会直接打印），其次才是人工核对。同一项在多个仓库出现时合并成一行，不重复列。

路径简称约定（均相对技能根 `C:\Users\32858\.dsh\skills\tavern-card\`）：

- `check_card.py` → `vendor/card-maker/sillytavern-card-maker/scripts/check_card.py`
- `content-craft.md` / `adult-events.md` → `vendor/card-maker/sillytavern-card-maker/references/…`
- `card-audit.py` / `validation-guide.md` / `writing-optimization-guide.md` → `vendor/foreverse-card-skills/skills/campus-card-skill/…`
- `review-system.md` / `checklists.md` / `governance.md` → `vendor/ln-lore-pipeline/ln-lore-pipeline/references/…`
- `quality.md` / `qa.md` / `worldbook-audit.md` → `vendor/chunshui-fengyue/skills/chunshui-card-studio/references/…`

### 2.1 卡文件与结构

| 检查项 | 判定方法 | 修复动作 |
|---|---|---|
| [错误] 缺 `card.json` 或 JSON 非法 | `check_card.py` 报「缺少 card.json」/「不是合法 JSON：…」 | 修 JSON（`json.load` 能过）；工程目录必须有 card.json |
| [错误] 缺 `name` / `first_mes` | 同上，报「缺少 name」「缺少 first_mes（开场白）」 | 补字段；`first_mes` 是唯一不可空的叙事字段 |
| [错误] `name` 是占位文本 | 报「还是占位文本」——命中 `【卡名`、`填写`、`与世界书名称保持一致`、`占位` 任一 | 换成真名，卡名 / 文件名 / 世界书名三处一致 |
| [错误] `spec` 不是 `chara_card_v2` 且七关键字段有空 | `review-system.md:5`：逐字段非空检查 | 补齐；v3 PNG 走 `build_card.py` 重打包 |
| [错误] 文件带 BOM / 非 UTF-8 | 读字节判断 EF BB BF；`json.load` 用 `encoding="utf-8-sig"` 能过但平台不一定 | 另存为 UTF-8 无 BOM（`checklists.md:30` 列为红线） |
| [错误] PNG 无 `chara`/`ccv3` 块或不是合法 PNG | 报「PNG 中没有 chara/ccv3 卡数据」「不是合法 PNG」 | 用 `build_card.py --image` 重打包；只有 ccv3 会降兼容（脚本给 [信息]） |
| [错误] `meta.json` 不是对象 | 报「meta.json 必须是对象」 | 改成对象或删掉 |
| [信息] PNG 只写了 `ccv3` 没写 `chara` | 报「兼容性略降，建议打包时同时写入」 | 打包时两个块都写；只写 ccv3 不是错误但会掉老客户端 |

### 2.2 世界书条目

| 检查项 | 判定方法 | 修复动作 |
|---|---|---|
| [错误] 条目不是对象 / entries 不是对象 | 报「worldbook.json 结构不对（应为 {"name":…,"entries":{…}}）」 | 按 ST 世界书结构重建 |
| [错误] uid 重复 | 报「worldbook 的 uid 有重复」 | 重建 uid 序；**uid 序建立后不再变**（`checklists.md:30`） |
| [警告] uid 与键不一致 | 报「uid=… 与键不一致」 | 推荐两者一致，便于 diff |
| [警告] `comment` 为空 | 报「没有 comment（标题），面板里难以辨认」 | 补中文短语条目名，名称即用途（`content-craft.md:52`） |
| [错误] 空正文条目 | `card-audit.py:120-121` 对 `content` 空给 warning | 删掉或补正文；空条目纯粹烧预算 |
| [警告] 条目正文完全重复 | `card-audit.py:122-125` 报「Duplicate of …」；近似重复人工判 | 合并；差异部分单独成条（`scan_duplicates.py` 可批量体检） |
| [错误] 占位语残留（同上 / 后续补充 / 其余类似 / 【待补】） | 搜正文；`quality.md:13` 明令禁止用「同上、后续补充、其余角色类似」交付 | 写出内容，或明确报告「未完成范围」，不许称完整成品 |
| [错误] 常驻字段复刻 disable 条目（P0 最高频） | `review-system.md:7` 的泄底启发式：取 disable 条目去掉注释后按句切 ≥14 字句，在 description/personality/scenario/first_mes/mes_example/system_prompt/PI 里做子串搜索 | 从活跃字段撤出，整段留在 disable 条目 |
| [错误] `personality`/`mes_example` 逐字引 disable 台词（第二高频且最易漏） | 同上启发式，单独扫这两字段（`review-system.md:34`） | 删引文；需要口癖就自写一句不带引号的 |
| [错误] 统计残留混入活跃字段（字数、条数、「第X条」） | 扫「N 字」「共 N 条」「（N）」这类模式（`review-system.md:39`） | 删；统计只留在作者笔记 |
| [错误] `key`/`keys` 不一致，或非常驻条目没有关键词 | `card-audit.py:175-179` 报「No keyword: verify intentional vector/template/other activation」 | 两字段同步；非常驻必须有 key（红线 `checklists.md:30`） |
| [错误] 未知宏残留（非 `{{char}}`/`{{user}}`/标准宏） | `review-system.md:6` 宏审计 | 删除或替换成标准宏 |
| [错误] 引文与语料不符 / 归属错 / 自创口癖带引号冒充原文 | 逐条直核原句（`review-system.md:7` 的 L 号直核；`§7.4-7`） | 改逐字，或去掉引号改为转述 |
| [错误] 正文被管道截断（典型 scenario 400/420 字处断成残句） | 末字不是句末标点、或句子缺谓语（`review-system.md:36`） | 补成完整句；截断若含禁用内容按泄底一并处理 |
| [错误] `probability` 不在 0~100 / `scanDepth` 非负整数 | `card-audit.py:134-139` 直接报 error | 改回合法值或删字段（继承默认） |
| [错误] taberna：悬空 `categoryId` / `insertionPositions` 非整数数组 | `card-audit.py:150-163` | 补分类或改引用；单数位置必须出现在复数数组里 |
| [错误] 常态上下文超预算（常驻+变量列表+规则 > 预设 1/3） | 数常驻条目正文字符占比（`content-craft.md:101`） | 砍复述、合并条目、把细节改绿灯 |

### 2.3 MVU 变量条目

| 检查项 | 判定方法 | 修复动作 |
|---|---|---|
| [错误] `[initvar]` 条目未禁用 | 报「必须处于禁用状态（MVU 仍会读取它，但启用会把初始值发给 AI）」 | 关掉 `disable`；MVU 照样读 |
| [错误] 「变量列表」不是蓝灯 | 报「必须是蓝灯（constant=true）且启用」 | 勾 constant |
| [错误] 「变量列表」缺 `{{format_message_variable::stat_data}}` | 报「内容缺少」；旧宏 `get_message_variable` 只给警告 | 换新宏；EJS 快照要读整个 `stat_data` 并输出 |
| [错误] 没有任何条目输出变量当前值 | 报「AI 将看不到变量状态」（脚本注入方案例外，会给 [信息]） | 加变量列表，或走 injectPrompts 方案并确认符合预期 |
| [错误] 「变量输出格式」缺 `<UpdateVariable>` + JSONPatch | 报「缺少 <UpdateVariable>/JSONPatch 模板」；旧 `_.set` 只给 [信息] | 换 JSONPatch 模板 |
| [错误] 「变量更新规则」正文为空 | 报「内容为空」 | 写规则；空规则等于让 AI 自由发挥 |
| [警告] 缺输出格式 / 更新规则条目 | 报「AI 可能不会输出更新块」「将自由发挥更新逻辑」 | 补条目；自定义命名可行但用不了额外模型解析模式 |
| [错误] 开场白的数值与 initvar 不一致（写「好感度 15」但 initvar 是 0） | 逐项对照 `first_mes` 里出现的数字与 `[initvar]`/`<initvar>` | 改文字或改初值（`content-craft.md:74`） |
| [错误] 该挂变量的判定没挂变量 | 数值闸门缺失（如「快感<100 禁止高潮」这类可判条件没写进 schema/规则，`adult-events.md:125`） | 把阈值挂到变量上：能被 schema 兜底、能被状态栏显示 |

### 2.4 正则、脚本、前端

| 检查项 | 判定方法 | 修复动作 |
|---|---|---|
| [错误] `findRegex` 缺失 / 无法编译 | 报「缺少 findRegex」「findRegex 无法编译：…」；JS 专属语法（变长后顾、`\p{…}`）只给 [信息]，不算错 | 修表达式；命名组用 `(?<name>)` |
| [错误] 正则 id 重复 | 报「id 与前面重复」；缺 id 只给 [警告] | 换 UUID；跨卡复制时务必换 id |
| [警告] 缺 `replaceString` 字段 | 报「没有 replaceString 字段（应显式写 ""）」 | 显式写空串，别留字段不存在 |
| [警告] HTML 替换内容没被代码块包裹 | 报「替换内容像 HTML，但没有用 ``` / ~~~ 代码块包裹」 | 包进代码块，否则酒馆助手不渲染 |
| [警告] 界面正则与闸门不配套 | 三种报法：闸门在但界面只匹配 `<StatusPlaceHolderImpl/>`（放行后不渲染）／界面同时匹配 Impl 与 READY（抢占位符）／有 READY 但无闸门（永不生成） | 闸门场景下界面只匹配 `<StatusPlaceHolderREADY/>` |
| [警告] `localhost` / `127.0.0.1` 残留 | 正则替换串与脚本文本各扫一次 | 改线上地址或内联（玩家环境访问不到） |
| [警告] 操作 MVU 变量但没等初始化 | 报「未见 waitGlobalInitialized('Mvu')」 | 加等待，否则变量未就绪 |
| [错误] 脚本内容被整体粘成 JSON 导出 | 报「疑似为 JSON 导出格式被整体粘贴」——以 `{` 开头且含 `"type"`/`"content"` | 只保留 `content` 字段里的代码 |
| [错误] 脚本用相对路径 import / import `.ts` | 报「无法解析相对路径」「只支持 .js/远程模块」 | 改 CDN 绝对地址或内联 |
| [警告] 缺 MVU 引入 / 缺变量结构脚本 | 报「没有找到 MVU 引入脚本」「没有找到变量结构脚本」 | 补 `MagVarUpdate` 引入与 `registerMvuSchema` |
| [警告] 卡里没有酒馆助手脚本 | 报「卡内没有酒馆助手脚本——如果这是变量卡，玩家将无法运行 MVU」 | 变量卡必须带脚本；纯内容卡可忽略 |
| [错误] Python 正则通过就宣称 RE2 通过 | `qa.md:28`：正则须用 RE2 或平台原引擎验证，`unsupported` 不能删掉凑「全绿」 | 换引擎重验；验不了就标未验证 |
| [错误] 状态栏超预算 | `qa.md:36`：仅一个普通状态区，各栏唯一；≤900 可见字 / ≤6000 原始 HTML 字符（不含独立记忆）；≤3 名 NPC、3 项未完事项、3 条建议 | 拆栏/裁重复；**不许删长期记忆来达标** |

---

## 三、反 AI 味

### 3.1 先分清三层，别把口味当 bug

`writing-optimization-guide.md:7-11` 的分层是本节的地基：

- **事实错误**：人设矛盾、认知越界、代替玩家决定、状态与正文冲突 → 必须修。
- **明确约束**：用户/项目 `AGENTS.md` 指定的禁词、视角、结构 → 在本轮范围内遵守。
- **风格候选**：套话、修辞密集、重复微表情 → **结合语境判断，不强求零命中**。修理工谈零件「弧度」、人物数「纽扣」、不确定时说「好像」，都不是 AI 味。

所以下面六条是**诊断线索**，不是正则黑名单。命中就回去读原句。

### 3.2 六类机器味特征与替代写法

| 特征 | 怎么认（判定线索） | 替代写法 |
|---|---|---|
| **形容词堆叠** | 一句话两个以上修饰语且删掉不影响信息；「温柔又强势、危险又迷人」式并置；外貌段全是形容词没有动作 | 一个具体动作胜过三个形容词。本技能 `SKILL.md:51` 审美基准：拒绝「形容词堆砌的『高级感』」。`campus-card-skill/SKILL.md:36`：用有情境的对话样例校准声音，**避免只有形容词和口头禅** |
| **万能过渡句** | 「与此同时」「不知过了多久」「就这样」「值得注意的是」「总而言之」；每段开头都有一句不推进情节的承接 | 直接切下一个动作或一个物件特写。`content-craft.md:88` 文风 taboo 明写：不使用「AI 助手」式总结句、不跳出角色点评 |
| **均匀高密度** | 每一段都是同样的信息浓度，没有呼吸；全篇都在「使劲写」 | 本技能 `SKILL.md:52`：复杂度局部化——有高密度区，也有安静区。让某段只做一件事（一个动作、一句对白、一个环境音） |
| **状态栏代替叙事** | 数值变了但剧情没痕迹（「好感 +5」而正文无事发生）；或反过来，事件全靠面板播报、正文两句话带过 | 数值必须能被叙事感知（`content-craft.md:98`）；事件场景按楼层推进，一楼一个节拍、楼尾切在未完成处（`adult-events.md:11-18`）。结算放事件结束一次性做（`adult-events.md:36`），不要在每楼播报 |
| **无因果细节** | 设定只是罗列（「喜欢猫、讨厌雨天、有秘密」），问不出「所以呢」；经历不解释现在的反应 | 写成可演出的链条：关键经历 → 形成的信念 → 当前欲望与顾虑 → 情境下的行为（`quality.md:17`）。判断标准是「模型知道何时、为何、怎样反应」（`quality.md:25`）。`content-craft.md:99`：极端值要有出口 |
| **情绪标签化** | 「她很生气」「他感到绝望」「气氛变得暧昧」直接给结论；或用肌肉学拆解代替动作（「嘴角上扬 15 度」） | 先写行为依据再让读者推断（`writing-optimization-guide.md:21`）；但不要把所有句子压成「她笑了」「他沉默」——保留动机、节奏与声音差异。`adult-events.md:126` 的白名单思路通用：写「应激」而非「失控」（呼吸变沉、指节泛白、喉间闷哼，但仍在掌控中） |

补充两条**结构性的机器味**（不是句子层面的）：

- **人人同款**：所有角色都有一模一样的微笑、秘密和身世（`quality.md:17` 明令禁止）。配角按戏份分配细节，但不能只精写主角（`quality.md:29`）。
- **用形式冒充内容**：把「加标题 / 加字数 / 加条目数」当质量（`quality.md:3-5`）；用固定句式或机械段落数量代替逻辑（`quality.md:51`）。

### 3.3 白描候选词表（可疑，不是禁词）

来自 `writing-optimization-guide.md:14`，`card-audit.py:12-13` 的 `STYLE_WORDS` 是它的机器版：

```
一丝、一缕、一抹、不易察觉、不易觉察、难以察觉、鲜明对比、形成对比、弧度、
弯起嘴角、翘起嘴角、喉结、纽扣、指节发白；心湖/涟漪/石子式心理比喻；
似乎、仿佛、宛如、极度、万分、无比；解释性破折号；重复的「不是……而是……」句式
```

纪律三条：

1. **命中后读原句**，能说出必要性就留着（`writing-optimization-guide.md:16`）。
2. **词表用于作者审校，不整份注入世界书**（`:27`）——正例给短说明加少量示例；负面约束只保留高风险误写，避免反例污染声音。
3. **命中数不是质量分**（`:31`，`card-audit.py:206` 也写 "Review in context"）。谁拿词频当评分，谁就在做伪验收。

---

## 四、审查流程

### 4.1 十维审查（来自 `review-system.md:18-23`）

必对照四方：**角色专属世界书（事实权威）＋共通世界书＋卡＋异名统合表**；按需旁证角色库/清洗标注版/年表。4~5 卡一批，任务书写成 txt 固化，判级规则随判例逐批传递。

| 维度 | 问的问题 | 不合格怎么办 |
|---|---|---|
| ① 事实一致性 | 主客方向对不对？亲疏变化有没有依据？ | P0：语料直证后改；改不动就登记「错在书侧」 |
| ② 剧透管控 | 默认时段的后期揭示有没有出现在常驻字段？PI（PHI）的隐瞒指令算不算遮羞布？ | P0：撤出常驻字段，放进 disable 手动条目。**PHI 不是泄底遮羞布**（`governance.md:15`） |
| ③ 台词指纹 | 每句引号台词归属对不对？有没有编造咏唱/口癖？ | P0：改逐字或去引号；编造的删 |
| ④ 引文直核 | L 号所指是否真的在那（含 ±3 行惯例偏移）？ | 逐条核；仅文字/归属实错＝漂移，须改 |
| ⑤ 表达层 | 错字、语病、占位符、截断尾？ | P1/P2：直接修，不改剧情含义 |
| ⑥ 机械线索复核 | 脚本报的 [错误]/[警告] 有没有被解释或修掉？ | 报错必改；警告必须给出保留理由 |
| ⑦ 统计残留 | 活跃字段里还有字数/条数/编号吗？ | P0：删 |
| ⑧ 数值面板 | HP/MP/状态栏数值与语料原文一致吗？与变量初值一致吗？ | P0：对齐；面板与正文冲突时以正文因果为准 |
| ⑨ 称呼方式 | 本角对他者的称谓体系一致吗？有没有混用同义称呼（「依存度/好感度」）？ | P0：全书统一（`content-craft.md:102`） |
| ⑩ 关系亲疏变化 | 随卷次/阶段演化的前后态对得上吗？ | P0：补中间态，不许跳级 |

**发现记录五要素（强制，`checklists.md:5-11`）**：

```
【卡内原文】（短引）
【语料出处】文件名＋章节（＋L 号）
【差异说明】…
【建议改为】…（保持原格式风格）
【置信度】高／中／低（证据不足一律降级，禁止编造补齐）
```

证据不足就降置信度，不许「大概是这样」补一句。

### 4.2 判级与修复纪律

- **P0**＝事实错误/泄底/串线，必修；**P1**＝建议修；**P2**＝备案/表达层（`governance.md:11`）。
- **报告先审后改**：批准前零修改；「肯定错误」（免审：定案异名、客观错字、泄底撤出、截断尾、语料直证的事实错误）与「人工决策」（措辞二选一、待裁项）分档（`review-system.md:44`）。
- **断言式＋幂等**：每条替换先断言旧串命中数，全过才落盘，任一失败零写入，落盘后重读复检（`governance.md:7`）。手工改大 JSON 是最常见的返工来源。
- **冻结字段**：批量修复前列清单（name/文件名/creator_notes/tags/first_mes 等），落盘后逐字段比对（`governance.md:10`）。
- **范围外残留**：发现 ● 项之外的问题，按纪律不动，写「未动，提请定夺」（`review-system.md:48`）。
- **三源对照**：卡↔书↔语料至少两源；**严禁用世界书记载反推原文**——那是循环论证（`governance.md:6`）。

### 4.3 顺序（照抄，别改）

```
1. python -X utf8 scripts/check_card.py <工程目录>        # 硬伤清零
2. python -X utf8 scripts/build_card.py <工程目录> --image 底图.png
3. python -X utf8 scripts/check_card.py 输出/<卡名>.json    # 打包后再查一遍
4. 十维审查（§4.1）→ 报告 → 批准 → 修 → 双层复检
5. 场景回归（validation-guide.md 的最小行为场景表）
6. 平台实测：导入、提示词查看器、状态栏、数轮对话
```

`templates/维护检查清单.md:21-26` 就是这个顺序的改卡版：先备份、写幂等补丁脚本、按固定顺序跑校验、版本号 +0.1、新机制关键词加进一致性审计表。

第 5 步最小场景（`validation-guide.md:31-42` 节选，都验「不变量」而不是「看起来像」）：不填引导页直接开始、玩家拒绝邀请、玩家离场后只说「她」、NPC 被问未在场密谈、重复交付、跳一天/压缩上下文、多角色同场、阈值前一档/边界/后一档、玩家声明新事实。

---

## 五、实测结论：LLM 当裁判不可靠

> 本节是一条**验收方法学**结论，不是文风建议。它决定你最后那一步能不能用。

**结论**：LLM 作为裁判区分「人类卡 / AI 卡」的判断正确率，远低于它对自身判断的自洽率——它很少说「我不确定」，却经常判错。因此「让 AI 打分」只能做初筛信号，**不得作为唯一验收手段**。

**本仓库内可核实的相邻证据**：

- `vendor/card-maker/README.md:94`：两轮子代理盲测，带技能 **100%** 通过 vs 无技能基线 **47.8%**（3 用例 × 28 断言）。盲测是可用的验收设计，但它测的是**执行正确率**，不是文笔好坏。
- `governance.md:79`：外部模型交叉审查时「对方 PASS 判定须逐张复核——实战中 3 张 PASS 全部判错」。**AI 裁判的 PASS 不可信**，FAIL 也需复核。
- `writing-optimization-guide.md:31`：不要用命中数代替写作质量评分。
- `qa.md:32`：不给空泛总分；`worldbook-audit.md:40`：近似匹配只作审阅提示，不给文学质量评分；`qa.md:16`：不能把格式成功当成唯一验收。

**可判定替代品**（按可靠性排序）：硬伤脚本 → 断言清单 → 场景回归表 → 平台实测 → 用户拍板。要引入 AI 评分时，必须同时满足：双盲（评者不知道哪张是 AI 卡）、多条独立判据而非一个总分、人类复核每条 PASS、判例落盘可追溯。

[待核] 上述「人类卡/AI 卡盲测」的具体正确率与自洽率数值，在 `vendor/foreverse-card-skills/` 内未检索到对应记录（该仓库只有 `writing-optimization-guide.md` 与 `validation-guide.md` 的原则性表述）。本条结论按外部实测记录收录，**数值不作为引用依据**；引用时只引结论，别编百分比。

---

## 六、不要做的事

- 不要用「AI 觉得不错」当验收结论（§五）。
- 不要拿词表命中数当质量分，也不要因为一次命中就删掉必要的「好像」（§3.3）。
- 不要在硬伤没清零时讨论文笔——顺序错了。
- 不要为了过预算删长期记忆（`qa.md:36`），不要为了过字限隐藏/裁切超长文本（`qa.md:42`）。
- 不要把「加标题/加字数/加条目数」当交付（`quality.md:3`）。
- 不要声称跑过没跑的脚本、读过没读的原文。状态标签只有 `SPEC` / `CARD-PENDING` / `CARD-BUILT` / `CHECK-PASSED` / `USER-APPROVED`。
- 不要把「格式校验通过」写成「内容精彩」，也不要把「内容审阅过」写成「长局稳定」（`quality.md:55`）。

---

## Sources

本地原文（均在 `C:\Users\32858\.dsh\skills\tavern-card\vendor\` 下，一字未改）：

- `card-maker/sillytavern-card-maker/scripts/check_card.py` —— §2.1~2.4 全部机器判定项的唯一权威来源（479 行已逐行核对）
- `card-maker/sillytavern-card-maker/references/content-craft.md` —— 字段分工、文风条目 taboo、§6 质量标准自查七条
- `card-maker/sillytavern-card-maker/references/adult-events.md` —— 演出时长、计分护栏、现实感限制器、白名单/黑名单写法
- `card-maker/sillytavern-card-maker/templates/维护检查清单.md` —— §4.3 固定校验顺序与改卡收尾
- `card-maker/README.md:94` —— 子代理盲测 100% vs 47.8%
- `foreverse-card-skills/skills/campus-card-skill/SKILL.md` —— 角色由行为定义、五条创作约束、交付标准
- `foreverse-card-skills/skills/campus-card-skill/references/validation-guide.md` —— 四层验证、最小行为场景表
- `foreverse-card-skills/skills/campus-card-skill/references/writing-optimization-guide.md` —— 三层区分、白描词表、命中数≠质量分
- `foreverse-card-skills/skills/campus-card-skill/references/experience-sources.md:9` —— 「把排版形式当 AI 味的唯一标准」被列为不可迁移项
- `foreverse-card-skills/skills/campus-card-skill/scripts/card-audit.py` —— 结构审计项、`STYLE_WORDS`、`--style bai-miao` 只给候选
- `ln-lore-pipeline/ln-lore-pipeline/references/review-system.md` —— 机械审计六项、十维四对照、五要素、修复工程学
- `ln-lore-pipeline/ln-lore-pipeline/references/checklists.md` —— 质量红线速查、发现记录模板、任务书要素
- `ln-lore-pipeline/ln-lore-pipeline/references/governance.md` —— 十二军规、P0/P1/P2、外部审查交叉对比（3 张 PASS 全判错）
- `chunshui-fengyue/skills/chunshui-card-studio/references/quality.md` —— 经历→信念→欲望→行为的链条、缺项修正纪律
- `chunshui-fengyue/skills/chunshui-card-studio/references/qa.md` —— 四层结论、状态栏预算、正文篇幅、不给空泛总分
- `chunshui-fengyue/skills/chunshui-card-studio/references/worldbook-audit.md` —— 自然场景集、报告怎么用、不给文学评分

合并关系：§二 以 `check_card.py` 为主干，其余仓库的清单只做补充与去重；`[错误]`/`[警告]`/`[信息]` 三档沿用 `check_card.py` 的退出码语义（有 `[错误]` 退出码 1）。
