# EJS 动态内容集成指南

> EJS 依赖 MVU 提供变量。MVU 独立运行不需要 EJS，但 EJS 必须有 MVU 变量值才能实现动态控制。本文档教你把静态世界书条目改造成"根据变量值切换内容"的动态条目。

## 本文内容

>本文是 EJS 动态内容设计指引。指引根据已有的 MVU 变量系统（好感度、关系状态、信任度等），编写条件判断代码让世界书条目在不同变量值下发送不同内容。本文只讲解了 EJS 代码逻辑，人设内容、调色盘描写等文本由其他阶段完成。

---

## 工作流程

### 阶段一：确认 MVU 变量路径

在写任何 EJS 代码前，必须先确认以下信息：

1. **好感度路径**：如 `stat_data.角色名.好感度`
2. **关系状态路径**：如 `stat_data.角色名.关系状态`
3. **其他判定变量**：信任度、剧情阶段、日期等所有用于阶段划分的变量
4. **默认值**：每个变量在用户未设定时的兜底值

> 变量路径写法见 `mvu-guide.md`。核心铁律：EJS 中读取 MVU 变量必须加 `stat_data` 前缀，无需 `[0]` 索引。

#### 阶段判定条件规划

用一张表格明确每个阶段的触发条件：

```
阶段一（陌生期）：好感度 < 150，关系状态为"陌生人"
阶段二（熟悉期）：好感度 150–400，关系状态为"熟人"
阶段三（暧昧期）：好感度 400–700，关系状态非"恋人"
阶段四（恋人间）：关系状态为"恋人"
```

**条件边界必须无重叠、无遗漏**。数值用 `<` `>=` `&&` 连接。

---

### 阶段二：选条目结构与装饰器

根据控制类型选择结构方案：

#### 方案 A：控制器 + 禁用阶段条目（推荐用于大量内容）

适用于每个阶段内容超过 200 字的情况。结构与多阶段人设系统一致：

```
[控制器条目]     ← 蓝灯常驻，Order 100
  ├── 读取变量
  ├── 条件判断
  └── 用 getwi() 加载阶段条目

[阶段01条目]     ← 禁用，Order 98
[阶段02条目]     ← 禁用，Order 98
[阶段03条目]     ← 禁用，Order 98
```

控制器通过 `@activate` 装饰器保持蓝灯激活，阶段条目设为 `enabled=false`，由 `getwi()` 按需加载。未命中的阶段内容不会被发送给 AI，节省 token。

#### 方案 B：单条目内 if/else 分块（适用于中小内容）

所有内容写在一个条目中，用 `<%_ _%>` 包裹条件判断：

```
蓝灯条目，Order 99
  ├── 变量读取头
  ├── 阶段一的提示词（if 包裹）
  ├── 阶段二的提示词（else if 包裹）
  ├── 阶段三的提示词（else 包裹）
  └── 通用提示词（if 外面，始终发送）
```

#### 装饰器速查

| 装饰器 | 场景 |
|--------|------|
| `@activate` | 控制器条目：视为蓝灯常驻 |
| `@preprocessing` | 动态关键词：处理后激活绿灯条目 |
| `@private` | 自动包裹作用域，防变量冲突 |
| `@iframe` | HTML 状态栏：样式隔离不污染全局 |
| `@if 条件` | 简洁条件：条件成立才发送条目 |
| `@render_after` | 渲染到消息末尾（不发给 AI） |
| `@generate_before` | 注入到提示词开头 |

---

### 阶段三：编写 EJS 代码

按以下顺序编写代码块。

#### 步骤 1：写变量读取头

条目最顶部，读取所有阶段判定变量：

```javascript
<%_
if (typeof gw === 'undefined') var gw = getvar('stat_data.角色名.好感度', { defaults: 0 });
if (typeof rel === 'undefined') var rel = getvar('stat_data.角色名.关系状态', { defaults: '陌生人' });
if (typeof trust === 'undefined') var trust = getvar('stat_data.角色名.信任度', { defaults: 0 });
_%>
```

