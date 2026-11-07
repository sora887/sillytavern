# taberna 格式与工具边界

依据是项目中 2026-08 的导出样例和当前构建脚本，**不是已核验的最新官方 schema**。遇到新导出，以原文件和目标平台测试更新兼容结论；保留未知字段，不为了满足旧检查器删除新字段。

## 本地已用结构

外层为 `version/ns/exportedAt/braindance`；内容在 `braindance`，包括 title、summary、description、renderMode、systemPrompt、prePrompt、outputFormat、assets、embeddedWorldBook、embeddedWorldBookCategories、firstMessage、greeting 等。

本地条目模板：

```json
{
  "content": "写明主体及设定",
  "enabled": true,
  "logic": 2,
  "triggerArea": 1,
  "triggerAreas": [3, 4],
  "scanDepth": 2,
  "insertionPosition": 1,
  "insertionPositions": [1],
  "insertionOrder": 50,
  "probability": 100,
  "triggerExpression": "修理铺 OR 店主",
  "categoryId": "已有分类ID"
}
```

这 12 字段是兼容样例，不要求集合永远恰好等于 12。布尔值、范围和分类引用需有效；单复数字段保留导出约定，不凭 ST 枚举解释数值。

## 触发与分类

项目样例使用 `A OR B` 关键词式；`NOT (__常驻__)` 配合 scanDepth=0 模拟常驻。普通关键词的 scanDepth=2 是当前项目默认，不是已证实的全平台强制值。

哨兵词只是低碰撞文本，用户或模型仍可输出它；它不是不可绕过的开关。`NOT (__格式关闭__)` 也不会自动理解自然语言“关闭格式”。真正关闭功能须让 UI/配置发出精确 token 或修改启用状态，并说明扫描窗口结束后是否恢复。

空表达式不要自动当作常驻：先判断是未配置、故意不触发还是原常驻丢失。复杂布尔式与正则不能简单替换成 OR 后宣称等价。

分类 ID 需存在且唯一，引用必须有效。分类名按题材，不强制“核心常驻/校园场景/人际纪律”。

## 引导页与编辑

本发布版只提供纯文本或 Markdown 引导内容，不加入可执行页面、脚本、模板或自动加载资源。现有卡若含 HTML/JS，不运行它，只记录内容与字段供用户审阅。

旧同步工具已经移除。更新 JSON 时使用稳定 ID 映射，并逐项检查差异；不要按正文前缀模糊覆盖条目，也不要把零概率改成默认值。

## 迁移验收

记录原 ID → 新条目的明确映射，复核启用、内容、触发、概率（含 0）、位置、顺序、扫描范围与分类。不支持的机制明确列出，不能静默丢弃。保留未知扩展，比较两次构建只应有预期变化。

`.taberna.json` 与普通 `.json` 可能是别名，也可能属于不同平台；先识别包装再决定是否同步。
