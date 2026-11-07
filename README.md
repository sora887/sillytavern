# tavern-card · 酒馆角色卡工作台

一个把「写 SillyTavern 角色卡」变成有流程、有闸门、有验收的工程活技能包。

合并了九个开源写卡技能包的方法论，去重后写成 7 份可执行参考；上游原文全量留档，每条规则都能反查到出处。

```
SKILL.md                  入口：路线判定 + 四条红线 + 审美基准
references/
  00-routes.md            任务路由 + 四道闸门
  10-worldbook.md         世界书：分条粒度 / 双递归 / position 两派 / 泄底门控
  20-character.md         人设：调色盘路线 vs 人物生境路线（互斥）
  30-opening.md           开场白：形式分类 / 钩子 / 5 组正反改写
  40-mvu-regex-ejs.md     MVU 变量 / 正则闸门 / EJS / 状态栏
  50-format.md            v2 JSON / v3 PNG 字段表 · 编译与拆包
  60-quality.md           49 行硬伤清单 · 反 AI 味 · 十维审查
scripts/                  打包 / 检查 / 拆包 / 查重 / 封面文字
vendor/                   九个上游仓库原文镜像（30 MB，一字未改）
examples/                 成品卡示例：苏茧 · 补衣
```

## 安装

**DSH（DeepSeek Harness）**

skill 的发现深度是 **1 层**，所以要把内容放进技能目录本身，不能把仓库当子目录丢进去：

```powershell
git clone --depth 1 https://github.com/sora887/sillytavern "$env:USERPROFILE\.dsh\skills\tavern-card"
```

**Claude Code / Cursor / Codex**

```bash
git clone --depth 1 https://github.com/sora887/sillytavern ~/.claude/skills/tavern-card
```

装完对 AI 说「写张卡」即可触发；也可以直接说「读 SKILL.md 和 references/00-routes.md，按里面的闸门走」。

## 怎么用

它不是一个「一键出卡」的模板，是一套**会拦你的流程**：

1. **判路线** — 新建完整卡 / 世界书优先 / 存量卡改造 / 局部变体，读 `00-routes.md` 定档。
2. **过闸门 0** — 锁定体裁、玩家位置、人物核心矛盾、技术档位、交付形态。
3. **过闸门 1** — 先交 `design-spec.md`（只有决策，没有正文），你点头才动笔。
4. **分批写** — 人设 → 世界书 → 开场白 → 变量/状态栏 → 示例对话 → 打包，每批停一次。
5. **过闸门 3** — 跑硬伤清单，`check_card.py` 报 0 错误才算完。

交付状态只用这几个标签，不许含糊：

```
SPEC → CARD-PENDING → CARD-BUILT → CHECK-PASSED → USER-APPROVED
```

## 工具

```bash
python scripts/build_card.py   <项目目录>            # project → 完备卡 JSON/PNG
python scripts/check_card.py   <卡.json>             # 30+ 条硬伤检查
python scripts/extract_card.py <卡.json|卡.png>      # 拆包成可编辑项目
python scripts/scan_duplicates.py <项目目录>          # 条目级查重
python scripts/apply_cover_text.py                    # 封面文字（唯一需要 Pillow）
```

打包脚本主体只用标准库；只有封面文字脚本需要 `pip install pillow`。

## 示例卡

`examples/苏茧-补衣.json` — 纯文本卡，12 条世界书（1 条常驻 + 2 条深度触发），`check_card.py` 错误 0 项。设计说明见同目录 md，里面有命题、信息分工表、技术选型和验收记录。

## 来源

方法论合并自以下仓库，原文镜像在 `vendor/`，每份参考都在文末列了对应的源文件路径：

| 仓库 | 主要贡献 | 许可 |
|---|---|---|
| [echo-xianyu/worldbook-skill](https://github.com/echo-xianyu/worldbook-skill) | 世界书体系、XML 包 YAML、CLI | CC BY-NC-SA |
| [LiarMTTT/TavernWeave](https://github.com/LiarMTTT/TavernWeave) | 正则契约、前端与运行时 | 非商用 |
| [yukk4159-bit/charcard-workshop](https://github.com/yukk4159-bit/charcard-workshop) | 设计→条目的两段式框架 | MIT |
| [Wallslqq/moyu-cards](https://github.com/Wallslqq/moyu-cards) | 墨月写卡：调色盘 / 人物生境 / 开场白 | 未声明 |
| [Pra-Moon/sillytavern-card-maker](https://github.com/Pra-Moon/sillytavern-card-maker) | 格式规范、CLI 工具链、硬伤检查 | MIT |
| [foreverse-app/character-card-skills](https://github.com/foreverse-app/character-card-skills) | 反 AI 味、盲测实验 | Other |
| [wenyu1123/deepseek-harness-card-skills](https://github.com/wenyu1123/deepseek-harness-card-skills) | 状态面板、世界书审计 | MIT |
| [master666-max/ln-lore-pipeline](https://github.com/master666-max/ln-lore-pipeline) | 长文本→卡、泄底门控、审查 | MIT |
| [Marco0431/character-card-skills](https://github.com/Marco0431/character-card-skills) | 校园/日常向指南 | MIT |

`vendor/` 里保留各家原始 LICENSE / NOTICE。合并部分以 MIT 精神提供，供学习与自用；第三方内容的授权条件各自为准，商业使用前请回到原仓库确认。

## 两条不妥协

- **不虚构**：不声称读过没读的文件、跑过没跑的脚本、检查过没检查的卡。
- **不让 AI 自己给自己打分当验收**：LLM 当裁判的自洽率远高于正确率，最终验收是「实际聊一轮」。
