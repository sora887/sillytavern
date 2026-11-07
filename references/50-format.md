# 50 · 打包与拆包：v2 JSON / v3 PNG 格式参考

> **何时读**：要出可导入的文件（不只是文字方案）、要拆别人的卡、要手改字段、或卡导入后字段对不上时。
> 定位：这是「机械层」参考。人设怎么分条看 `10-worldbook.md`，变量/正则语义看 `40-mvu-regex-ejs.md`，验收清单看 `60-quality.md`。
> 本文所有字段名、默认值、校验规则，以 `scripts/` 的**实际代码行为**为准；文档与代码冲突时信代码。标 `[待核]` 的是本机未验证/无明文出处的部分。

---

## 一、格式家族（先认清你在处理哪种）

| 形态 | 标识 | 承载 | 备注 |
|---|---|---|---|
| v1 JSON | 无 `spec`，字段平铺 | `.json` | 老卡；`creatorcomment` 是备注字段 |
| v2 JSON | `"spec": "chara_card_v2", "spec_version": "2.0"` | `.json` | 字段进 `data`，顶层仍留一份兼容副本 |
| v3 JSON | `"spec": "chara_card_v3", "spec_version": "3.0"` | `.json` | `data` 布局与 v2 一致，增设可选项（如 `assets`/`nickname`）`[待核]` 语义 |
| v3 PNG | v2/v3 JSON 塞进 PNG `tEXt` | `.png` | 生态主流交付形态；`build_card.py` 新卡默认 v3 |

- SillyTavern 1.13+ **两种都收**。`build_card.py` 新建卡默认 `chara_card_v3` + `3.0`，但沿用 extract 保留的 `card.json` 里已有的 spec。
- 判断实例规格：读 `data` 是否存在；`extract_card.py` 会原样保留 `spec`/`spec_version` 到 `card.json`。

---

## 二、v2/v3 JSON 字段表（`data` 内 + 顶层兼容副本）

| 字段 | 类型 | 脚本行为 | 说明 |
|---|---|---|---|
| `name` | string | **必填**。build 缺省填「未命名」；含 `【卡名`/`填写`/`与世界书名称保持一致`/`占位` 直接 fail；check 报错 | 卡名，也决定输出文件名 |
| `description` | string | 透传 | 人设主体，模型每轮都读 |
| `personality` | string | 透传 | 可留空（很多卡把内容全写 description） |
| `scenario` | string | 透传 | 场景设定 |
| `first_mes` | string | **必填**。check 报错 if 空 | 开场白 |
| `mes_example` | string | 透传 | 示例对话，`<START>` 分节，`{{user}}`/`{{char}}` |
| `creator_notes` | string | build 回退读 `creatorcomment` | 作者备注/玩法说明，玩家导入时可见 |
| `system_prompt` | string | 透传 | 卡级 system 覆盖，通常留空 |
| `post_history_instructions` | string | 透传 | 卡级越狱/尾注，通常留空 |
| `alternate_greetings` | array[string] | `[] or []`，缺省空数组 | 备选开局 |
| `group_only_greetings` | array | **build 恒写 `[]`**（extract 不回收） | 群聊专用开局，roundtrip 会丢 |
| `tags` | array[string] | 透传 | 显示在 ST 角色列表，用于筛选 |
| `creator` | string | 透传 | 作者名 |
| `character_version` | string | 缺省 `"1.0"` | 卡版本号（字符串，不是数字） |
| `character_book` | object | 有 `worldbook.json` 就生成 | 内嵌世界书，见 §3 |
| `extensions` | object | 合并生成，见 §4 | 正则/脚本/第三方元数据都挂这里 |
| `spec` / `spec_version` | string | 顶层写，缺省 v3/`3.0` | 不进 `data` 时才用 `data` 里的 |

顶层兼容副本（build 一并写出，老客户端靠它）：`name`/`description`/`personality`/`scenario`/`first_mes`/`mes_example`/`creatorcomment`/`tags`/`talkativeness`/`fav`/`avatar: "none"`/`chat: ""`/`create_date`，加 `spec`/`spec_version`/`data`。

