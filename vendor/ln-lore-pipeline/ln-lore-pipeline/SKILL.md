---
name: ln-lore-pipeline
description: 轻小说/web小说全本项目流水线：全文清洗标注→角色语料分析→AI知识库→事件年表→SillyTavern世界书(共通+角色专属)→角色卡(V2/PNG)→十维审查→断言式修复→酒馆发布。当用户提到 轻小说 角色卡 世界书 年表 语料清洗 SillyTavern tavern character card worldbook lore timeline 校验 审查 异名 剧透管控 PNG注入 时使用本技能。适用于把一部小说全本转化为可导入酒馆的完整卡书体系，或对既有卡书做全面校验修复。不适用于非轻小说语料的正典库构建（通用/长篇小说走 cbb-pipeline）。
license: CC-BY-4.0 (content)
compatibility: 需 Python 3.10+（Windows 用 py 启动器）；脚本涉及 JSON/PNG 字节操作，无需联网
metadata:
  author: misdeep-pipeline
  version: "1.2"
  origin: 《异世界迷宫最深部为目标》项目全流程实战沉淀（2026-09）
agent_created: true
---
# 轻小说卡书全流程流水线（ln-lore-pipeline）

把一部轻小说全本，从原文转化为「可导入 SillyTavern 的角色卡＋世界书＋年表」完整体系，并配备审查与修复工程学。本技能来自一个 37 角色、37 本世界书、12 章语料项目的完整实战，每条规则都有事故背书。

## 使用边界（触发校准）

- 触发：web 轻小说/文库本全本流水线（清洗→角色分析→年表→ST 世界书/角色卡）→ 用本技能
- 不触发：通用小说正典库 → cbb-pipeline；单篇文档 → 直接处理

## 何时使用
- 新项目：拿到小说全本文本，要建卡/书/年表
- 存量项目：已有卡和书，要做全面校验、异名治理、泄底审查、修复
- 发布：生成酒馆可导入的 PNG 卡、世界书 JSON、合并审查文件

## 目录地图（按需读取，勿一次全读）

| 文件 | 内容 | 何时读 |
|---|---|---|
| [references/stage-guide.md](references/stage-guide.md) | 阶段1~6：语料层/分析/知识库/年表/世界书格式军规/角色卡写法 | 建设新内容时 |
| [references/review-system.md](references/review-system.md) | 阶段7：机械审计＋十维四对照审查＋典型问题模式＋外部吸收 | 做审查时 |
| [references/governance.md](references/governance.md) | 总则军规/判例治理/合并规格/子代理协议/特别设定通道 | 任何阶段开始前先读军规；治理决策时 |
| [references/publish.md](references/publish.md) | 阶段9：PNG注入/自动挂载/大统合卡/发布坑清单 | 发布交付时 |
| [references/git-governance.md](references/git-governance.md) | Git 版本治理：init/.gitignore 模板/批次双 commit/回滚/发布 tag | git 化工作区、批次提交、GitHub 发布时 |
| [references/checklists.md](references/checklists.md) | 五要素发现格式/审核门/红线速查/progress断点协议 | 审查与修复执行时 |
| [scripts/](scripts/) | audit_cards.py 机械审计、merge_review.py 合并文件、png_inject.py PNG注入 | 对应场景直接运行 |
| [assets/](assets/) | 角色卡/世界书模板、审查任务书模板 | 建新内容或派审查子代理时 |

## 流程路由

```
阶段0 摸底 ──→ 语料构成/卡书清单/格式识别 → 摸底报告（编号交付物）
阶段1 语料层 ──→ 清洗标注版(L号坐标系/block头/对白标注/说话人归属/译注隔离)
阶段2 分析  ──→ 场景块/角色证据包/归属定稿/画像量化(禁入活跃字段)
阶段3 知识库 ──→ 每角色双库(事实档案+台词库Q段位)
阶段4 年表  ──→ full_event_list/伏笔链/反转节点/QA审计/交付四件套
阶段5 世界书 ──→ 共通书 + 每角色专属书 uid0~9 十段结构 + 格式军规九条
阶段6 角色卡 ──→ V2七字段 + 防串线 + PI红线(隐瞒≠泄底遮羞布)
阶段7 审查  ──→ 机械审计脚本 + 子代理十维四对照 + P0/P1/P2 + 五要素
阶段8 修复  ──→ 报告先审后改 → 断言式/幂等/冻结字段落盘 → 双层复检
阶段9 发布  ──→ PNG注入 + character_book自动挂载 + 大统合 + WI原生格式兜底
治理(贯穿) ──→ 判例集/异名统合表/审查合并文件/批次文档/记忆回写
```

## 核心纪律（十三军规精要，全文见 governance.md）

1. **语料只读**——证据层永不修改；误写登记备查
2. **三源对照**——卡↔书↔语料至少两源比对；严禁以书反推原文（防循环论证）
3. **断言式+幂等修改**——替换前断言命中数；内存构建、断言全过才落盘；失败即零写入
4. **引文逐字**——「」台词不润色不拼接不改归属；例外仅限判例定案
5. **判例积累**——每项裁定入判例集，后续照表执行禁止重裁
6. **冻结字段**——批量修复明列冻结清单，落盘后逐字段比对
7. **P0/P1/P2 分级**——P0=事实错误/泄底/串线；标准全项目统一并传递给子代理
8. **批次文档**——每批 `_bN*_调度_日期\`：prompts txt 固化＋results 归档＋汇总 md＋基线快照
9. **子代理运行方式不预设、过程中动态决定**——综合任务性质/前序产出/当前环境随时切换：后段依赖前段产出的工作（不限小说：剧情连贯、累积归纳、多轮递进）＝串行＋链式传递；对象互不依赖＝可并行探测。判定方法与切换规范见 references/governance.md
10. **报告先审后改**——批准前零修改；"肯定错误"与"人工决策"分档
11. **泄底门控**——后期揭示一律 disable 手动条目；常驻字段禁复刻禁用内容
12. **自主提案不入正式文件**——特别设定走提案→人工审核门（§13 通道）
13. **Git 版本治理**——批次前基线 commit、验收后成果 commit、发布打 tag；git 缺席时退化为快照目录制度（详见 references/git-governance.md）

## 快速开始

新项目：读 stage-guide.md 从阶段1顺序推进，每个阶段产物落盘并回写 progress.md。
校验存量：直接跑 `py scripts/audit_cards.py --cards <卡目录> --worldbook <书目录> --corpus <语料目录>`，再按 review-system.md 组建子代理深审。
发布：读 publish.md，用 png_inject.py / merge_review.py。

## 已知高危问题模式（来自实战，审查时优先排查）

- 常驻字段（scenario/personality/system_prompt）复刻世界书 disable 条目 → P0 最高频
- personality 例句引用 disable 台词 → 第二高频且极易漏审
- 事实错误：主语错置/归属反置/张冠李戴/主客颠倒 → 需语料直证，启发式抓不到
- scenario 400/420 字管道截断（生成期字段上限）
- 引号内措辞与原句不一致（改写后仍带引号）
- 统计残留（MATTR/Delta/LL）混入活跃字段
- L 号惯例偏移：标注 L 常落在引文前 1~3 行叙述行，±3 且说话人文字相符＝相符
- 精确替换失败先 repr() 查码点（引号形制/不可见字符），再退短锚点切片；详见 checklists.md §I