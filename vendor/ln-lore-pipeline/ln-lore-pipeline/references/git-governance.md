# Git 版本治理（把手工快照/备份/版本命名全部交给 git）

> 实战教训：本方法论第一版用 `_backup_*` 目录＋`Bn后_` 版本命名＋基线快照 json 手工实现版本治理——
> 这正是 git 的本职工作。新项目从阶段0 起直接 git 化；存量项目按下文"存量接手"补化。

## 一、初始化（阶段0 一次性）

1. 在工作区根 `git init -b main`（语料层/知识库/产出物一并纳管；git 只读不改文件，与"语料只读"军规无冲突）。
2. 写 `.gitignore`（模板见 assets/gitignore_template）：
   - 排除大体积二进制：插画目录、角色配图初筛池、PNG 成品目录（发布物走 Release 不走 git）
   - 排除临时物：`__pycache__/`、`_tmp_*`、`*.log`、`_tools/`（绿色 exe）
   - 排除 `_backup_*/`（git 化后手工备份目录冗余；保留亦可）
   - 保留：全部 md/json/yaml/txt/docx（知识资产）、脚本、模板
3. 首次提交＝**基线 commit**（message 标明"基线：阶段0 摸底后"）。

## 二、批次纪律（每个 Bn 批次两个 commit）

| 时点 | 动作 | message 示例 |
|---|---|---|
| 批次开始 | 基线 commit（或确认工作区干净） | `b18: 批次基线（13● 预检通过）` |
| 断言验收全过后 | 成果 commit | `b18: 修书 13 项落地（终扫清零，37/37 绿）` |

- **回滚＝`git checkout`/`git revert`**，取代手工快照目录
- **审查合并文件**照常生成，但 SHA256 之外 git 自带内容寻址；`Bn后_` 版本命名可同时保留作人类可读标记，并 `git tag b18` 对齐
- **报告先审后改**：修复 commit 在用户批准后才做——批准前的修改留在工作区 unstaged，`git diff` 即审阅材料

## 三、发布（阶段9）

- 发布物打 tag：`git tag v1.0 && git push --tags`
- 有 gh CLI：`gh release create v1.0 发布物.zip --notes …`（附 zip，网页零操作）
- 无 gh：手动在 GitHub 网页 Release 区上传 zip

## 四、存量项目 git 化（接手时补做）

1. 同"初始化"，基线 commit 前先跑一遍全绿断言（确认当前态值得当基线）
2. 历史 `_backup_*` 目录保留在 .gitignore 外或内均可（git 化后它们仅是死重，建议 ignore）
3. 接管协议（§11）相应加一条：接手时先 `git log --oneline | head` 看批次历史，再读批次汇总 md

## 五、注意事项

- 路径含中文/全角字符：git 完全支持；若 `git status` 显示转义码，`git config --global core.quotepath false`
- 大仓库（全本小说＋全部知识库）首次 commit 可能数十秒~分钟级，正常
- 子代理只做文件修改，**git 操作集中在主代理**（避免并发 add/commit 冲突）
- git 缺席的极端环境：退回快照目录制度（本方法论 v1.0 的做法）
