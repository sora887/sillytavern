---
name: tavern-card
description: SillyTavern（酒馆）角色卡工程技能：从主题或小说文本出发，写出可导入的人设、世界书（WorldBook）、开场白、MVU 变量、正则与状态栏，并编译成 v2 JSON / v3 PNG。合并了九个开源写卡技能包的方法论（worldbook-skill、TavernWeave、charcard-workshop、moyu-cards 墨月写卡、card-maker、春水与风月、ln-lore-pipeline 等）。当用户说"写张卡 / 做个角色卡 / 酒馆角色 / 世界书 / 开场白 / 拆卡 / 改卡 / MVU / 状态栏"，或贴一段小说要求做成卡时加载。
whenToUse: 任何 SillyTavern / 酒馆 / 角色卡 / WorldBook / 开场白 / MVU 变量 / 正则 / 状态栏 / 卡文件打包拆包 / 存量卡体检与改造的任务。也用于"这张卡为什么不好玩"这类诊断。
metadata:
  author: 本地合并构建（非上游单一作者）
  built: "2026-11-05"
  merged_from: worldbook-skill(echo-xianyu) · TavernWeave(LiarMTTT) · charcard-workshop(yukk4159-bit) · moyu-cards(Wallslqq) · card-maker(Pra-Moon) · foreverse-card-skills(foreverse-app) · chunshui-fengyue(wenyu1123) · ln-lore-pipeline(master666-max) · marco-card-skills(Marco0431)
  install_kind: full-offline-merge
  vendor_mirror: "30.3 MB / 1469 files"
---

# tavern-card · 酒馆角色卡工作台

九份开源写卡技能包合并成一个。**方法论在 `references/`，原文全量在 `vendor/`，工具在 `scripts/`。**

## 必读顺序

1. **先读 `references/00-routes.md`** —— 它判定本次走哪条路线（新建卡 / 世界书优先 / 存量改造 / 局部变体），并列出四道闸门。**跳过它直接开写是最常见的失败方式。**
2. 按路线只读需要的那几篇：
   - `references/15-card-archetypes.md` —— **判型**：设定集 / 长篇剧情 / 系统面板 / 角色互动，四类原型的字段取舍与位置分工
   - `references/10-worldbook.md` —— 世界书分条、触发、位置、泄底门控
   - `references/20-character.md` —— 人设：调色盘路线 vs 人物生境路线
   - `references/30-opening.md` —— 开场白的形式、钩子、正反改写对照
   - `references/40-mvu-regex-ejs.md` —— MVU 变量、正则闸门、EJS、状态栏
   - `references/50-format.md` —— v2 JSON / v3 PNG 字段表、编译与拆包
   - `references/60-quality.md` —— 硬伤清单、反 AI 味、审查流程
3. 需要**原始依据**时读 `vendor/<repo>/...`（九个仓库完整镜像，一字未改）。`references/` 里每条规则都能在 `vendor/` 找到出处。
4. 要**落地成文件**时用 `scripts/`：`build_card.py`（project→完备卡）、`check_card.py`（硬伤检查）、`check_hygiene.py`（数据卫生：关键词写坏、空条目、测试残留、常驻预算）、`extract_card.py`（拆包）、`scan_duplicates.py`（查重）。依赖 Python 3 + Pillow。

## 四条红线

- **闸门 1 不可跳。** 先出 `design-spec.md` 给用户过目，确认后才写正文。一口气生成整张卡 = 返工。
- **分批交付。** 人设 → 世界书 → 开场白 → 变量/状态栏 → 示例对话 → 打包，每批停一次。
- **设计 ≠ 出图。** 本技能只产出文本与卡文件；卡面立绘/封面的提示词走 `personal-agent-skills`，实际生图需用户明确要求。
- **不虚构。** 不得声称读过未读的文件、跑过没跑的脚本、检查过没检查的卡。交付状态只用这几个标签：

```
SPEC           仅文字方案
CARD-PENDING   字段已写，未编译成 JSON/PNG
CARD-BUILT     已跑 build_card.py 产出文件
CHECK-PASSED   已跑 check_card.py 且通过
USER-APPROVED  用户明确认可
```

## 审美基准（写卡文案时同时生效）

若 `personal-agent-skills` 技能可用，其 `bundle/references/personal-identity-profile/references/taste-core.md` 与 `design-dislikes.md` 是本技能文案的默认审美参照。要点：

- 精致的结构基底上，一处怪，一点危险
- 服装按真实结构分层，交代剪裁/材质/固定点/承重
- 默认拒绝无因果的钟表、链条、蝴蝶、玫瑰、粒子、形容词堆砌的"高级感"
- 复杂度局部化：有高密度区，也有安静区
- 人物要像人不像模特

用户当轮明确要求永远优先于以上所有默认。

## 不要做的事

- 不要用本文件代替 `references/00-routes.md` 的路线判定。
- 不要把九套方法论的平均值当成答案——路线之间是**互斥选择**（尤其调色盘 vs 人物生境），不是叠加。
- 不要在没跑 `60-quality` 清单前宣布卡"写好了"。
- 不要修改 `vendor/` 里的原文（那是证据源）；要改就改 `references/`。
