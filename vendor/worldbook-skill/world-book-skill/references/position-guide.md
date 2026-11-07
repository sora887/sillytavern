# Position Reference

Sourced from SillyTavern `public/scripts/world-info.js:855-864`.

| Value | Label | JS Constant | Description |
|-------|-------|-------------|-------------|
| 0 | ↑Char | `world_info_position.before` | 角色定义之前 — Before character definitions |
| 1 | ↓Char | `world_info_position.after` | 角色定义之后 — After character definitions |
| 2 | ↑AT | `world_info_position.ANTop` | Author's Note 之前 — Before Author's Note |
| 3 | ↓AT | `world_info_position.ANBottom` | Author's Note 之后 — After Author's Note |
| 4 | @D | `world_info_position.atDepth` | 指定深度处 — At specific depth in chat |
| 5 | ↑EM | `world_info_position.EMTop` | 示例消息之前 — Before Example Messages |
| 6 | ↓EM | `world_info_position.EMBottom` | 示例消息之后 — After Example Messages |
| 7 | Outlet | `world_info_position.outlet` | 输出到指定 Outlet — Requires `--outlet-name` |

## Recommended usage

| Entry type | Position | Reason |
|------------|----------|--------|
| 世界观总纲、背景设定、社会规则 | 0 (↑Char) | AI needs world framework before character info |
| 角色速览 (multi-character) | 0 (↑Char) | Macro-level: what characters exist |
| 角色详细信息 (all) | 1 (↓Char) | Supplements character description, placed after it |
| NPC 详情 | 1 (↓Char) | Supports character details, keyword-triggered |
| 场景/事件/物品 | 1 (↓Char) | Specific details, keyword-triggered |
| 写作规范/指导 | 2 (↑AT) | Writing rules injected into system prompt area |
| 二次解释 (behavior correction) | 4 (@D, depth=0) | Last thing AI reads → strongest influence. role=system |
| 格式要求 for examples | 5 (↑EM) or 6 (↓EM) | Wraps example messages |

## What NOT to do

- **Never use D1/D2/D3+ (@D with depth >= 1)**: inserting content between chat messages breaks conversation flow and confuses the AI
- **D0 only for behavior guidance, not for settings**: D0 is for direct instructions like "when X happens, do Y", not for worldbuilding lore
- **All entries must have recursion prevention**: use `--prevent-recursion` for every entry

## Notes

- When using position 7 (Outlet), `--outlet-name` is required
- The `@D` position uses the entry's `depth` value to determine insertion point
- `role` field matters for `@D`: use `--role 0` (system) for D0 behavior instructions
