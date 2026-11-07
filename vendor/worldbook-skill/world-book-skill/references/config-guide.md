# 世界书配置规则速查

## 本文内容

>本文档是世界书配置速查手册。本文档不教怎么写内容,只教怎么把写好的内容配置成 AI 能正确读取的条目。所有字段说明、参数取值、场景速查表均在此，配置前必读，配置后必查。

---

## 一、工作流程

```
写内容 → 判定卡片类型 → 查速查表分配蓝绿灯 → 设位置/顺序/递归 → 用脚本写入 → query.py 自查
```

执行顺序不可跳过：先判定类型再配置，先配置再写入，先写入再自查。

---

## 二、位置对照表 (position)

`position` 决定条目内容插入到系统提示词的哪个位置。合法值 0–7：

| 值 | 标识 | CLI flag | 含义 | 用途 |
|----|------|----------|------|------|
| 0 | ↑Char | `--position 0` | 角色定义之前 (before_char) | 宏观设定：世界观总纲、规则、地理、历史 |
| 1 | ↓Char | `--position 1` | 角色定义之后 (after_char) | 具体信息：角色详情、NPC、场景、物品 |
| 2 | ↑AT | `--position 2` | 作者注之前 | 文风规则、格式指令 |
| 3 | ↓AT | `--position 3` | 作者注之后 | 极少使用 |
| 4 | @D | `--position 4 --depth 0 --role 0` | D齿轮深度注入 (at_depth) | 行为纠正、二次解释、直接指导 AI |
| 5 | ↑EM | — | 示例对话之前 | 不使用 |
| 6 | ↓EM | — | 示例对话之后 | 不使用 |
| 7 | Outlet | `--position 7 --outlet-name <名>` | 预设端口 | 不使用 |

**@D 的深度铁律**：position=4 时必须配 depth，且**只用 depth=0**。D1 及以上深度会插入到聊天记录中间，破坏互动历史的完整性。AI 读来像是剧情中间突然插进设定说明书。D0 是整个聊天记录最底部，影响力最大。

**role 参数**：position=4 时 `--role 0` (System)，其余位置无需指定 role。

---

## 三、constant 含义

`constant` 控制条目的激活方式：

| 值 | 俗称 | 行为 |
|----|------|------|
| `true` | 蓝灯 | 条目始终激活，每轮都发给 AI |
| `false` | 绿灯 | 仅在最近消息中出现关键词时激活 |

蓝灯 = 必须始终存在的信息。绿灯 = 按需加载的信息。选错的代价：蓝灯过多 → token 爆炸；绿灯过多 → AI 缺信息开始猜测。

---

## 四、scanDepth 扫描深度

仅对绿灯条目生效。控制"最近消息"的范围：

| 值 | 含义 |
|----|------|
| `null` (不设) | 扫描全部聊天记录 |
| `2` | 只看最后一条用户消息 + 最后一条 AI 消息 |

**推荐：所有绿灯条目统一设 `scanDepth=2`。** 扫全量会导致过度触发。角色被提到一次后很久不再出场，但 AI 每轮都扫到历史中的关键词，条目持续激活，越写越多无法推进。

---

## 五、递归双字段（强制）

```
preventRecursion:  true    ← 本条目不会触发其他条目
excludeRecursion:  true    ← 本条目不被其他条目触发
```

**所有条目必须同时设为 `true`，无一例外。** 蓝灯和绿灯都需要。

不设 `preventRecursion=true` 的后果：条目 A 内容中出现条目 B 的关键词 → B 被触发 → B 的内容触发 C → 连锁反应 → token 爆炸。不设 `excludeRecursion=true` 的后果：B 被 C 触发的同时 C 也被 B 触发 → 双向递归 → 关键设定条目互相驱逐出上下文。

**脚本默认值均为 `false`，不加 flag 就不会设。** 创建每条命令时必须带 `--prevent-recursion --exclude-recursion`。

---

