"""Scatter plot of leaf height vs width from leaves.csv, split by tree type."""
import csv, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.reader(open("leaves.csv", newline="", encoding="utf-8-sig")))
recs = [(float(a), float(b), c.strip()) for a, b, c in rows[1:]]

types = [t for t, _ in collections.Counter(r[2] for r in recs).most_common()]
colors = {"maple": "#c1440e", "cherry": "#8e2f4e", "walnut": "#4a6b8a"}
sizes = {"maple": 46, "cherry": 40, "walnut": 40}

fig = plt.figure(figsize=(13, 6.1))
gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.24)

# ---- left: the requested scatter ------------------------------------
ax = fig.add_subplot(gs[0, 0])
for t in types:
    pts = [(h, w) for h, w, tt in recs if tt == t]
    x = [p[0] for p in pts]; y = [p[1] for p in pts]
    ax.scatter(x, y, s=sizes[t], c=colors[t], alpha=0.6, edgecolors="white",
               linewidths=0.5, label=f"{t} (n={len(pts)})", zorder=3)

lim = (0, 31)
ax.plot(lim, lim, ls=":", lw=1.2, c="0.45", zorder=2)
ax.text(27.4, 28.2, "height = width", rotation=35, fontsize=8, color="0.35",
        ha="center", va="bottom")

# mean point per type
for t in types:
    xs = [h for h, w, tt in recs if tt == t]; ys = [w for h, w, tt in recs if tt == t]
    mx, my = np.mean(xs), np.mean(ys)
    ax.scatter([mx], [my], marker="X", s=175, c=colors[t], edgecolors="black",
               linewidths=0.9, zorder=5)

ax.set_xlim(*lim); ax.set_ylim(*lim)
ax.set_xlabel("Leaf height")
ax.set_ylabel("Leaf width")
ax.set_title("Leaf height vs. leaf width, by tree type", fontsize=12, pad=10)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.92, handletextpad=0.15)
ax.grid(alpha=0.25, lw=0.7, zorder=0)
ax.set_axisbelow(True)
ax.annotate("maple: wide, near-circular", xy=(20, 22.5), fontsize=8.5, color="#8a3324",
            ha="left", va="center")
ax.annotate("cherry / walnut: narrow, elongated", xy=(15.5, 2.6), fontsize=8.5,
            color="#3d5875", ha="center", va="bottom")

# ---- right: one panel per type, same axes ---------------------------
axes = [fig.add_subplot(sub) for sub in gs[0, 1].subgridspec(3, 1, hspace=0.34)]
for ax2, t in zip(axes, types):
    pts = [(h, w) for h, w, tt in recs if tt == t]
    ax2.scatter([p[0] for p in pts], [p[1] for p in pts], s=18, c=colors[t],
                alpha=0.65, edgecolors="none")
    ax2.plot(lim, lim, ls=":", lw=0.9, c="0.55")
    ax2.set_xlim(*lim); ax2.set_ylim(*lim)
    ax2.set_xticks([0, 10, 20, 30]); ax2.set_yticks([0, 10, 20, 30])
    ax2.tick_params(labelsize=7.5)
    ax2.grid(alpha=0.2, lw=0.6); ax2.set_axisbelow(True)
    ax2.set_title(f"{t}  (n={len(pts)})", fontsize=9, loc="left", pad=3)
axes[0].set_ylabel("width", fontsize=8.5)
axes[1].set_ylabel("width", fontsize=8.5)
axes[2].set_ylabel("width", fontsize=8.5)
axes[2].set_xlabel("height", fontsize=9)

fig.suptitle("leaves.csv — 518 rows; X marks the mean of each type",
             fontsize=9.5, y=0.995, color="0.35")
fig.savefig("leaves_scatter.png", dpi=145, bbox_inches="tight", facecolor="white")
print("wrote leaves_scatter.png")

# Pearson r overall and per type, for the write-up
def r(x, y):
    x, y = np.asarray(x), np.asarray(y)
    return np.corrcoef(x, y)[0, 1]
h = [a for a, _, _ in recs]; w = [b for _, b, _ in recs]
print(f"r all     = {r(h, w):+.3f}")
for t in types:
    g = [(a, b) for a, b, tt in recs if tt == t]
    print(f"r {t:8}= {r([p[0] for p in g], [p[1] for p in g]):+.3f}")
