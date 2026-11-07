# 40 · MVU / 正则 / EJS / 状态栏：技术方法论参考

> 提炼自 tavern-card 上游四包，只用指定源文件。源文件**冲突**处标 `[冲突]` 并给取用建议，**未覆盖**处标 `[待核]`；代码/字段/正则一律照抄原文。

## 0. 总览：六件套与一次交互

```
变量结构脚本（Zod Schema）→ [initvar] 初始值（YAML）→ 变量列表（@D0 注入当前值）
→ [mvu_update] 更新规则（何时改）→ [mvu_update] 输出格式（JSON Patch 协议）
→ 酒馆正则（剥更新块 / 占位符换界面 / 可选闸门）→ 前端界面（无沙盒 iframe）
```
楼层变量结构：`{ stat_data: {…}, display_data, delta_data, initialized_lorebooks, … }`。**生命周期**（`mvu.md` §1）：① 新开聊天——MVU 扫启用世界书中标题含 `[initvar]` 的条目（**含禁用的**），YAML/JSON/TOML 解析后 merge 进 `stat_data`；开局若有 `<initvar>` 块则**完全覆盖**保底条目。② 每轮回复——解析 `<UpdateVariable>` 里的命令按序应用，**每次应用后过 schema 校验与纠错**。③ 更新完触发 `VARIABLE_UPDATE_ENDED` 等事件并写入楼层，回复末尾自动补 `<StatusPlaceHolderImpl/>` 供正则做界面。
两种更新模式（MVU 设置切换）：**随 AI 输出**（默认）与**额外模型解析**（回复后再发一次生成，只有 `[mvu_update]` 前缀条目发给更新轮；`[mvu_plot]` 反之——普通轮发、更新轮删）。

## 1. 变量声明：变量结构脚本（Zod schema）

### 1.1 骨架（头尾固定；存放于「酒馆助手脚本库 → 角色脚本」，命名 `变量结构`）
```js
import { registerMvuSchema } from 'https://testingcf.jsdelivr.net/gh/StageDog/tavern_resource/dist/util/mvu_zod.js';

export const Schema = z.object({
  世界: z.object({
    当前时间: z.string(),
    当前地点: z.string(),
  }),
  白娅: z.object({
    依存度: z.coerce.number().transform(v => _.clamp(v, 0, 100)),
  }),
});

$(() => {
  registerMvuSchema(Schema);
});
```
`z`（zod 4）与 `_`（lodash）由环境全局注入，**严禁 import**（只 import `registerMvuSchema`）；CDN 镜像 `testingcf`/`gcore`/`cdn`.jsdelivr.net 均可；顶层必须是 `z.object({...})`。注册成功日志：`【脚本|变量结构】: 变量结构注册成功`。

### 1.2 类型速查
| 场景 | 写法 |
|---|---|
| 数字 / 整数 | `z.coerce.number()` / `.int()`（**永不**裸 `z.number()`，AI 常写 `"5"`） |
| 真假 | `z.boolean()`（不用 `z.coerce.boolean()`） |
| 固定取值 | `z.enum(['进行中','已完成'])` |
| 键固定 / 键可缺省 | `z.record(z.enum([...]), 值)` / `z.partialRecord(...)` |
| 动态键对象（物品栏/称号） | `z.record(z.string().describe('物品名'), z.object({…}))` |
| 固定键 + 允许新类别 | `z.object({…}).catchall(z.record(z.string(), 子对象))` |
| 默认值 | `.prefault(值)`（**不用** `z.default()`）；可整体清除的子对象 `z.object({…}).prefault({})` |

禁用 `.strict()`/`.passthrough()`；`transform` 只接受**一个**参数 `(value)=>newValue`。

### 1.3 三条硬纪律 + 兜底 helper
幂等（`Schema.parse(Schema.parse(x)) === Schema.parse(x)`）；**纠错优先于拒绝**（越界用 `transform` 修正，不用 `.min/.max`）；**新增/老存档/脏值全部走 helper**——无兜底字段一旦缺失，`parse` 直接失败，**整次更新被拒**（玩家侧表现为「变量更新错误」）。
```js
// 文本：缺失、空串、"undefined"/"null" 字符串一律回退默认值
const normText = def =>
  z.coerce.string()
    .transform(s => { const t = String(s ?? '').trim(); return (t && t !== 'undefined' && t !== 'null') ? t : def; })
    .prefault(def);
// 数值：越界取整 + 字段缺失回退 + 非数字（NaN/类型错）回退
const clampNum = (def, min, max) =>
  z.coerce.number()
    .transform(v => (Number.isFinite(v) ? Math.min(max, Math.max(min, Math.round(v))) : def))
    .catch(def)      // 校验错误（NaN 等）兜底
    .prefault(def);  // 字段缺失兜底
```
`z.coerce.number()` 收到 `"abc"` 得 **NaN，而 zod 在进 transform 之前就拒它**——必须 `.catch(def)`。用 `.prefault({})` 的复合对象，**内部每个字段也要逐个 `.prefault()`**。

