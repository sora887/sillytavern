#!/usr/bin/env python3
"""
世界书查询工具
输出结构兼容 world-book-create.py 的输入格式。
- 默认模式：输出所有条目摘要（名称、内容预览、长度、触发词、位置等）
- --uid N：输出指定条目的完整 JSON（与 create.py 写入格式一致，可直接用于 --batch-edit）
- --search：按关键词搜索条目
- --resolve：解析条目的 @UID/@名称 嵌套引用
- --brief：极简模式
"""

import argparse
import json
import os
import sys
import re

POSITION_LABELS = {
    0: "↑Char",
    1: "↓Char",
    2: "↑AT",
    3: "↓AT",
    4: "@D",
    5: "↑EM",
    6: "↓EM",
    7: "Outlet",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_worldbook(path):
    if not os.path.exists(path):
        print(f"错误: 文件不存在 - {path}", file=sys.stderr)
        sys.exit(1)
    book = load_json(path)
    entries = book.get("entries", {})
    name = book.get("name", None)
    return book, entries, name


def build_summary(uid_str, entry):
    content = entry.get("content", "")
    return {
        "uid": int(uid_str),
        "comment": entry.get("comment", ""),
        "content_length": len(content),
        "content_preview": content[:80] + "..." if len(content) > 80 else content,
        "keys": entry.get("key", []),
        "position": entry.get("position", 0),
        "position_label": POSITION_LABELS.get(entry.get("position", 0), str(entry.get("position", "?"))),
        "constant": entry.get("constant", False),
        "order": entry.get("order", 0),
        "depth": entry.get("depth", 1),
        "scanDepth": entry.get("scanDepth"),
        "selective": entry.get("selective", False),
        "preventRecursion": entry.get("preventRecursion", False),
        "excludeRecursion": entry.get("excludeRecursion", False),
        "disable": entry.get("disable", False),
    }


def search_entries(entries, keyword):
    keyword_lower = keyword.lower()
    results = {}
    for uid_str, entry in entries.items():
        comment = entry.get("comment", "").lower()
        content = entry.get("content", "").lower()
        keys = [k.lower() for k in entry.get("key", [])]

        if keyword_lower in comment or keyword_lower in content or any(keyword_lower in k for k in keys):
            results[uid_str] = entry
    return results


def resolve_refs(entries):
    uid_map = {}
    name_map = {}
    for uid_str, entry in entries.items():
        uid_map[int(uid_str)] = entry
        comment = entry.get("comment", "")
        if comment:
            name_map[comment] = int(uid_str)

    refs = {}
    for uid_str, entry in entries.items():
        content = entry.get("content", "")
        comment = entry.get("comment", "")
        found_refs = []
        for match in re.finditer(r'@(\d+|[^\s\n,，。；;、\u3000\]\)]+)', content):
            ref = match.group(1)
            if ref.isdigit():
                ref_uid = int(ref)
                if ref_uid in uid_map:
                    found_refs.append({
                        "reference": f"@{ref}",
                        "resolved_uid": ref_uid,
                        "resolved_comment": uid_map[ref_uid].get("comment", ""),
                    })
                else:
                    found_refs.append({
                        "reference": f"@{ref}",
                        "resolved_uid": None,
                        "resolved_comment": None,
                        "valid": False,
                    })
            else:
                if ref in name_map:
                    found_refs.append({
                        "reference": f"@{ref}",
                        "resolved_uid": name_map[ref],
                        "resolved_comment": ref,
                    })
                else:
                    found_refs.append({
                        "reference": f"@{ref}",
                        "resolved_uid": None,
                        "resolved_comment": None,
                        "valid": False,
                    })

        if found_refs:
            refs[uid_str] = {
                "uid": int(uid_str),
                "comment": comment,
                "references": found_refs,
            }

    return refs


def main():
    parser = argparse.ArgumentParser(
        description="世界书查询工具 - 输出结构兼容 world-book-create.py 的输入格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看所有条目摘要
  python query.py my_book.json

  # 查看指定条目的完整信息（输出可直接用于 --batch-edit）
  python query.py my_book.json --uid 3

  # 搜索关键词
  python query.py my_book.json --search "林小雨"

  # 解析嵌套引用
  python query.py my_book.json --resolve

  # 极简总览（含配置字段）
  python query.py my_book.json --brief
        """,
    )

    parser.add_argument("worldbook", help="世界书 JSON 文件路径")
    parser.add_argument("--uid", type=int, help="查看指定 UID 条目的完整信息")
    parser.add_argument("--search", help="搜索关键词（匹配标题/内容/触发词）")
    parser.add_argument("--resolve", action="store_true", help="解析条目的 @UID/@名称 嵌套引用")
    parser.add_argument("--brief", action="store_true", help="极简模式（含配置字段）：输出 uid/comment/content_length/keys/constant/preventRecursion/excludeRecursion")

    args = parser.parse_args()

    book, entries, name = load_worldbook(args.worldbook)

    if not entries:
        print("[]")
        return

    # --uid 模式：输出指定条目的完整 JSON
    if args.uid is not None:
        uid_str = str(args.uid)
        if uid_str not in entries:
            print(f"错误: 未找到 UID={args.uid} 的条目", file=sys.stderr)
            sys.exit(1)
        entry = dict(entries[uid_str])
        entry["uid"] = int(uid_str)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return

    # --resolve 模式：解析嵌套引用
    if args.resolve:
        refs = resolve_refs(entries)
        if not refs:
            print("未发现嵌套引用")
        else:
            result = {
                "worldbook": os.path.abspath(args.worldbook),
                "name": name,
                "references": list(refs.values()),
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # --search 模式：搜索并输出摘要
    if args.search:
        target_entries = search_entries(entries, args.search)
        if not target_entries:
            print(f"未找到匹配 '{args.search}' 的条目")
            return
        entries = target_entries

    # 默认 / --search / --brief 模式：输出摘要
    if args.brief:
        summary_list = []
        for uid_str in sorted(entries.keys(), key=int):
            e = entries[uid_str]
            summary_list.append({
                "uid": int(uid_str),
                "comment": e.get("comment", ""),
                "content_length": len(e.get("content", "")),
                "keys": e.get("key", []),
                "constant": e.get("constant", False),
                "preventRecursion": e.get("preventRecursion", False),
                "excludeRecursion": e.get("excludeRecursion", False),
            })
    else:
        summary_list = []
        for uid_str in sorted(entries.keys(), key=int):
            summary_list.append(build_summary(uid_str, entries[uid_str]))

    output = {
        "worldbook": os.path.abspath(args.worldbook),
        "name": name,
        "total_entries": len(summary_list),
        "entries": summary_list,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
