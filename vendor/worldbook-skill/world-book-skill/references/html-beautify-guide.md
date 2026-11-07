# HTML 前端美化编写指南

> 为 MVU 变量卡编写状态栏面板、全局装饰、开场选择器等 HTML 界面代码。输出可直接嵌入酒馆正则 `replaceString` 字段的完整 HTML 文档。

## 本文内容

>本文指引 HTML 前端美化的代码生成。指引涵盖美化范围确认、CSS 变量体系与响应式规范、SVG 图标系统、MVU 安全读写模式、正则脚本配置、以及页面导航/触控/API 调用等交互逻辑。不涉及人设写作或世界书内容，仅处理 HTML/CSS/JS 代码生成。

---

## 工作流程

### 阶段一：确认需求边界

在生成代码之前，必须逐一确认以下四个维度：

1. **美化范围**：是仅替换状态栏标记（如 `<StatusPlaceHolderImpl/>`）、全局覆盖对话界面、二者都需要、还是开场选择面板（如 `<start>` 标记）？不同范围对应不同的正则触发词和 placement 配置。
2. **角色卡主题**：从五大配色预设中选择一个，或由用户自定义色板。主题决定 CSS 变量体系中的核心色值。
3. **交互复杂度**：状态栏通常是纯展示面板（只读），开场选择器则需要多步骤表单（输入框、单选卡片、多选标签、总览确认页）。两者在 JS 逻辑上差异很大。
4. **完成后动作**：是否需要创建世界书条目？是否触发 AI 回复？是否清空第 0 楼 HTML 以释放性能？

### 阶段二：确定正则策略

每套可视化界面至少需要两条正则规则，形成"显示 + 隐藏"配对：

| 规则用途 | 关键字段 | 说明 |
|---------|---------|------|
| 显示界面（用户可见） | `markdownOnly: true` | 完整的 HTML 文档，渲染在对话窗口中 |
| 隐藏原文（AI 不可见） | `promptOnly: true` | `replaceString: ""`，阻止原始标记进入上下文 |

两条规则使用完全相同的 `findRegex`，确保同一个触发标记在用户端被替换为 UI、在模型端被替换为空串。`placement` 统一使用 `[1, 2]`，分别对应显示层和提示词层。`runOnEdit` 设为 `true` 以保证每次编辑对话时重新执行替换。

### 阶段三：生成 HTML 文档

输出为一个完整的内联 HTML 文件，包含 `<style>` 块和 `<script>` 块。所有资源（图标、装饰、字体效果）必须通过内联方式实现，不能依赖任何外部 URL。

### 阶段四：配置正则脚本 JSON

将 HTML 文档填入正则对象的 `replaceString` 字段，按角色卡规范格式输出完整的 `regex_scripts` 配置。

---

## 详细规范

### 3.1 CSS 变量体系

所有视觉参数集中定义在 `:root` 块中，让后续修改只需变动变量值而非逐行查找色值。

#### 色彩变量命名规则

使用功能语义命名，而非视觉描述命名。变量名表达"这个颜色用在什么地方"，而不是"这个颜色长什么样"。

```css
:root {
  /* 页面基底 */
  --bg-primary: #0f0d0a;
  --bg-card: #1a1714;
  --bg-card-hover: #231f19;
  --bg-input: #161310;

  /* 文字层级 */
  --text-primary: #e8dcc8;
  --text-secondary: #b5a78e;
  --text-muted: #7d7264;

  /* 强调与交互 */
  --accent: #c9a84c;
  --accent-light: #e8d5a0;
  --accent-dark: #8a7230;
  --border: #3d3428;
  --shadow-accent: 0 0 30px rgba(201,168,76,0.08);
}
```

#### 五大配色预设速查