### 1.4 ★ `.catchall()`：新类别被静默剥离
把"设施类别"写成固定键 `z.object({种植园, 牧场, 林场, 矿场})`，AI 新增的 `渔场/盐田` 会在 zod 校验时**被悄悄丢掉**——变量管理器看不到、状态栏不显示、**且不报错**。
```js
生产设施: z.object({
  种植园: z.record(z.string(), z.object({ 面积: clampNum(0, 0, 999), 状态: normText('正常') })).prefault({}),
  // …其余固定类别
}).catchall(z.record(z.string(), z.object({}).catchall(z.any())))   // ← 新类别整体放行
```
值类型要给**宽松**的 `z.record(...)`/`z.any()`（给严 schema 则新类别内部字段又被剥）；前端渲染器本就用 `Object.keys()` 遍历，放行即自动出现。验证：本地 `Schema.parse({生产设施:{渔场:{近海渔场:{面积:2}}}})` 断言 `渔场` 还在。

### 1.5 `_` 与 `$` 前缀
| 前缀 | AI 可见 | AI 可更新 | 用途 |
|---|---|---|---|
| 无 | ✅ | ✅ | 普通变量 |
| `_变量` | ✅ | ❌ 更新被 MVU 忽略 | 固定设定、世界观常数（**不要**写更新规则） |
| `$变量` | ❌ 不进 `{{format_message_variable::stat_data}}` | ❌（脚本/提示词可改） | 隐藏旗标、开局类型、脚本开关 |


## 2. 初始值：`[initvar]` 两种写法

### 2.1 保底条目（对所有开局生效；**标题含 `[initvar]` 且必须禁用**）
`mvu-guide.md` 完整配置：名称 `[initvar]变量初始化勿开`、状态**禁用**、位置 @D depth=4、顺序 200、蓝灯。
```yaml
世界:
  当前时间: 2025-04-07 08:42
  当前地点: 私立星见学园·2年A班教室
白娅:
  依存度: 15
  称号:
    转学生:
      效果: 初来乍到，对环境陌生，容易引起他人注意但本人倾向于保持低调
      自我评价: 又是一个新的开始，但我注定会再次搞砸一切
主角:
  物品栏:
    旧手帕:
      描述: 角落绣着歪歪扭扭小兔子的手帕，有些年头了，但洗得很干净
      数量: 1
系统日志: []
```
缩进与 Zod Schema **一一对应**；节点按 YAML→JSON5→TOML 顺序解析，任一失败即报错。**★含特殊字符必须加引号**：以 `{` 开头的值（如 `{{user}}`）会被 YAML 解析成 **flow mapping**——`YAML.parse("姓名: {{user}}")` 得 `{"姓名":{"{ user }":null}}`，再经 `String()` 变 `[object Object]`；正确写法 `姓名: '{{user}}'`。同理需引号：含 `: `、以 `#`/`&`/`*`/`!` 开头、含 `[`/`]`/`,`。不用旧式 `变量: [值, 描述]`；变量名不用宏（用"主角"而非 `{{user}}`）。

### 2.2 按开局覆盖
在 `first_mes` / 各 `alternate_greetings` 末尾追加 `<UpdateVariable><initvar>`+完整 YAML+`</initvar></UpdateVariable>`。有 `<initvar>` 的开局**完全忽略**保底条目；外层 `UpdateVariable` 包裹是为了让 `[不发送]去除变量更新` 正则顺手清掉。增量方案：开局里直接写 JSON Patch（此时**必须先有** `[initvar]` 保底，Patch 在其上叠加）。

## 3. 更新规则放哪 + 模型如何被要求输出更新块

### 3.1 三个条目（全蓝灯）
| 条目名 | 前缀 | 作用 | 位置 |
|---|---|---|---|
| `变量列表` | **不加** `[mvu_update]` | 让 AI 看到最新变量值 | @D0（`mvu-guide.md`：depth=0 或 1，order=200） |
| `[mvu_update]变量更新规则` | **必须**加 | 教 AI 何时改、改多少 | @D0 / after_char |
| `[mvu_update]变量输出格式` | **必须**加 | 规定输出块结构 | @D0（Gemini）/ depth=4（Claude） |

变量列表必须 @D0/D1：它代表**最新**数值，放 D2 以深会被夹在历史消息之间，AI 会误判为旧数据。固定模板（可只引用子路径）：
```text
---
<status_current_variable>
{{format_message_variable::stat_data}}
</status_current_variable>
```
该宏在**发送给 AI 时**展开、**显示楼层时同样**展开；楼层逐楼更新、条目每轮重发，故 AI 总看到"截止上一楼"的值。条目名不是硬接口（实测有 `[系统]当前变量情况` 等），硬要求是"一个启用条目里含这个宏"；用 EJS 自定快照时记得过滤 `$` 前缀与 `$__META_EXTENSIBLE__$`。

