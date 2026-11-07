#!/usr/bin/env python3
"""Read-only structural audit. Not a platform validator, tokenizer or trigger engine."""
import argparse
import json
import re
import sys
from pathlib import Path


MAX_INPUT_BYTES = 8 * 1024 * 1024

STYLE_WORDS = ("一丝", "一缕", "一抹", "不易察觉", "弧度", "喉结", "纽扣",
               "指节发白", "似乎", "仿佛", "宛如", "——")


def audit(document, style="none"):
    report = {"format": "unknown", "errors": [], "warnings": [], "stats": {},
              "limitations": "Static subset only; chars are not tokens; no trigger/UI/model execution."}
    prose = []

    def issue(level, path, message):
        report[level].append({"path": path, "message": message})

    def error(path, message):
        issue("errors", path, message)

    def warn(path, message):
        issue("warnings", path, message)

    def text_field(obj, key, path, required=False):
        if key not in obj:
            if required:
                error(path + "." + key, "Missing text field")
            return ""
        value = obj[key]
        if not isinstance(value, str):
            error(path + "." + key, "Expected string")
            return ""
        prose.append((path + "." + key, value))
        return value

    if not isinstance(document, dict):
        error("$", "Expected JSON object")
        return report

    category_ids = set()
    fixed_chars = 0
    if "braindance" in document:
        kind = report["format"] = "taberna"
        body = document["braindance"]
        if not isinstance(body, dict):
            error("$.braindance", "Expected object")
            return report
        entries = body.get("embeddedWorldBook", [])
        ep = "$.braindance.embeddedWorldBook"
        for key in ("systemPrompt", "jailbreakPrompt", "prePrompt", "outputFormat"):
            fixed_chars += len(text_field(body, key, "$.braindance"))
        for key in ("title", "summary", "description", "firstMessage", "greeting"):
            text_field(body, key, "$.braindance")
        categories = body.get("embeddedWorldBookCategories", [])
        if not isinstance(categories, list):
            error("$.braindance.embeddedWorldBookCategories", "Expected array")
            categories = []
        for i, cat in enumerate(categories):
            cp = f"$.braindance.embeddedWorldBookCategories[{i}]"
            if not isinstance(cat, dict) or not isinstance(cat.get("id"), str) or not cat["id"]:
                error(cp, "Category needs a nonempty string id")
            elif cat["id"] in category_ids:
                error(cp, "Duplicate category id")
            else:
                category_ids.add(cat["id"])
        desc = body.get("description", "")
        if isinstance(desc, str) and re.search(r"<(?:div|style|script|html)\b", desc, re.I):
            if body.get("renderMode") != "html":
                warn("$.braindance.renderMode", "HTML description without html mode in local profile")
    elif document.get("spec") in ("chara_card_v2", "chara_card_v3"):
        kind = report["format"] = document["spec"]
        body = document.get("data")
        if not isinstance(body, dict):
            error("$.data", "Expected object")
            return report
        for key in ("description", "personality", "scenario", "system_prompt", "post_history_instructions"):
            fixed_chars += len(text_field(body, key, "$.data"))
        for key in ("name", "first_mes", "mes_example"):
            text_field(body, key, "$.data")
        greetings = body.get("alternate_greetings", [])
        if not isinstance(greetings, list) or not all(isinstance(x, str) for x in greetings):
            error("$.data.alternate_greetings", "Expected array of strings")
        else:
            prose.extend((f"$.data.alternate_greetings[{i}]", x) for i, x in enumerate(greetings))
        book = body.get("character_book", {})
        if not isinstance(book, dict):
            error("$.data.character_book", "Expected object")
            return report
        entries = book.get("entries", [])
        ep = "$.data.character_book.entries"
    elif "entries" in document:
        kind = report["format"] = "st-worldbook"
        entries = document["entries"]
        ep = "$.entries"
    else:
        error("$", "Unsupported wrapper; expected taberna, ST v2/v3 or standalone ST worldbook")
        return report

    if isinstance(entries, dict) and kind == "st-worldbook":
        items = [(f"{ep}[{json.dumps(k, ensure_ascii=False)}]", v) for k, v in entries.items()]
    elif isinstance(entries, list):
        items = [(f"{ep}[{i}]", v) for i, v in enumerate(entries)]
    else:
        error(ep, "Expected entry array (standalone ST also accepts object)")
        return report

    seen_ids, seen_content = set(), {}
    active_chars = constant_chars = conditional_chars = disabled = 0
    for path, entry in items:
        if not isinstance(entry, dict):
            error(path, "Expected entry object")
            continue
        content = text_field(entry, "content", path, required=True)
        if not content.strip():
            warn(path + ".content", "Empty content")
        elif content in seen_content:
            warn(path + ".content", "Duplicate of " + seen_content[content])
        else:
            seen_content[content] = path
        for key in ("enabled", "disable", "constant"):
            if key in entry and not isinstance(entry[key], bool):
                error(path + "." + key, "Expected boolean")
        enabled = entry.get("enabled", True) is not False and entry.get("disable", False) is not True
        ext = entry.get("extensions", {})
        if not isinstance(ext, dict):
            error(path + ".extensions", "Expected object")
            ext = {}
        probability = entry.get("probability", ext.get("probability"))
        if probability is not None and (type(probability) not in (int, float) or not 0 <= probability <= 100):
            error(path + ".probability", "Expected number from 0 through 100")
        depth = entry.get("scanDepth", ext.get("scan_depth", ext.get("scanDepth")))
        if depth is not None and (type(depth) is not int or depth < 0):
            error(path + ".scanDepth", "Expected nonnegative integer or inherited null")

        if kind == "taberna":
            expr = entry.get("triggerExpression", "")
            if not isinstance(expr, str):
                error(path + ".triggerExpression", "Expected string")
                expr = ""
            if enabled and not expr.strip():
                warn(path + ".triggerExpression", "No trigger; do not automatically convert to constant")
            # Only this exact local convention counts; arbitrary NOT is conditional.
            constant = expr.strip() == "NOT (__常驻__)"
            cat_id = entry.get("categoryId")
            if cat_id is None or cat_id == "":
                warn(path + ".categoryId", "Uncategorized entry")
            elif not isinstance(cat_id, str) or cat_id not in category_ids:
                error(path + ".categoryId", "Dangling or invalid category reference")
            for singular, plural in (("insertionPosition", "insertionPositions"), ("triggerArea", "triggerAreas")):
                if plural in entry and (not isinstance(entry[plural], list) or
                                        not all(type(x) is int for x in entry[plural])):
                    error(path + "." + plural, "Expected integer array")
                if plural not in entry:
                    warn(path + "." + plural, "Missing plural field used by local export profile")
            positions = entry.get("insertionPositions")
            if isinstance(positions, list) and "insertionPosition" in entry and entry["insertionPosition"] not in positions:
                warn(path + ".insertionPositions", "Singular position absent from plural positions")
        else:
            constant = entry.get("constant", False) is True
            id_key = "uid" if kind == "st-worldbook" else "id"
            identity = entry.get(id_key)
            if identity is not None:
                if type(identity) not in (str, int):
                    error(path + "." + id_key, "Expected string or integer ID")
                elif (type(identity).__name__, identity) in seen_ids:
                    error(path + "." + id_key, "Duplicate entry ID")
                else:
                    seen_ids.add((type(identity).__name__, identity))
            keys = entry.get("key", entry.get("keys", []))
            if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
                error(path + ".keys", "Expected keyword array of strings")
            elif enabled and not constant and not keys:
                warn(path + ".keys", "No keyword: verify intentional vector/template/other activation")

        if enabled:
            active_chars += len(content)
            if constant:
                constant_chars += len(content)
            else:
                conditional_chars += len(content)
        else:
            disabled += 1

    report["stats"] = {"entries": len(items), "disabled_entries": disabled,
                       "fixed_prompt_field_chars": fixed_chars,
                       "enabled_entry_chars": active_chars,
                       "constant_candidate_chars": constant_chars,
                       "conditional_candidate_chars": conditional_chars,
                       "counting_note": "Raw text before rendering; enabled does not mean injected. Probability/budget not evaluated."}
    if style == "bai-miao":
        candidates = []
        for path, value in prose:
            # Drop HTML code blocks for triage; do not claim a full HTML parser.
            value = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", "", value, flags=re.I | re.S)
            for word in STYLE_WORDS:
                count = value.count(word)
                if count:
                    candidates.append({"path": path, "term": word, "count": count})
        report["style_candidates"] = candidates
        report["style_note"] = "Review in context; quotes, examples and legitimate uses are not automatic failures."
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    parser.add_argument("--style", choices=("none", "bai-miao"), default="none")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if str(args.card).startswith(("//", "\\\\")):
            raise ValueError("Network paths are not accepted")
        if not args.card.is_file():
            raise ValueError("Expected a local file")
        with args.card.open("rb") as stream:
            payload = stream.read(MAX_INPUT_BYTES + 1)
        if len(payload) > MAX_INPUT_BYTES:
            raise ValueError("Input exceeds size limit")
        document = json.loads(payload.decode("utf-8-sig"))
    except (OSError, UnicodeError, ValueError, RecursionError):
        print(json.dumps({"errors": [{"path": "$", "message": "Cannot read local JSON (maximum 8 MiB)."}]}, indent=2))
        return 2
    report = audit(document, args.style)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