| 预设名称 | 适用场景 | 背景深色 | 卡片色 | 主文字 | 强调色 | 边框色 |
|---------|---------|---------|--------|-------|--------|--------|
| 暗金古韵 | 修仙/古风/东方 | `#0f0d0a` | `#1a1714` | `#e8dcc8` | `#c9a84c` | `#3d3428` |
| 霓虹脉冲 | 赛博/科幻/机甲 | `#0a0a14` | `#12122a` | `#e0e0ff` | `#00f0ff` | `#2a2a4a` |
| 深红夜幕 | 恐怖/血族/末世 | `#0a0608` | `#1a0e12` | `#e8d0d0` | `#c94c4c` | `#3d2828` |
| 翠意栖林 | 精灵/森林/自然 | `#0a0f0d` | `#141a17` | `#c8e8d0` | `#4cc98a` | `#283d34` |
| 晨光白昼 | 校园/日常/现代 | `#f5f7fa` | `#ffffff` | `#2c3e50` | `#3498db` | `#e0e6ed` |

#### 响应式字号

使用 `clamp(最小值, 视窗比例值, 最大值)` 三段式定义，确保从手机到桌面都有可读的字体大小。比例值取视窗宽度的 2% 到 6% 不等，按层级递增。

```css
--fs-xs:  clamp(10px, 2vw, 11px);
--fs-sm:  clamp(11px, 2.2vw, 12px);
--fs-base: clamp(12px, 2.5vw, 14px);
--fs-md:  clamp(13px, 2.8vw, 15px);
--fs-lg:  clamp(15px, 3.2vw, 18px);
--fs-xl:  clamp(18px, 4vw, 22px);
--fs-2xl: clamp(22px, 5vw, 26px);
--fs-3xl: clamp(26px, 6vw, 32px);
```

#### 响应式间距

同样使用三段式 clamp，保证内外边距随屏幕宽度同比例缩放。

```css
--space-xs:  clamp(4px, 1vw, 8px);
--space-sm:  clamp(8px, 2vw, 12px);
--space-md:  clamp(12px, 3vw, 16px);
--space-lg:  clamp(16px, 4vw, 24px);
--space-xl:  clamp(20px, 5vw, 32px);
--space-2xl: clamp(24px, 6vw, 40px);
```

#### 安全区域（异形屏适配）

通过 `env()` 获取系统级安全区插入量，为刘海屏、灵动岛等异形屏预留边距。每个变量提供 `0px` 作为降级默认值。

```css
--safe-top:    env(safe-area-inset-top, 0px);
--safe-bottom: env(safe-area-inset-bottom, 0px);
--safe-left:   env(safe-area-inset-left, 0px);
--safe-right:  env(safe-area-inset-right, 0px);
```

### 3.2 布局与重置

#### 全局重置

```css
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html {
  -webkit-text-size-adjust: 100%;
  -webkit-tap-highlight-color: transparent;
}
body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'SimSun', serif;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  justify-content: center;
  line-height: 1.6;
  overflow-x: hidden;
}
.container {
  position: relative;
  width: 100%;
  max-width: 640px;
  min-height: 100vh;
  min-height: 100dvh;
}
```

#### 响应式断点

五个标准断点覆盖所有设备形态：

```css
/* 超小屏（手机竖屏，宽度不足360px） */
@media (max-width: 360px) {
  .card-row { grid-template-columns: 1fr 1fr; gap: var(--space-xs); }
  .btn { padding: 10px 20px; }
}

/* 横屏模式（高度不足480px，手机横持） */
@media (max-height: 480px) and (orientation: landscape) {
  .page { justify-content: flex-start; padding-top: var(--space-md); }
  .page-inner { gap: var(--space-sm); }
  .decorative-svg { display: none; }
  .separator { display: none; }
}

/* 平板（768px 以上） */
@media (min-width: 768px) {
  /* 增加网格列数、放宽间距 */
}

/* 桌面（1024px 以上） */
@media (min-width: 1024px) {
  .container { max-width: 680px; }
}

/* 用户偏好减少动画 */
@media (prefers-reduced-motion: reduce) {
  .animated-el { animation: none !important; }
}
```

### 3.3 绝对禁止清单

以下六条为硬性红线，违反将导致界面在酒馆环境中无法正常渲染：