### 3.2 更新规则（最小可抄）
```yaml
---
变量更新规则:
  世界:
    当前时间:
      format: YYYY-MM-DD HH:MM        # 可选：格式要求
  好感度:
    type: number
    range: 0~100
    check:
      - 根据角色对 <user> 行为的感知与态度更新，±(3~6)
      - 仅在角色能察觉到 <user> 行为时更新
      - 单次变化不超过 ±6，除非剧情有明确强烈转折
  # 固定键合并：主角.能力面板.${力量|敏捷|体质|智力|感知|魅力}
```
字段：`type`（自明变量可省）、`range`（数值才写）、`format`（无要求不写）、`check`（**从不省略**）。写作规范：同类固定键合并成 `X.${A|B|C}`；动态键对象的 `type` 写成带索引签名的 TS 块；`check` 每条一句话，用 `±(3~6)`、`仅当……` 措辞，别穷举旁支；`_` 变量不写。**规则本身即提示词**——不写=自由发挥，过细=烧 token 且僵化，以覆盖 90% 走向为度。

### 3.3 输出格式：`<UpdateVariable>` + JSON Patch（`templates/变量输出格式.yaml`）
`rule` 段原文摘要：①必须在下次回复**末尾**同时给出分析与实际更新命令；②命令形如 **JSON Patch (RFC 6902)**，但支持 `replace`（替换已有路径）、`delta`（数值增减）、`insert`（插新键；数组用 `-` 追加）、`remove`、`move`；③**不要更新 `_` 开头的只读字段**。`format` 段全文：
```yaml
  format: |-
    <UpdateVariable>
    <Analysis>$(IN ENGLISH, no more than 80 words)
    - ${calculate time passed: ...}
    - ${decide whether dramatic updates are allowed as it's in a special case or the time passed is more than usual: yes/no}
    - ${analyze every variable based on its corresponding `check`, according only to current reply instead of previous plots: ...}
    </Analysis>
    <JSONPatch>
    [
      { "op": "replace", "path": "${/path/to/variable}", "value": "${new_value}" },
      { "op": "delta", "path": "${/path/to/number/variable}", "value": "${positive_or_negative_delta}" },
      { "op": "insert", "path": "${/path/to/object/new_key}", "value": "${new_value}" },
      { "op": "insert", "path": "${/path/to/array/-}", "value": "${new_value}" },
      { "op": "remove", "path": "${/path/to/object/key}" },
      { "op": "move", "from": "${/path/to/variable}", "to": "${/path/to/another/path}" }
    ]
    </JSONPatch>
    </UpdateVariable>
```
`rule` 段 AI **只读不输出**，`format` 段按结构输出：`${描述}` 由 AI 替换、`$(要求)` 听从但不输出该标记、`...` 仿照补充。`<Analysis>` 英文 ≤80 词，是"先想再改"的手段：①估时间推进 ②判是否允许剧烈变动 ③**逐变量回顾 `check`，只看本轮回复而非历史剧情**——第三步等于让 AI 复习一遍规则，**这就是规则条目可以放得不太近的原因**。**路径从 `stat_data` 内部开始**（`/世界/当前时间`，**不带** `/stat_data/`）。

### 3.4 输出纪律补丁
轻量版（`templates/变量输出格式强调.yaml`，蓝灯 @D0）：`rule: The following must be inserted to the end of reply, and cannot be omitted` + `<UpdateVariable>...</UpdateVariable>` 骨架。重装版（`templates/强制结尾输出.yaml`）：
```yaml
---
强制结尾输出:
  importance: 最高优先级。此规则优先于其他所有规则。
  rule: The following block MUST be inserted at the very end of every reply, and CANNOT be omitted under any circumstance.
  checklist:
    - 回复的最后一段必须是 <UpdateVariable> 块
    - 回复的最后一个字符必须是 </UpdateVariable>
    - 即使本轮没有任何变量变化，也必须输出 <JSONPatch>[]</JSONPatch>
    - 禁止以 NPC 台词、场景描写、或状态栏作为回复的结尾
```

## 4. 正则：字段契约与标准条目

正则 = 变量卡的管道工：**去掉不该给 AI 看的文本、把占位符变成界面、把更新块折叠**。

### 4.1 两种方言的字段名
卡片方言（`RegexScriptData`，驼峰，本文件模板都用这套）：`id, scriptName, findRegex, replaceString, trimStrings, placement, disabled, markdownOnly, promptOnly, runOnEdit, substituteRegex, minDepth, maxDepth`。酒馆助手方言（`TavernRegex`，下划线）：`id, script_name, enabled, find_regex, replace_string, trim_strings, source, destination, run_on_edit, min_depth, max_depth`；`source` 含布尔 `user_input/ai_output/slash_command/world_info`，`destination` 含布尔 `display/prompt`。
| 通用叫法 | 卡片字段 | 填什么 |
|---|---|---|
| name | `scriptName` | `[前缀]用途`，如 `[不发送]去除变量更新`（`[不发送]`=只改提示词、`[折叠]`/`[美化]`=显示美化、`[闸门]`/`[校验]`=变量块校验放行、`[界面]`/`[状态栏]`=界面） |
| regex | `findRegex` | **slash 风格字符串** `"/pattern/flags"`；内部 `/` 写 `\/`，写进 JSON 再转义成 `\\/` |
| replacement | `replaceString` | `$1`/`$2` 捕获组、`$&` 全匹配；要字面 `$1` 写 `$$1`；隐藏类**必须空串** |
| placement | `placement` | 数字数组：`[1]`=用户输入、`[2]`=AI 输出，可并存；常用 `[2]` 或 `[1, 2]` |
| 方向 | `markdownOnly`/`promptOnly` | 见 4.2 |
| 深度 | `minDepth`/`maxDepth` | 见 4.3，默认 `null`/`null` |
| 其他 | `id`（UUID，**每条换新**）、`disabled`、`runOnEdit`（闸门/界面设 `true`）、`trimStrings: []`、`substituteRegex: 0` | |