**铁律三条：**

1. 必须用 `typeof` 防重复声明。多个条目可能使用同名变量
2. 必须用 `var` 声明。不可用 `const` / `let`
3. 路径必须带 `stat_data` 前缀，不需要 `[0]` 索引

#### 步骤 2：写条件判断块

**基础模板：if / else if / else**

```javascript
<%_ if (gw < 150) { _%>
此处为初识期 AI 可见的描述
<%_ } else if (gw < 400) { _%>
此处为熟悉期 AI 可见的描述
<%_ } else if (gw < 700) { _%>
此处为暧昧期 AI 可见的描述
<%_ } else { _%>
此处为恋人间 AI 可见的描述
<%_ } _%>
```

**多变量组合模板：**

```javascript
<%_ if (gw >= 400 && trust >= 30 && rel !== '恋人') { _%>
好感达标 + 信任足够 + 尚未交往 → 暧昧期表现
<%_ } _%>

<%_ if (rel === '恋人') { _%>
关系确认后 → 恋人专属内容
<%_ } _%>
```

**嵌套条件模板（二层判断）：**

```javascript
<%_ if (rel !== '恋人') { _%>
  <%_ if (gw < 400) { _%>
  非恋人 + 低好感 → 保持距离
  <%_ } else { _%>
  非恋人 + 高好感 → 亲近但未表白
  <%_ } _%>
<%_ } else { _%>
恋人 → 亲密无间
<%_ } _%>
```

#### 步骤 3：用 getwi() 加载阶段条目（方案 A 专用）

控制器蓝图：

```javascript
<%_
if (typeof gw === 'undefined') var gw = getvar('stat_data.角色名.好感度', { defaults: 0 });
if (typeof rel === 'undefined') var rel = getvar('stat_data.角色名.关系状态', { defaults: '陌生人' });
_%>

<%_ if (gw < 150) { _%>
<%- await getwi('角色名_阶段01_初识') %>
<%_ } else if (gw < 400) { _%>
<%- await getwi('角色名_阶段02_熟悉') %>
<%_ } else if (rel === '恋人') { _%>
<%- await getwi('角色名_阶段04_恋人') %>
<%- await getwi('角色名_扩展内容') %>
<%_ } else { _%>
<%- await getwi('角色名_阶段03_暧昧') %>
<%_ } _%>
```

**getwi() 铁律：**
- 必须加 `await`：`<%- await getwi('条目名') %>`
- 等价写法：`<%_ print(await getwi('条目名')); _%>`
- 传递数据：`await getwi('条目名', { key: value })`
- 阶段条目必须设为禁用状态（`enabled=false`），不能同时设为蓝灯

#### 步骤 4：放通用内容

不需要条件判断的通用内容直接写在所有 `if` 块外面：

```
此处为始终发送的描述，不受阶段影响
```

#### 步骤 5：写 print() 风格代码块（可选）

当内容全部是动态推导时，用 `print()` 避免频繁切换 `<%_ _%>`：

```javascript
<%_
if (gw < 150) {
  print('当前阶段：初识。角色对你很陌生，态度疏远。');
} else if (gw < 400) {
  print('当前阶段：熟悉。角色开始习惯你的存在。');
} else {
  print('当前阶段：亲近。角色对你很放心。');
}
_%>
```

---

### 阶段四：配置与测试

#### 条目配置速查

| 条目角色 | 激活方式 | Order | 状态 | 递归 |
|---------|----------|-------|------|------|
| 控制器（含 getwi） | `@activate` 蓝灯 | 100 | enabled=true | 防递归 |
| 阶段条目（被 getwi 加载） | 禁用 | 98–800 | enabled=false | 防递归 |
| 单条目 if/else 型 | 蓝灯 | 99 | enabled=true | 防递归 |
| @preprocessing 词条 | `@preprocessing` 蓝灯 | 100 | enabled=true | 防递归 |
| 被词条激活的绿灯条目 | 绿灯 | 按需 | enabled=true | 防递归 |
| @iframe 状态栏 | `@render_after` 蓝灯 | 按需 | enabled=true | 防递归 |