1. **禁止使用 emoji 字符作为图标**：如 `content: "&#x2764;"` 或 `&#x1F499;` 等 Unicode 符号。它们在跨平台渲染中差异极大，必须用内联 SVG 替代。
2. **禁止使用 `vh` 单位设定高度**：酒馆的 iframe 环境中 `vh` 计算不可靠（某些内核取视口高度而非 iframe 高度）。统一使用 `dvh` 动态视口单位。
3. **禁止引用外部字体**：`@import url('https://fonts.googleapis.com/...')` 和 `<link rel="stylesheet">` 均不可用，外部网络可能在运行时不可达。字体回退列表（font-family 栈）必须最终落到系统内置字体。
4. **禁止引用外部图片**：`background-image: url(...)` 和 `<img src="...">` 均不得指向外部域名。所有图形元素用 CSS 渐变、内联 SVG 或纯色块实现。
5. **禁止用 `position: absolute` 撑高页面主体**：脱离文档流的定位方式会导致容器高度计算异常。装饰元素可以用 absolute 放在角落，但主体内容布局必须依靠 flex 或 grid。
6. **禁止 `let` / `const` 和箭头函数**：部分内嵌浏览器内核为旧版本 WebView，不完全支持 ES6。所有变量声明使用 `var`，所有函数使用 `function` 关键字。

### 3.4 全局美化与文本换行规则

全局美化正则通过 `(.*)<StatusPlaceHolderImpl/>` 捕获 AI 回复正文并包装为自定义 HTML 容器。以下三条规则用于防止文本挤作一团或换行失效。

#### 规则 1：包装容器必须设置换行和行高

AI 回复经过 markdown 转换后，部分文本可能是 `<br>` 换行而非 `<p>` 标签换行。全局 CSS 仅对 `p` 选择器设置样式时，`<br>` 换行的文本将没有段间距。对策：在包装容器本身上设置 `white-space` 和 `line-height`，确保即使没有 `<p>` 标签，纯文本也能正常显示。

```css
.global-chat-wrapper {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.8;
}
.global-chat-wrapper p {
  margin: 0 0 12px 0;
}
```

`white-space: pre-wrap` 保留原始换行符并自动折行。`line-height` 直接设在容器上，不依赖 `<p>` 标签。

#### 规则 2：正则捕获必须保留 `<StatusPlaceHolderImpl/>`

全局美化正则的 findRegex 捕获 `$1` 后，replaceString 中必须原样放回 `<StatusPlaceHolderImpl/>`，否则状态栏正则找不到匹配目标。

```
# 正确：$1 之后保留占位符
findRegex: /(.*)<StatusPlaceHolderImpl\/>/gs
replaceString: <style>...</style><div class="wrapper">$1<StatusPlaceHolderImpl/></div>

# 错误：占位符被吃掉
findRegex: /(.*)<StatusPlaceHolderImpl\/>/gs
replaceString: <style>...</style><div class="wrapper">$1</div>
```

#### 规则 3：状态栏 CSS 重置必须限定作用域

状态栏 HTML 是独立的 `<!DOCTYPE html>` 文档，在 iframe 中渲染。状态栏内的 `* { margin: 0; padding: 0 }` 被 iframe 隔离，不会泄漏到主对话区。但全局美化 CSS 是直接注入对话 DOM 的，其重置规则 **绝不能用通用选择器 `*`**，必须限定在容器 class 下：

```css
/* 全局美化：用容器 class 限定 */
.global-chat-wrapper, .global-chat-wrapper * {
  box-sizing: border-box;
}

/* 状态栏（iframe 内）：可以用通用选择器，不会被外部感知 */
body { margin: 0; padding: 0; }
```

#### 规则 4：状态栏变量优先用宏渲染

在 iframe 环境中，JS 的 `getAllVariables()` 路径解析可能与主窗口不一致。状态栏中的 MVU 变量值优先使用宏 `{{format_message_variable::stat_data.路径}}` 直接渲染到 HTML，而非在 JS 中通过 `getAllVariables() + _.get()` 读取。宏在正则替换时一次性展开，不受 iframe 沙箱影响。

