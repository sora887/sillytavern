# Character Card Skills

面向 **SillyTavern 与 BrainDance/taberna** 的中文角色卡创作技能：从人物、开场白到世界书、状态与记忆，配套本地 JSON 查询和只读结构审计工具。支持校园及其他题材。

**English:** Chinese-language agent skills for authoring and revising SillyTavern and BrainDance/taberna character cards and world books (lorebooks). Includes writing guides, local JSON queries, and read-only structural audits using the Python standard library.

[安装](#安装) · [使用示例](#使用示例) · [参考指南](#参考指南) · [安全边界](SECURITY.md) · [文档索引 / llms.txt](llms.txt)

- [campus-card-skill](skills/campus-card-skill/SKILL.md)：创作主入口，涵盖人物、开场、世界书、状态和记忆，支持校园及其他题材。
- [world-book-skill](skills/world-book-skill/SKILL.md)：ST 兼容入口，复用主技能的指南。

## 安装

将 `skills/` 下的两个目录一起复制到目标工具的技能目录，保持同级；项目内可放入 `.agents/skills/`。这两项是项目技能，只有文件所在的项目环境才能使用该安装。仓库中的 `skills/` 是分发目录，上传 GitHub 本身不会将技能安装到其他项目。

使用 `$campus-card-skill` 或 `$world-book-skill` 并说明目标卡文件和需求。所有 Python 工具只依赖标准库；验证环境为 Python 3.12。

## 使用示例

在支持这些技能的代理环境中，指定自己的卡文件与改动范围：

```text
使用 $campus-card-skill 检查 ./card.json 的人物动机与开场白。
先指出不一致之处，再按我的要求修改，保留其他字段和条目 ID。
```

也可以直接从仓库根目录运行 CLI，无需模型或 API 密钥。`card.json` 与 `worldbook.json` 为你提供的本地文件：

```sh
# 检查 ST / taberna 角色卡或独立 ST 世界书的结构
python skills/campus-card-skill/scripts/card-audit.py card.json

# 查看独立 ST 世界书的条目概览或搜索指定内容
python skills/campus-card-skill/scripts/query.py worldbook.json --brief
python skills/campus-card-skill/scripts/query.py worldbook.json --search "图书馆"
```

想先验证查询工具，可将以下**最小演示数据**保存为 `worldbook.json`，然后运行上面的 `--brief` 命令。这只是一个世界书条目，不是完整角色卡，也不是平台导入效果展示：

```json
{
  "entries": {
    "0": {
      "uid": 0,
      "comment": "图书馆",
      "key": ["图书馆"],
      "content": "图书馆每天 20:00 闭馆。"
    }
  }
}
```

审计只检查本地数据结构与部分内容特征；通过不等于平台导入成功、触发行为正确或长聊稳定。

## 参考指南

| 任务 | 入口 |
|---|---|
| 人设、开场与互动场景 | [创作流程](skills/campus-card-skill/references/writing-guide.md) · [角色与开场](skills/campus-card-skill/references/character-card-guide.md) |
| 世界书、触发、递归与预算 | [ST 配置指南](skills/campus-card-skill/references/config-guide.md) |
| 关系变化与长聊延续 | [状态与记忆](skills/campus-card-skill/references/state-and-memory-guide.md) |
| BrainDance/taberna 格式与迁移 | [格式指南](skills/campus-card-skill/references/taberna-format-guide.md) |
| 交付前检查与平台试跑 | [验证方法](skills/campus-card-skill/references/validation-guide.md) |

## 能力与边界

可以创作、改稿和组织 JSON；附带 CLI 只读取用户指定的 JSON，不自动修改文件、不联网、不执行卡内代码。输入限制为 8 MiB。查询会展示卡内内容，分享结果前应检查隐私。

发布版已移除远程 JavaScript、MVU/EJS/动态 HTML 示例、旧自动生成和写入工具，以及绕过安全约束的旧提示。引导页采用纯文本或 Markdown，不提供脚本按钮和动态面板。

## 验证

在仓库根目录运行：

```sh
python -m unittest discover -s skills/campus-card-skill/scripts -p "test_*.py"
python -m unittest discover -s tests -p "test_*.py"
```

范围和限制见 [SECURITY.md](SECURITY.md)。不包含私人角色作品、凭据、本机绝对路径或原项目提交历史。