#### 制作与测试的关键开关

输入框上方有"启用/禁用提示词模板"按钮：

- **制作阶段**：关闭开关 → AI 看到原始 EJS 代码（方便检查逻辑是否正确）
- **测试/游玩阶段**：打开开关 → AI 看到处理后的结果（如具体数值代替 `<%= getvar(...) %>`）

#### 调试方法

```javascript
<%_ console.info('当前好感度:', gw); _%>   // F12 Console 查看
<%_ toastr.info('已触发阶段二'); _%>        // 右上角弹通知
<%_ debugger; _%>                           // F12 打开后暂停，可查看所有变量
```

通过输入框左下角魔棒 → 提示词查看器，可查看 EJS 处理后实际发送给 AI 的完整内容。

---

## 详细规范

### 标签类型速查

| 标签 | 执行 | 输出 | 说明 |
|------|------|------|------|
| `<%_ _%>` | ✅ | ❌ | 执行代码，去除空白（推荐） |
| `<%= %>` | ❌ | ✅ 转义 | 输出变量值，HTML 转义 |
| `<%- %>` | ❌ | ✅ 原样 | 输出值，不转义（getwi 专用） |
| `<%# %>` | ❌ | ❌ | 注释，不处理 |

### 变量读取关键规则

```javascript
/* 读取数值，不存在时用默认值 */
getvar('stat_data.角色名.好感度', { defaults: 0 })

/* 判断变量是否存在 */
getvar('stat_data.角色名.好感度') !== undefined

/* 文本相等判断必须用 === */
getvar('stat_data.天气') === '晴天'

/* 文本不等用 !== */
getvar('stat_data.关系状态') !== '恋人'

/* 模糊匹配 */
getvar('stat_data.日期', { defaults: '' }).includes('10月25日')
```

### 内容注入前缀

在条目**标题（comment）**中添加前缀，将内容注入到指定位置：

| 前缀 | 注入位置 |
|------|---------|
| `[GENERATE:BEFORE]` | 发送给 AI 的提示词开头 |
| `[GENERATE:AFTER]` | 发送给 AI 的提示词末尾 |
| `[RENDER:BEFORE]` | 消息渲染开头（不发给 AI） |
| `[RENDER:AFTER]` | 消息渲染末尾（不发给 AI） |

### @preprocessing 动态关键词

将条目内容作为关键词来源，动态激活绿灯条目：

```javascript
@preprocessing
<%_
if (typeof evt === 'undefined') var evt = getvar('stat_data.事件.当前事件', { defaults: '' });
_%>

<%_ if (evt === '学园祭') { _%>
学园祭活动 摊位 演出
<%_ } else if (evt === '修学旅行') { _%>
修学旅行 合宿 观光
<%_ } _%>
```

处理后条目内容变为对应关键词，激活以此为关键词的绿灯条目。要求 SillyTavern 1.13.4+。

注意：`@preprocessing` 不能与 `@generate_before` / `@generate_after` 同时使用。

### @iframe 隔离状态栏

```javascript
@render_after
@iframe
@if !is_user && !is_system
<html>
<head></head>
<body>
<div>
好感度：<%- variables.stat_data.角色名.好感度 %>
</div>
</body>
</html>
```

在角色楼层末尾渲染 HTML，样式不污染全局。`@iframe` 后加标题文字可折叠。

### @@if 简洁条件

单条件简写，不写完整 `<%_ _%>` 块：

```
@if variables.stat_data.角色名.好感度 >= 90
角色对你非常信任
```

```
@if variables.stat_data.角色名.好感度 > 50 && variables.stat_data.角色名.好感度 < 90
角色视你为朋友
```

### 多阶段调色盘 EJS 结构

将手写好的多阶段调色盘整合为一条 EJS 条目的完整骨架：

