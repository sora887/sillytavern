#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""png_inject.py — 角色卡 JSON 注入 PNG（tEXt chara，酒馆标准）

流程：BOM 扫描 → 卡↔PNG 双射映射（规范化＋长名优先＋占用排除＋双射断言）
     → 备份原图 → 注入（IHDR 后插 tEXt，CRC 重算）→ 回读验证（逐字节比对）

用法：
  py png_inject.py --cards <卡json目录> --pngs <png目录> --backup <备份目录> \
      [--aliases aliases.json]

aliases.json：{"png短名": "卡全名key", ...}（映射兜底用，如 {"帕林库洛": "帕林库洛・勒迦希"}）
"""
import argparse, base64, json, os, shutil, struct, sys, zlib

sys.stdout.reconfigure(encoding="utf-8")


def norm(s, aliases):
    s = (s.replace("_card", "").replace(".png", "").replace(".json", ""))
    for a, b in aliases.items():
        s = s.replace(a, b)
    s = s.split("_")[0]                      # 去别名段（" _ 另一名"）
    return s.replace(" ", "").replace("　", "")


def parse_chunks(raw):
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "非 PNG"
    chunks, i = [], 8
    while i < len(raw):
        ln = struct.unpack(">I", raw[i:i + 4])[0]
        typ, data, crc = raw[i + 4:i + 8], raw[i + 8:i + 8 + ln], raw[i + 8 + ln:i + 12 + ln]
        assert zlib.crc32(typ + data) & 0xFFFFFFFF == struct.unpack(">I", crc)[0], "CRC 校验失败"
        chunks.append((typ, data))
        i += 12 + ln
        if typ == b"IEND":
            break
    return chunks


def build(chunks):
    out = b"\x89PNG\r\n\x1a\n"
    for typ, data in chunks:
        out += struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def extract_chara(raw):
    i = 8
    while i < len(raw):
        ln = struct.unpack(">I", raw[i:i + 4])[0]
        typ, data = raw[i + 4:i + 8], raw[i + 8:i + 8 + ln]
        if typ == b"tEXt" and data.startswith(b"chara\x00"):
            return base64.b64decode(data[6:])
        i += 12 + ln
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", required=True)
    ap.add_argument("--pngs", required=True)
    ap.add_argument("--backup", required=True)
    ap.add_argument("--aliases", default=None)
    args = ap.parse_args()
    aliases = json.load(open(args.aliases, encoding="utf-8")) if args.aliases and os.path.exists(args.aliases) else {}
    os.makedirs(args.backup, exist_ok=True)

    cards = sorted(f for f in os.listdir(args.cards) if f.endswith(".json"))
    pngs = sorted(f for f in os.listdir(args.pngs) if f.endswith(".png"))
    assert len(cards) == len(pngs), f"卡 {len(cards)} vs PNG {len(pngs)} 数量不一致"

    taken, mapping = set(), {}
    for c in sorted(cards, key=lambda x: len(norm(x, aliases)), reverse=True):
        key = norm(c, aliases)
        exact = [q for q in pngs if q not in taken and norm(q, aliases) == key]
        cand = exact or [q for q in pngs if q not in taken
                         and (key in norm(q, aliases) or norm(q, aliases) in key)]
        assert len(cand) == 1, f"映射失败: {c} -> {cand}"
        mapping[c] = cand[0]
        taken.add(cand[0])
    assert len(mapping) == len(cards)
    print(f"卡↔PNG 映射 {len(mapping)}/{len(cards)} 成立（双射断言通过）")

    ok = 0
    for c, png in mapping.items():
        cp, pp = os.path.join(args.cards, c), os.path.join(args.pngs, png)
        card_raw = open(cp, "rb").read()
        if card_raw.startswith(b"\xef\xbb\xbf"):
            card_raw = card_raw[3:]                      # 去 BOM（并回写源卡）
            open(cp, "wb").write(card_raw)
        raw = open(pp, "rb").read()
        if extract_chara(raw) is not None:
            print(f"  跳过（已有 chara）: {png}")
            continue
        shutil.copy2(pp, os.path.join(args.backup, png))  # 备份空白原图
        chunks = parse_chunks(raw)
        ihdr = next(i for i, (t, _) in enumerate(chunks) if t == b"IHDR")
        chunks.insert(ihdr + 1, (b"tEXt", b"chara\x00" + base64.b64encode(card_raw)))
        open(pp, "wb").write(build(chunks))
        got = extract_chara(open(pp, "rb").read())
        assert got is not None and json.loads(got.decode("utf-8")) == json.loads(card_raw.decode("utf-8-sig")), png
        ok += 1
    print(f"注入并回读验证 {ok}/{len(mapping)}；空白原图备份于 {args.backup}")


if __name__ == "__main__":
    main()