### 4.2 `markdownOnly` / `promptOnly` 三态
`tavern-regex-contract.md` 依 ST 正则引擎（`public/scripts/extensions/regex/engine.js`，校核日 2026-10-13）给出的映射：
| `markdownOnly` | `promptOnly` | 生效目标 |
|---|---|---|
| false/缺省 | false/缺省 | `raw`（卡片正则预处理，两个 host 标记都没设） |
| true | false/缺省 | `display`（只改屏幕显示） |
| false/缺省 | true | `prompt`（只改发给 AI 的文本） |
| **true** | **true** | `display` + `prompt`（两 stage 各自启用，OR 条件） |

`[冲突]` `regex.md` §1 写"两者都 true = 均不生效"，与源码映射相反。**取用建议**：以契约文档为准；但别依赖 true/true——按用途各写一条更清晰、更好排查。已装 ST 版本的实际行为需实测 `[待核]`。

### 4.3 深度语义（最容易写反）
深度**从最新消息数起（0 = 最新一楼）**，`minDepth ≤ 深度 ≤ maxDepth` 生效，两侧可 `null` 不限；显示层同样按 0=最新 计（ST 源码 `usableMessages.length - indexOf - 1`）。`null/null` → **所有楼层**（隐藏类默认值）；`minDepth: N` → **跳过最新 N 楼**、只清更早 = "给 AI 保留最近 N 楼原文"（只发最新 6 楼更新 → `minDepth: 6`）；`maxDepth: N`（配 minDepth null）→ **只**对最新 N+1 楼生效，对"清旧楼层"是**反方向**（历史坑点），但它是显示层"只管最新楼层"的正当工具（`maxDepth: 1` 只让最新两楼渲染该界面）。**正则按数组顺序依次应用**：同一标记可被多条"接力消费"——闸门先把 `Impl` 改名 `READY`、界面再打 `READY`，就靠这个顺序。

### 4.4 标准条目（覆盖 90% 的卡）

**① `[不发送]去除变量更新`**（promptOnly，把更新块清出提示词）
```json
{
  "id": "3d9a5f1e-6b2c-4f8a-9d1e-7a4b2c8f0e51",
  "scriptName": "[不发送]去除变量更新",
  "findRegex": "/<(update(?:variable)?)>(?:(?!.*<\\/\\1>)(?:(?!<\\1>).)*$|(?:(?!<\\1>).)*<\\/\\1?>)/gsi",
  "replaceString": "",
  "placement": [1, 2], "markdownOnly": false, "promptOnly": true,
  "disabled": false, "runOnEdit": false, "trimStrings": [], "substituteRegex": 0, "minDepth": null, "maxDepth": null
}
```
`\1` 反向引用匹配开闭标签：既覆盖完整块，也覆盖**流式未闭合的尾巴**（第一个分支）；`gsi` 兼容 `<updatevariable>` 大小写漂移与跨行。**默认全楼层生效**（块已被 MVU 解析过，再发只浪费 token、诱导照抄）；想保留最近几楼给 AI 参考就改用 `minDepth`（**不是** `maxDepth`）。

**②③ `[折叠]变量更新中` / `[折叠]完整变量更新`**（markdownOnly）：完整版 `findRegex: /<(update(?:variable)?)>\\s*((?:(?!<\\1>).)*)\\s*<\\/\\1>/gsi`，`replaceString: "\n\n<details>\n<summary>变量更新情况</summary>\n$2\n</details>\n"`；未完成版把 `>` 后加 `(?!.*<\\/\\1>)\\s*`，summary 写 `变量更新中{{random::.::..::...}}`（宏显示随机点动画）。

**④ `[不发送]界面占位符`**（promptOnly，占位符不占 token）：`findRegex: "/<StatusPlaceHolder(?:Impl|READY)\\s*\\/>/g"`、`replaceString: ""`、`placement: [2]`、`markdownOnly: false`、`promptOnly: true`。`(?:Impl|READY)` + `\s*` 覆盖闸门改名后的 READY 和 `<StatusPlaceHolderImpl />` 带空格写法。

**⑤ `[界面]状态栏`**（markdownOnly，占位符 → 界面）：见 §7。

## 5. 「闸门」：让"AI 没更新变量"可见