## 六、order 编号规则

同一位置内的条目按 `order` 从小到大排列，数值越大越靠后。

| 条目类型 | order | 备注 |
|----------|-------|------|
| 世界观总纲 | 1 | 最前，AI 最先读到 |
| 背景设定 / 区域速览 | 2–3 | 次于总纲 |
| 角色速览 | 4 | 所有角色一句话简介 |
| 场景 / 事件详情 | 50–98 | 具体场景按需排列 |
| 核心角色详细信息 | 99 | 最详细的人设放最后 |
| NPC / 控制器 | 100 | 最靠后 |

单角色卡拆分条目的内部编号：基础信息 10 → 外貌 20 → 性格 30 → 背景 40 → NSFW 50。

多角色卡的二次解释条目分别编号：角色A=1、角色B=2，依此类推。

---

## 七、keys 格式

关键词用**英文逗号** `,` 分隔。中文逗号 `，` 和空格均会失效。

覆盖所有可能的称呼方式：

| 条目类型 | keys 构成 |
|----------|-----------|
| 角色条目 | 全名, 昵称, 外号 |
| NPC 条目 | 全名, 昵称, 外号, 职务 |
| 场景条目 | 场景名, 所在区域, 别称, 相关动作词 |
| 势力条目 | 全名, 简称, 所在地名 |

正确示例：`林小雨,小雨,班长`
错误示例：`林小雨，小雨，班长` `林小雨 小雨 班长`

---

## 八、蓝绿灯分配速查表

配置前必须先判断场景类型。判断依据：世界书中描述了几个**不同的核心角色**。同一角色的拆分条目（基础/外貌/性格/背景……）不等于不同角色。

### 8.1 单角色卡（1 个核心角色）

**铁律：该角色的所有拆分条目全部蓝灯。** 拆成 5 条 = 5 个蓝灯，拆成 10 条 = 10 个蓝灯。没有例外。

| 条目类型 | 蓝灯/绿灯 | position | order | keys | scanDepth |
|----------|----------|----------|-------|------|-----------|
| 世界观总纲 | 蓝灯 | 0 (↑Char) | 1 | — | — |
| 背景设定 | 蓝灯 | 0 (↑Char) | 2–3 | — | — |
| 角色基本信息 | 蓝灯 | 1 (↓Char) | 10 | — | — |
| 角色外貌 | 蓝灯 | 1 (↓Char) | 20 | — | — |
| 角色性格 | 蓝灯 | 1 (↓Char) | 30 | — | — |
| 角色背景 | 蓝灯 | 1 (↓Char) | 40 | — | — |
| 角色 NSFW | 蓝灯 | 1 (↓Char) | 50 | — | — |
| 角色二次解释 | 绿灯 | 4 (@D, depth=0) | 1 | 角色名,昵称 | 2 |
| NPC | 绿灯 | 1 (↓Char) | 100 | NPC名,昵称,职务 | 2 |
| 场景/事件 | 绿灯 | 1 (↓Char) | 50–98 | 场景名,地点名 | 2 |

### 8.2 多角色卡（2+ 个核心角色）

**铁律：速览蓝灯，角色详情全部绿灯。** 不能让所有角色同时常驻。

| 条目类型 | 蓝灯/绿灯 | position | order | keys | scanDepth |
|----------|----------|----------|-------|------|-----------|
| 世界观总纲 | 蓝灯 | 0 (↑Char) | 1 | — | — |
| 背景设定 | 蓝灯 | 0 (↑Char) | 2–3 | — | — |
| 角色速览 | 蓝灯 | 0 (↑Char) | 4 | — | — |
| 角色A 详细信息 | 绿灯 | 1 (↓Char) | 99 | 角色A名,昵称,外号 | 2 |
| 角色B 详细信息 | 绿灯 | 1 (↓Char) | 99 | 角色B名,昵称,外号 | 2 |
| 角色A 二次解释 | 绿灯 | 4 (@D, depth=0) | 1 | 角色A名,昵称 | 2 |
| 角色B 二次解释 | 绿灯 | 4 (@D, depth=0) | 2 | 角色B名,昵称 | 2 |
| NPC | 绿灯 | 1 (↓Char) | 100 | NPC名,昵称,职务 | 2 |
| 场景/事件 | 绿灯 | 1 (↓Char) | 50–98 | 场景名,地点名 | 2 |

