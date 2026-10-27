# -*- coding: utf-8 -*-
"""Fig. 6  The 0.26 m bound is a wall, not a soft tail.

(a) smallest non-floor reading of every instrument;
(b) the five readings that fall below 0.25 m, with their neighbours;
(c) distribution of all readings between 0.25 and 0.35 m, in 10 mm bins.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import figstyle as S

S.apply()

SHORT = {
    "867948079403574": "01 Chifeng Rd", "867948079405843": "02 Structure Lab",
    "863721076643276": "03 NW Bldg", "867948079405678": "04 Pumped ch.",
    "867948079409829": "05 Ocean Bldg", "867948079405785": "06 Aixiao Rd",
    "867948079405611": "07 Medical Bldg", "867948079405652": "08 Dewen Lib.",
    "867948079405165": "09 Gymnasium", "867948079409803": "10 Gate",
    "867948079409621": "11 Tongwen Bldg", "867948079405546": "12 Cont. Educ.",
    "867948079407252": "13 Wenyuan Bldg",
}
a = pd.read_csv(f"{S.DATADIR}/fig6a_minburial.csv", encoding="utf-8-sig", dtype={"dev": str})
b = pd.read_csv(f"{S.DATADIR}/fig6b_excursion.csv", encoding="utf-8-sig", dtype={"dev": str})
c = pd.read_csv(f"{S.DATADIR}/fig6c_hist.csv", encoding="utf-8-sig")

a["short"] = a.dev.map(SHORT)
a["daily"] = a.dt_med > 600
a = a.sort_values(["min_nonfloor", "n"], ascending=[True, False]).reset_index(drop=True)

fig = plt.figure(figsize=(S.W2, 100 * S.MM))
gs = fig.add_gridspec(2, 2, width_ratios=[1.08, 1.0], height_ratios=[1.0, 1.12],
                      left=0.145, right=0.975, top=0.905, bottom=0.235,
                      wspace=0.42, hspace=0.72)

# ------------------------------------------------------- (a) smallest non-floor
ax = fig.add_subplot(gs[:, 0])
ax.axvspan(0, 0.26, color=S.C_BAND, lw=0, zorder=0)
ax.axvline(0.26, color="#6E6E6E", lw=0.6, ls=(0, (3, 1.6)), zorder=2)
ny = len(a)
for i, r in a.iterrows():
    filled = not bool(r.daily)
    ax.plot([0.26, r.min_nonfloor], [i, i], color="#CFCFCF", lw=0.7, zorder=2,
            solid_capstyle="butt")
    ax.scatter(r.min_nonfloor, i, s=16, zorder=4,
               facecolor=S.C_IN if filled else "white",
               edgecolor=S.C_IN if filled else "#7A7A7A",
               linewidth=0.7 if filled else 0.7)
    ax.text(0.955, i, "n = %d" % r.n, ha="right", va="center", fontsize=5.4, color="#7A7A7A")
ax.set_yticks(range(ny))
ax.set_yticklabels(a.short, fontsize=6.1)
ax.set_ylim(-0.7, ny - 0.3)
ax.set_xlim(0, 0.96)
ax.set_xticks([0, 0.1, 0.2, 0.26, 0.4, 0.6, 0.8])
ax.set_xticklabels(["0", "0.1", "0.2", "0.26", "0.4", "0.6", "0.8"])
ax.set_xlabel("smallest burial ever reported  (m)")
ax.text(0.125, ny - 0.55, "no depth\ninformation", ha="center", va="top", fontsize=5.7,
        color="#4D4D4D", linespacing=1.25)
ax.annotate("8 of 13 stop at\nexactly 0.26 m", xy=(0.276, 7.2), xytext=(0.40, 9.5),
            fontsize=5.8, ha="left", va="center", color=S.C_IN, linespacing=1.25,
            arrowprops=dict(arrowstyle="-", lw=0.45, color=S.C_IN))
h = [plt.Line2D([], [], marker="o", ls="none", ms=3.4, mfc=S.C_IN, mec=S.C_IN),
     plt.Line2D([], [], marker="o", ls="none", ms=3.4, mfc="white", mec="#7A7A7A")]
ax.legend(h, ["10-min or hourly cadence", "one reading per day"], loc="lower left",
          bbox_to_anchor=(0.015, 0.50), fontsize=5.5, handletextpad=0.35, labelspacing=0.25)
S.tag(ax, "a", x=-0.30, y=1.03)

# ------------------------------------------------------- (b) the five excursions
axb = fig.add_subplot(gs[0, 1])
axb.axhspan(0, 0.26, color=S.C_BAND, lw=0, zorder=0)
axb.axhline(0.25, color=S.C_ALERT, lw=0.5, ls=(0, (1.6, 1.4)), zorder=1)
xs = np.arange(len(b))
for i, r in b.iterrows():
    axb.plot([i - 0.17, i, i + 0.17], [r.prev, r.cur, r.nxt], color="#9A9A9A", lw=0.7, zorder=2)
    axb.scatter([i - 0.17, i + 0.17], [r.prev, r.nxt], s=9, color="#6E6E6E", zorder=3, lw=0)
    axb.scatter(i, r.cur, s=13, color=S.C_ALERT, zorder=4, lw=0)
axb.set_xticks(xs)
axb.set_xticklabels([SHORT[d].split(" ", 1)[1] for d in b.dev], fontsize=5.4, rotation=34,
                    ha="right", rotation_mode="anchor")
axb.set_xlim(-0.5, len(b) - 0.5)
axb.set_ylim(0, 2.95)
axb.set_yticks([0, 1, 2])
axb.set_ylabel("burial  (m)", labelpad=2)
axb.text(0.50, 0.94, "3 readings in one day,\n2 in the following July:\nsingle-point dips below the floor",
         transform=axb.transAxes, fontsize=5.6, va="top", linespacing=1.28, color="#4D4D4D")
S.tag(axb, "b", x=-0.24, y=1.10)

# ------------------------------------------------------- (c) the gap
axc = fig.add_subplot(gs[1, 1])
x = np.arange(len(c))
axc.bar(x, c.n, width=0.78, color=S.C_IN, lw=0)
axc.bar([0], [0], width=0.78)
axc.scatter(0, 0, s=16, marker="v", color=S.C_ALERT, zorder=4, clip_on=False)
axc.text(0, 3.0, "0", ha="center", va="bottom", fontsize=6.0, color=S.C_ALERT)
axc.set_xticks([0, 2, 4, 6, 8])
axc.set_xticklabels(["0.25", "0.27", "0.29", "0.31", "0.33"], fontsize=6.0)
axc.set_xlim(-0.65, 9.65)
axc.set_xlabel("burial  (m)", labelpad=2)
axc.set_ylabel("readings", labelpad=2)
axc.set_ylim(0, 66)
axc.set_yticks([0, 20, 40, 60])
# mark the modal 24 in the first occupied bin
for i, r in c.iterrows():
    if r.n:
        axc.text(i, r.n + 1.6, "%d" % r.n, ha="center", va="bottom", fontsize=5.2, color="#4D4D4D")
axc.text(0.02, 0.95, "321 readings from 11 instruments", transform=axc.transAxes,
         ha="left", va="top", fontsize=5.7, color="#4D4D4D")
S.tag(axc, "c", x=-0.24, y=1.12)

if S.CAPTION:
    fig.text(0.045, 0.012,
             S.cap("The lower bound is a wall, not the tail of a distribution. (a) Smallest reading above "
                   "the write-back value for each instrument; the dashed line is $D+B=0.26$ m. The three "
                   "open symbols are instruments that report once a day, so their bound is weak. (b) All "
                   "five readings below 0.25 m, with the reading before and after: every one is an "
                   "isolated point, four of them within three hours of the same reconnection. (c) All "
                   "readings between 0.25 and 0.35 m; the first bin is empty.", 150),
             fontsize=6.0, ha="left", va="bottom", color="#333333", linespacing=1.32)

S.save(fig, "Fig6_window_evidence")
