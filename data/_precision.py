"""Are the high-precision rows a separate subpopulation?"""
import csv, collections, statistics as st

rows = list(csv.reader(open("leaves.csv", newline="", encoding="utf-8-sig")))
raw = [(a.strip(), b.strip(), c.strip()) for a, b, c in rows[1:]]
recs = [(float(a), float(b), c) for a, b, c in raw]

def dp(s):
    return len(s.split(".")[1]) if "." in s else 0

# group by whether either field has >=4 decimal places
hi = [(h, w, t) for (a, b, t), (h, w, t) in zip(raw, recs) if max(dp(a), dp(b)) >= 4]
lo = [(h, w, t) for (a, b, t), (h, w, t) in zip(raw, recs) if max(dp(a), dp(b)) <= 3]
print(f"high-precision rows (>=4 dp): {len(hi)}   low-precision rows (<=3 dp): {len(lo)}")

for label, g in (("HIGH-PRECISION", hi), ("LOW-PRECISION", lo)):
    print(f"\n--- {label} (n={len(g)}) ---")
    print("   types:", dict(collections.Counter(t for _, _, t in g)))
    for idx, nm in ((0, "height"), (1, "width")):
        v = [x[idx] for x in g]
        print(f"   {nm:6} mean {st.fmean(v):6.2f}  min {min(v):6.2f}  max {max(v):6.2f}")
    ar = [h / w for h, w, _ in g if w]
    print(f"   mean height/width = {st.fmean(ar):.2f}")

# aspect ratio per type, split by precision group
print("\n=== mean height/width per type, split by precision group ===")
for t in ("maple", "cherry", "walnut"):
    a = [h / w for h, w, tt in hi if tt == t if w]
    b = [h / w for h, w, tt in lo if tt == t if w]
    fa = f"{st.fmean(a):.2f} (n={len(a)})" if a else "-"
    fb = f"{st.fmean(b):.2f} (n={len(b)})" if b else "-"
    print(f"   {t:7} high-precision {fa:16} low-precision {fb}")

# position of high-precision rows in the file
pos = [i + 2 for i, (a, b, t) in enumerate(raw) if max(dp(a), dp(b)) >= 4]
print("\nfile line numbers of high-precision rows:")
print("   first 15:", pos[:15])
print("   last 15 :", pos[-15:])
# are they contiguous / clustered?
runs, start, prev = [], None, None
for p in pos + [None]:
    if prev is not None and p is not None and p == prev + 1:
        prev = p; continue
    if start is not None:
        runs.append((start, prev))
    start = prev = p
long_runs = [r for r in runs if r[1] - r[0] >= 3]
print(f"   contiguous runs (>=4 in a row): {long_runs}")
print(f"   total runs: {len(runs)} -> {'clustered block(s)' if len(runs) < 15 else 'scattered throughout'}")

# do the extreme outliers belong to the high-precision group?
print("\n=== the 6 most extreme rows and their precision ===")
order = sorted(zip(raw, recs), key=lambda rc: -(rc[1][0] + rc[1][1]))[:6]
for (a, b, t), (h, w, tt) in order:
    print(f"   {a:>10} , {b:>10} , {t:7} max_dp={max(dp(a), dp(b))}")
small = sorted(zip(raw, recs), key=lambda rc: (rc[1][0] + rc[1][1]))[:6]
for (a, b, t), (h, w, tt) in small:
    print(f"   {a:>10} , {b:>10} , {t:7} max_dp={max(dp(a), dp(b))}")
