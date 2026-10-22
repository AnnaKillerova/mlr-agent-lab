"""Deeper anomaly checks on leaves.csv."""
import csv, collections, statistics as st

rows = list(csv.reader(open("leaves.csv", newline="", encoding="utf-8-sig")))
recs = [(float(a), float(b), c.strip()) for a, b, c in rows[1:]]

def quart(v):
    q = st.quantiles(sorted(v), n=4, method="inclusive")
    return q[0], q[2]

print("=== outliers outside 1.5*IQR fences (fences per type+measure) ===")
total = 0
for t in ("maple", "cherry", "walnut"):
    g = [(h, w) for h, w, tt in recs if tt == t]
    for idx, name in ((0, "height"), (1, "width")):
        v = [x[idx] for x in g]
        q1, q3 = quart(v)
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        outs = sorted({x[idx] for x in g if x[idx] < lo or x[idx] > hi})
        for o in outs:
            total += 1
            print(f"   {t:7} {name:6} = {o:7.2f}   fence [{lo:7.2f}, {hi:7.2f}]")
print("flagged:", total)

# Round numbers -> hand-entered / fabricated look ------------------
def is_round(x):
    return abs(x - round(x)) < 1e-9
rnd = [r for r in recs if is_round(r[0]) and is_round(r[1])]
print(f"\n=== rows where BOTH height and width are whole numbers: {len(rnd)} / {len(recs)}"
      f"  ({100*len(rnd)/len(recs):.1f}%)")
one_dp = [r for r in recs if not is_round(r[0]) or not is_round(r[1])]
def dp(x):
    s = f"{x:.10f}".rstrip("0").rstrip(".")
    return len(s.split(".")[1]) if "." in s else 0
print("   decimal places, height:", dict(collections.Counter(dp(h) for h, _, _ in recs)))
print("   decimal places, width :", dict(collections.Counter(dp(w) for _, w, _ in recs)))
print("   sample all-integer rows:", rnd[:12])

# Possible height/width transposition ------------------------------
# maple averages wider-than-tall; cherry & walnut taller-than-wide.
print("\n=== rows contradicting their type's usual aspect (possible transposed columns) ===")
for t in ("maple", "cherry", "walnut"):
    g = [(h, w) for h, w, tt in recs if tt == t]
    if t == "maple":
        odd = [(h, w) for h, w in g if h > w]
        desc = "height > width (maple is usually wider than tall)"
    else:
        odd = [(h, w) for h, w in g if w > h]
        desc = "width > height (this type is usually taller than wide)"
    print(f"   {t:7} {len(odd):3d}/{len(g):3d} {desc}  e.g. {odd[:6]}")

# Duplicates in context -------------------------------------------
dups = {k: v for k, v in collections.Counter(recs).items() if v > 1}
print(f"\n=== duplicates: {sum(dups.values())} rows covering {len(dups)} distinct values"
      f"  ({sum(v-1 for v in dups.values())} redundant copies) ===")
by_t = collections.Counter(k[2] for k in dups)
print("   distinct duplicated rows per type:", dict(by_t))
print("   duplicated rows that are all-integer:",
      sum(1 for k in dups if is_round(k[0]) and is_round(k[1])), "of", len(dups))

# Linearity / grid artefacts: repeated exact values ---------------
print("\n=== most frequent exact values ===")
print("   height:", collections.Counter(h for h, _, _ in recs).most_common(6))
print("   width :", collections.Counter(w for _, w, _ in recs).most_common(6))

# Separability: can type be recovered from (h,w)? ------------------
print("\n=== do types overlap in the h/w plane? (min/max box per type) ===")
for t in ("maple", "cherry", "walnut"):
    g = [(h, w) for h, w, tt in recs if tt == t]
    print(f"   {t:7} height [{min(h for h,_ in g):5.2f}, {max(h for h,_ in g):5.2f}]"
          f"  width [{min(w for _,w in g):5.2f}, {max(w for _,w in g):5.2f}]")
