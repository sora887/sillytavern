#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_hygiene.py — 角色卡数据卫生检查

不是查"卡好不好玩"，是查"数据能不能正常跑"：
能导入 ≠ 数据干净。实测多张成熟卡里都有全角逗号关键词、残留测试条目、
非法 initvar JSON —— 它们能跑，但那些条目/触发器等于白写。

用法：
    python check_hygiene.py <卡.json | 世界书.json>
    python check_hygiene.py <项目目录>      # 自动找 worldbook.json / 输出/*.json

退出码：0 = 无错误；1 = 有错误。
"""
import json
import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ERROR, WARN, INFO = "错误", "警告", "信息"

BAD_SEP = ["，", "、", "；", ";", " ", "\t", "｜", "|"]
TEST_MARK = re.compile(r"测试|test\d|TODO|FIXME|临时|占位demo|复制粘贴|用过的例子")
INITVAR_HINT = re.compile(r"\. .*?: ,|:\s*,\s*$|\}\s*\"|[^,{]\s*\}$")


class Report:
    def __init__(self, name):
        self.name = name
        self.rows = []

    def add(self, level, where, msg, fix=""):
        self.rows.append((level, where, msg, fix))

    def emit(self):
        print(f"== 数据卫生检查：{self.name} ==")
        for level, where, msg, fix in self.rows:
            print(f"  [{level}] {where}：{msg}")
            if fix:
                print(f"         → {fix}")
        err = sum(1 for r in self.rows if r[0] == ERROR)
        war = sum(1 for r in self.rows if r[0] == WARN)
        inf = sum(1 for r in self.rows if r[0] == INFO)
        print(f"\n结果：[错误] {err} 项，[警告] {war} 项，[信息] {inf} 项")
        if err:
            print("有错误：这些条目/触发器上线后不会按预期工作。")
        elif war:
            print("没有致命错误，但有可疑项，建议逐条确认。")
        else:
            print("数据干净。")
        return 1 if err else 0


def load_entries(path):
    """返回 (display_name, entries, raw)。自动识别卡片 JSON / 世界书 JSON。"""
    raw = json.load(open(path, encoding="utf-8"))
    if isinstance(raw, dict) and isinstance(raw.get("data"), dict):
        data = raw["data"]
        name = data.get("name") or os.path.basename(path)
        cb = data.get("character_book") or {}
        return name, cb.get("entries") or [], raw
    if isinstance(raw, dict) and isinstance(raw.get("entries"), (dict, list)):
        name = raw.get("name") or os.path.basename(path)
        ents = raw["entries"]
        return name, list(ents.values()) if isinstance(ents, dict) else ents, raw
    raise SystemExit(f"无法识别为卡片或世界书：{path}")


def entry_name(e):
    return (e.get("comment") or e.get("name") or e.get("id") or "?")[:40]


def check_entries(rep, entries):
    seen_comments = {}
    const_chars = total_chars = 0
    disabled = 0
    rec_true = rec_false = 0

    for e in entries:
        nm = entry_name(e)
        keys = e.get("keys") or e.get("key") or []
        content = e.get("content") or ""
        enabled = e.get("enabled", not e.get("disable", False))
        ext = e.get("extensions") or {}
        total_chars += len(content)

        # 1. 关键词分隔符（const 条目不靠触发，只算观赏性问题）
        is_const = bool(e.get("constant"))
        for k in keys:
            for sep in BAD_SEP:
                if sep in k:
                    if is_const:
                        rep.add(INFO, f"关键词[{k[:24]}]",
                                f"含分隔符 {sep!r}，但本条 const=true，不影响触发",
                                "仅影响可读性，可改可不改")
                    else:
                        rep.add(ERROR, f"关键词[{k[:24]}]",
                                f"含分隔符 {sep!r}，整串会被当成一个关键词，永远命中不到",
                                "改用英文半角逗号把关键词拆成多个")
                    break
            if k != k.strip():
                rep.add(WARN, f"关键词[{k[:24]}]", "首尾有空格", "去掉多余空格")

        # 2. 空内容
        if not content.strip():
            rep.add(ERROR, f"条目[{nm}]", "content 为空", "补内容或删除条目")
        elif len(content.strip()) < 30 and not e.get("constant"):
            rep.add(INFO, f"条目[{nm}]", f"内容仅 {len(content.strip())} 字", "确认不是写了一半")

        # 3. initvar 是否禁用
        low = (nm + " " + content[:60]).lower()
        if "initvar" in low and enabled:
            rep.add(WARN, f"条目[{nm}]", "initvar 条目处于启用状态",
                    "初始变量条目应 disable=true，否则会被当正文读入")
        if "initvar" in low and INITVAR_HINT.search(content[:4000]):
            rep.add(WARN, f"条目[{nm}]", "疑似非法 JSON/YAML（空值或缺逗号）",
                    "导入前用解析器验证一遍，坏 JSON 会导致变量初始化失败")

        # 4. 测试残留
        if TEST_MARK.search(nm) or TEST_MARK.search(content[:120]):
            rep.add(WARN, f"条目[{nm}]", "疑似测试/临时残留", "发布前删除或改成正式内容")

        # 5. 常驻与递归口径
        if e.get("constant"):
            const_chars += len(content)
            if keys:
                rep.add(INFO, f"条目[{nm}]", "const=true 但仍写了 keys", "keys 此时只是注释，不参与触发")
            if not enabled:
                rep.add(WARN, f"条目[{nm}]", "const=true 但被禁用", "确认这是有意关闭的模块")
        if not enabled:
            disabled += 1
            if not re.search(r"手动条目|启用条件|DLC|扩展|可选", content[:300] + nm):
                rep.add(INFO, f"条目[{nm}]", "禁用条目未写明启用条件", "首行补 <!--【手动条目】启用条件：… -->")
        if ext.get("prevent_recursion") is True:
            rec_true += 1
        else:
            rec_false += 1

        # 6. 重复名（跨条拼 XML 的「起/止」对不算重复）
        bare_tag = re.fullmatch(r"\s*</?[A-Za-z_][\w\-.:]*\s*/?>\s*", content)
        if nm in seen_comments and not bare_tag and not seen_comments[nm]:
            rep.add(WARN, f"条目[{nm}]", "条目名重复", "同名条目难以区分，改名或合并")
        seen_comments[nm] = bool(bare_tag) or seen_comments.get(nm, False)

    # 7. 预算（按字数，不按条数）
    if total_chars:
        share = const_chars * 100 // total_chars
        rep.add(INFO, "常驻预算",
                f"常驻 {const_chars}/{total_chars} 字（{share}%），共 {len(entries)} 条，禁用 {disabled} 条")
        if share > 60:
            rep.add(WARN, "常驻预算", f"常驻字数占 {share}%，偏高",
                    "逐条问：这一条每轮真的都需要吗；见 references/15-card-archetypes.md §3")
    rep.add(INFO, "递归保护", f"prevent_recursion 开 {rec_true} 条 / 关 {rec_false} 条",
            "关掉不是错误，但要能说出理由（见 10-worldbook.md §1.1）")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    target = sys.argv[1]
    if os.path.isdir(target):
        cands = []
        for root, _, files in os.walk(target):
            for f in files:
                if f.endswith(".json") and ("worldbook" in f or "世界书" in f):
                    cands.append(os.path.join(root, f))
        if not cands:
            raise SystemExit(f"目录里没找到 worldbook.json / 世界书*.json：{target}")
        targets = cands
    else:
        targets = [target]

    rc = 0
    for t in targets:
        name, entries, _raw = load_entries(t)
        rep = Report(f"{name}（{os.path.basename(t)}）")
        if not entries:
            rep.add(WARN, "世界书", "没有任何条目", "确认卡是否漏打包")
        check_entries(rep, entries)
        rc |= rep.emit()
        print()
    return rc


if __name__ == "__main__":
    sys.exit(main())
