# 发布层（阶段9）：PNG 注入 / 自动挂载 / 大统合 / 坑清单

## 9.1 PNG 角色卡注入（scripts/png_inject.py）

**原理**：PNG tEXt chunk `chara` ＝ base64(V2 JSON)，插在 IHDR 后，CRC 重算——与 SillyTavern 官方导出一致，纯 struct+zlib 实现。

**流程**：
1. 卡↔PNG 双射映射：规范化（旧形→新形、去后缀、去别名段）＋专名映射表＋精确匹配优先/包含兜底＋长名优先＋占用排除＋**双射断言**（37↔37 全配对且不重复）
2. **备份空白原图**（`_备份_PNG空白_日期\`）
3. 注入 → **回读验证**（提取 chara→json.loads→与源卡逐字节比对）
4. 注入前全量 BOM 扫描（实战：源卡带 BOM 导致下游解析失败）

## 9.2 自动挂载（专属世界书随角色）

- V2 原生机制：`data.character_book`（内嵌书）＋`data.extensions.world`（书名）→ 酒馆导入即建书并挂到该角色
- **格式转换**：ST 世界书导出格式 → character_book：
  - disable → `enabled: false`（手动条目保持手动）
  - 原 entry.extensions 原样带入（position/depth 数值保留）
  - id / insertion_order ＝ uid；comment/name ＝ 内容首行标题
  - 书对象：name/description/scan_depth/recursive_scanning
- **实测教训**：内嵌书路线在个别酒馆版本导入失败 → **兜底＝世界书面板直接导入同构格式 json**（与源书同构＝已验证可导入），Hub 卡只做"封面＋激活指针"

## 9.3 大统合卡（格式上限认知）

**硬上限：1 PNG ＝ 1 角色 ＋ 1 内嵌书**。"一图导入全部角色"不可行。

**方案 B（推荐）**：
- 大统合 Hub 卡 ＝ 封面＋功能说明＋内嵌"共通资料库合并书"（多本共通书条目拼接：uid 重排唯一、display_index 同步、comment 加来源标签【库A】【库B】、disable 门控保留）
- 37 角色卡各自内嵌专属书
- 合并书同时提供**独立 WI json**（源书同构格式）作兜底导入路径
- 封面素材注意实际位置（实战：封面图不在 PNG 目录而在插画库）

## 9.4 发布目录规范

```
发布目录\
├── 大统合Hub.png（封面＋共通合并书）
├── 角色卡PNG\（N 张，各内嵌专属书）
├── 角色卡JSON\（N 张）
└── 世界书JSON\（N 专属＋共通各本）
```

## 9.4b GitHub 发布（推荐 gh CLI）

```
winget install GitHub.cli        # 或官方 zip 绿色版（免管理员）
gh auth login -h github.com -p https -w    # 设备码：浏览器输一次，永久生效
git init -b main && git add -A && git commit -m "基线"
gh repo create 仓库名 --public --source . --push   # 建仓库+推送一步完成
gh release create v1.0 发布物.zip --notes "…"
```

- 登录细节：gh 打印 8 位一次性代码 → 浏览器开 github.com/login/device → 粘贴 → Authorize
- 推送会弹 Git Credential Manager 登录窗（同为浏览器授权，一次即可）
- 提交身份：`git config user.name 你的用户名`＋`user.email 用户名@users.noreply.github.com`（隐私默认）

## 9.5 发布坑清单（实战全踩过）

| 坑 | 症状 | 解法 |
|---|---|---|
| 内嵌书导入失败 | 个别酒馆版本卡导入报错 | WI 原生格式 json 兜底＋Hub 卡瘦身 |
| scenario 400/420 截断 | 尾句半悬空、单词腰斩 | 有语料依据补全，否则指针化 |
| 源卡 BOM | 下游解析失败 | 注入前全量扫描去 BOM |
| tags 泄底 | PNG 元数据/标签栏外显终局词 | tags 中性化（如"星之理的盗窃者"→阵营词） |
| 合并文件尾部截断 | 排序靠后的文件"看起来断了" | 按字数均衡切份（每份≤1800 行） |
| 标题粘连 | 前文件无尾换行+后文件标题贴死 | 标题前强制补换行 |
| 语料 L 号偏移 | 引文核验大量误报 | 惯例偏移 ±1~3 判定带 |
| 卡/书 name 与文件名不同步 | 映射断言失败 | 专名映射表＋双向包含＋长名优先 |