**已知不保真的字段**：`extract_card.py` 的 `card.json` 只收上表字段 + `spec` + `extensions_extra`；`data.assets`、`data.nickname`、`data.creation_date`、`group_only_greetings` 等不在其列，重建时会变空/变默认。全部原字段在 `原始卡.json` 里，改卡前先备份它。

---

## 三、`character_book`（内嵌世界书）与字段映射

条目字段（`entries` 是**数组**，与 ST 世界书的对象键不同）：

| 字段 | 类型 | 对应 ST 世界书 | 说明 |
|---|---|---|---|
| `id` | number | `uid` | 数字唯一；extract 遇 `null`/重复/非数字会顺延到下一个空位 |
| `keys` | array[string] | `key` | 主动触发词（蓝灯时留空） |
| `secondary_keys` | array[string] | `keysecondary` | 二次过滤 |
| `comment` | string | `comment` | 条目面板标题 |
| `content` | string | `content` | 正文 |
| `constant` | bool | `constant` | **true = 蓝灯常驻**；false = 按 keys 触发（绿灯） |
| `selective` | bool | `selective` | 次级关键词逻辑开关 |
| `insertion_order` | int | `order` | 同位置内排序，**数字越小越先注入** |
| `enabled` | bool | `!disable` | false = 条目禁用（`[initvar]` 必须 false） |
| `position` | string | 由数字位置推导 | 仅 `"before_char"` / `"after_char"`（0→before，其余→after） |
| `use_regex` | bool | — | build **恒写 true** |
| `extensions.position` | int | `position` | **精确位置，优先于上面的字符串** |
| `extensions.case_sensitive` | bool/null | `caseSensitive` | 大小写敏感 |
| `extensions.selectiveLogic` | int | `selectiveLogic` | 0 AND_ANY / 1 NOT_ALL / 2 NOT_ANY / 3 AND_ALL |
| `extensions.depth` `role` | int | `depth` `role` | `position=4`(@D) 时才生效；role 0 system 1 user 2 assistant |
| `extensions.probability` `useProbability` | int/bool | 同名 | 触发概率 0–100 |
| `extensions.scan_depth` | int/null | `scanDepth` | 扫描最近几条 |
| `extensions.match_whole_words` | bool/null | `matchWholeWords` | 整词匹配 |
| `extensions.exclude_recursion` `prevent_recursion` `delay_until_recursion` | bool | 同名驼峰 | 递归控制；卡内 `delay_until_recursion` 写布尔 |
| `extensions.group` `group_override` `group_weight` `use_group_scoring` | — | `group`/`groupOverride`/`groupWeight`/`useGroupScoring` | 互斥组与评分 |
| `extensions.sticky` `cooldown` `delay` | int/null | 同名 | 时效修饰 |
| `extensions.display_index` | int | — | 面板显示序，build 按 uid 升序从 0 递增 |
| `extensions.ignore_budget` | bool | `ignoreBudget` | 忽略 token 预算 |
| `extensions.triggers` `automation_id` `outlet_name` `vectorized` | — | `triggers`/`automationId`/`outletName`/`vectorized` | 高级字段 |

**`position` 数字位置表**（ST 内部常量，两个方向都按此表）：

| 值 | 位置 | 场景 |
|---|---|---|
| 0 | Character Before | 世界规则、分隔条、`[initvar]` |
| 1 | Character After | 人设补充 |
| 2 / 3 | AN Top / AN Bottom | 作者注释上下 |
| 4 | @D（atDepth） | 配合 `depth`+`role`；**变量卡主用，深度 0** |
| 5 / 6 | EM Top / EM Bottom | 示例消息上下 |
| 7 | Outlet | 出口 |

映射由 `worldbook_to_character_book()` / `character_book_to_worldbook()` 双向执行，除上表外还有：`delayUntilRecursion` 数值会被强制转布尔；`addMemo` 反向由 `comment.strip()` 是否为真得出；六个 `match_*` 字段 build 一律写 false。

---

## 四、`extensions` 里必须保留的东西

`build_card.py` 的合并顺序 = **先透传，后覆盖**：

