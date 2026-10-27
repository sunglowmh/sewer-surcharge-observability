# -*- coding: utf-8 -*-
"""Fig. 4  Dose and response.

(a) blindness rate for every instrument x event combination with a sampling
    interval of one hour or less, ordered by rate in the 164.6 mm event;
(b) the same response against surface standing water, pooled over
    device-by-ten-minute cells, with the zero-rain baseline.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import figstyle as S

S.apply()

dm = pd.read_csv(f"{S.DATADIR}/../p3a_dose_matrix.csv", encoding="utf-8-sig",
                 dtype={"dev": str})
dr = pd.read_csv(f"{S.DATADIR}/../p3a_dose_response_dual.csv", encoding="utf-8-sig")

EV = [("巴威", "Bavi\n19.4 mm"), ("0719暴雨", "19 Jul\n164.6 mm"),
      ("白海豚", "Dolphin\n243.2 mm")]
SHORT = {  # short instrument names for the heat-map rows
    "403574": "01 Chifeng Rd", "405843": "02 Structure Lab",
    "643276": "03 NW Bldg", "405678": "04 Pumped ch.",
    "409829": "05 Ocean Bldg", "405785": "06 Aixiao Rd",
    "405611": "07 Medical Bldg", "405652": "08 Dewen Lib.",
    "405165": "09 Gymnasium", "409803": "10 Gate",
    "409621": "11 Tongwen Bldg", "405546": "12 Cont. Educ.",
    "407252": "13 Wenyuan Bldg",
}
dm["short"] = dm.dev.map(SHORT)
dm["ev_i"] = dm.ev.map({e: i for i, (e, _) in enumerate(EV)})

# order rows by the 19 Jul rate, then by the largest rate available
piv = dm.pivot_table(index="short", columns="ev", values="f_cell", aggfunc="max")
piv = piv.reindex(columns=[e for e, _ in EV])
order = piv.assign(k=piv.get("0719暴雨", pd.Series(dtype=float)).fillna(-1)) \
           .sort_values("k", ascending=False).index.tolist()

fig = plt.figure(figsize=(S.W2, 110 * S.MM))
gs = fig.add_gridspec(1, 2, width_ratios=[1.28, 1.0], wspace=0.42,
                      left=0.145, right=0.985, top=0.905, bottom=0.285)

# ============================================================ (a) heat map
ax = fig.add_subplot(gs[0, 0])
nx, ny = len(EV), len(order)
for i, name in enumerate(order):
    for j, (ev, _) in enumerate(EV):
        r = dm[(dm.short == name) & (dm.ev == ev)]
        y = ny - 1 - i
        if len(r) == 0:
            ax.add_patch(Rectangle((j + 0.06, y + 0.06), 0.88, 0.88, fc="#FAFAFA",
                                   ec="#DCDCDC", lw=0.4, hatch="xxx", zorder=2))
            continue
        r = r.iloc[0]
        nlab = "n=%d" % int(r.n)
        if not bool(r.usable):
            ax.add_patch(Rectangle((j + 0.06, y + 0.06), 0.88, 0.88, fc="#F2F2F2",
                                   ec="#BFBFBF", lw=0.4, hatch="////", zorder=2))
            ax.text(j + 0.92, y + 0.92, nlab, ha="right", va="top",
                    fontsize=5.0, color="#8C8C8C", zorder=3)
            continue
        v = float(r.f_cell) * 100
        pump = name.startswith("04")
        fc = (plt.cm.Greys(0.10 + 0.52 * v / 100) if pump
              else plt.cm.Blues(0.06 + 0.80 * v / 100))
        ax.add_patch(Rectangle((j + 0.06, y + 0.06), 0.88, 0.88, fc=fc, ec="none", zorder=2))
        dk = (v > 55) and not pump
        ax.text(j + 0.5, y + 0.44, "%.0f%%" % v, ha="center", va="center", fontsize=7.2,
                color="w" if dk else "#111111", fontweight="bold", zorder=3)
        ax.text(j + 0.92, y + 0.92, nlab, ha="right", va="top",
                fontsize=5.0, color="w" if dk else "#555555", zorder=3)

ax.set_xlim(0, nx)
ax.set_ylim(0, ny)
ax.set_xticks(np.arange(nx) + 0.5)
ax.set_xticklabels([lab for _, lab in EV], fontsize=6.3, linespacing=1.25)
ax.xaxis.set_ticks_position("top")
ax.set_yticks(np.arange(ny)[::-1] + 0.5)
ax.set_yticklabels(order, fontsize=6.2)
for sp in ("top", "right", "left", "bottom"):
    ax.spines[sp].set_visible(False)
ax.tick_params(length=0)
ax.text(-0.02, ny + 0.72, "rainfall total", ha="right", va="center", fontsize=6.0,
        color="#4D4D4D", style="italic")

for row in ax.get_yticklabels():
    if row.get_text().startswith("04"):
        row.set_color("#7A7A7A")
        row.set_style("italic")
        row.set_text("04 Pumped ch.  (pumped)")
h = [Rectangle((0, 0), 1, 1, fc="#F2F2F2", ec="#BFBFBF", lw=0.4, hatch="////",
               label="too few readings to resolve a storm"),
     Rectangle((0, 0), 1, 1, fc="#FAFAFA", ec="#DCDCDC", lw=0.4, hatch="xxx",
               label="no readings in the event"),
     Rectangle((0, 0), 1, 1, fc=plt.cm.Greys(0.38), ec="none",
               label="pumped chamber, excluded")]
ax.legend(handles=h, loc="upper left", bbox_to_anchor=(0.0, -0.045), handlelength=1.9,
          handleheight=1.15, borderpad=0.0, handletextpad=0.55)
S.tag(ax, "a", x=-0.30, y=1.13)

# ============================================================ (b) vs flooding
ax2 = fig.add_subplot(gs[0, 1])
dr["lab"] = dr.dbin.astype(str).str.replace('"(0,10]"', "0–10").str.replace('"(10,20]"', "10–20") \
    .str.replace('"(20,30]"', "20–30").str.replace('"(30,50]"', "30–50") \
    .str.replace('"(50,80]"', "50–80").str.replace(">80", ">80").str.replace("0", "0")
x = np.arange(len(dr))
v = dr.f_cell_pooled.values * 100
sz = np.clip(dr.n_bins.values * 0.55, 8, 90)
ax2.axhline(dr.f_cell_pooled.iloc[0] * 100, color="#8C8C8C", lw=0.6, ls=(0, (3, 2)))
ax2.vlines(x, dr.f_cell_pooled.iloc[0] * 100, v, color="#C9C9C9", lw=0.7, zorder=1)
ax2.scatter(x, v, s=sz, c=v, cmap="Blues", vmin=-25, vmax=110, edgecolor="k",
            linewidth=0.45, zorder=3)
for xi, vi, nb in zip(x, v, dr.n_bins.values):
    ax2.text(xi, vi + 7, "%.0f" % vi, ha="center", va="bottom", fontsize=5.9)
ax2.set_xticks(x)
ax2.set_xticklabels(["0", "0–10", "10–20", "20–30", "30–50", "50–80", ">80"], fontsize=6.2)
ax2.set_xlabel("surface standing water in the same 10 min bin  (mm)")
ax2.set_ylabel("depth-limited readings  (%)")
ax2.set_ylim(-2, 116)
ax2.set_xlim(-0.6, len(dr) - 0.4)
ax2.text(0.02, 0.965, "dashed: no standing water  (7.8%)",
         transform=ax2.transAxes, fontsize=5.7, ha="left", va="top", color="#8C8C8C")
ax2.annotate("all %d device–10-min\ncells in this bin" % int(dr.n_bins.iloc[-1]), xy=(6, 96),
             xytext=(4.45, 62), fontsize=5.8, ha="right", va="center", linespacing=1.2,
             arrowprops=dict(arrowstyle="-", lw=0.4, color="#8C8C8C"))
S.tag(ax2, "b", x=-0.30, y=1.06)

if S.CAPTION:
    fig.text(0.055, 0.012,
             S.cap("Panel (a) keeps only combinations sampled at one hour or less in both directions; "
                   "hatched cells could not resolve a storm (sparse sampling, or no reading inside the "
                   "event window). The pumped chamber (04, grey) is shown for completeness but "
                   "excluded from the pooled response: its level is set by pump cycling, not by "
                   "rainfall. "
                   "Panel (b) pools device-by-10-min cells (marker area scales with the number of "
                   "cells), so a cell is not an independent observation."),
             fontsize=6.1, ha="left", va="bottom", color="#333333", linespacing=1.35)
S.save(fig, "Fig4_dose_response")