三部件（两张独立来源的实测卡配置完全一致）。**① 放行**（markdownOnly，`runOnEdit: true`）——把占位符改名为 `READY`：
```json
{
  "id": "c2e5f8a1-3b4c-5d6e-7f80-9a1b2c3d4e5f",
  "scriptName": "[闸门]变量块校验-放行",
  "findRegex": "/(<\\/UpdateVariable(?:variable)?>[\\s\\S]*?)<StatusPlaceHolderImpl\\/>|()<StatusPlaceHolderImpl\\/>(?=[\\s\\S]*<UpdateVariable(?:variable)?>)/g",
  "replaceString": "$1<StatusPlaceHolderREADY/>",
  "placement": [2], "markdownOnly": true, "promptOnly": false,
  "disabled": false, "runOnEdit": true, "trimStrings": [], "substituteRegex": 0, "minDepth": null, "maxDepth": null
}
```
分支一：占位符**在闭合更新块之后**（常规顺序）→ 放行；分支二：占位符**在更新块之前**（有些卡协议先行占位符）→ 也放行。两分支兼容两种协议顺序；放行是"仅显示层"改名，**不写入消息原文**。
**② 界面正则改打 READY**：⑤ 的 findRegex 改为 `<StatusPlaceHolderREADY\\s*\\/>`（**去掉 Impl**——没更新块时不该渲染界面）。**数组顺序：闸门必须排在界面之前。**
**③ `[变量]变量未更新警告`**：匹配剩余未被放行的 `<StatusPlaceHolderImpl\s*\/>` → 替换为一张"本轮未检测到变量更新——剧情继续，但角色状态可能没有更新"的红边小卡片（markdownOnly，`runOnEdit: true`，`placement: [2]`）。

### 5.1 它防什么、不防什么（别误解）
- **防的**：模型**整体省略**更新块 → 界面不渲染，改为警告卡片，即"漏更新"变成可见故障。
- **不防的**：模型**伪造**更新块。任何含 `<UpdateVariable>…</UpdateVariable>` 的文本（哪怕内容胡写）都会被判为"已更新"并放行；源文件里**没有**签名/校验和机制，且 `强制结尾输出.yaml` 明确鼓励"没有变化就输出 `<JSONPatch>[]</JSONPatch>`"，空块是合法输出。
- **真正的防线在别处**：①schema 纠错（`transform` clamp + `.catch()` + `.prefault()`，§1.3；`.catchall()` 防静默剥离，§1.4）；②事件钩子审计；③`_` 前缀只读（AI 写进 Patch 路径也会被 MVU 拒绝）。要"更强防伪"得自己写脚本比对 `old/new` 与正文语义——源文件未提供现成方案 `[待核]`。

### 5.2 钩子与安全写回
```js
await waitGlobalInitialized('Mvu');
const variables = Mvu.getMvuData({ type: 'message', message_id: -1 });   // 楼层号支持负数
_.update(variables, 'stat_data.白娅.依存度', v => v + 5);
await Mvu.replaceMvuData(variables, { type: 'message', message_id: -1 });

eventOn(Mvu.events.VARIABLE_UPDATE_ENDED, (new_variables, old_variables) => {
  const old_v = _.get(old_variables, 'stat_data.白娅.依存度');
  const new_v = _.get(new_variables, 'stat_data.白娅.依存度');
  if (old_v < 30 && new_v >= 30) toastr.success('白娅的依存度突破了 30！');
});
```
★ **写回必须三步法**（`html-beautify-guide.md` §3.7）：MVU 在 MvuData 里维护 `initialized_lorebooks` 等引擎私有字段，直接构造 `{ stat_data: … }` 写入会覆盖它们 → 下次处理时**重新初始化、玩家数据归零**。
```js
// ✅ 读完整对象 → 只换 stat_data → 写回
var fullData = Mvu.getMvuData({ type: 'message', message_id: 0 }) || {};
fullData.stat_data = myStatData;
await Mvu.replaceMvuData(fullData, { type: 'message', message_id: 0 });
// ❌ 禁止：await Mvu.replaceMvuData({ stat_data: myStatData }, {…});
```
`createChatMessages([{ role:'user', message, data: fullData }])` 同理必须传完整 `data`。

## 6. EJS：渲染时机与可访问变量

EJS = ST-Prompt-Template（`codeberg.org/zonde306/ST-Prompt-Template`，镜像 `zonde306/ST-Prompt-Template`；文档 `README_CN.md` + `docs/reference_cn.md`），把世界书/角色卡文本变成**小脚本**：发送前先执行 JS，再决定发什么、发多少。依赖关系：**MVU 不需要 EJS，但 EJS 需要 MVU**。

### 6.1 渲染时机
- **默认**：世界书先激活、模板后处理 → 无法用 EJS 决定**绿灯条目要不要激活**。
- **`@@preprocessing`**（ST 1.13.4+）：写在条目**首行**，模板在世界书激活**之前**处理此条目，结果再参与绿灯/黏性/冷却判定 → 可用变量动态产出关键词。该行本身不发给 AI。
- 制作时用输入框上方「启用/禁用提示词模板和酒馆助手宏」按钮关闭处理以看原始代码；**玩家游玩时必须开启**。