```
extensions_extra（extract 自动生成的未知键备份）
  → depth_prompt（card.json 直接给了且未被覆盖）
  → talkativeness(缺省 "0.5") / fav(缺省 false)
  → world（有 worldbook.json 时 = 世界书名，缺省卡名）
  → regex_scripts（有 regex.json 时）
  → tavern_helper: {scripts: [...], variables: {}}
```

| 键 | 是什么 | 处理 |
|---|---|---|
| `tavern_helper.scripts` | 酒馆助手角色卡脚本（玩家导入即得） | build 扫描 `scripts/*.js` 生成 |
| `regex_scripts` | ST 正则数组（未授权时玩家首次使用会弹窗） | 原样搬运，id 不重写 |
| `depth_prompt` | ST 自身 @D 深度提示，绝大多数卡都有 | 透传 |
| `world` | 关联的**外部**世界书名（≠ 内嵌 `character_book`） | 有 worldbook.json 时自动写 |
| 第三方键 | `xiaobaix-tasks`、`cfMvuVarGroups`、`quick-response-force`、`QuickReply_Profile_V54`、`cm_manager`、`luker`、`mvu_worldbook_name` 等 | **一律透传，不认识的键不要删**——删了会改变玩家侧行为 |

**正则条目**（`regex_scripts[]`）：`id`(UUID) / `scriptName` / `disabled` / `runOnEdit` / `findRegex`（JS 字面量 `/pattern/flags`，JSON 里反斜杠双写）/ `replaceString`（必写，可为 `""`）/ `trimStrings` / `placement`（1=用户输入 2=AI 输出）/ `substituteRegex`(0–3) / `minDepth` / `maxDepth` / `markdownOnly` / `promptOnly`。

**脚本条目**（`tavern_helper.scripts[]`）：`name` / `id` / `enabled` / `type`（`"script"`，或 `"folder"` 带 `scripts`）/ `content`（ESM 代码，可 `import 'https://…'`）/ `info` / `button: {enabled, buttons}` / `data` / `export_with`。
`build_card.py` 的 id 用固定命名空间做 `uuid5(namespace, "script:"+文件名)` → **跨构建稳定；但改 .js 文件名 = 换 id = 换脚本身份**。

历史形态（`extract_card.py` 四种全兼容）：现代 `tavern_helper.scripts[]`；`Object.fromEntries` 旧型（`[["scripts",[…]],["variables",{…}]]`）；嵌套型 `TavernHelper_scripts=[{"type":"script","value":{…}}]`；名值对 `[[name, content], …]`。新卡只用现代型。

---

## 五、v3 PNG 的 chunk 结构

```
89 50 4E 47 0D 0A 1A 0A          ← 8 字节 PNG 签名
IHDR                              ← 必须在最前
tEXt  keyword=chara               ← base64(UTF-8 JSON)
tEXt  keyword=ccv3                ← 同一份内容的 v3 兼容副本
IDAT …                            ← 图像数据
IEND                              ← 必须在最后
```

单个 chunk 的字节布局：`长度(4B 大端) + 类型(4B) + 数据 + CRC32(4B 大端)`，CRC 覆盖「类型+数据」。

- `tEXt` 的数据段是 `keyword + 0x00 + text`，**text 只允许 Latin-1 字节** → 中文 JSON 必须整体 base64（无换行）。这是「为什么要 base64」的唯一原因，不是可选优化。
- `ccv3` 与 `chara` 内容相同（`build_card.py` 就是这么写的）。本地工具优先取 `chara`（`extract_card.py`/`check_card.py` 的解码顺序）；只有 `ccv3` 时仍能解出，但 `check_card.py` 会给「兼容性略降，建议打包时同时写入」的信息级提示。关键字**大小写敏感，固定小写**。
- 写入位置：`build_card.py` 固定插在 **IHDR 之后**。位置不敏感 `[待核]`（未在本机逐版本验证，但插在 IHDR 后是安全惯例）。
- 覆盖旧卡前必须先剥掉已有的 `chara`/`ccv3` 块，否则会残留旧数据/出现重复块。
- 体积：base64 使载荷膨胀约 **+33%**；PNG 长度字段是 4 字节（理论上限远大于实际）；**ST/各平台对卡文件的实际上限无明文** `[待核]` —— 工程上按「PNG 超过数 MB 就该外置资源」处理。