```html
<!-- 优先：宏直接展开 -->
<span>{{format_message_variable::stat_data.角色名.好感度}}</span>

<!-- 降级：仅当需要实时刷新时才用 JS + eventOn 监听 -->
```

### 3.5 图标与装饰

#### 内联 SVG 图标

所有图标通过 `<svg>` 标签直接嵌入 HTML。常用做法是编写一个 JS 辅助函数，按需生成 SVG 字符串，避免在 HTML 中堆砌大量重复的 `<svg>` 块。

```javascript
function makeIcon(pathData, vb) {
  vb = vb || '0 0 24 24';
  return '<svg viewBox="' + vb + '" fill="none" stroke="currentColor" ' +
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" ' +
    'style="width:32px;height:32px;color:var(--accent);opacity:0.8;">' +
    pathData + '</svg>';
}
```

#### 主题装饰 SVG（首页）

每个主题应配备一个识别性的 SVG 图形置于欢迎页顶部，例如：
- 暗金古韵 → 双鱼旋绕图案（两段圆弧相互交叠）
- 霓虹脉冲 → 六边形网格与节点连线
- 深红夜幕 → 哥特尖拱窗与十字分割
- 翠意栖林 → 叶脉放射纹理
- 晨光白昼 → 圆角矩形堆叠

装饰 SVG 的尺寸使用 clamp 响应式控制，在横屏模式或极小屏幕下可隐藏以节省垂直空间。

#### 分隔线

页面标题与引导文案之间使用细线分隔符，由 SVG 绘制一条水平线加中心小圆点：

```html
<svg class="separator" viewBox="0 0 400 20" aria-hidden="true">
  <line x1="60" y1="10" x2="180" y2="10" stroke="var(--accent)" stroke-width="0.5" opacity="0.3"/>
  <circle cx="200" cy="10" r="2" fill="none" stroke="var(--accent)" stroke-width="0.5" opacity="0.4"/>
  <line x1="220" y1="10" x2="340" y2="10" stroke="var(--accent)" stroke-width="0.5" opacity="0.3"/>
</svg>
```

### 3.6 正则脚本配置规范

#### 标准配对模板

以状态栏为例，完整的两条正则配置如下：

```json
{
  "id": "uuid-v4-xxxx-001",
  "scriptName": "[UI]状态栏展示",
  "findRegex": "/<StatusPlaceHolderImpl\\/>/g",
  "replaceString": "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n...完整HTML...\n</html>",
  "trimStrings": [],
  "placement": [1, 2],
  "disabled": false,
  "markdownOnly": true,
  "promptOnly": false,
  "runOnEdit": true,
  "substituteRegex": 0,
  "minDepth": null,
  "maxDepth": null
}
```

```json
{
  "id": "uuid-v4-xxxx-002",
  "scriptName": "[UI]状态栏隐藏(AI)",
  "findRegex": "/<StatusPlaceHolderImpl\\/>/g",
  "replaceString": "",
  "trimStrings": [],
  "placement": [1, 2],
  "disabled": false,
  "markdownOnly": false,
  "promptOnly": true,
  "runOnEdit": true,
  "substituteRegex": 0,
  "minDepth": null,
  "maxDepth": null
}
```

#### 字段说明

| 字段 | display 规则 | prompt 规则 | 说明 |
|------|-------------|-------------|------|
| `markdownOnly` | `true` | `false` | 标记为仅用户显示层可见 |
| `promptOnly` | `false` | `true` | 标记为仅提示词层可见 |
| `placement` | `[1, 2]` | `[1, 2]` | 两套规则使用相同值 |
| `runOnEdit` | `true` | `true` | 编辑时重新执行 |
| `replaceString` | 完整 HTML | `""` 空字符串 | 用户看 UI，模型什么也看不到 |
| `findRegex` | 相同 | 相同 | 匹配同一个触发标记 |

#### findRegex 转义规则