### 8.3 纯世界书（系统驱动卡，无角色卡）

**铁律：所有条目蓝灯。** 通过 EJS 条件模板实现内容的动态变化，而非依赖关键词触发。

| 条目类型 | 蓝灯/绿灯 | position | order | keys | 备注 |
|----------|----------|----------|-------|------|------|
| 世界背景 | 蓝灯 | 0 (↑Char) | 1 | — | |
| 规则/机制 | 蓝灯 | 0 (↑Char) | 2 | — | |
| 玩家设定 | 蓝灯 | 1 (↓Char) | 99 | — | 可含 EJS 动态渲染 |
| 变量更新规则 | 蓝灯 | 1 (↓Char) | 100 | — | |
| EJS 控制器 | 蓝灯 | 1 (↓Char) | 100 | — | |
| EJS 被加载条目 | 禁用 (enabled=false) | 1 (↓Char) | — | — | 由控制器通过 getwi() 动态加载，手动开启会导致多阶段内容同时出现 |

---

## 九、插入位置推荐

```
世界观总纲       → position=0 (↑Char, before_char)
                    放宏观设定：世界规则、地理、历史、背景。AI 先读这些再读角色定义。

角色详细信息     → position=1 (↓Char, after_char)
                    放具体信息：角色人设、NPC、场景、物品。AI 先理解角色再补充细节。

二次解释         → position=4, depth=0, role=0 (@D)
                    放直接指导 AI 行为的内容。不写"他习惯喝牛奶"，写"到早上时写出他喝牛奶的剧情"。
                    D0 影响力最强，用于纠正 AI 对角色/世界的误解。

文风规则         → position=2 (↑AT)
                    放格式指令和文风约束。

D1 及以上 (@D, depth≥1) → 永不使用。
```

---

## 十、配置命令模板

以下模板可直接复制后替换尖括号内的值使用。所有命令均含双递归 flag。

```bash
# 世界观总纲（蓝灯，角色定义前）
python world-book-create.py <世界书.json> --add \
  --comment "<标题>" --content "@<内容文件.txt>" \
  --constant --position 0 --order 1 \
  --prevent-recursion --exclude-recursion

# 角色基本信息（蓝灯，角色定义后，单角色卡）
python world-book-create.py <世界书.json> --add \
  --comment "<角色名>_基础信息" --content "@<内容文件.txt>" \
  --constant --position 1 --order 10 \
  --prevent-recursion --exclude-recursion

# 角色详细信息（绿灯，角色定义后，多角色卡）
python world-book-create.py <世界书.json> --add \
  --comment "<角色名>_详细信息" --content "@<内容文件.txt>" \
  --keys "<角色名>,<昵称>,<外号>" --position 1 --order 99 --scan-depth 2 \
  --prevent-recursion --exclude-recursion

# NPC（绿灯，角色定义后）
python world-book-create.py <世界书.json> --add \
  --comment "NPC_<角色名>" --content "@<内容文件.txt>" \
  --keys "<全名>,<昵称>,<职务>" --position 1 --order 100 --scan-depth 2 \
  --prevent-recursion --exclude-recursion

# 场景（绿灯，角色定义后）
python world-book-create.py <世界书.json> --add \
  --comment "场景_<场景名>" --content "@<内容文件.txt>" \
  --keys "<场景名>,<地点名>" --position 1 --order 80 --scan-depth 2 \
  --prevent-recursion --exclude-recursion

# 二次解释（绿灯，D0）
python world-book-create.py <世界书.json> --add \
  --comment "<角色名>_二次解释" --content "@<内容文件.txt>" \
  --keys "<角色名>,<昵称>" --position 4 --depth 0 --role 0 --scan-depth 2 \
  --prevent-recursion --exclude-recursion

# 禁用条目（EJS 被加载条目等）
python world-book-create.py <世界书.json> --add \
  --comment "<条目名>" --content "@<内容文件.txt>" \
  --disable --position 1 --order 100 \
  --prevent-recursion --exclude-recursion

# 编辑已有条目（按 UID）
python world-book-create.py <世界书.json> --edit <UID> \
  --content "@<新内容文件.txt>" --depth 4

# 列出所有条目
python world-book-create.py <世界书.json> --list

# 批量添加（从 JSON 数组文件）
python world-book-create.py <世界书.json> --batch <批量配置.json>
```