---

## 六、编译流程：project 目录 → 完备卡

工程目录（`card.json` 必备，其余可选）：

```
<工程>/
  card.json        # §2 字段 + extensions_extra + 可选 spec/spec_version
  worldbook.json   # ST 导入格式 {name, entries:{uid:{...}}}（可选）
  regex.json       # ST 正则数组（可选）
  scripts/*.js     # 文件名 = 脚本名（可选）
  meta.json        # {"scripts_disabled":[…], "script_buttons":{名:[…]}}（可选）
```

命令级步骤（脚本在 `C:\Users\32858\.dsh\skills\tavern-card\scripts\`）：

```bash
# 0) 依赖：Python 3 即可。这四支脚本只用标准库（json/base64/struct/zlib/re/difflib/uuid）；
#    Pillow 只有 apply_cover_text.py（做封面文字）需要。
cd C:\Users\32858\.dsh\skills\tavern-card

# 1) 先体检工程（有 [错误] 时退出码 1，修完再打包）
python scripts/check_card.py <工程目录>

# 2) 打包：JSON 必出，给 --image 才出 PNG
python scripts/build_card.py <工程目录> --image 底图.png
#    --outdir 改输出目录（默认 <工程>/输出/）　--name 覆盖卡名
#    产物：<卡名>.json（+ <卡名>.png）、世界书.json、正则.json

# 3) 验成品（工程和成品两条路径都走同一个校验器）
python scripts/check_card.py <工程目录>\输出\<卡名>.json
python scripts/check_card.py <工程目录>\输出\<卡名>.png

# 4) 世界书赘述体检（行级精确查重 + 句级模糊查重）
python scripts/scan_duplicates.py <工程目录> --threshold 0.55 --top 25
```

编译期硬行为（记住这几条，否则「打包成功但内容不对」）：

1. `character_book` 按 worldbook 条目键的**整数值升序**转数组，`id` 沿用 uid，`display_index` 从 0 递增。
2. 没有 `regex.json` 就不写 `regex_scripts`；没有 `scripts/` 也会写 `tavern_helper: {scripts: [], variables: {}}`。
3. `world` 取 `worldbook.json` 的 `name`，缺省回落卡名 —— 世界书名与卡名不一致时，玩家侧看到的是这个名字。
4. 换封面必须重跑 build（只替换底图文件不会改变已产出的 PNG）；build 只在原图上追加 `tEXt`，IDAT 应逐字节不变，可用 sha256 对比底图与新卡的 IDAT。
5. 打包后再手改 JSON 是禁止路径：改源 → 重打包（TavernWeave 同规矩：never inject a fix after packing）。

---

## 七、拆包流程：卡 → 可编辑工程（反推）

```bash
cd C:\Users\32858\.dsh\skills\tavern-card

# 1) 拆（PNG 或 JSON 都收；输出目录不能是源文件所在目录的子目录）
python scripts/extract_card.py <卡.png> <新工程目录>
python scripts/extract_card.py <卡.json> <新工程目录>

# 2) 看体检报告再动手（这一步能列出正则 id 重复、脚本相对 import、变量条目违规）
python scripts/check_card.py <新工程目录>

# 3) 改 card.json / worldbook.json / regex.json / scripts/*.js

# 4) 原样重打包（用拆出来的 底图.png 作底图）
python scripts/build_card.py <新工程目录> --image <新工程目录>\底图.png

