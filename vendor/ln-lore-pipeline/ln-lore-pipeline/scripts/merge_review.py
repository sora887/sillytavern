#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_review.py — 审查合并文件生成（防截断/防粘连/均衡分份）

把目录内全部 json 合并为若干"审查合并文件"：
  按文件名排序 → 按字节 DP 均衡切 K 份（最小化最大份） → 分入 2 个文件夹（累计差最小）
  每文件前插独立成行 ===== 文件名 ===== 标题（前文件无尾换行则强制补）
  UTF-8 无 BOM → SHA256 回验 → 拆解 QA（逐文件反向拆出独立解析）→ 清单 manifest

用法：
  py merge_review.py --src <json目录> --out <输出根目录> \
      --name-fmt "B{n}后_审查合并_第{pi}部分" [--parts 9] [--folders 2]
"""
import argparse, glob, hashlib, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
INF = float("inf")


def dp_balance(order, sizes, K):
    n = len(order)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] + sizes[i]
    dp = [[INF] * (K + 1) for _ in range(n + 1)]
    cut = [[0] * (K + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for j in range(1, K + 1):
        for i in range(1, n + 1):
            for m in range(j - 1, i):
                v = max(dp[m][j - 1], pre[i] - pre[m])
                if v < dp[i][j]:
                    dp[i][j] = v
                    cut[i][j] = m
    bounds, i = [], n
    for j in range(K, 0, -1):
        m = cut[i][j]
        bounds.append((m, i))
        i = m
    bounds.reverse()
    parts = [[order[a:b] for a, b in bounds][k] for k in range(K)]
    psums = [pre[b] - pre[a] for a, b in bounds]
    best_k, bd = 1, INF
    for k in range(1, K):
        dd = abs(sum(psums[:k]) - sum(psums[k:]))
        if dd < bd:
            best_k, bd = k, dd
    return parts, best_k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name-fmt", required=True, help='如 "B{n}后_审查合并_第{pi}部分"')
    ap.add_argument("--parts", type=int, default=9)
    ap.add_argument("--folders", type=int, default=2)
    args = ap.parse_args()

    order = sorted(f for f in os.listdir(args.src) if f.endswith(".json"))
    assert order, "源目录无 json"
    sizes = [len(open(os.path.join(args.src, f), "rb").read()) for f in order]
    K = min(args.parts, len(order))
    parts, best_k = dp_balance(order, sizes, K)

    folders = {i + 1: os.path.join(args.out, f"{args.name_fmt.split('_')[0]}_第{i+1}组")
               for i in range(args.folders)}
    for d in folders.values():
        os.makedirs(d, exist_ok=True)
        for g in glob.glob(os.path.join(d, "*.json")):
            os.remove(g)

    manifest = []
    for pi, files in enumerate(parts, 1):
        buf = bytearray()
        for f in files:
            if buf and not buf.endswith(b"\n"):
                buf += b"\n"                      # 防粘连
            buf += f"===== {f} =====\n".encode("utf-8")
            buf += open(os.path.join(args.src, f), "rb").read()
        data = bytes(buf)
        folder = 1 if pi <= best_k else 2
        fname = args.name_fmt.format(n="", pi=pi) + ".json"
        path = os.path.join(folders[folder], fname)
        open(path, "wb").write(data)
        back = open(path, "rb").read()
        txt = back.decode("utf-8")
        glued = sum(1 for l in txt.split("\n") if "=====" in l and not l.startswith("====="))
        manifest.append({"part": pi, "folder": folder, "files": files, "bytes": len(data),
                         "lines": txt.count("\n"), "sha256": hashlib.sha256(back).hexdigest(),
                         "glued": glued, "verify": back == data})
        print(f"第{pi}部分(第{folder}组): {len(files)}个 {len(data)}B 粘连={glued} 回验={back == data}")

    # 拆解 QA：逐文件反向拆出独立解析
    bad = []
    for m in manifest:
        p = os.path.join(folders[m["folder"]], args.name_fmt.format(n="", pi=m["part"]) + ".json")
        cur, buf = None, []
        for l in open(p, "rb").read().decode("utf-8").split("\n"):
            if l.startswith("===== ") and l.endswith(".json ====="):
                if cur:
                    try:
                        json.loads("\n".join(buf))
                    except Exception as e:
                        bad.append(f"{cur}: {e}")
                cur, buf = l[6:-6], []
            else:
                buf.append(l)
        if cur:
            try:
                json.loads("\n".join(buf))
            except Exception as e:
                bad.append(f"{cur}: {e}")
    print("拆解QA:", f"{len(order)}/{len(order)} 通过" if not bad else bad)
    json.dump(manifest, open(os.path.join(args.out, "审查合并_清单.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("清单已写入 审查合并_清单.json")


if __name__ == "__main__":
    main()