---

## 十一、query.py 命令速查

```bash
# 查看所有条目摘要（含 content_preview、keys、position、constant 等）
python query.py <世界书.json>

# 极简模式（uid / comment / content_length / keys / constant / 双递归状态）
python query.py <世界书.json> --brief

# 查看指定 UID 条目的完整 JSON（输出可直接用于 --batch-edit）
python query.py <世界书.json> --uid <UID>

# 按关键词搜索条目（匹配标题/内容/触发词）
python query.py <世界书.json> --search "<关键词>"

# 解析条目的 @UID/@名称 嵌套引用
python query.py <世界书.json> --resolve
```

查询结果中各字段含义：

| 字段 | 含义 | 重点检查 |
|------|------|----------|
| `constant` | true=蓝灯，false=绿灯 | 单角色卡所有角色条目必须为 true |
| `preventRecursion` | 阻止触发其他条目 | 全部条目必须为 true |
| `excludeRecursion` | 阻止被其他条目触发 | 全部条目必须为 true |
| `scanDepth` | null=全扫，2=只看最后两条 | 绿灯条目应为 2 |
| `keys` | 关键词数组 | 英文逗号分隔，无空格 |

---

## 十二、自查清单

配置完成后，用 `python query.py <世界书.json> --brief` 逐条检查，不得跳过任何一项：

- [ ] **先数核心角色数**：1 个 → 单角色卡，2+ 个 → 多角色卡
- [ ] 单角色卡？→ 所有该角色的条目 `constant=true`
- [ ] 多角色卡？→ 速览 `constant=true`，角色详情 `constant=false` + 有 `keys`
- [ ] 世界观条目全部 `constant=true`
- [ ] NPC / 场景 / 故事章节全部 `constant=false` + 有 `keys`
- [ ] **所有条目 `preventRecursion=true` 且 `excludeRecursion=true`**（脚本默认 false，不加 flag 就不会设！）
- [ ] 关键词用英文逗号 `,` 分隔，无空格、无中文逗号
- [ ] 绿灯条目 `scanDepth=2`
- [ ] 没有任何条目使用 position=3/5/6/7
- [ ] 没有任何条目 depth≥1（仅 D0 可用）
- [ ] 单角色卡的拆分条目内部 order 按逻辑递增（10→20→30→40→50）
- [ ] 二次解释条目在 position=4, depth=0, role=0

---

## 十三、常见错误示例

### 错误 1：单角色卡把角色拆分条目设成绿灯

```
错误：林小雨_性格 → constant=false（绿灯）
后果：AI 在对话中看不到性格设定，凭空猜测角色行为，角色千人一面。
正确：单角色卡所有角色条目 constant=true。拆成多少条就多少蓝灯。
```

### 错误 2：忘记双递归 flag

```
错误：创建条目时没加 --prevent-recursion --exclude-recursion
后果：脚本默认写入 preventRecursion=false, excludeRecursion=false。
      蓝灯条目之间互相触发，token 爆炸式增长。
正确：每条命令都带 --prevent-recursion --exclude-recursion。
```

