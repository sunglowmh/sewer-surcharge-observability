# -*- coding: utf-8 -*-
"""Fig. 8  The platform label is a function of one sign.

(a) two-by-two table of the 164 alarm records whose current value equals the
    write-back value J-0.25 m, by the side of the threshold and by the label;
(b) share read as "level has receded" against floor minus threshold.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import figstyle as S

S.apply()

d = pd.read_csv(f"{S.ROOT}/outputs/p3a_alarm_sign_flip.csv", encoding="utf-8-sig",
                dtype={"dev": str})
f = d[d.at_floor.astype(bool)].copy()
f["d"] = f.floor - f.thr
f["yellow"] = f.type.str.contains("黄")
g = f.groupby(["dev", "thr", "d"]).agg(n=("yellow", "size"),
                                       y=("yellow", "sum")).reset_index()
g["b"] = g.n - g.y
print("at-floor records %d, yellow %d, blue %d" % (len(f), g.y.sum(), g.b.sum()))

fig = plt.figure(figsize=(S.W2, 74 * S.MM))
gs = fig.add_gridspec(1, 2, width_ratios=[0.86, 1.0], wspace=0.40,
                      left=0.175, right=0.975, top=0.845, bottom=0.235)

# ---------------------------------------------------------------- (a) 2 x 2
ax = fig.add_subplot(gs[0, 0])
hi = f.floor > f.thr
lo = f.floor < f.thr
cells = [(0, 1, int((hi & f.yellow).sum())), (1, 1, int((hi & ~f.yellow).sum())),
         (0, 0, int((lo & f.yellow).sum())), (1, 0, int((lo & ~f.yellow).sum()))]
for cx, cy, n in cells:
    zero = n == 0
    ax.add_patch(Rectangle((cx + 0.04, cy + 0.04), 0.92, 0.92,
                           fc="white" if zero else (S.C_Y if cx == 0 else S.C_B),
                           ec=S.C_ALERT if zero else "none", lw=0.9 if zero else 0,
                           alpha=0.30 if not zero else 1.0, zorder=2))
    ax.text(cx + 0.5, cy + 0.5, "%d" % n, ha="center", va="center", fontsize=11 if n else 9,
            color=S.C_ALERT if zero else "#222222", fontweight="bold", zorder=3)
ax.set_xlim(0, 2)
ax.set_ylim(0, 2)
ax.set_xticks([0.5, 1.5])
ax.set_xticklabels(["above\nthreshold", "level has\nreceded"], fontsize=6.3, linespacing=1.2)
ax.set_yticks([1.5, 0.5])
ax.set_yticklabels(["$J-0.25$ > threshold", "$J-0.25$ < threshold"], fontsize=6.3)
ax.xaxis.set_ticks_position("top")
ax.tick_params(length=0)
for sp in ("top", "right", "left", "bottom"):
    ax.spines[sp].set_visible(False)
ax.text(0.5, -0.13, "two empty cells: no record contradicts the sign rule", ha="center",
        va="top", fontsize=5.8, color=S.C_ALERT)
# Panel (a) carries two-line tick labels above its top spine, so both tags sit
# above them at one COMMON height: the two axes share the same gridspec top,
# hence the same y in axes coords is the same height on the canvas.  1.20 clears
# the tick-label tops (~1.15) by ~2.5 mm; 1.30 (the old value for a) left b 7 mm lower.
S.tag(ax, "a", x=-0.34, y=1.20)

# ---------------------------------------------------------------- (b) the step
ax2 = fig.add_subplot(gs[0, 1])
ax2.axvline(0, color="#9A9A9A", lw=0.6, ls=(0, (3, 1.6)), zorder=1)
ax2.axvspan(-0.19, 0, color=S.C_B, alpha=0.05, lw=0, zorder=0)
ax2.axvspan(0, 0.19, color=S.C_Y, alpha=0.05, lw=0, zorder=0)
off = {}
for _, r in g.iterrows():
    k = off.get(r.d, 0)
    off[r.d] = k + 1
    xj = r.d + (0.0135 if k % 2 else -0.0135) * (1 + k // 2)
    share = r.b / r.n * 100
    ax2.scatter(xj, share, s=6 + r.n * 1.35, facecolor="white", edgecolor=S.C_B,
                linewidth=0.8, zorder=3)
    if r.n >= 20:
        ax2.text(xj, share + (8 if share > 50 else -8), "%d records" % r.n, ha="center",
                 va="bottom" if share > 50 else "top", fontsize=5.6, color="#4D4D4D")
ax2.set_xlim(-0.19, 0.19)
ax2.set_ylim(-26, 124)
ax2.set_yticks([0, 50, 100])
ax2.set_xticks([-0.15, -0.05, 0.05, 0.10, 0.15])
ax2.set_xticklabels(["-0.15", "-0.05", "+0.05", "+0.10", "+0.15"], fontsize=6.2)
ax2.set_xlabel("write-back value minus threshold  (m)")
ax2.set_ylabel("read as\nlevel has receded  (%)", linespacing=1.25, labelpad=3)
ax2.text(0.60, 0.55, "every record above the threshold is\nlabelled \"above\"; every record below\n"
                     "is labelled \"receded\"",
         transform=ax2.transAxes, fontsize=5.8, va="top", linespacing=1.3, color="#4D4D4D")
ax2.text(0.014, 0.06, "marker area = records (1 to 54)", transform=ax2.transAxes, fontsize=5.5,
         color="#8C8C8C", style="italic")
S.tag(ax2, "b", x=-0.24, y=1.20)

if S.CAPTION:
    fig.text(0.045, 0.012,
             S.cap("The sign of one difference fixes the label. Of the 305 alarms in the record, 164 "
                   "carry a current value exactly equal to the write-back value; (a) cross-tabulates "
                   "those 164 by the side of the threshold and by the label the platform printed. (b) "
                   "The same 164 records grouped by configuration: the share read as \"level has "
                   "receded\" is 100% on one side and 0% on the other, with nothing in between.", 150),
             fontsize=6.0, ha="left", va="bottom", color="#333333", linespacing=1.32)

S.save(fig, "Fig8_sign_flip")