```
<%_
if (typeof gw === 'undefined') var gw = getvar('stat_data.角色名.好感度', { defaults: 0 });
if (typeof rel === 'undefined') var rel = getvar('stat_data.角色名.关系状态', { defaults: '陌生人' });
_%>

性格调色盘：人的性格就像调色盘，由多种性格衍生组合而成才是活生生的人

<%_ if (gw < 150) { _%>
底色：初识期底色
主色调：初识期主色调
性格点缀：初识期点缀
<%_ } else if (gw < 400) { _%>
底色：熟悉期底色
主色调：熟悉期主色调
性格点缀：熟悉期点缀
<%_ } else { _%>
底色：亲近期底色
主色调：亲近期主色调
性格点缀：亲近期点缀
<%_ } _%>

<%_ if (gw < 150) { _%>
初识期专属衍生一：...
初识期专属衍生二：...
<%_ } _%>

<%_ if (gw >= 150 && gw < 400) { _%>
熟悉期专属衍生一：...
熟悉期专属衍生二：...
<%_ } _%>

<%_ if (gw >= 400 && rel !== '恋人') { _%>
暧昧期专属衍生一：...
暧昧期专属衍生二：...
<%_ } _%>

<%_ if (rel === '恋人') { _%>
恋人专属衍生一：...
恋人专属衍生二：...
<%_ } _%>

跨阶段通用衍生一：...（始终发送）
跨阶段通用衍生二：...

对角色的理解与思考:

<%_ if (gw < 150) { _%>
  关于初识期行为的注释：
    ...
<%_ } _%>

<%_ if (gw >= 150 && gw < 400) { _%>
  关于熟悉期行为的注释：
    ...
<%_ } _%>

  关于通用衍生的注释：（不用 if 包裹）
    ...

  总结：这就是[角色名]的性格调色盘...
```

条目配置：蓝灯常驻，position=after_char，order=99，防递归。

### 多阶段人设系统控制器模板

```javascript
<%_
if (typeof gw === 'undefined') var gw = getvar('stat_data.角色名.好感度', { defaults: 0 });
if (typeof rel === 'undefined') var rel = getvar('stat_data.角色名.关系状态', { defaults: '陌生人' });
if (typeof trust === 'undefined') var trust = getvar('stat_data.角色名.信任度', { defaults: 0 });
_%>

<%_ if (gw < 150) { _%>
<%- await getwi('角色名_阶段01_初识') %>
<%_ } else if (gw < 400) { _%>
<%- await getwi('角色名_阶段02_熟悉') %>
<%_ } else if (gw < 700 && rel !== '恋人') { _%>
<%- await getwi('角色名_阶段03_暧昧') %>
<%_ } else if (rel === '恋人') { _%>
<%- await getwi('角色名_阶段04_恋人') %>
<%_ } else { _%>
<%- await getwi('角色名_阶段03_暧昧') %>
<%_ } _%>
```

### 常见阶段判定模式

**纯数值分段：**

```javascript
<%_ if (gw < 150) { _%>   // 初识
<%_ } else if (gw < 400) { _%>   // 熟悉
<%_ } else if (gw < 700) { _%>   // 暧昧
<%_ } else { _%>   // 恋人
<%_ } _%>
```

**数值 + 文本组合：**

```javascript
<%_ if (gw >= 400 && trust >= 30 && rel !== '恋人') { _%>
// 好感高 + 信任足 + 非恋人 = 暧昧期
<%_ } _%>
```

**日期事件判定：**

```javascript
<%_
if (typeof date === 'undefined') var date = getvar('stat_data.世界信息.当前日期', { defaults: '' });
_%>
<%_ if (date.includes('12月24日') || date.includes('12月25日')) { _%>
圣诞活动专属内容
<%_ } _%>
```

---

## 自查清单