### 6.2 可访问对象
| 对象 | 说明 |
|---|---|
| `getvar('stat_data.…')` | 读 MVU 变量；`{ defaults: 0 }` 给默认值 |
| `setvar('路径', 值)` | 写变量（注意与 MVU 行为差异） |
| `getwi('条目标题')` | 取其他世界书条目内容，**必须 `await`** |
| `print('文本')` | 代码块内输出 |
| `matchChatMessages(['关键词'])` | 最近 2 楼命中才发送；`{ start: -4 }` 扫最近 4 楼 |
| `variables.stat_data.…` | 装饰器式条目（`@if`/`@iframe`）里的直接访问 |
| `_`、`YAML`、`TavernHelper.…`、`console.info`/`toastr.info`/`debugger` | lodash、YAML、酒馆助手 API、调试三件套 |

标签：`<%_ 代码 _%>` 执行不输出（`_` 吃掉前后空白）；`<%= 表达式 %>` 输出并转义；`<%- 表达式 %>` 输出不转义（**`getwi` 专用**）；`<%# %>` 注释。

### 6.3 三条铁律 + 条件分段
```javascript
<%_
if (typeof gw === 'undefined') var gw = getvar('stat_data.角色名.好感度', { defaults: 0 });
if (typeof rel === 'undefined') var rel = getvar('stat_data.角色名.关系状态', { defaults: '陌生人' });
_%>
```
①必须 `typeof` 防重复声明（多条目可能同名）；②必须 `var`（`const`/`let` 会重复声明报错）；③路径必须带 `stat_data` 前缀、**无** `[0]` 索引。
```ejs
<%_ if (gw < 30) { _%>
【络络对你态度平淡，甚至有些冷漠】
<%_ } else if (gw < 60) { _%>
【络络对你抱有好感，但仍保持着一些距离】
<%_ } else { _%>
【络络现在非常信任你，愿意和你分享她的小秘密】
<%_ } _%>
```
条件边界必须**无重叠无遗漏**：`if (gw < 400) … else if (gw < 700) … else …`；`else if (gw <= 400)` 会与 `gw < 400` 在 400 处双命中；字符串相等**必须 `===`**。控制器 + 禁用阶段条目（内容大时省 token）：`<%_ if (gw < 150) { _%><%- await getwi('角色名_阶段01_初识') %><%_ } else { _%><%- await getwi('角色名_阶段02_熟悉') %><%_ } _%>`；`getwi` **必须 `await`**（等价 `<%_ print(await getwi('条目名')); _%>`，带数据 `await getwi('条目名', { key: value })`），被加载条目必须 `enabled=false`，否则所有阶段同时发送、动态控制失效。
`[冲突]` `prompt-template.md` 的"过滤版变量列表"示例在**单个** `<%_ _%>` 块内用了 `const raw = getvar('stat_data');`（克隆 `stat_data`、`delete` 掉内部字段、再 `JSON.stringify` 输出，比逐字段加 `$` 更灵活）。取用建议：跨条目复用的变量一律 `var + typeof`（ejs-guide 硬规则）；仅单块内一次性使用可 `const`，实际是否报错随扩展版本而异 `[待核]`。

## 7. 状态栏 HTML：最小可用骨架

### 7.1 渲染链路（决定写法）
①AI 回复末尾被 MVU 追加 `<StatusPlaceHolderImpl/>`（可能带空格）→ ②`[界面]状态栏`（markdownOnly）把占位符换成一段 **``` 围栏代码块** → ③酒馆助手扫描消息代码块：**文本含 `html>`、`<head>` 或 `<body` 任一**，就替换为无沙盒 iframe（类名 `TH-render`）→ ④玩家须开启酒馆助手**渲染开关**（扩展设置 → 酒馆助手 → 渲染，可设渲染深度/流式）。
推论：HTML 必须在 ``` 围栏里；**必须含 `<head>` 或 `<body>`**；流式未输出完**不会**渲染。
```html
<body>
<style>
  #mvu-statusbar { font-size: 13px; padding: 8px 10px; border: 1px solid rgba(128,128,128,.4); border-radius: 10px; }
  #mvu-statusbar .row { display: flex; justify-content: space-between; }
</style>
<div id="mvu-statusbar">
  <div class="row"><span>💖 好感度</span><span id="sb-depend">--</span></div>
</div>
<script type="module">
await waitGlobalInitialized('Mvu');
const sleep = ms => new Promise(r => setTimeout(r, ms));
for (let i = 0; i < 100; i++) {
  if (_.has(getVariables({ type: 'message' }), 'stat_data')) break;
  await sleep(100);
}
const render = () => {
  const d = _.get(Mvu.getMvuData({ type: 'message', message_id: getCurrentMessageId() }), 'stat_data', {});
  document.getElementById('sb-depend').textContent = _.get(d, '好感度', '--');
};
render();
setInterval(render, 1000);
</script>
</body>
```
配套正则（`regex-界面.json`；装闸门后把 findRegex 改 `<StatusPlaceHolderREADY\\s*\\/>` 并置于闸门之后）：
```json
{
  "id": "b1d4e7f0-2a3b-4c5d-6e7f-8a9b0c1d2e3f",
  "scriptName": "[界面]状态栏",
  "findRegex": "/<StatusPlaceHolder(?:Impl|READY)\\s*\\/>/g",
  "replaceString": "```\n<body>\n…上面的 HTML…\n```",
  "placement": [2], "markdownOnly": true, "promptOnly": false,
  "disabled": false, "runOnEdit": false, "trimStrings": [], "substituteRegex": 0, "minDepth": null, "maxDepth": null
}
```