# 5) 验收：再拆一次做 roundtrip 对拍（可选但推荐）
python scripts/extract_card.py <新工程目录>\输出\<卡名>.png <对拍目录>
```

拆出来的东西：

| 产物 | 内容 | 反推注意 |
|---|---|---|
| `card.json` | §2 字段 + `spec`/`spec_version` + `extensions_extra` | 只收有限字段，未知 `data` 字段靠 `原始卡.json` |
| `worldbook.json` | 由 `character_book` 还原的 ST 世界书 | `id` 重复/null 会被顺延，roundtrip 可能改号 |
| `regex.json` | `extensions.regex_scripts` 原数组 | 卡外（ST 全局）正则不会进卡 |
| `scripts/*.js` | 每个脚本一个文件，按名生成（非法字符剔除，重名加 `_2`） | 改文件名 = 改脚本名与 uuid5 id |
| `原始卡.json` | 解码后的完整原始卡 | **唯一全字段备份，先留档** |
| `底图.png` | 输入为 PNG 时复制一份 | 覆盖卡内元数据后图像数据不变 |
| `说明.md` | 骨架 | 交付说明用 |

- 卡内**没有** `character_book` 但 `extensions.world` 有值 → 说明它挂的是外部世界书，必须先在 ST 里导出成 `worldbook.json` 才能一起编辑打包。
- 拆包默认是「只读侦察」：TavernWeave 的规矩是 reverse extraction 默认关闭，只作打包后的沙箱 roundtrip 校验。

---

## 八、`check_card.py` 的校验规则（比文档权威）

分两套路径：目录 → 查工程；`.json`/`.png` → 解码后查成品。存在 `[错误]` 时退出码 1。

| 类别 | 规则 | 级别 |
|---|---|---|
| 结构 | `card.json`/卡数据 `name` 缺失或含占位文本；`first_mes` 为空 | 错误 |
| 结构 | `description` 为空（变量卡可接受） | 信息 |
| 世界书 | `entries` 必须是对象 `{name, entries:{}}`；`uid` 与键不一致；`comment` 为空 | 错误 / 警告 / 警告 |
| 正则 | `regex.json` 必须是数组；条目非对象；`id` 缺失；`id` 重复；`findRegex` 缺失或不可编译；无 `replaceString` | 错误/警告混合（id 重复与不可编译是错误） |
| 正则 | `findRegex` 含变长后顾或 `\p{…}` → 归 `js_only`（JS 合法，Python 无法完整校验） | 信息 |
| 正则 | `markdownOnly` 与 `promptOnly` 同为 true / 同为 false（后者=永久替换不可逆） | 信息 |
| 正则 | `replaceString` 像 HTML 却没用 ``` / ~~~ / `$(` 包裹；含 `localhost`/`127.0.0.1` | 警告 |
| 闸门 | 有「校验-放行/闸门」正则时界面正则仍只匹配 `Impl`；有 `READY` 匹配却无闸门 | 警告 |
| 变量 | `[initvar]` 条目未禁用；`变量列表` 非蓝灯或缺 `{{format_message_variable::stat_data}}`；`[mvu_update]变量输出格式` 缺 `<UpdateVariable>`/`JSONPatch`；`变量更新规则` 空 | 错误（旧宏 `get_message_variable` 只警告） |
| 变量 | 全卡没有任何条目输出变量当前值（宏或 EJS `getvar('stat_data')`+stringify），且脚本也没做注入 | 错误 |
| 脚本 | 内容疑似整个 JSON 导出被粘贴（`{` 开头且含 `"type"`/`"content"`）；相对路径 `import './…'` | 错误 |
| 脚本 | 无 `MagVarUpdate` 引入；无 `registerMvuSchema`/`mvu_zod`/名含「变量结构」；`localhost`；`import … .ts` | 警告 |

已知校验盲区（读代码得出，不要误当已覆盖）：worldbook 的 `uid` 去重那行比较的是 dict 的键（天然唯一），所以「uid 重复」几乎不可能被它触发；真实重复要用 `uid` 值比对。`png` 只有 `ccv3` 块时给信息提示而非错误。

`scan_duplicates.py` 的判读口径：先看 D（常驻条目字数排行），A 是 ≥14 字整行精确重复，B 是跨条目句级相似（默认阈值 0.55），C 是条目内自我重复（阈值 ≥0.6）。它只读不写；「单一权威源 + 短指针」是处理原则，咒语型短指针只压短不删。

---

## 九、另外两套工程流（对照用，不必混用）

| 体系 | 关键命令 | 与本文的关系 |
|---|---|---|
| moyu-cards（`tavern-cards`） | `node scripts/tavern-cards-forge.mjs init / patch / configure / query / pack {project}` | 状态文件 `tavern-cards-state.json` 驱动；`configure` 按「策略→位置→排序」推导 `constant`/`selective` 与 order（tens-group：从 10 起每项 +1，跨类型跳整十）；**铁律 D1+ 深度禁止使用**；有头像出 `.png`，无头像出 `.json`；`vectorized`/`constant_selective` 只来自 ST unpack，configure 不会生成 |
| TavernWeave（`sillytavern-card-pipeline`） | 不自带引擎，先发现项目的 adapter | 规矩是「先定闸门（live/iteration/checkpoint/RC/accepted）→ 复现 profile/manifest/plan/contract → 按影响面校验 → 装配到 staging → pack JSON → 嵌入 PNG 壳（保留无关 chunk）→ 校验 payload 解码回 JSON 语义相等」；世界书按 manifest 的稳定 ID 解析，不按显示名/时间戳选；**不许 pack 后打补丁**；反向拆包默认禁用，仅作 roundtrip |

---

## 十、常见打包事故

**1. 中文字符编码**
- `tEXt` 的 text 只能是 Latin-1 → 中文 JSON 必须 `base64(UTF-8 bytes)`。直接把中文塞进 `tEXt` 会在 `encode("latin-1")` 处炸掉，或写出 ST 解不开的乱码。
- 读文件一律 `encoding="utf-8-sig"`（脚本做法），否则带 BOM 的 `card.json` 会让 `json.load` 报 `Expecting value: line 1 column 1`。
- Windows 控制台/管道：脚本已 `sys.stdout.reconfigure(encoding="utf-8")`；重定向抓输出若仍报 `UnicodeEncodeError`，再考虑 `PYTHONIOENCODING=utf-8`（本机未复现，属常规兜底）。
- `json.dump` 务必 `ensure_ascii=False`（build 用 `separators=(",",":")` 减小体积），否则中文变 `\uXXXX`，虽然合法但难维护、且显著增大卡体。

**2. PNG chunk 写坏**
- 症状：ST 导入不报错但字段空、卡名变成文件名、或报 "Could not parse card"/"Unexpected end of PNG"。
- 手写 chunk 的三个坑：忘算 CRC32（必须覆盖「类型+数据」）、长度字段漏掉大端、把 `IEND` 之后的字节写进去。
- 重复块/旧数据：覆盖式重建没剥旧 `chara`/`ccv3` → ST 取第一个，看到的是旧内容。
- 二次加工毁卡：某些图床、图片压缩、截图工具会重编码 PNG 并丢弃 `tEXt`。**卡图只能原样复制或用 build 重写**。
- 自检：`python scripts/extract_card.py 卡.png 临时目录` 能完整拆出来，就说明块是好的。

**3. 卡体积过大**
- base64 膨胀 +33%：1 MB 的 JSON ≈ 1.33 MB 的 PNG 载荷；体积主因是整本世界书内嵌 + 超长开场白 + 内联脚本/HTML。
- 对策（按性价比）：脚本与界面 HTML 外置到 CDN 一行 `import`；世界书按需拆成「内嵌必需 + 可选外置」；封面 768×768；`scan_duplicates.py` 压赘述。
- 外置是双刃剑：仓库删档/改名/网络不可达 = 玩家侧功能消失；关键功能随卡内联或双写兜底。
- 平台硬上限无明文出处 `[待核]`。

**4. 正则丢失 / 不生效**
- 卡外正则（ST 全局）不会因为拆卡进卡；只搬 `extensions.regex_scripts`。
- 丢了 `id` 或跨卡复制导致 `id` 重复 → 导入后互相覆盖/不执行（check 报错误）。
- `findRegex` 写成 `"/a/g"` 的字符串转义错误；JSON 里 `\\d` 才是正则里的 `\d`，`\\/` 才是 `/`。
- 漏写 `replaceString`（哪怕空串）；`markdownOnly`/`promptOnly` 组合选错 → 显示被替换但提示词没替换，或反之。
- 界面类替换没被 ``` / ~~~ 包住 → 酒馆助手不渲染，玩家只看到一坨 HTML 源码。
- 玩家侧还要过一次授权：首次使用弹窗允许卡内正则；被拒可在 扩展→正则 里补。

**5. 世界书 id 重复**
- `character_book.entries[].id` 必须唯一；extract 遇 `null`/重复/非数字时顺延 → **roundtrip 会悄悄改号**，依赖 id 的外部逻辑（变量组、正则锚点）要一并核对。
- `worldbook.json` 里 `entries` 的**键**与条目 `uid` 字段必须一致（不一致 check 只警告，但转换时以键为准）。
- 转换顺序固定：build 按条目键的整数值升序生成数组，`id` 取 uid，不改号；因此要改号就在 `worldbook.json` 里改键与 uid 两处。

**6. 未知字段被吃掉（最隐蔽的一类）**
- `extensions` 里不认识的键必须透传（`extensions_extra` 机制）；删掉等于改玩家侧行为。
- `data` 层的非标准键（`assets`/`nickname` 等）不在 `card.json` 里，改造前先从 `原始卡.json` 比对差异。
- `group_only_greetings` 会被 build 写空 → 群聊开局丢失。

---

## 十一、不确定项（`[待核]` 汇总）

1. ST/各分发平台对卡文件（PNG/JSON）体积的硬上限，无明文出处。
2. v3 新增字段（`assets`、`nickname`）在 ST 各版本的运行时语义，`card-format.md` 只说「可选」。
3. `chara` 与 `ccv3` 内容不一致时 ST 的取舍策略：脚本实测两者同内容可被接受，未见 ST 源码依据。
4. 写入位置「不敏感」：`card-format.md` 称 ST 解析所有块，本机未逐版本验证。
5. `scan_duplicates.py` 默认阈值 0.55 / 0.6 来自脚本默认值，不是语料评测结论。

---

## Sources

- `C:\Users\32858\.dsh\skills\tavern-card\vendor\card-maker\sillytavern-card-maker\references\card-format.md`（JSON/PNG/世界书/正则字段与映射）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\card-maker\sillytavern-card-maker\references\ecosystem.md`（酒馆助手/MVU/EJS/小白X 与 CDN 分发、玩家侧要求）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\card-maker\sillytavern-card-maker\references\cover-art.md`（768×768 卡面、换封面必须重打包、IDAT 哈希对比）
- `C:\Users\32858\.dsh\skills\tavern-card\scripts\build_card.py`（与 vendor 同名文件 SHA256 一致；tEXt 写入、chunk 剥离、字段合并顺序、uuid5 命名空间、CLI）
- `C:\Users\32858\.dsh\skills\tavern-card\scripts\extract_card.py`（同上；PNG 解码、character_book→worldbook、四种脚本形态、产物清单）
- `C:\Users\32858\.dsh\skills\tavern-card\scripts\check_card.py`（同上；全部校验规则与级别、JS→Python 正则近似编译）
- `C:\Users\32858\.dsh\skills\tavern-card\scripts\scan_duplicates.py`（同上；A/B/C/D 四段查重口径）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\card-maker\sillytavern-card-maker\scripts\apply_cover_text.py`（唯一依赖 Pillow 的脚本）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\moyu-cards\tavern-cards\references\packaging.md`（forge pack 产物形态与打包前清单）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\moyu-cards\tavern-cards\references\configuration.md`（strategy/position/order 推导、字段语义、D1+ 禁令）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\moyu-cards\tavern-cards\references\project-setup.md`（init/patch/query、typeLists、state 结构）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\moyu-cards\tavern-cards\references\resume.md`（断点续接、条目完成判定）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\moyu-cards\tavern-cards\references\error-handling.md`（pack 警告：avatar 回退、后缀修正）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\tavernweave\skills\sillytavern-card-pipeline\SKILL.md`（闸门分类、先 pack JSON 再嵌 PNG、payload parity、禁止 pack 后补丁）
- `C:\Users\32858\.dsh\skills\tavern-card\vendor\tavernweave\skills\sillytavern-api-reference\SKILL.md`（运行时面分类、置信度纪律，用于本文 `[待核]` 判定）