正则表达式以 slash 风格书写（`/pattern/flags`）。如果正则内部包含 `/` 字符，必须转义为 `\/`。例如匹配 XML 自闭合标签：

```
/<StatusPlaceHolderImpl\/>/g
```

### 3.7 MVU 变量安全写入

这是最容易出错的环节。MVU 内部在 MvuData 对象中维护了 `initialized_lorebooks` 等引擎私有字段。如果直接构造一个只有 `stat_data` 的 payload 写入，会覆盖掉这些私有字段，导致 MVU 在下次消息处理时重新初始化所有变量，用户填写的全部数据瞬间归零。

**安全写入三步法：**

1. 读取完整数据对象
2. 仅替换其中的 `stat_data` 属性
3. 将完整对象写回

```javascript
// === 正确做法 ===
var fullData = Mvu.getMvuData({ type: 'message', message_id: 0 }) || {};
fullData.stat_data = myStatData;
await Mvu.replaceMvuData(fullData, { type: 'message', message_id: 0 });

// === 错误做法（禁止） ===
var payload = { stat_data: myStatData };
await Mvu.replaceMvuData(payload, { type: 'message', message_id: 0 });
```

创建新楼层时同样需要传入完整数据对象：

```javascript
await createChatMessages([{
  role: 'user',
  message: openingText,
  data: fullData
}]);
```

### 3.8 四种 HTML 注入模式

| 模式 | replaceString | 典型用途 | 说明 |
|------|--------------|---------|------|
| 内联 HTML | 完整 `<!DOCTYPE html>...` | 状态栏面板、开场选择器 | 最常见，所有 CSS/JS 写死在替换字符串中 |
| 外部 CDN | `<script>$('body').load('https://cdn.example.com/ui.html')</script>` | 体积敏感的大型 UI | HTML 不占角色卡体积，但依赖 CDN 可用性 |
| 空串替换 | `""` | 对 AI 隐藏标记 | 完全移除匹配内容，两端都看不到 |
| 折叠面板 | `<details><summary>标题</summary>$1</details>` | 变量更新日志 | 用户可展开查看，默认折叠节省空间 |

**模式选择建议：**
- 状态栏 → 内联 HTML（体量可控，几百行即可）
- 开场选择器 → 内联 HTML（需要 JS 交互，无法折叠或隐藏）
- 对 AI 隐藏的配合规则 → 空串替换
- 调试 / 变量变化日志 → 折叠面板

### 3.9 页面导航（开场选择器）

当开场选择器包含多个步骤（选择世界、设定姓名、分配属性等），使用多页面切换模式。所有页面置于同一个容器中，通过 class 控制可见性。

```javascript
var currentPage = 0;
var TOTAL_PAGES = 8;

function goToPage(n) {
  if (n < 0 || n >= TOTAL_PAGES) return;
  var allPages = document.querySelectorAll('.page');
  for (var i = 0; i < allPages.length; i++) {
    allPages[i].classList.remove('active');
  }
  currentPage = n;
  var target = document.getElementById('page-' + n);
  if (target) target.classList.add('active');
  window.scrollTo(0, 0);
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;
  refreshStepDots();
  if (n === TOTAL_PAGES - 1) renderSummary();
}
```

#### 步骤指示器

底部固定圆点指示器展示用户在流程中的位置：

```css
.step-indicator {
  position: fixed;
  bottom: calc(var(--space-md) + var(--safe-bottom));
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: clamp(4px, 1vw, 8px);
  z-index: 10;
  padding: 4px 8px;
  border-radius: 12px;
  background: rgba(15,13,10,0.8);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}
.step-dot {
  width: clamp(5px, 1.2vw, 7px);
  height: clamp(5px, 1.2vw, 7px);
  border-radius: 50%;
  background: var(--border);
  transition: background 0.3s, box-shadow 0.3s;
}
.step-dot.active { background: var(--accent); box-shadow: 0 0 8px rgba(201,168,76,0.4); }
.step-dot.done { background: var(--accent-dark); }
```

### 3.10 触控与滚动