### 错误 3：关键词用中文逗号

```
错误：--keys "林小雨，小雨，班长"
后果：中文逗号不被识别为分隔符，整个字符串被视为一个关键词。
      非要用户输入完整字符串"林小雨，小雨，班长"才能触发。
正确：--keys "林小雨,小雨,班长"
```

### 错误 4：二次解释放在 position=1

```
错误：二次解释放在 ↓Char (position=1)，和其他详情条目混在一起
后果：二次解释的信息优先级和普通设定相同，AI 可能忽略。
正确：position=4, depth=0, role=0。D0 是最强注入位置。
```

### 错误 5：多角色卡全蓝灯

```
错误：3 个核心角色，每人 5 条详情，全部 constant=true
后果：15 条常驻 + 世界观 + NPC，上下文直接撑爆。
正确：速览蓝灯，各角色详情绿灯 + 关键词覆盖。
```

### 错误 6：EJS 被加载条目设为启用

```
错误：多阶段人设的各个阶段条目 enabled=true，且 constant=true
后果：所有阶段内容同时出现在 AI 上下文中，角色行为在不同状态间跳跃混乱。
正确：这些条目 enabled=false，由 EJS 控制器通过 getwi() 按需动态加载。
```

### 错误 7：scanDepth 不设或设错

```
错误：绿灯条目不设 scanDepth（默认 null，扫全量）
后果：角色被提到一次后，即使 20 轮不再出场，AI 每轮都从历史中扫到关键词，
      条目持续激活，token 浪费且剧情被无关信息干扰。
正确：所有绿灯条目 scanDepth=2。
```

---

## 十四、字段速查总表

世界书条目常用字段一览，按 CLI 参数 / JSON 字段对照：

| CLI flag | JSON 字段 | 类型 | 默认值 | 说明 |
|----------|-----------|------|--------|------|
| `--comment` | `comment` | string | `""` | 条目标题/备注 |
| `--content` | `content` | string | `""` | 条目正文，支持 `@文件路径` 从文件读取 |
| `--keys` | `key` | string[] | `[]` | 主触发词，英文逗号分隔 |
| `--keys2` | `keysecondary` | string[] | `[]` | 辅助触发词 |
| `--constant` | `constant` | bool | `false` | true=蓝灯常驻 |
| `--position` | `position` | 0–7 | `0` | 注入位置 |
| `--order` | `order` | int | 自动递增+100 | 排序值，越大越靠后 |
| `--depth` | `depth` | int | `1` | 深度层级（仅 position=4 时用 0） |
| `--role` | `role` | 0–2 | `0` | 0=System, 1=User, 2=Assistant |
| `--scan-depth` | `scanDepth` | int/null | `null` | 扫描深度，绿灯推荐 2 |
| `--prevent-recursion` | `preventRecursion` | bool | `false` | 必须设为 true |
| `--exclude-recursion` | `excludeRecursion` | bool | `false` | 必须设为 true |
| `--disable` | `disable` | bool | `false` | true=禁用条目 |
| `--selective` | `selective` | bool | `false` | 选择性激活 |
| `--selective-logic` | `selectiveLogic` | 0–3 | `0` | 0=AND_ANY, 1=NOT_ALL, 2=NOT_ANY, 3=AND_ALL |
| `--group` | `group` | string | `""` | 分组名 |
| `--group-weight` | `groupWeight` | int | `100` | 分组权重 |
| `--probability` | `probability` | int | `100` | 触发概率 1–100 |
| `--case-sensitive` | `caseSensitive` | bool/null | `null` | 区分大小写 |
| `--match-whole-words` | `matchWholeWords` | bool/null | `null` | 全词匹配 |
| `--sticky` | `sticky` | int | `0` | 粘性值 |
| `--cooldown` | `cooldown` | int | `0` | 冷却值 |
| `--delay` | `delay` | int | `0` | 延迟值 |