### 7.2 读变量的三条路径与冲突
- `Mvu.getMvuData({type:'message', message_id: getCurrentMessageId()})` + `_.get(…, 'stat_data.路径')` —— 精确到"本界面所在楼层"，往回翻旧楼看到当时状态（`mvu.md` §5.1 / `frontend.md` §3）。
- 宏 `{{format_message_variable::stat_data.路径}}` 直接写进 HTML —— **正则替换时一次性展开，不受 iframe 沙箱影响**，`html-beautify-guide.md` §3.4 建议"状态栏优先用宏"。
- `getAllVariables()` + `_.get(vars, 'stat_data.路径', 默认值)` —— `mvu-guide.md` §6.2 写"**必须**用 getAllVariables()"，但它只给当前全量变量、不区分楼层。

`[冲突]` 三者并存且各有"必须/优先"表述。取用建议：**要楼层精确 → `getCurrentMessageId()` + `Mvu.getMvuData`；只做静态展示 → 宏最稳；`getAllVariables()` 仅在需跨作用域总览时用**（iframe 内其路径解析可能与主窗口不一致，是最不稳的一条 `[待核]`）。

### 7.3 样式规范（避免"界面炸掉"）
| 规范 | 原因 |
|---|---|
| `width:100%; max-width:100%` | iframe 随消息宽度变化（PC/手机） |
| **禁用 `vh`/`min-height`**（消息内嵌状态栏） | iframe 高度由内容撑开；`vh` 引发高度反馈循环（酒馆助手会自动换成 `var(--TH-viewport-height)` 抢救，别依赖） |
| 主体不用 `position:absolute`；不出横向滚动条 | 否则高度塌陷/重叠；移动端体验极差 |
| 颜色用 `rgba`/`color-mix` 自适应深浅主题 | ST 有明暗主题，硬编码纯色容易看不见 |
| `body { margin:0; padding:0 }` | 非零 padding 会让状态栏错位；边距加在容器上 |
| 触控元素 `min-height:44px` + `touch-action: manipulation` | 手指最小舒适尺寸；消除 300ms 点击延迟 |

`[冲突]` `html-beautify-guide.md`（面向**整页型** UI，如开场选择器）要求"禁止 `vh`，统一 `dvh`"，其 `body` 还写了 `min-height:100vh` + `100dvh` 覆盖；`frontend.md`（面向**消息内嵌**状态栏）要求"禁用 vh/min-height"。二者场景不同：内嵌状态栏按 frontend.md；独占整页按 html-beautify。混用需实测 `[待核]`。
**响应式用 `@container` 而非 `@media`**（iframe 宽度变化时 `@media` 不重算）：
```css
.status-container { container-type: inline-size; }              /* 祖先必须声明 */
.self-sex-wrap { display: flex; flex-wrap: wrap; gap: 12px 14px; }
.self-sex-left  { flex: 1 1 180px; min-width: 0; }              /* 缺 min-width:0 必炸 */
@container (max-width: 420px) {
  .self-sex-wrap { flex-direction: column; align-items: stretch; }
  .self-quick-gauge { width: auto; height: 14px; }              /* 竖向条 → 横向条 */
}
```
实测坑点：`flex-basis: auto` 是重灾区（子项必须 `min-width:0`）；`@container` 必须挂在声明 `container-type` 的**祖先**上；竖向仪表窄屏要**真的**改 `width/height` 并把刻度标记从 `bottom` 改 `left`，不是简单缩窄。
**固定配色**三件事：容器给实底 + 明确文字色（如 `background:#fdf1f7; color:#46253a`）；容器设 **`color-scheme: light`**（否则深色主题下原生 select/滚动条按深色渲染）；次级文字用固定中间色（如 `#bd8fae`），**不要用 opacity 调淡**。图标：`html-beautify` 硬性禁止 emoji/Unicode 符号图标（`content:"&#x2764;"`），要内联 SVG 且禁外部字体/图片；`frontend.md` 与实测卡则有用 `💖 好感度` 的做法 `[冲突]`——一致性敏感的面板用 SVG，原型可用 emoji。

## 8. 常见失效模式

### 8.1 变量不更新（AI 根本不输出更新块）
| 可能原因 | 定位 | 处置 |
|---|---|---|
| 三个提示词条目没启用 / 没在 @D0 | 查 `constant` + `position` | 蓝灯 @D0（§3.1） |
| `[mvu_update]` 前缀缺失 | 输出格式/更新规则条目名 | 补前缀，否则只在"额外模型解析"模式下发 |
| 变量列表误加 `[mvu_update]` / 放太深（D2+） | 条目名、depth | 去掉前缀；移 D0/D1，否则 AI 当成旧数据 |

