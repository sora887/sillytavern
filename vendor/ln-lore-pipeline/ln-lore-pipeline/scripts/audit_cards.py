#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_cards.py — 角色卡机械审计（只读）

检查项：BOM / JSON / spec / 必填字段 / 可疑宏 / depth_prompt /
       泄底启发式（世界书 disable 条目句在卡活跃字段）/ L号引文直核 / 异名变体扫描

用法：
  py audit_cards.py --cards <卡目录> --worldbook <世界书目录> --corpus <语料目录> \
      [--variants variants.json] [--book-prefix 角色专属世界书_] [--out report.txt]

variants.json 格式：{"组名": ["旧形1","旧形2",...], ...}  （如 {"西斯误写": ["希丝"]}）
语料格式：目录内 .md 文件，L 号＝章内行号（清洗标注版规范）。
"""
import argparse, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")

ACTIVE_FIELDS = ("description", "personality", "scenario", "first_mes",
                 "mes_example", "system_prompt", "post_history_instructions")
REQ_FIELDS = ["name", "description", "personality", "scenario", "first_mes",
              "mes_example", "system_prompt"]
STD_MACROS = {"char", "user", "random", "roll", "time", "date", "weekday", "lastusermessage"}


def find_book(wb_files, prefix, cname):
    """按 角色名 ↔ 书文件名 双向包含匹配（长名优先）。"""
    exact = f"{prefix}{cname}.json"
    if exact in wb_files:
        return exact
    cands = []
    for f in wb_files:
        short = f[len(prefix):-5] if f.startswith(prefix) else f[:-5]
        if cname.endswith(short) or short.endswith(cname) or short in cname or cname in short:
            cands.append((len(short), f))
    cands.sort()
    return cands[0][1] if cands else None


def load_corpus(corpus_dir):
    """返回 {章名(文件名去扩展): [行,...]}"""
    corpus = {}
    for f in os.listdir(corpus_dir):
        if f.endswith(".md"):
            corpus[f[:-3]] = open(os.path.join(corpus_dir, f), encoding="utf-8", errors="replace").read().split("\n")
    return corpus


def check_l_citations(active, corpus):
    """「引文」（Lxxxx）→ 全语料章文件 L±4 行检索引文头 8 字。"""
    bad = []
    for m in re.finditer(r"「([^」]{6,60})」[^「」]{0,12}〔?L?（?L?(\d{3,5})）?", active):
        quote, L = m.group(1), int(m.group(2))
        head = quote[:8].replace("⋯", "").replace("…", "")
        if len(head) < 6:
            continue
        found = False
        for lines in corpus.values():
            if len(lines) < L:
                continue
            for i in range(max(0, L - 4), min(len(lines), L + 4)):
                if head in lines[i].replace("⋯", "…"):
                    found = True
                    break
            if found:
                break
        if not found:
            bad.append(f"L{L}:{quote[:14]}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", required=True)
    ap.add_argument("--worldbook", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--variants", default=None, help="异名组 json：{组:[旧形...]}")
    ap.add_argument("--book-prefix", default="角色专属世界书_")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    variants = json.load(open(args.variants, encoding="utf-8")) if args.variants else {}
    corpus = load_corpus(args.corpus) if os.path.isdir(args.corpus) else {}
    wb_files = [f for f in os.listdir(args.worldbook) if f.endswith(".json")]
    out_lines = []

    def P(s=""):
        out_lines.append(s)

    for f in sorted(os.listdir(args.cards)):
        if not f.endswith(".json"):
            continue
        p = os.path.join(args.cards, f)
        raw = open(p, "rb").read()
        issues = []
        if raw.startswith(b"\xef\xbb\xbf"):
            issues.append("P1 BOM 存在")
        try:
            d = json.loads(raw.decode("utf-8-sig"))
        except Exception as e:
            P(f"[{f}] JSON 解析失败: {e}")
            continue
        data = d.get("data", {})
        if d.get("spec") != "chara_card_v2":
            issues.append(f"P1 spec={d.get('spec')}")
        missing = [k for k in REQ_FIELDS if not data.get(k)]
        if missing:
            issues.append(f"P2 缺字段 {missing}")
        full = json.dumps(d, ensure_ascii=False)
        badm = [m for m in re.findall(r"\{\{([^}]+)\}\}", full)
                if m.strip().lower() not in STD_MACROS]
        if badm:
            issues.append(f"P1 可疑宏 {{{{{badm[0]}}}}} 等×{len(badm)}")
        if "extensions" in data and "depth_prompt" not in data["extensions"]:
            issues.append("P2 无 depth_prompt")
        # 泄底启发式 + L 号直核（仅当能配到书/有语料）
        active = "".join(str(data.get(k, "")) for k in ACTIVE_FIELDS)
        bname = find_book(wb_files, args.book_prefix, data.get("name", ""))
        if bname:
            try:
                wd = json.loads(open(os.path.join(args.worldbook, bname), "rb").read().decode("utf-8-sig"))
                ents = wd.get("entries", [])
                items = ents.values() if isinstance(ents, dict) else ents
                for e in items:
                    if not e.get("disable"):
                        continue
                    body = re.sub(r"<!--.*?-->", "", e.get("content", ""), flags=re.S)
                    for sent in re.split(r"[。\n]", body):
                        s = sent.strip().strip("「」『』“”\"")
                        if len(s) >= 14 and s in active:
                            issues.append(f"P0 活跃字段疑似复述禁用条目 uid{e.get('uid')}: {s[:18]}…")
                            break
            except Exception:
                pass
        if corpus:
            bad = check_l_citations(active, corpus)
            if bad:
                issues.append(f"P2 L号引文未直核×{len(bad)}: {'；'.join(bad[:3])}")
        # 异名变体
        for grp, forms in variants.items():
            n = full.count(grp) if False else sum(full.count(x) for x in forms)
            if n:
                issues.append(f"变体[{grp}] ×{n}（对照统合表判性：叙述→改/引文标注→保留）")
        P(f"[{f[:-5]}] " + ("；".join(issues) if issues else "—"))

    report = "\n".join(out_lines)
    print(report)
    if args.out:
        open(args.out, "w", encoding="utf-8", newline="\n").write(report + "\n")
        print(f"\n已写入 {args.out}")


if __name__ == "__main__":
    main()