所有可点击元素必须同时满足两条最低标准：
- `min-height: 44px`（手指触碰的最小舒适尺寸）
- `touch-action: manipulation`（禁用双击缩放，消除 300ms 点击延迟）

滚动容器设置：

```css
.scroll-area {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  max-height: 60vh;
  max-height: 60dvh;
}
```

### 3.11 完成确认流程

```javascript
function onConfirm() {
  var btn = document.getElementById('btn-confirm');
  btn.disabled = true;
  btn.textContent = '正在处理...';

  if (typeof getCharWorldbookNames === 'undefined') {
    alert('请在酒馆环境中运行');
    btn.disabled = false;
    btn.textContent = '确认';
    return;
  }

  var charWB = getCharWorldbookNames('current');
  var wbName = charWB.primary;
  if (!wbName) {
    alert('未绑定主世界书');
    btn.disabled = false;
    btn.textContent = '确认';
    return;
  }

  var statData = buildStatData();
  var existingData = Mvu.getMvuData({ type: 'message', message_id: 0 }) || {};
  existingData.stat_data = statData;

  createChatMessages([{
    role: 'user',
    message: openingText,
    data: existingData
  }], { refresh: 'all' }).then(function() {
    return Mvu.replaceMvuData(existingData, { type: 'message', message_id: 0 });
  }).then(function() {
    btn.textContent = '已完成';
    btn.style.borderColor = '#10b981';
    btn.style.color = '#10b981';
    setChatMessages([{
      message_id: 0,
      message: '初始化完成'
    }], { refresh: 'affected' });
  }).catch(function(err) {
    alert('操作失败: ' + (err.message || String(err)));
    btn.disabled = false;
    btn.textContent = '确认';
  });
}
```

### 3.12 可用的酒馆 API 速览

| API 方法 | 作用 |
|---------|------|
| `Mvu.getMvuData(option)` | 读取 MVU 完整数据（含引擎内部字段） |
| `Mvu.replaceMvuData(data, option)` | 写回 MVU 数据 |
| `createChatMessages(messages, option)` | 创建新的消息楼层 |
| `setChatMessages(messages, option)` | 修改已有消息楼层内容 |
| `getCharWorldbookNames('current')` | 获取当前角色卡关联的世界书名 |
| `deleteWorldbookEntries(wbName, filter)` | 按条件删除世界书条目 |
| `createWorldbookEntries(wbName, entries)` | 批量创建世界书条目 |
| `generate({ user_input, should_stream })` | 触发 AI 生成回复 |
| `getLastMessageId()` | 获取最新楼层号 |
| `waitGlobalInitialized('Mvu')` | 等待 MVU 内核初始化完成 |

### 3.13 组件速查表

以下为开场选择器中最常用的五种交互组件及其关键 HTML 结构，按实际需要选取组合。

#### 欢迎首页

全屏居中、大标题、装饰 SVG、引导副标题、开始按钮。

#### 文本输入

单行 `<input>` 配合 placeholder 提示，聚焦时边框变色，必填项为空时抖动提示。

#### 单选卡片

Grid 布局的卡片阵列，每张卡片有标题和描述行。点击后高亮选中态（边框变强调色、背景叠加半透明强调色），同时取消其他卡片选中态。

#### 多选标签

Flex wrap 排列的胶囊形按钮，每个代表一个可选项。点击切换激活态，支持同时选中多个。底层用数组维护已选值列表。

#### 摘要确认表

最后一步汇总用户所有选择，以两列表格呈现：左列为字段名（右对齐、弱化色），右列为用户选值（强调色、自动换行）。下方放"返回修改"和"确认提交"两个按钮。

### 3.14 初始化时机

由于 iframe 的加载时机不固定，使用双重保险确保初始化函数被执行：

```javascript
document.addEventListener('DOMContentLoaded', init);
if (document.readyState !== 'loading') init();
```

### 3.15 输出格式规定

输出必须是用三个反引号包裹的完整 HTML 代码块，标记语言为 `html`。代码内部按功能分区加中文注释：

