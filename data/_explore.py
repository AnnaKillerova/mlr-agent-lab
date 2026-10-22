"""Structural + statistical exploration of leaves.csv (stdlib + numpy only)."""
import csv, collections, statistics as st

PATH = "leaves.csv"

raw = open(PATH, "rb").read()
print("bytes:", len(raw),
      "| UTF-8 BOM:", raw[:3] == b"\xef\xbb\xbf",
      "| CRLF:", raw.count(b"\r\n"),
      "| bare LF:", raw.count(b"\n") - raw.count(b"\r\n"))

rows = list(csv.reader(open(PATH, newline="", encoding="utf-8-sig")))
header, data = rows[0], rows[1:]
print("header:", header)
print("data rows:", len(data))
print("field-count per row:", dict(collections.Counter(len(r) for r in data)))

blank = [i + 2 for i, r in enumerate(data) if not any(f.strip() for f in r)]
print("fully blank lines (file line no.):", blank[:20], "count:", len(blank))

# Row-level parsing -----------------------------------------------
bad = []          # (line, row, reason)
recs = []         # (h, w, type)
for i, r in enumerate(data):
    line = i + 2
    if not any(f.strip() for f in r):
        continue
    if len(r) != 3:
        bad.append((line, r, "wrong field count"))
        continue
    hs, ws, t = (f.strip() for f in r)
    vals = []
    reason = None
    for name, s in (("height", hs), ("width", ws)):
        if s == "":
            reason = f"missing {name}"
            break
        try:
            v = float(s)
        except ValueError:
            reason = f"non-numeric {name}: {s!r}"
            break
        if v != v:  # NaN
            reason = f"NaN {name}"
            break
        vals.append(v)
    if reason:
        bad.append((line, r, reason))
        continue
    if not t:
        bad.append((line, r, "missing tree type"))
        continue
    if vals[0] < 0 or vals[1] < 0:
        bad.append((line, r, f"negative measurement {vals}"))
    recs.append((vals[0], vals[1], t))

print("\nparsed OK:", len(recs), "| problem rows:", len(bad))
for line, r, why in bad[:40]:
    print("   line", line, r, "->", why)

# Tree types -------------------------------------------------------
types = collections.Counter(t for _, _, t in recs)
print("\n=== leaf counts by tree type ===")
for t, n in types.most_common():
    print(f"{t!r:20} {n:4d}  {100*n/len(recs):5.1f}%")
print("distinct types:", len(types))
print("raw type strings, case/whitespace variants:",
      sorted({t for _, _, t in recs}))

# Exact duplicate rows --------------------------------------------
dupes = collections.Counter(tuple(r) for r in recs)
dups = {k: v for k, v in dupes.items() if v > 1}
print("\nexact duplicate rows:", sum(v - 1 for v in dups.values()),
      "extra copies of", len(dups), "distinct rows")
for k, v in sorted(dups.items(), key=lambda kv: -kv[1])[:10]:
    print("   x%d" % v, k)

def report(vals, label):
    s = sorted(vals)
    q = lambda p: st.quantiles(s, n=100, method="inclusive")[p - 1] if len(s) > 1 else s[0]
    print(f"\n--- {label} --- n={len(s)}")
    print(f"  min {min(s):8.2f}   q1 {q(25):7.2f}   median {q(50):7.2f}   "
          f"q3 {q(75):7.2f}   max {max(s):8.2f}")
    print(f"  mean {st.fmean(s):7.2f}   sd {st.pstdev(s):6.2f}   "
          f"IQR {q(75)-q(25):6.2f}   zeros {sum(1 for v in s if v == 0)}   "
          f"neg {sum(1 for v in s if v < 0)}")
    return q(25), q(75)

hs = [r[0] for r in recs]
ws = [r[1] for r in recs]
qh = report(hs, "height")
qw = report(ws, "width")

# Per-type summary -------------------------------------------------
print("\n=== per type: n, mean/median height, mean/median width, h/w ratio ===")
for t, _ in types.most_common():
    g = [(h, w) for h, w, tt in recs if tt == t]
    H = [h for h, _ in g]; W = [w for _, w in g]
    ratio = st.fmean([h / w for h, w in g if w])
    print(f"{t:10} n={len(g):4d}  h {st.fmean(H):6.2f}/{st.median(H):6.2f}   "
          f"w {st.fmean(W):6.2f}/{st.median(W):6.2f}   h/w {ratio:5.2f}")

# Outliers by Tukey fence, per type -------------------------------
print("\n=== outliers outside 1.5*IQR fences, computed per type ===")
n_out = 0
for t, _ in types.most_common():
    g = [(h, w) for h, w, tt in recs if tt == t]
    for idx, name in ((0, "height"), (1, "width")):
        v = sorted(x[idx] for x in g)
        q1, q3 = st.quantiles(v, n=4, method="inclusive")
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        outs = sorted(set(x[idx] for x in g if x[idx] < lo or x[idx] > hi))
        for o in outs:
            n_out += 1
            print(f"   {t:8} {name:6} {o:8.2f}  (fence {lo:7.2f} .. {hi:7.2f})")
print("total flagged:", n_out)

# Global extremes --------------------------------------------------
print("\n=== 5 largest and 5 smallest by height ===")
for h, w, t in sorted(recs, key=lambda r: -r[0])[:5]:
    print("   max h", h, "w", w, t)
for h, w, t in sorted(recs, key=lambda r: r[0])[:5]:
    print("   min h", h, "w", w, t)

# Correlation ------------------------------------------------------
def pearson(x, y):
    n = len(x); mx, my = st.fmean(x), st.fmean(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx = sum((a - mx) ** 2 for a in x); vy = sum((b - my) ** 2 for b in y)
    return cov / (vx * vy) ** 0.5 if vx and vy else float("nan")

print("\nPearson r (all):", round(pearson(hs, ws), 4))
for t, _ in types.most_common():
    g = [(h, w) for h, w, tt in recs if tt == t]
    print(f"   {t:10} r = {pearson([a for a,_ in g],[b for _,b in g]):+.4f}")

# Decimal precision / granularity ---------------------------------
def dp(s):
    s = s.strip()
    return len(s.split(".")[1]) if "." in s else 0
prec = collections.Counter(dp(r[0] if isinstance(r[0], str) else f"{r[0]:g}") for r in data if len(r) == 3)
print("\ndecimal places on raw height field:", dict(prec))
