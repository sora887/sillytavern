# MVU ZOD 变量系统集成指南

> **我的角色：** 我是 MVU 变量系统集成专家，负责引导你完成从零搭建完整 MVU ZOD 变量框架的全过程。
>
> **前置说明：** MVU 是独立的变量管理框架，不依赖 EJS 即可运行。但如果你希望在世界书中做条件判断、动态发送提示词，EJS 必须依赖 MVU（需要有变量才能读取和判断）。换言之。**MVU 不需要 EJS，但 EJS 需要 MVU**。

---

## 目录

1. [系统概览](#一系统概览)
2. [阶段一：设计变量结构脚本](#二阶段一设计变量结构脚本)
3. [阶段二：编写世界书条目](#三阶段二编写世界书条目)
4. [阶段三：配置酒馆正则](#四阶段三配置酒馆正则)
5. [阶段四：不同开局设置不同初始值](#五阶段四不同开局设置不同初始值)
6. [阶段五：状态栏界面搭建](#六阶段五状态栏界面搭建)
7. [特殊变量前缀](#七特殊变量前缀)
8. [两种命令风格对比](#八两种命令风格对比)
9. [自查清单](#九自查清单)
10. [常见错误示例](#十常见错误示例)

---

## 一、系统概览

MVU ZOD 是 SillyTavern 酒馆中管理动态变量的完整框架。一张完整的 MVU 角色卡由以下组件构成：

```
角色卡 MVU 系统
├── 变量结构脚本          → Zod Schema（角色脚本），定义变量类型与约束
├── [initvar] 初始变量     → YAML，开局的变量初始值（世界书禁用条目）
├── 变量列表               → 实时展示当前变量值给 AI（世界书蓝灯条目 D0/D1）
├── [mvu_update] 更新规则  → 定义每个变量何时应被修改（世界书蓝灯条目）
├── [mvu_update] 输出格式  → 规定 AI 以 JSON Patch 格式输出更新指令（世界书蓝灯条目）
├── 酒馆正则               → 隐藏 UpdateVariable 块、处理 StatusPlaceHolderImpl
├── 酒馆助手脚本（可选）    → 监听 MVU 事件，后台控制变量、激活绿灯
└── 前端界面（可选）        → 通过占位符替换为 HTML 状态栏
```

### 运转流程

1. **变量结构脚本** 向 MVU 蓝图注册变量的骨架（类型、范围、默认值、转换逻辑）
2. **[initvar]** 在新会话开始时据此填充变量的初值
3. **变量列表** 随每一轮对话将当前值注入 AI 上下文
4. **变量更新规则** 告知 AI 各变量变动的触发条件
5. **变量输出格式** 指导 AI 在回复末尾输出标准化的 JSON Patch 指令
6. **MVU 蓝图引擎** 解析 AI 的更新指令，执行实际修改
7. **变量结构脚本** 对修改后的值进行校验与自动修复（如 clamp 范围限制）
8. **正则** 把 `<UpdateVariable>` 块从发送给 AI 的文本中剥离，并在用户界面做美化

---

## 二、阶段一：设计变量结构脚本

### 2.1 先想好要追踪什么

在写任何代码之前，先盘点这张角色卡需要记录哪些动态信息：

| 卡片类型 | 典型变量需求 |
|---------|------------|
| 恋爱/互动卡 | 好感度、心情、着装、称号、信赖层级 |
| 冒险/探索卡 | 背包物品、技能、任务列表、地点标记 |
| 系统/经营卡 | 商城商品、事件触发器、角色状态旗帜 |

> 变量名中避免使用 `{{user}}` 等宏。用 `主角` 这类固定名称替代。

### 2.2 脚本骨架

变量结构脚本存放在 **酒馆助手脚本库 → 角色脚本** 中。头尾为固定模板，不可改动：

```js
import { registerMvuSchema } from 'https://testingcf.jsdelivr.net/gh/StageDog/tavern_resource/dist/util/mvu_zod.js';

export const Schema = z.object({
  // 你的变量树定义放在这里
});

$(() => {
  registerMvuSchema(Schema);
});
```

`z`（Zod 4）和 `_`（Lodash）已由环境全局注入，**严禁手动 import 它们**。唯一需要 import 的是 `registerMvuSchema`。

### 2.3 Zod 4 核心语法速查

| 写法 | 说明 |
|-----|------|
| `z.string()` | 字符串类型 |
| `z.coerce.number()` | 数值类型（自动把字符串转数字，推荐优先使用） |
| `z.boolean()` | 布尔类型（勿用 `z.coerce.boolean()`） |
| `z.literal('固定值')` | 仅允许某个字面量 |
| `z.enum(['A','B','C'])` | 枚举，值只能从列表中选 |
| `z.object({...})` | 固定字段的对象（作为文件夹组织层级） |
| `z.record(键Schema, 值Schema)` | 动态键名对象（如物品栏、称号表、记忆库） |
| `z.partialRecord(键, 值)` | 类似 record 但键为可选，不必全填 |
| `.describe('说明')` | 为字段附加描述，AI 可读取 |
| `.prefault(默认值)` | 字段被遗漏时的回退值（MVU 专用，勿用 `.default()`） |
| `.transform(v => ...)` | 值写入后执行转换/校验，仅接受一个参数 |
| `.transform(v => _.clamp(v, 0, 100))` | 将数值限制在闭区间内 |
| `.transform(data => _.pickBy(data, fn))` | 按条件过滤对象中的属性 |

### 2.4 编写要点

1. **数值范围用 transform 约束，不用 min/max：** `z.coerce.number().transform(v => _.clamp(v, 0, 100))` 让越界值被修复而非直接报错丢弃。
2. **用 prefault 而非 default：** MVU 环境推荐 `.prefault()`。
3. **对象优于数组：** `z.record()` 比 `z.array()` 更容易定位和更新单个元素。
4. **保持幂等性：** 任何合法数据经过 `Schema.parse()` 两次后结果必须不变。
5. **不要加入 `.strict()` 或 `.passthrough()`：** MVU Zod 4 不支持这两个方法。
6. **transform 只管一个参数：** `(value) => ...` 正确，`(value, ctx) => ...` 不被允许。
7. **复合对象用了 `.prefault({})` 后，其内部所有字段也必须逐一 `.prefault()`。**

### 2.5 完整示例

```js
import { registerMvuSchema } from 'https://testingcf.jsdelivr.net/gh/StageDog/tavern_resource/dist/util/mvu_zod.js';

export const Schema = z.object({
  世界: z.object({
    当前时间: z.string(),
    当前地点: z.string(),
    近期事务: z.record(z.string().describe('事务名'), z.string().describe('事务简述')),
  }),

  亚丝娜: z
    .object({
      好感度: z.coerce.number().transform(v => _.clamp(v, 0, 100)),
      着装: z.record(
        z.enum(['上装', '下装', '内衣', '袜子', '鞋子', '饰品']),
        z.string().describe('服装描述'),
      ),
      称号: z.record(
        z.string().describe('称号名'),
        z.object({
          效果: z.string(),
          自我评价: z.string().prefault('待评价'),
        }),
      ).transform(data => {
        // 好感度越高，保留的称号上限越多
        const maxSlots = Math.ceil(_.get(data, '__好感度__', 0) / 10);
        return _(data).entries().takeRight(maxSlots).fromPairs().value();
      }),
    })
    .transform(data => {
      // 给 transform 传一个内置的好感度引用（依赖 Schema 执行顺序需注意，
      // 实际项目中建议把称号数量控制逻辑放到酒馆助手脚本中监听 VARIABLE_UPDATE_ENDED）
      return data;
    }),

  主角: z.object({
    背包: z.record(
      z.string().describe('物品名'),
      z.object({
        描述: z.string(),
        数量: z.coerce.number().prefault(1),
      }),
    ).transform(data => _.pickBy(data, ({ 数量 }) => 数量 > 0)),
  }),
});

$(() => {
  registerMvuSchema(Schema);
});
```

此示例演示了：数值区间限制、枚举着装槽位、动态称号库、背包自动清理数量归零的物品。

### 2.6 存放与验证

- **存放位置：** 酒馆助手脚本库 → 角色脚本，命名为 `变量结构`
- **验证方式：** 新开对话后，在 `酒馆输入框左边魔棒 → 日志查看器` 中寻找 `【脚本|变量结构】: 变量结构注册成功`

若日志中出现错误提示，复制 `【脚本|变量结构】` 开头的全部日志条目排查问题。

---

## 三、阶段二：编写世界书条目

### 3.1 [initvar] 初始变量条目

**内容（YAML 格式，与变量结构一一对应）：**

```yaml
世界:
  当前时间: 2024-04-08 10:45
  当前地点: 私立风祭学院 高中部 2年A班教室
  近期事务:
    转学生安置: 亚丝娜刚刚转入，需要领取教材、熟悉校园环境
亚丝娜:
  好感度: 35
  着装:
    上装: 整洁的深蓝色校服外套
    下装: 深蓝色百褶裙
    内衣: 素白色内衣套装
    袜子: 黑色过膝袜
    鞋子: 黑色皮质学生鞋
    饰品: 无
  称号:
    行尸:
      效果: 日常行动带有明显的倦怠感
      自我评价: 活着本身就是惩罚
主角:
  背包:
    创可贴:
      描述: 钱包夹层里的卡通创可贴，粘性大概已失效
      数量: 1
```

**世界书配置：**

| 配置项 | 值 |
|-------|----|
| 条目名 | `[initvar]变量初始化勿开` |
| 状态 | **禁用**（必须勾选 disabled） |
| 位置 | D 齿轮 @D，depth=4 |
| 顺序 | 200 |
| 常驻 | 蓝灯（constant=true） |

> MVU 引擎只会读取禁用状态下的 `[initvar]` 条目。如果启用了，它会被当作普通提示词发给 AI，不会触发初始化。

### 3.2 变量列表条目

**内容（固定模板，直接使用）：**

```yaml
---
<status_current_variable>
{{format_message_variable::stat_data}}
</status_current_variable>
```

`{{format_message_variable::stat_data}}` 是酒馆助手的宏，运行时会展开为所有变量的 YAML 格式值，AI 便能看到实时状态。

**进阶写法。按需展示子集：**

```yaml
---
<status_current_variable>
世界:
  {{format_message_variable::stat_data.世界}}
亚丝娜:
  好感度: {{format_message_variable::stat_data.亚丝娜.好感度}}
  着装:
    {{format_message_variable::stat_data.亚丝娜.着装}}
主角:
  {{format_message_variable::stat_data.主角}}
</status_current_variable>
```

**世界书配置：**

| 配置项 | 值 |
|-------|----|
| 条目名 | `变量列表`（**不要**加 `[mvu_update]` 前缀） |
| 状态 | 启用 |
| 位置 | D 齿轮 @D，depth=0 或 1 |
| 顺序 | 200 |
| 常驻 | 蓝灯 |

> **为什么必须放在 D0 或 D1？** 变量列表代表当前最新数值，必须注入到离 AI 最近的消息上下文中。如果放在 D2 或更深，它会被卡在历史消息之间，AI 可能误判为之前的旧数据。

### 3.3 [mvu_update] 变量更新规则

**内容模板：**

```yaml
---
变量更新规则:
  世界:
    当前时间:
      format: YYYY年MM月DD日 星期X HH:MM
    近期事务:
      type: |-
        {
          [事务名: string]: string; // 事务描述
        }
      check:
        - 记录需要完成的任务、约定、重要事件
        - 完成后从列表移除，新增事务时及时添加
        - 保留 5~8 项活跃事务
  亚丝娜:
    好感度:
      type: number
      range: 0~100
      check:
        - 根据亚丝娜对主角行为的感知和反应调整 ±(3~6)
        - 正面互动增加 5~8，负面互动减少 5~10
        - 仅当亚丝娜当前察觉到主角行为时才更新
    着装.${上装|下装|内衣|袜子|鞋子|饰品}:
      check:
        - 换装、衣物损坏、特殊场合时更新
        - 描述需包含颜色、材质、款式细节
    称号:
      type: |-
        {
          [称号名: string]: {
            效果: string;
            自我评价?: string;  // 默认 '待评价'
          }
        }
      check:
        - 基于重要行为、心理变化或互动获得
        - 反映当前好感状态的阶段性特征
        - 上限关联好感度：Math.ceil(好感度/10) 个称号
  主角:
    背包:
      type: |-
        {
          [物品名: string]: {
            描述: string;
            数量?: number;  // 默认 1
          }
        }
      check:
        - 获取、消耗、丢弃物品时更新
        - 数量归零则条目不再显示
```

**各字段解释：**

| 字段 | 含义 | 何时省略 |
|-----|------|---------|
| `type` | 变量的数据类型定义，如 `number`、TypeScript 类型串 | 自明变量可省略（如 `当前地点`） |
| `range` | 数值的允许区间 | 非数值变量不写 |
| `format` | 特殊格式约束 | 无格式要求时不写 |
| `check` | 更新触发条件。最核心的字段，AI 据此判断是否该更新 | 从不省略 |

**编写技巧：**
- 自明变量不写冗余规则（如 `当前地点` 名字本身已说明如何更新）
- 同类变量合并（如 `着装.${上装|下装|内衣|...}` 一条规则覆盖所有部位）
- 以 `_` 开头的只读变量不用写更新规则
- 动态键对象（如 `称号`）的键名在 `type` 中用索引签名 `[键名: string]` 说明
- 更新规则可以放在角色定义之前或之后，不必挤在 D0。AI 输出格式中的思维链会自动"召回"它

**世界书配置：**

| 配置项 | 值 |
|-------|----|
| 条目名 | `[mvu_update]变量更新规则`（**必须**含 `[mvu_update]` 前缀） |
| 状态 | 启用 |
| 位置 | D 齿轮 @D，depth=0（或 after_char） |
| 顺序 | 200 |
| 常驻 | 蓝灯 |

### 3.4 [mvu_update] 变量输出格式

**内容（固定模板，直接使用）：**

```yaml
---
变量输出格式:
  rule:
    - you must output the update analysis and the actual update commands at once in the end of the next reply
    - the update commands works like the **JSON Patch (RFC 6902)** standard, must be a valid JSON array containing operation objects, but supports the following operations instead:
      - replace: replace the value of existing paths
      - delta: update the value of existing number paths by a delta value
      - insert: insert new items into an object or array (using `-` as array index intends appending to the end)
      - remove
      - move
    - don't update field names starts with `_` as they are readonly, such as `_变量`
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
      { "op": "remove", "path": "${/path/to/array/0}" },
      { "op": "move", "from": "${/path/to/variable}", "to": "${/path/to/another/path}" },
      ...
    ]
    </JSONPatch>
    </UpdateVariable>
```

**格式解读：**

此模板属于"额外输出格式"写法。`rule` 段 AI 只读取不输出；`format` 段 AI 按结构输出。其中：
- `${描述}` → AI 根据描述替换为对应内容
- `$(要求)` → AI 听从要求但不输出该标记本身
- `...` → AI 仿照前例补充输出
- 其余内容（如 `<UpdateVariable>`、`<Analysis>`）原样输出

**Analysis 思维链的作用：**

思维链是变量更新的关键。它要求 AI 在输出操作命令之前先做三步分析：
1. 估算时间推进了多少
2. 判断是否允许剧烈变动（如好感度从 100 直接跌到 0）
3. 逐一回顾每个变量的 `check` 规则，基于**当前回复**（而非历史剧情）判断是否需要更新

第三步相当于让 AI 重新"复习"一遍更新规则。这就是为什么更新规则条目可以放在不太近的位置。

**JSON Patch 操作速查：**

| 操作 | 效果 | 路径示例 |
|-----|------|---------|
| `replace` | 替换某个路径的完整值 | `"/亚丝娜/好感度"` |
| `delta` | 对数值做增减（正增负减） | `"/亚丝娜/好感度"` |
| `insert` | 向对象插入新键，或向数组追加（`-`） | `"/主角/背包/新物品"` |
| `remove` | 删除某条路径 | `"/主角/背包/薄荷糖"` |
| `move` | 移动路径 | `from: "/A"`, `to: "/B"` |

**路径规则：** 以 `/` 为分隔符，从变量根开始，**不需要** `stat_data` 前缀。即 `/亚丝娜/好感度` 而非 `/stat_data/亚丝娜/好感度`。

**AI 输出示例：**

```
（前段剧情文本...）

<UpdateVariable>
<Analysis>
- Time advanced by 10 minutes (from 10:47 to 10:57).
- Special Case? No, routine plot progression.
- 亚丝娜.好感度: Displayed strong reaction, warranting increase.
- 主角.背包: Mints were placed on her desk. Should be removed.
</Analysis>
<JSONPatch>
[
  { "op": "replace", "path": "/世界/当前时间", "value": "2024-04-08 10:57" },
  { "op": "replace", "path": "/亚丝娜/好感度", "value": 40 },
  { "op": "remove", "path": "/主角/背包/薄荷糖" }
]
</JSONPatch>
</UpdateVariable>
```

**世界书配置：**

| 配置项 | 值 |
|-------|----|
| 条目名 | `[mvu_update]变量输出格式`（**必须**含 `[mvu_update]` 前缀） |
| 状态 | 启用 |
| 位置 | D 齿轮 @D，depth=0（Gemini）/ depth=4（Claude） |
| 顺序 | 200 |
| 常驻 | 蓝灯 |

### 3.5 可选：变量输出格式强调

如果测试时 AI 频繁遗忘输出 `<UpdateVariable>` 块，新增此条目强化约束：

```yaml
---
变量输出格式强调:
  rule: The following must be inserted to the end of reply, and cannot be omitted
  format: |-
    <UpdateVariable>
    ...
    </UpdateVariable>
```

**配置同上，条目名为 `[mvu_update]变量输出格式强调`。**

---

## 四、阶段三：配置酒馆正则

AI 的回复中包含 `<UpdateVariable>` 块，MVU 引擎处理完后，不应再将其发给 AI（浪费 token，且可能诱导 AI 偷懒照抄或重复更新）。同时，MVU 会在每层楼末尾自动附加 `<StatusPlaceHolderImpl/>`，也需要正则处理。

### 4.1 必须的三个正则

在 `酒馆右上角积木按钮 → 正则` 中创建局部正则。MVP 至少需要以下两个：

**正则 A：隐藏变量更新（不发送给 AI）**

| 配置项 | 值 |
|-------|----|
| 脚本名称 | `[不发送]去除变量更新` |
| findRegex | `/<UpdateVariable>[\s\S]*?<\/UpdateVariable>/gs` |
| replaceString | （留空） |
| 作用范围 | AI 输出 |
| 短暂 | 仅格式提示词 ✅ |
| minDepth | 4（可选：保留最近 2~3 楼给 AI 参考，避免重复更新） |

**正则 B：隐藏状态栏占位符（不发送给 AI）**

| 配置项 | 值 |
|-------|----|
| 脚本名称 | `[不发送]界面占位符` |
| findRegex | `<StatusPlaceHolderImpl/>` |
| replaceString | （留空） |
| 作用范围 | AI 输出 |
| 短暂 | 仅格式提示词 ✅ |
| runOnEdit | true |

**正则 C：状态栏美化（用户可见）**

| 配置项 | 值 |
|-------|----|
| 脚本名称 | `[界面]状态栏` |
| findRegex | `<StatusPlaceHolderImpl/>` |
| replaceString | （你的 HTML 界面代码—详见阶段五） |
| 作用范围 | AI 输出 |
| 短暂 | 仅格式显示 ✅ |

**效果：** 正则 B 让 AI 看不到占位符（不消耗 token），正则 C 让玩家看到美化后的状态栏。两条正则一隐一显，互不冲突。

在状态栏相关的两个正则中，两个正则的 findRegex 都是 `<StatusPlaceHolderImpl/>`。一个 promptOnly 为空，另一个 markdownOnly 为替换为界面代码。

### 4.2 可选美化正则

你也可以用折叠面板美化用户端显示，让 `<UpdateVariable>` 块变成可收起的 `<details>` 元素：

```
findRegex: /<UpdateVariable>[\s\S]*?<\/UpdateVariable>/gs
replaceString: <details><summary>变量更新完成</summary>$1</details>
markdownOnly: true
```

这将替换"去除变量更新"那一条的角色。你可以选择只隐藏不美化，也可以隐藏旧楼层、美化最新楼层的组合策略。

---

## 五、阶段四：不同开局设置不同初始值

一张角色卡通常有多个开场情景，每个开场的变量初始值应当不同。

### 方案一：全量重写（`<initvar>` 块）

在开局文本中嵌入 `<initvar>` 包裹的完整 YAML 变量值：

```text
开局 2 的剧情故事……

<UpdateVariable>
<initvar>
世界:
  当前时间: 2025年4月7日 星期一 08:42
  当前地点: 私立星见学园·2年A班教室
亚丝娜:
  好感度: 15
  着装:
    上装: 整洁的私立星见学园女生制服
    下装: 深蓝色百褶裙
    ...
主角:
  背包:
    旧手帕:
      描述: 角落绣着歪歪扭扭小兔子的手帕
      数量: 1
</initvar>
</UpdateVariable>
```

也可以用 YAML 代码块包裹（` ```yaml ... ``` `），效果相同。

### 方案二：增量修补（JSON Patch）

如果不同开局间仅差一两个变量，可用 JSON Patch 在保底初始值上做增量修改：

```text
开局 2 剧情……

<UpdateVariable>
<JSONPatch>
[
  { "op": "replace", "path": "/亚丝娜/好感度", "value": 50 },
  { "op": "insert", "path": "/主角/背包/钥匙", "value": { "描述": "生锈的铁钥匙", "数量": 1 } }
]
</JSONPatch>
</UpdateVariable>
```

### 优先级规则

```
开局文本中包含 <initvar> 块？
├── 是 → 使用 <initvar> 中的完整值（直接覆盖，忽视世界书中的 [initvar] 保底条目）
└── 否 → 使用世界书中禁用的 [initvar] 保底条目
```

你甚至可以不在世界书里设置 `[initvar]` 条目，改为每个开场单独写一个 `<initvar>` 块。两种方式选其一即可。

> 如果在开场中用了 JSON Patch 增量方案：底层会先用 `[initvar]` 保底条目初始化，再叠加 Patch 修改。因此必须确保 `[initvar]` 存在。

---

## 六、阶段五：状态栏界面搭建

### 6.1 纯文本版

最简单的方式。直接在正则 C 的 replaceString 中写一行宏：

```
💖 好感度: {{format_message_variable::stat_data.亚丝娜.好感度}}
```

用 HTML 稍作美化：

```html
<style>
.stat-bar {
  font-size: 14px; color: #ff69b4;
  border: 1px solid #ff69b4; border-radius: 8px;
  padding: 6px 12px; display: inline-block;
}
</style>
<div class="stat-bar">
💖 好感度: {{format_message_variable::stat_data.亚丝娜.好感度}}
</div>
```

### 6.2 前端交互版

对于需要进度条、实时刷新、甚至可点击操作的状态栏，使用 JS 驱动：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  body { margin: 0; padding: 0; }
  .card {
    width: 320px; max-width: 100%;
    background: linear-gradient(145deg, #1a1a2e, #16213e);
    border-radius: 16px; padding: 16px; color: #e0e0e0;
  }
  .row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }
  .bar { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; margin: 0 10px; }
  .fill { height: 100%; background: linear-gradient(90deg, #ff6b9d, #c44dff); border-radius: 3px; }
</style>
<script type="module">
  function render() {
    const vars = getAllVariables();
    const aff = _.get(vars, 'stat_data.亚丝娜.好感度', 0);
    const mood = _.get(vars, 'stat_data.亚丝娜.心情', '--');
    $('#aff-val').text(aff);
    $('#aff-bar').css('width', aff + '%');
    $('#mood-val').text(mood);
  }

  async function init() {
    await waitGlobalInitialized('Mvu');
    render();
    eventOn(Mvu.events.VARIABLE_UPDATE_ENDED, () => render());
  }

  $(errorCatched(init));
</script>
</head>
<body>
<div class="card">
  <div class="row">
    <span>好感度</span>
    <div class="bar"><div id="aff-bar" class="fill" style="width:0%"></div></div>
    <span id="aff-val">--</span>/100
  </div>
  <div class="row">
    <span>心情</span><span id="mood-val">--</span>
  </div>
</div>
</body>
</html>
```

**前端界面核心规则：**

| 要点 | 说明 |
|-----|------|
| `body { margin: 0; padding: 0; }` | 必须置零。需要边距给容器元素加 margin |
| 变量路径须以 `stat_data.` 开头 | `_.get(all_variables, 'stat_data.亚丝娜.好感度')` |
| 必须用 `getAllVariables()` | 而非其他方式 |
| 必须用 `_.get(vars, '路径', '默认值')` | 防御性读取，避免路径不存在时报错 |
| 必须用 `await waitGlobalInitialized('Mvu')` | 等待 MVU 初始化完成 |
| 必须用 `$(errorCatched(init))` | 包装初始化函数，捕获异常 |
| 必须监听 `VARIABLE_UPDATE_ENDED` | 变量变更时自动刷新 |

### 6.3 在消息开头显示状态栏

如果希望状态栏出现在消息文本之前而非末尾，将正则 C 的 findRegex 改为：

```
findRegex: /(.*)<StatusPlaceHolderImpl\/>/s
replaceString: 你的界面HTML\n$1
```

这样状态栏会被渲染到消息正文上方。

---

## 七、特殊变量前缀

MVU 提供两个特殊前缀来控制变量对 AI 的可见性和可写性：

| 前缀 | AI 可见 | AI 可更新 | 典型用途 |
|-----|---------|----------|---------|
| 无前缀 | ✅ 可看 | ✅ 可改 | 普通变量 |
| `_` 前缀 | ✅ 可看 | ❌ 只读 | 固定设定、角色名、世界观常数 |
| `$` 前缀 | ❌ 看不到 | ❌ AI 不可改（脚本/提示词可改） | 隐藏旗标、开局类型标记、脚本专用 |

**示例：**

```yaml
世界:
  _类型: 魔法          # AI 能读到但不能修改
  $开局: 青梅竹马线     # AI 完全看不到，仅供 EJS/脚本判断分支

亚丝娜:
  _生日: 09-30         # 只读的固定信息
  好感度: 35            # AI 可读可写
```

`$` 前缀的变量在 `{{format_message_variable::stat_data}}` 中自动被遮蔽；`_` 前缀的变量即使出现在 JSON Patch 路径中也会被 MVU 引擎拒绝执行更新。

---

## 八、两种命令风格对比

MVU 演变过程中形成了两套不兼容的命令体系。选定一套后**全部配置必须统一**。

| 维度 | MVU ZOD（推荐） | MVU Beta（旧版） |
|-----|----------------|-----------------|
| 初始化格式 | YAML | JSON（`{"变量": [值, "描述"]}`） |
| 更新命令 | JSON Patch（RFC 6902） | `_.set('路径[0]', 旧, 新)` / `_.add('路径[0]', delta)` |
| 读取方式 | `{{format_message_variable::stat_data.路径}}` | `{{get_message_variable::stat_data}}` + `getvar("stat_data.路径[0]")` |
| 路径尾部 | 无 `[0]` 后缀 | 必须加 `[0]` 后缀 |
| EJS 中使用 | `getvar('stat_data.亚丝娜.好感度')` | `getvar('stat_data.亚丝娜.好感度[0]')` |
| 变量的 AI 更新路径 | `/亚丝娜/好感度` | 需用 `_.set` 格式 |

> **选择建议：** 新项目一律使用 ZOD 风格。Beta 风格仅用于维护已有旧卡。

---

## 九、自查清单

完成 MVU 集成后，按以下顺序逐项检查。

### 变量结构脚本

- [ ] 头 `import { registerMvuSchema } from 'https://testingcf.jsdelivr.net/gh/StageDog/tavern_resource/dist/util/mvu_zod.js';` 完整正确
- [ ] 尾 `$(() => { registerMvuSchema(Schema); });` 完整正确
- [ ] 仅 import 了 `registerMvuSchema`，未 import `z` 和 `_`
- [ ] 无 `.strict()`、`.passthrough()`、`.optional()`
- [ ] 数值范围用 `.transform(v => _.clamp(v, min, max))` 而非 `.min()/.max()`
- [ ] 默认值用 `.prefault()` 而非 `.default()`
- [ ] `.transform()` 仅接受一个参数
- [ ] 优先使用 `z.record()` 而非 `z.array()`
- [ ] 复合对象使用 `.prefault({})` 后，内部全部字段也有 `.prefault()`
- [ ] JavaScript 语法正确（括号、引号闭合）
- [ ] 无繁体字

### [initvar] 初始变量

- [ ] 条目名为 `[initvar]变量初始化勿开`
- [ ] 状态为**禁用**
- [ ] 内容为 YAML 格式，语法正确
- [ ] YAML 结构与变量结构脚本的 Zod Schema 层级对应
- [ ] 值类型符合 Zod 定义
- [ ] 无繁体字

### 变量列表

- [ ] 条目名为 `变量列表`（无 `[mvu_update]` 前缀）
- [ ] depth=0 或 1，order=200
- [ ] 内容为固定模板：`<status_current_variable>{{format_message_variable::stat_data}}</status_current_variable>`

### 变量更新规则

- [ ] 条目名以 `[mvu_update]` 开头
- [ ] 每个变量有 `check` 字段
- [ ] 自明变量未写冗余规则
- [ ] 同类变量已合并
- [ ] `_` 前缀变量未写规则
- [ ] `type` 与 Zod Schema 一致

### 变量输出格式

- [ ] 条目名以 `[mvu_update]` 开头
- [ ] `rule` 包含 JSON Patch 操作说明
- [ ] `format` 包含 `<UpdateVariable>`、`<Analysis>`、`<JSONPatch>` 结构
- [ ] 路径中不含 `stat_data` 前缀

### 正则

- [ ] 有 promptOnly 正则隐藏 `<UpdateVariable>` 块
- [ ] 有 promptOnly 正则隐藏 `<StatusPlaceHolderImpl/>`
- [ ] 有 markdownOnly 正则将 `<StatusPlaceHolderImpl/>` 替换为界面代码

### 前端状态栏（如有）

- [ ] `body { margin: 0; padding: 0; }` 正确
- [ ] 变量路径以 `stat_data.` 开头
- [ ] 使用 `getAllVariables()` + `_.get()`
- [ ] 包含 `await waitGlobalInitialized('Mvu')`
- [ ] 包含 `$(errorCatched(init))`
- [ ] 包含 `eventOn(Mvu.events.VARIABLE_UPDATE_ENDED, ...)` 并回调刷新

---

## 十、常见错误示例

### 错误 1：变量结构脚本中 import 了 z 或 _

```js
// 错误
import { z } from 'zod';
import _ from 'lodash';
import { registerMvuSchema } from '...';

// 正确：z 和 _ 由环境注入，只 import registerMvuSchema
import { registerMvuSchema } from 'https://testingcf.jsdelivr.net/gh/StageDog/tavern_resource/dist/util/mvu_zod.js';
```

### 错误 2：变量列表放在了 D3 或更深

```
变量列表 depth=3  ✗
```
AI 会误认为列表里的数值是 3 轮对话之前的状态，导致更新判断错误。

```
变量列表 depth=0  ✓
```

### 错误 3：变量列表条目名加了 [mvu_update]

```
条目名："[mvu_update]变量列表"  ✗
```

加了 `[mvu_update]` 前缀后 MVU 引擎会认为这个条目仅供"额外模型解析"模式使用，普通对话 AI 收不到。

```
条目名："变量列表"  ✓
```

### 错误 4：JSON Patch 路径带了 stat_data

```json
{ "op": "replace", "path": "/stat_data/亚丝娜/好感度", "value": 40 }
```
路径应直接从变量根开始。`stat_data` 是存储键名，AI 不需要知道它。

```json
{ "op": "replace", "path": "/亚丝娜/好感度", "value": 40 }
```

### 错误 5：前端状态栏 body padding 不为 0

```css
body { margin: 0; padding: 10px; }  /* ✗ */
```

非零 padding 会导致状态栏在酒馆界面中显示错位。

```css
body { margin: 0; padding: 0; }
.card { margin: 8px; }              /* ✓ 边距加在容器上 */
```

### 错误 6：前端 JS 中变量路径缺少 stat_data

```js
_.get(all_variables, '亚丝娜.好感度', 'N/A')  // ✗
```

MVU 将变量存储在 `stat_data` 键下，js 读取时必须带上。

```js
_.get(all_variables, 'stat_data.亚丝娜.好感度', 'N/A')  // ✓
```

### 错误 7：忘记监听 VARIABLE_UPDATE_ENDED

```js
async function init() {
  await waitGlobalInitialized('Mvu');
  render();  // 只渲染一次，变量变化后界面不会更新
}
$(errorCatched(init));
```

必须加上事件监听，变量更新后自动刷新：

```js
async function init() {
  await waitGlobalInitialized('Mvu');
  render();
  eventOn(Mvu.events.VARIABLE_UPDATE_ENDED, () => render());  // ✓
}
$(errorCatched(init));
```

### 错误 8：Zod 和 Beta 风格混用

```
[initvar] 用 YAML  ← ZOD 风格
AI 输出格式用 _.set() ← Beta 风格
```

两套体系不兼容。初始化格式、更新指令、读取路径必须全选同一套。新项目统一用 ZOD。

### 错误 9：[initvar] 条目未禁用

```
[initvar]条目 enabled: true  ✗
```

MVU 只读取禁用状态的 `[initvar]` 条目做变量初始化。启用后会被当作普通提示词发送给 AI，变量不会被初始化。

### 错误 10：对 `_` 前缀变量写了更新规则

```yaml
变量更新规则:
  世界:
    _类型:       # ✗ _前缀是只读的，AI 不可更新
      check: ...
```

只读变量不需要出现在更新规则中。

---

> **文档版本：** 1.0 | **最后更新：** 2026-05-16
