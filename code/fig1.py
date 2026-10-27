# -*- coding: utf-8 -*-
"""Fig. 1  Where the window closes.

(a) scale section through a monitoring well (J = 1.60 m);
(b) the upper 45 cm repeated three times, with the operating threshold drawn at
    four of the five depths configured in the network (inside the window and
    outside it) plus the edge case 0.26 m, which is the limit of the readable
    range and not an operating value. Nothing but D+B = 0.26 m, J and the
    thresholds is used.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
import figstyle as S

S.apply()

J = 1.60
DB = 0.26
D_USED = 0.10          # split used for drawing only; the paper claims the sum
CONC = "#D2D2D2"

fig = plt.figure(figsize=(S.W2, 76 * S.MM))
outer = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.92], wspace=0.26,
                         left=0.055, right=0.988, top=0.885, bottom=0.185)

# ============================================================ (a) section
ax = fig.add_subplot(outer[0, 0])
ax.set_xlim(0, 1.16)
ax.set_ylim(J + 0.14, -0.17)
ax.set_xticks([])
for sp in ("top", "right", "bottom"):
    ax.spines[sp].set_visible(False)
ax.spines["left"].set_position(("data", 0.0))

WALL_L, WALL_R, IN_L, IN_R = 0.14, 0.78, 0.26, 0.66

ax.add_patch(Rectangle((WALL_L, 0), IN_L - WALL_L, J, fc=CONC, ec="none", zorder=1))
ax.add_patch(Rectangle((IN_R, 0), WALL_R - IN_R, J, fc=CONC, ec="none", zorder=1))
for xv in (WALL_L, IN_L, IN_R, WALL_R):
    ax.plot([xv, xv], [0, J], color="k", lw=0.5, zorder=2)

ax.add_patch(Rectangle((0.04, -0.080), 0.84, 0.080, fc="#7A7A7A", ec="k", lw=0.6, zorder=4))
ax.text(0.46, -0.108, "cover", ha="center", va="bottom", fontsize=6.4)

# blind window
ax.add_patch(Rectangle((IN_L, 0.0), IN_R - IN_L, DB, fc=S.C_BAND, ec="none", zorder=3))
ax.plot([IN_L, IN_R], [DB, DB], color="k", lw=0.9, ls=(0, (3, 1.5)), zorder=4)
ax.add_patch(Rectangle((0.26, D_USED - 0.026), 0.10, 0.052, fc="#333333", ec="k",
                       lw=0.4, zorder=6))
ax.text(0.385, D_USED, "sensor face, $D$", fontsize=5.8, ha="left",
        va="center", color="#222222", zorder=7)
ax.text(0.46, 0.205, "blind window", fontsize=6.0, ha="center", va="center",
        color="#4D4D4D", zorder=6)

# water + pipe
ax.add_patch(Rectangle((IN_L, 0.90), IN_R - IN_L, J - 0.90, fc="#CFE3EE", ec="none", zorder=3))
xw = np.linspace(IN_L, IN_R, 40)
ax.plot(xw, 0.90 + 0.012 * np.sin(np.linspace(0, 3 * np.pi, 40)),
        color="#2E6E8E", lw=0.7, zorder=5)
ax.text(0.46, 1.10, "water", fontsize=6.0, ha="center", va="center", color="#2E6E8E")
ax.add_patch(Rectangle((0.06, 1.43), 0.80, 0.17, fc=CONC, ec="k", lw=0.5, zorder=2))
ax.add_patch(Rectangle((0.26, 1.43), 0.40, 0.17, fc="w", ec="none", zorder=2.5))
ax.add_patch(Circle((0.46, 1.515), 0.098, fc="#CFE3EE", ec="k", lw=0.5, zorder=3))

# brackets on the right
def spans(y0, y1, x, txt, fs=6.3):
    ax.annotate("", xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle="|-|,widthA=0.16,widthB=0.16", lw=0.5,
                                color="k", shrinkA=0, shrinkB=0))
    ax.text(x + 0.03, (y0 + y1) / 2, txt, fontsize=fs, va="center", ha="left",
            linespacing=1.15)

spans(0, DB, 0.82, r"$D+B$" + "\n0.26 m")

for yv, lab in [(0, "0"), (DB, "0.26"), (J, "1.60")]:
    ax.plot([-0.012, 0], [yv, yv], color="k", lw=0.6)
    ax.text(-0.035, yv, lab, ha="right", va="center", fontsize=6.2)
ax.set_ylabel("depth below cover  (m)", labelpad=3)
ax.set_yticks([])
S.tag(ax, "a", x=-0.20, y=1.02)

# ============================================================ (b) three cases
right = outer[0, 1].subgridspec(1, 3, wspace=0.10)
CASES = [
    ("inside", [(0.10, "0.385"), (0.20, "0.769")], S.C_OUT, "not estimable"),
    ("at the edge", [(0.26, "1.000")], "#7A7A7A", "limiting case"),
    ("outside", [(0.30, "1.154"), (0.40, "1.538")], S.C_IN, "estimable"),
]
axes = []
for i, (title, rows, col, verdict) in enumerate(CASES):
    a = fig.add_subplot(right[0, i], sharey=axes[0] if axes else None)
    axes.append(a)
    a.set_xlim(0, 1)
    a.set_ylim(0.465, -0.045)
    a.set_xticks([])
    a.spines["left"].set_visible(i == 0)
    a.spines["bottom"].set_visible(False)
    a.spines["right"].set_visible(False)
    if i == 0:
        a.set_yticks([0, 0.10, 0.20, 0.30, 0.40])
        a.set_yticklabels(["0", "0.10", "0.20", "0.30", "0.40"])
    else:
        a.tick_params(left=False, labelleft=False)

    a.add_patch(Rectangle((0, 0), 1, DB, fc=S.C_BAND, ec="none", zorder=0.5))
    a.plot([0, 1], [DB, DB], color="k", lw=0.9, ls=(0, (3, 1.5)), zorder=1, clip_on=False)
    for yv, om in rows:
        a.plot([0.08, 0.92], [yv, yv], color=col, lw=1.9, solid_capstyle="butt", zorder=3)
        a.annotate(r"$\Omega$ = %s" % om, xy=(0.5, yv), xytext=(0, 2.6),
                   textcoords="offset points", ha="center", va="bottom",
                   fontsize=6.4, color=col, fontweight="bold")
    a.text(0.5, 1.035, title, transform=a.transAxes, ha="center", va="bottom",
           fontsize=6.5, color="#222222")
    a.text(0.5, -0.030, verdict, transform=a.transAxes, ha="center", va="top",
           fontsize=6.5, color=col,
           fontweight="bold" if verdict == "not estimable" else "normal")

axes[0].text(0.03, 0.13, r"$D+B$", fontsize=6.2, ha="left", va="center",
             color="#4D4D4D", zorder=6)
axes[0].set_ylabel("threshold depth  $b_\\theta$\n(m below cover)", labelpad=2,
                   linespacing=1.25)
S.tag(axes[0], "b", x=-0.30, y=1.02)

if S.CAPTION:
    fig.text(0.055, 0.012,
             "Shaded band: no depth information is returned.  A threshold set inside the band "
             "gives $\\Omega \\leq 1$: the archive returns the floor value\n"
             "$J-0.25$ m rather than a level, and no reading can lie below the threshold.",
             fontsize=6.2, ha="left", va="bottom", color="#333333", linespacing=1.45)

S.save(fig, "Fig1_window_concept")