### 8.2 更新被吞（块有了，变量没变 / 整次被拒）
| 可能原因 | 定位 | 处置 |
|---|---|---|
| 日志 `【脚本|MVU】发生变量更新错误` | 日志查看器看报错路径与值 | 补 `transform`/`.catch()`/`.prefault()` |
| schema 某字段无兜底 → `parse` 失败 | 同上；本地 `Schema.parse({})` 复现 | 全字段 helper 兜底（§1.3） |
| 新增字段老存档没有 / AI 漏写 | — | `.prefault()` + 变量自愈脚本（把默认值 merge 回旧楼层） |
| `.catchall()` 缺失 → 新类别静默剥离 | 管理器看不到新键、**不报错** | 补 `.catchall()`，本地 parse 断言（§1.4） |
| Path 带了 `/stat_data/` 前缀 | 看 `<JSONPatch>` 内容 | 改为 `/世界/当前时间` |
| 写到 `_` 前缀变量 | Patch 路径 | `_` 只读；换无前缀字段或脚本写入 |
| `[initvar]` 条目没禁用 / YAML 非法 | 条目状态；日志 `【脚本|变量结构】变量初始化失败` | 必须 `disabled`；修缩进/引号（§2） |

### 8.3 状态栏空白 / 不渲染
| 可能原因 | 定位 | 处置 |
|---|---|---|
| 没开酒馆助手「渲染」开关 | 扩展设置 → 酒馆助手 → 渲染 | 打开 |
| 代码块里没有 `<head>`/`<body>` | replaceString | 补标签，否则不接管 |
| 装闸门后突然不显示 | 闸门把 `Impl` 改名 `READY`，界面还在打 `Impl` | 界面改打 `READY`（或双写并**去掉**闸门） |
| 有 READY 正则但不渲染 | 没装闸门 / 闸门被禁用 / 界面排在闸门前 | 顺序：闸门 → 界面 |

### 8.4 正则误伤正文
| 现象 | 原因 | 处置 |
|---|---|---|
| 正文被吃掉一大段 | 贪婪 `.*` + `s` 跨全文；或"显示在消息开头"的 `/(.*)<StatusPlaceHolderImpl\/>/s` 没把 `$1` 放回 | 用惰性匹配；确认 replaceString 里 `$1` 在前 |
| 全局美化后状态栏消失 | 包装正则（`(.*)<StatusPlaceHolderImpl\/>`）没把占位符原样放回 | 必须 `…$1<StatusPlaceHolderImpl/></div>` |
| 整站样式被带歪 | 全局 CSS 注入对话 DOM 却用 `*` 重置 | 限定容器 `.global-chat-wrapper, .global-chat-wrapper * { box-sizing:border-box }` |
| 旧楼层更新块仍进提示词 | `去除变量更新` 深度写反（误用 `maxDepth`） | 用 `minDepth`；默认 `null/null` 全楼层（§4.3） |
| 正文出现裸露 `<UpdateVariable>` | 折叠正则没启用或没写 `i` | 启用 ②③，flags 带 `gsi` |

### 8.5 移动端崩版
| 现象 | 原因 | 处置 |
|---|---|---|
| 高度异常 / 无限撑高 | `vh`、`min-height` 在 iframe 引发高度反馈循环 | 内嵌状态栏不用视口单位（§7.3） |
| 并排布局被挤到换行、错位 | flex 子项 `flex-basis: auto` 且无 `min-width: 0` | `min-width:0` 或给具体 `flex-basis` |
| 窄屏断点不生效 | 用 `@media`（iframe 宽度变了不重算） | 改 `@container`，祖先声明 `container-type: inline-size` |
| 出现横向滚动条 / 点击没反应 | 固定宽度或超长不可断行；未设 `touch-action`、元素过小 | `max-width:100%`+`word-wrap:break-word`；`min-height:44px`+`touch-action:manipulation` |
| 刘海屏内容被切 | 未用安全区 | `env(safe-area-inset-*)`，如 `--safe-top: env(safe-area-inset-top, 0px)` |
| 深色主题下看不见 / 长 CJK 挤成一团 | 硬编码纯色或用 opacity 调淡；只给 `p` 设样式但实际是 `<br>` 换行 | `rgba`/`color-mix` 或固定配色+`color-scheme:light`；容器设 `white-space:pre-wrap` + `line-height` |


## Sources

- 根：`C:\Users\32858\.dsh\skills\tavern-card\vendor\`。`worldbook-skill\world-book-skill\references\`：`mvu-guide.md`、`ejs-guide.md`、`html-beautify-guide.md`
- `card-maker\sillytavern-card-maker\references\`：`mvu.md`、`regex.md`、`frontend.md`、`prompt-template.md`
- `card-maker\sillytavern-card-maker\templates\`：`initvar.yaml`、`变量更新规则.yaml`、`变量输出格式.yaml`、`变量输出格式强调.yaml`、`强制结尾输出.yaml`、`regex-基础.json`、`regex-界面.json`、`regex-闸门.json`
- `tavernweave\skills\`：`sillytavern-render-regex-pipeline\SKILL.md` + `references\tavern-regex-contract.md`（§4.2 真值表与字段名的源码依据）、`sillytavern-card-components\SKILL.md`（变量链路顺序 `initial data -> schema -> update rules -> output format -> context -> variable groups -> runtime readers -> rendered examples`）、`sillytavern-runtime-debug\SKILL.md`（分层诊断链 `artifact/import -> card fields and regex -> message text and rendering -> … -> layout, interaction, and persistence`）

