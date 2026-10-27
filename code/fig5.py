# -*- coding: utf-8 -*-
"""Fig. 5  Coincidence at the storm peak (19 July 2026).

(a) surface forcing: peak standing water per 10 min bin and the share of surface
    readings that saw water;
(b) response of the sewer network: share of reporting instruments whose reading
    sits on the write-back value, marker area = number of such instruments;
(c) one record at the record scale: burial of 11 Tongwen Bldg, which stops at
    the write-back value while the surface is still rising.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import figstyle as S

S.apply()

t0 = pd.Timestamp("2026-07-19 12:00")
t1 = pd.Timestamp("2026-07-20 00:00")
P0 = pd.Timestamp("2026-07-19 14:00")   # peak window used in the text
P1 = pd.Timestamp("2026-07-19 17:00")

st = pd.read_csv(f"{S.DATADIR}/fig5_status.csv", encoding="utf-8-sig", dtype={"dev": str})
st["bin"] = pd.to_datetime(st.bin)
tr = pd.read_csv(f"{S.DATADIR}/fig5_trace.csv", encoding="utf-8-sig")
tr["t"] = pd.to_datetime(tr.t)
sf = pd.read_csv(f"{S.DATADIR}/fig5_surface.csv", encoding="utf-8-sig")
sf["b10"] = pd.to_datetime(sf.b10)
sf = sf[(sf.b10 >= t0) & (sf.b10 < t1)]
tr = tr[(tr.t >= t0) & (tr.t < t1)]

st["locked"] = st.f >= 0.5
g = st.groupby("bin").agg(cells=("locked", "size"), lock=("locked", "sum")).reset_index()
g["share"] = g.lock / g.cells * 100
mm = (g.bin >= P0) & (g.bin < P1)
print("peak window cells %d/%d = %.1f%%" % (g.loc[mm, "lock"].sum(), g.loc[mm, "cells"].sum(),
                                            g.loc[mm, "lock"].sum() / g.loc[mm, "cells"].sum() * 100))

fig = plt.figure(figsize=(S.W2, 112 * S.MM))
gs = fig.add_gridspec(3, 1, height_ratios=[1.05, 0.95, 2.15], hspace=0.20,
                      left=0.135, right=0.975, top=0.945, bottom=0.205)


def frame(ax, top=False):
    ax.set_xlim(t0, t1)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.axvspan(P0, P1, color="#F2F2F2", zorder=0, lw=0)
    if not top:
        ax.tick_params(axis="x", labelbottom=False)
    else:
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, 2)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.set_xlabel("19 July 2026  (UTC+8)")


# ------------------------------------------------------- (a) surface forcing
ax1 = fig.add_subplot(gs[0, 0])
frame(ax1)
ax1.fill_between(sf.b10, 0, sf.peak, color=S.C_RAIN, lw=0, alpha=0.9, step="mid")
ax1.plot(sf.b10, sf.peak, color="#4F93B8", lw=0.7, drawstyle="steps-mid")
ax1.set_ylim(0, 215)
ax1.set_ylabel("surface peak\n(mm)", labelpad=2, linespacing=1.25)
ax1.set_yticks([0, 100, 200])
mw = (sf.b10 >= P0) & (sf.b10 < P1)
ax1.text(0.012, 0.94, "water present in %d of %d surface readings, 14:00-17:00"
         % (int(sf.loc[mw, "k"].sum()), int(sf.loc[mw, "n"].sum())),
         transform=ax1.transAxes, ha="left", va="top", fontsize=5.8, color=S.C_SURF)
S.tag(ax1, "a", x=-0.132, y=1.16)

# ------------------------------------------------------- (b) network response
ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)
frame(ax2)
ax2.step(g.bin, g.share, where="mid", color=S.C_IN, lw=0.8)
sizes = 5 + 6.5 * g.cells
ax2.scatter(g.bin, g.share, s=sizes, color=S.C_IN, edgecolor="w", linewidth=0.3, zorder=3)
ax2.axhline(100, color="#C9C9C9", lw=0.5, ls=(0, (2, 2)), zorder=1)
ax2.set_ylim(-14, 132)
ax2.set_yticks([0, 50, 100])
ax2.set_ylabel("at write-back\nvalue (%)", labelpad=2, linespacing=1.25)
ax2.annotate("", xy=(P0, 112), xytext=(P1, 112),
             arrowprops=dict(arrowstyle="|-|,widthA=0.15,widthB=0.15", lw=0.5, color="#666666"))
ax2.text(P0 + (P1 - P0) / 2, 115, "%d of %d cells" % (g.loc[mm, "lock"].sum(),
                                                      g.loc[mm, "cells"].sum()),
         ha="center", va="bottom", fontsize=5.9, color="#333333")
S.tag(ax2, "b", x=-0.132, y=1.14)

# ------------------------------------------------------- (c) one record
ax3 = fig.add_subplot(gs[2, 0], sharex=ax1)
frame(ax3, top=True)
ax3.axhspan(0, 0.26, color=S.C_BAND, lw=0, zorder=0)
ax3.plot(tr.t, tr.burial, color="#333333", lw=0.7, zorder=3)
ax3.scatter(tr.loc[tr.cens, "t"], tr.loc[tr.cens, "burial"], s=3.2, color=S.C_ALERT,
            zorder=4, lw=0)
ax3.set_ylim(0.72, 0)
ax3.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
ax3.set_ylabel("burial below\ncover  (m)", labelpad=2, linespacing=1.25)
ax3.text(pd.Timestamp("2026-07-19 12:08"), 0.115, "no depth information", fontsize=5.8,
         color="#4D4D4D", va="center")
ax3.text(pd.Timestamp("2026-07-20 00:00"), 0.27, "0.26 m", fontsize=5.6, color="#8C8C8C",
         ha="right", va="bottom")
ax3.annotate("record stops at 0.25 m at 14:08\nand stays there for the whole peak",
             xy=(pd.Timestamp("2026-07-19 14:40"), 0.252),
             xytext=(pd.Timestamp("2026-07-19 14:55"), 0.46), fontsize=5.8, linespacing=1.25,
             ha="left", va="center",
             arrowprops=dict(arrowstyle="-", lw=0.4, color="#666666"))
ax3.annotate("recession: the record can be followed again",
             xy=(pd.Timestamp("2026-07-19 18:30"), 0.60),
             xytext=(pd.Timestamp("2026-07-19 18:45"), 0.69), fontsize=5.8, ha="left",
             va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color="#666666"))
ax3.text(0.988, 0.13, "%d of %d readings in 12 h at the write-back value" % (int(tr.cens.sum()), len(tr)),
         transform=ax3.transAxes, ha="right", va="center", fontsize=5.6, color=S.C_ALERT)
S.tag(ax3, "c", x=-0.132, y=1.07)

if S.CAPTION:
    fig.text(0.045, 0.012,
             S.cap("The storm peak is exactly where the sewer record goes blind. (a) 10-min peak "
                   "standing water at the surface gauges. (b) Share of reporting sewer instruments whose "
                   "reading equals the write-back value $J-0.25$ m; only four instruments reported at "
                   "10-min cadence on this day, so the marker area carries the sample size. (c) Burial "
                   "of 11 Tongwen Bldg on an inverted axis: the trace enters the 0.26 m window and is "
                   "clipped there while the surface is still rising; 52 of the 72 ten-minute readings of "
                   "the 12 h shown carry the write-back value, and the same 52 give 52 of 67 over the "
                   "11.2 h rainfall-active period. Grey band 14:00-17:00.", 150),
             fontsize=6.0, ha="left", va="bottom", color="#333333", linespacing=1.32)

S.save(fig, "Fig5_peak_coincidence")