- [ ] 所有变量使用 `typeof` 防重复声明 + `var` 声明
- [ ] 所有变量路径带 `stat_data` 前缀，无 `[0]` 索引
- [ ] `<%_ _%>` 格式正确，大括号成对闭合
- [ ] `getwi()` 前有 `await`
- [ ] 条件边界无重叠（同一好感度不会同时命中两个阶段）
- [ ] 条件边界无遗漏（任意好感度值都能命中某个阶段）
- [ ] 通用内容（跨阶段不变的内容）放在所有 `if` 块外面
- [ ] 每个阶段的二次解释（作者注释）的 if 条件与对应衍生条件一致
- [ ] 控制器条目：蓝灯常驻，order=100，防递归
- [ ] 阶段条目（被 getwi 加载的）：禁用状态，order 98–800，防递归
- [ ] 单条目型：蓝灯，order=99，防递归
- [ ] `@preprocessing` 条目不与 `@generate_before` / `@generate_after` 同时使用
- [ ] 制作时关闭提示词模板查看原始代码，测试时打开查看处理结果
- [ ] 文件内容自身不含禁词（叙事禁词/比喻禁词/描写禁律）

---

## 常见错误示例

### 错误 1：getwi 忘记 await

```javascript
/* ❌ 错误：缺少 await，条目不会加载 */
<%- getwi('角色_阶段01') %>

/* ✅ 正确 */
<%- await getwi('角色_阶段01') %>
```

### 错误 2：变量路径缺少 stat_data 前缀

```javascript
/* ❌ 错误：缺少 stat_data 前缀，读不到值 */
const gw = getvar('角色.好感度', { defaults: 0 });

/* ✅ 正确 */
const gw = getvar('stat_data.角色.好感度', { defaults: 0 });
```

### 错误 3：使用 const/let 声明变量

```javascript
/* ❌ 错误：const/let 在多个条目中会导致重复声明报错 */
const gw = getvar('stat_data.角色.好感度', { defaults: 0 });

/* ✅ 正确：var + typeof 防重复 */
if (typeof gw === 'undefined') var gw = getvar('stat_data.角色.好感度', { defaults: 0 });
```

### 错误 4：条件边界重叠

```javascript
/* ❌ 错误：好感度 400 同时命中两个条件 */
if (gw < 400) { ... }
else if (gw <= 400) { ... }   // 400 时两个都成立

/* ✅ 正确：用 < 和 >= 分割，边界唯一归属 */
if (gw < 400) { ... }
else if (gw < 700) { ... }    // 400 单独归属第二阶段
```

### 错误 5：条件边界遗漏

```javascript
/* ❌ 错误：好感度 ≥ 400 时落在所有条件外面 */
if (gw < 200) { ... }
else if (gw < 400) { ... }

/* ✅ 正确：用 else 兜底 */
if (gw < 200) { ... }
else if (gw < 400) { ... }
else { ... }    // ≥ 400 的情况
```

### 错误 6：阶段条目同时开启蓝灯

```javascript
/* ❌ 错误：阶段条目设了蓝灯，导致所有阶段内容同时发送，失去动态控制意义 */
/*
条目A（控制器）：@activate, enabled=true  → 正确
条目B（阶段01）：@activate, enabled=true  → 错误！应设为 enabled=false
*/

/* ✅ 正确：阶段条目设为禁用，由控制器通过 getwi 按需加载 */
```

### 错误 7：@preprocessing 与注入装饰器冲突

```javascript
/* ❌ 错误：两个装饰器互斥，preprocessing 会被忽略 */
@preprocessing
@generate_before
内容...

/* ✅ 正确：只保留 @preprocessing */
@preprocessing
内容...
```

### 错误 8：通用内容误放在 if 块内

```javascript
/* ❌ 错误：通用特征只在高好感度时出现 */
<%_ if (gw >= 400) { _%>
角色说话声音很轻
跨阶段通用特征 xxx
<%_ } _%>

/* ✅ 正确：通用内容放在所有 if 外面 */
角色说话声音很轻
<%_ if (gw < 400) { _%>
初识期专属特征
<%_ } else { _%>
亲近期专属特征
<%_ } _%>
```

### 错误 9：字符串相等用 == 而非 ===

```javascript
/* ❌ 错误：== 可能因类型转换导致误判 */
getvar('stat_data.关系状态') == '恋人'

/* ✅ 正确 */
getvar('stat_data.关系状态') === '恋人'
```