```
/* === 色彩变量 === */
/* === 基础重置 === */
/* === 页面布局 === */
/* === 组件样式 === */
// === 全局状态 ===
// === 页面导航 ===
// === 数据收集 ===
// === 提交确认 ===
// === 初始化 ===
```

---

## 自查清单

生成代码后，逐条核查以下 10 项：

1. [ ] CSS 变量中是否包含：5 个以上的色彩变量、8 级响应式字号（xs 到 3xl）、6 级响应式间距（xs 到 2xl）、4 个 safe-area 变量？
2. [ ] 所有图标是否均以 `<svg>` 内联形式呈现，无任何 emoji 字符或 Unicode 符号图标？
3. [ ] 高度相关属性是否全部使用 `dvh` 而非 `vh`？`min-height` 是否同时写了 `vh` 降级和 `dvh` 覆盖？
4. [ ] 是否完全不存在外部 URL 引用。无 `<link>`、无 `@import`、无 `url()` 指向外部域名、无 `<img src="http...">`？
5. [ ] 主体布局是否完全依赖 flex / grid，无 `position: absolute` 撑高页面的情况？
6. [ ] 所有 JavaScript 变量是否使用 `var` 声明，函数是否使用 `function` 关键字，无 `let`/`const`/`=>`？
7. [ ] MVU 变量写入是否遵循"先读取完整数据 → 仅替换 stat_data → 写回完整对象"三步法？
8. [ ] 是否同时生成了两条正则配置。display 规则（markdownOnly: true）和 prompt 规则（promptOnly: true, replaceString: ""）？
9. [ ] 所有可点击元素是否满足 `min-height: 44px` 和 `touch-action: manipulation`？
10. [ ] 是否覆盖了全部五个响应式断点（max-360 / max-height-480-landscape / min-768 / min-1024 / prefers-reduced-motion）？

---

## 常见错误

### 错误 1：直接构造 payload 覆盖写入

```javascript
// ❌ 丢失 initialized_lorebooks 等内部字段
var payload = { stat_data: statData };
Mvu.replaceMvuData(payload, { type: 'message', message_id: 0 });
```

修正：先 `getMvuData` 获取完整对象，只替换 `stat_data` 后再写回。

### 错误 2：createChatMessages 的 data 字段传空或不传

```javascript
// ❌ 新楼层的 data 中缺少内部字段，MVU 将重新初始化
createChatMessages([{ role: 'user', message: text }]);
```

修正：将完整数据对象传入 `data` 字段。

### 错误 3：混用不同 MVU 版本的路径格式

MVU beta 风格路径必须带 `[0]` 后缀（如 `stat_data.角色.好感度[0]`），而 Zod 风格使用 JSON Patch 斜杠路径（如 `/角色/好感度`）。两种格式不能共存于同一张角色卡中。确认角色卡使用的 MVU 版本后再决定路径写法。

### 错误 4：忘记转义正则中的斜杠

```json
// ❌ 内部 / 与 slash 风格的定界符冲突
"findRegex": "/<StatusPlaceHolderImpl/>/g"

// ✅ 正确转义
"findRegex": "/<StatusPlaceHolderImpl\\/>/g"
```

### 错误 5：promptOnly 规则用了非空 replaceString

隐藏规则的作用是阻止原文进入 AI 上下文。如果 `replaceString` 不是空字符串，这些内容仍然会出现在 prompt 中，白白消耗 token 预算。隐藏规则应该永远使用 `"replaceString": ""`。

### 错误 6：页面动画未适配 reduced-motion

部分用户开启了系统级"减少动态效果"设置。如果未在 `@media (prefers-reduced-motion: reduce)` 中禁用所有动画，这些用户会因持续旋转或闪烁的装饰元素感到不适。

### 错误 7：在非酒馆环境中未做兜底检测

HTML 文件可能被用户在浏览器中直接打开预览。所有涉及酒馆 API（`Mvu`、`getCharWorldbookNames` 等）的调用前，必须先检测 `typeof` 是否为 `'undefined'`，给出友好提示而非静默崩溃。
