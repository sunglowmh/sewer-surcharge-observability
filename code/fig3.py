# -*- coding: utf-8 -*-
"""Fig. 3  What the depth-limited readings are, and what they are not.

(a) progressive classification of the 3,308 depth-limited readings by an external
    (rainfall) criterion;
(b) the one long block, with forty days of the Chifeng Road record around it and
    the surface network beneath as an independent check on the weather;
(c) the rising-limb test: 3-hour antecedent rainfall for the eighteen blocks.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import figstyle as S

S.apply()

dec = pd.read_csv(f"{S.DATADIR}/fig3_decomp.csv", encoding="utf-8-sig")
blk = pd.read_csv(f"{S.DATADIR}/fig3_block.csv", encoding="utf-8-sig")
blk["t"] = pd.to_datetime(blk.t)
srf = pd.read_csv(f"{S.DATADIR}/fig3_surface_day.csv", encoding="utf-8-sig")
srf["d"] = pd.to_datetime(srf.d)
pbl = pd.read_csv(f"{S.DATADIR}/../p3a_precip_lock_blocks.csv", encoding="utf-8-sig",
                  dtype={"dev": str})

V = dict(zip(dec.label, dec.value))
TOT, PREC = V["floor readings"], V["rainfall-active period"]
CF, BLK, RES = V["Chifeng Road (site 01)"], V["one 21-day block"], V["residual"]

fig = plt.figure(figsize=(S.W2, 128 * S.MM))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05], width_ratios=[1.05, 1.0],
                      left=0.075, right=0.972, top=0.935, bottom=0.145,
                      hspace=0.60, wspace=0.26)

# ============================================================ (a) staircase
ax = fig.add_subplot(gs[0, 0])
ax.set_xlim(-40, TOT * 1.03)
ax.set_ylim(-1.25, 3.95)
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xlabel("depth-limited readings  (count)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: "{:,.0f}".format(v)))
ax.set_xticks([0, 1000, 2000, 3000])

C_P, C_R, C_K, C_S, C_K2 = "#9EC9E2", "#C9C9C9", S.C_OUT, "#EFD8C4", "#E4C6B0"
ROWS = [
    (2.90, [(0, TOT, C_R, "3,308  depth-limited readings")]),
    (1.95, [(0, PREC, C_P, ""), (PREC, TOT, C_R, "3,176  (96.0%)")]),
    (1.00, [(0, PREC, C_P, ""), (PREC, PREC + RES, C_S, ""),
            (PREC + RES, TOT, C_K, "3,028  site 01")]),
    (0.05, [(0, PREC, C_P, ""), (PREC, PREC + RES, C_S, ""),
            (PREC + RES, PREC + RES + BLK, C_K, "2,997  one block"),
            (PREC + RES + BLK, TOT, C_K2, "")]),
]
for y, segs in ROWS:
    for x0, x1, c, lab in segs:
        ax.add_patch(Rectangle((x0, y - 0.27), x1 - x0, 0.54, fc=c, ec="k", lw=0.45, zorder=3))
        if lab:
            ax.text((x0 + x1) / 2, y, lab, ha="center", va="center", fontsize=6.3,
                    zorder=4, fontweight="bold")

ax.text(0, 3.30, "132  within a rainfall-active period  (4.0%)", ha="left", va="bottom",
        fontsize=6.0, color="#2E6E8E")
ax.annotate("148 residual (4.5%)", xy=(PREC + RES * 0.5, 0.34), xytext=(PREC - 120, -0.40),
            fontsize=5.9, ha="center", va="top",
            arrowprops=dict(arrowstyle="-", lw=0.4, color="#7A7A7A"))
ax.annotate("31 outside the block", xy=(PREC + RES + BLK + 15, 0.34),
            xytext=(TOT * 1.02, -0.40), ha="right", va="top",
            fontsize=5.9, arrowprops=dict(arrowstyle="-", lw=0.4, color="#7A7A7A"))
for y0, y1 in [(2.90, 1.95), (1.95, 1.00), (1.00, 0.05)]:
    ax.plot([TOT * 1.015] * 2, [y0 - 0.28, y1 + 0.28], color="#C0C0C0", lw=0.4,
            ls=(0, (2, 2)), zorder=2)
S.tag(ax, "a", x=-0.155, y=1.02)

# ============================================================ (c) antecedent rain
ax3 = fig.add_subplot(gs[0, 1])
p = pbl.sort_values("rain_prev3h_mm").reset_index(drop=True)
yy = np.arange(len(p))
c = np.where(p.phase.values == "rain-driven", S.C_IN, S.C_ALERT)
ax3.scatter(p.rain_prev3h_mm, yy, s=np.clip(p.n.values * 1.1, 7, 44), c=c,
            edgecolor="k", linewidth=0.35, zorder=3)
ax3.axvline(5, color="k", lw=0.6, ls=(0, (3, 2)), zorder=2)
EVMAP = {"0719暴雨": "19 Jul", "巴威": "Bavi", "白海豚": "Dolphin"}
ax3.set_yticks(yy)
ax3.set_yticklabels(["%02d  %s" % (i + 1, EVMAP.get(e, e))
                     for i, e in enumerate(p.event.values)], fontsize=5.3)
ax3.set_ylim(-0.9, len(p) - 0.1)
ax3.set_xlim(-8, 172)
ax3.set_xlabel("rainfall in the 3 h before onset  (mm)")
ax3.text(6, -0.66, "5 mm", fontsize=5.8, ha="left", va="bottom")
ax3.annotate("2 of 18 blocks\n(1.0 and 0.0 mm)", xy=(2.0, 0.6), xytext=(34, 2.7),
             fontsize=5.9, ha="left", va="center", linespacing=1.2,
             arrowprops=dict(arrowstyle="-", lw=0.5, color="#7A7A7A"))
ax3.text(0.98, 0.05, "16 of 18 begin after rain\n(125 of 132 readings)",
         transform=ax3.transAxes, fontsize=6.0, ha="right", va="bottom", linespacing=1.25)
S.tag(ax3, "c", x=-0.30, y=1.02)

# ============================================================ (b) the block
sub = gs[1, :].subgridspec(2, 1, height_ratios=[3.0, 1.0], hspace=0.14)
axb = fig.add_subplot(sub[0])
gap = blk.t.diff().dt.total_seconds().div(60)
b2 = blk.burial.where(gap.fillna(0) < 90)
axb.plot(blk.t, b2, color="#4D4D4D", lw=0.6, zorder=3)
m = blk.cens.astype(bool)
axb.plot(blk.t[m], blk.burial[m], color=S.C_ALERT, lw=1.4, zorder=4, solid_capstyle="butt")
axb.axhline(0.25, color=S.C_ALERT, lw=0.6, ls=(0, (4, 2)), zorder=2)
axb.set_ylim(2.92, -0.30)
axb.set_ylabel("water-surface depth\nbelow cover  (m)", labelpad=3, linespacing=1.25)
axb.set_xlim(pd.Timestamp("2025-10-22"), pd.Timestamp("2025-12-06"))
axb.set_xticks([pd.Timestamp(x) for x in
                ["2025-10-22", "2025-11-01", "2025-11-11", "2025-11-21", "2025-12-01"]])
axb.set_xticklabels(["22 Oct", "1 Nov", "11 Nov", "21 Nov", "1 Dec"])
axb.tick_params(axis="x", labelbottom=False)

axb.annotate("no telemetry, 10.9 d", xy=(pd.Timestamp("2025-10-29"), 0.49),
             xytext=(pd.Timestamp("2025-10-27"), 1.42), fontsize=5.9, ha="center",
             va="center", color="#4D4D4D",
             arrowprops=dict(arrowstyle="-", lw=0.4, color="#8C8C8C", ls=(0, (2, 2))))
axb.plot([pd.Timestamp("2025-11-04 10:24")], [0.26], marker="o", ms=3.0, mfc="w",
         mec="k", mew=0.6, zorder=6)
axb.text(pd.Timestamp("2025-11-14"), 0.36,
         "2,997 readings · 20.8 d · one value",
         fontsize=6.3, ha="center", va="top", color=S.C_ALERT, fontweight="bold")
axb.text(pd.Timestamp("2025-11-14"), 0.60,
         "six further instruments report exactly their ceiling over the same interval",
         fontsize=5.8, ha="center", va="top", color="#4D4D4D")

axb.plot([pd.Timestamp("2025-11-25 12:06")], [2.70], marker="o", ms=3.4, mfc="w",
         mec="k", mew=0.6, zorder=6)
axb.annotate("""leaving the block:
0.25 → 2.70 → 0.14 → 1.37 m in 12 min;
2.70 m is the configured well depth""",
             xy=(pd.Timestamp("2025-11-25 12:40"), 1.60),
             xytext=(pd.Timestamp("2025-11-10 12:00"), 2.34), fontsize=5.8, ha="left",
             va="center", linespacing=1.3,
             arrowprops=dict(arrowstyle="-", lw=0.5, color="#333333"))
S.tag(axb, "b", x=-0.043, y=1.06)

axs = fig.add_subplot(sub[1], sharex=axb)
axs.bar(srf.d, srf.wet_pct, width=0.82, color=S.C_SURF, alpha=0.55, ec="none")
axs.axhline(11.0, color=S.C_SURF, lw=0.6, ls=(0, (3, 2)))
axs.set_ylim(0, 17)
axs.set_yticks([0, 10])
axs.set_ylabel("surface\nwet  (%)", labelpad=3, linespacing=1.2, fontsize=6.4)
axs.set_xlabel("2025", labelpad=2)
axs.tick_params(axis="x", labelsize=6.0)
axs.text(pd.Timestamp("2025-11-08"), 12.6, "annual mean 11.0%   ·   3.0% during the block",
         fontsize=5.7, color=S.C_SURF, ha="left", va="bottom")

if S.CAPTION:
    fig.text(0.075, 0.012,
             S.cap("The block is not a rain-driven state: the surface network recorded water in 3.0% of "
                   "its readings during it (peak 23 mm), seven instruments sat at their ceiling at once, "
                   "and the exit sequence cannot be produced by a water surface.", 140),
             fontsize=6.1, ha="left", va="bottom", color="#333333", linespacing=1.35)
S.save(fig, "Fig3_depth_limited_classification")
