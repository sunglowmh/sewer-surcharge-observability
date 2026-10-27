# -*- coding: utf-8 -*-
"""Fig. 2  The two networks.

(a) the thirteen in-sewer ultrasonic instruments and the five surface (buried)
    instruments, drawn from registry coordinates; equal metric scale;
(b) the span and cadence of each record, with the three gauge-covered events
    marked. Site 03 has no registry coordinate and is shown in (b) only.
"""
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
import figstyle as S

S.apply()

d = pd.read_csv(f"{S.DATADIR}/fig2_sites.csv", encoding="utf-8-sig", dtype={"dev": str})
d["t0"] = pd.to_datetime(d.t0)
d["t1"] = pd.to_datetime(d.t1)
SHORT = {
    "867948079403574": "01 Chifeng Rd", "867948079405843": "02 Structure Lab",
    "863721076643276": "03 NW Bldg", "867948079405678": "04 Pumped ch.",
    "867948079409829": "05 Ocean Bldg", "867948079405785": "06 Aixiao Rd",
    "867948079405611": "07 Medical Bldg", "867948079405652": "08 Dewen Lib.",
    "867948079405165": "09 Gymnasium", "867948079409803": "10 Gate",
    "867948079409621": "11 Tongwen Bldg", "867948079405546": "12 Cont. Educ.",
    "867948079407252": "13 Wenyuan Bldg",
    "863342076635699": "S1 Chifeng Rd", "863342076635152": "S2 Gymnasium",
    "863342076635186": "S3 Auditorium", "863342076635095": "S4 Ruian Bldg",
    "869158077679187": "S5 Surveying",
}
d["label"] = [SHORT.get(x, "?") for x in d.dev]
d["num"] = [lb.split()[0] for lb in d.label]

fig = plt.figure(figsize=(S.W2, 86 * S.MM))
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.78], wspace=0.40,
                      left=0.030, right=0.845, top=0.930, bottom=0.255)

# ================================================================== (a) map
ax = fig.add_subplot(gs[0, 0])
sev = d[(d.kind == "sewer") & d.lon_gcj.notna()].copy()
sur = d[d.kind == "surface"].copy()

# ------------------------------------------------------------------ basemap
# An OpenStreetMap vector extract, on the WGS-84 graticule that OSM uses.  The
# registry is BD-09, so the frame and both site sets are carried through
# S.gcj2wgs before they meet the basemap; nothing is drawn on the GCJ-02
# graticule any more, which is what the earlier AMap raster required.  The
# extract carries roads, buildings, green space and water only, so the layer
# reads as a quiet locator rather than as a street map.
x_g0, x_g1, y_g0, y_g1 = [float(v) for v in
                          open(f"{S.DATADIR}/basemap_campus.txt",
                               encoding="utf-8").read().split()]
_f0 = S.gcj2wgs(x_g0, y_g0)
_f1 = S.gcj2wgs(x_g1, y_g1)
EXT = [_f0[0], _f1[0], _f0[1], _f1[1]]          # lon0, lon1, lat0, lat1

B = pd.read_csv(f"{S.DATADIR}/basemap_osm.csv")
_wgs = [S.gcj2wgs(lo, la) for lo, la in zip(sev.lon_gcj, sev.lat_gcj)]
sev["lon"], sev["lat"] = [p[0] for p in _wgs], [p[1] for p in _wgs]
_wgs = [S.gcj2wgs(lo, la) for lo, la in zip(sur.lon_gcj, sur.lat_gcj)]
sur["lon"], sur["lat"] = [p[0] for p in _wgs], [p[1] for p in _wgs]

from matplotlib.collections import LineCollection, PolyCollection  # noqa: E402


def _group(cls):
    return [(k, g.lon.values, g.lat.values)
            for k, g in B[B.cls.isin(cls)].groupby("way_id", sort=False)]


def _area(cls, fc, ec, z, lw=0.22):
    """Fill the closed rings, stroke whatever is not closed."""
    rings, open_ = [], []
    for _, lo, la in _group([cls]):
        if (len(lo) > 3 and abs(lo[0] - lo[-1]) < 1e-7
                and abs(la[0] - la[-1]) < 1e-7):
            rings.append(np.column_stack([lo, la]))
        else:
            open_.append(np.column_stack([lo, la]))
    if rings:
        ax.add_collection(PolyCollection(rings, facecolors=fc, edgecolors=ec,
                                         linewidths=lw, zorder=z))
    if open_:
        ax.add_collection(LineCollection(open_, colors=ec if ec != "none" else fc,
                                         linewidths=0.7, zorder=z))


def _roads(cls, color, lw, z, ls="solid", casing=None):
    segs = [np.column_stack([lo, la]) for _, lo, la in _group(cls)]
    if not segs:
        return
    if casing:
        ax.add_collection(LineCollection(segs, colors=casing,
                                         linewidths=lw * 2.3, zorder=z,
                                         capstyle="round"))
    ax.add_collection(LineCollection(segs, colors=color, linewidths=lw,
                                     zorder=z + 0.01, linestyles=ls,
                                     capstyle="round"))


_area("green", "#EBF1E7", "none", 0.50)
_area("water", "#D9E8F2", "#C9DCEA", 0.55, lw=0.3)
_area("building", "#EDEDED", "#DEDEDE", 0.70)
_roads(["t4"], "#D2D2D2", 0.30, 1.00)
_roads(["t3"], "#C6C6C6", 0.55, 1.20)
_roads(["t2"], "#B4B4B4", 1.05, 1.40, casing="white")
_roads(["t1"], "#ABABAB", 1.55, 1.60, casing="white")
_roads(["rail"], "#BDBDBD", 0.55, 1.30, ls=(0, (2.4, 1.6)))

ax.set_xlim(EXT[0], EXT[1])
ax.set_ylim(EXT[2], EXT[3])
ax.set_aspect(1 / np.cos(np.deg2rad(31.283)))

# campus outline: the operator's own polygon, taken from the DEM clip boundary
poly = pd.read_csv(f"{S.DATADIR}/campus_outline.csv")
_p = [S.gcj2wgs(lo, la) for lo, la in zip(poly.lon_gcj, poly.lat_gcj)]
ax.plot([q[0] for q in _p], [q[1] for q in _p], color="white", lw=1.1, zorder=2,
        solid_joinstyle="round")
ax.plot([q[0] for q in _p], [q[1] for q in _p], color="#5E5E5E", lw=0.55,
        ls=(0, (3.4, 2.4)), zorder=3, solid_joinstyle="round")

ax.scatter(sev.lon, sev.lat, s=26, marker="o", fc="#FFFFFF", ec=S.C_IN,
           lw=0.95, zorder=4)
ax.scatter(sur.lon, sur.lat, s=20, marker="s", fc=S.C_SURF, ec="#FFFFFF",
           lw=0.6, zorder=5)

OFF = {  # label offsets in points, hand-placed to avoid the close pairs
    "01": (-7.5, -2.0), "02": (-7.5, 2.2), "04": (0, 6.4), "05": (0, 6.2),
    "06": (0, 4.8), "07": (0, -5.0), "08": (-6.2, -2.0), "09": (2.0, -6.6),
    "10": (5.4, -2.2), "11": (0, 6.4), "12": (-7.5, 0.6), "13": (2.4, 6.4),
    "S1": (4.4, 3.2), "S2": (5.4, -3.4), "S3": (-1.2, -6.6), "S4": (-6.8, -2.2),
    "S5": (4.6, 3.2),
}
for (x, y), (_, r) in zip(zip(sev.lon, sev.lat), sev.iterrows()):
    dx, dy = OFF.get(r.num, (4, 3))
    ax.annotate(r.num, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                fontsize=6.2, color=S.C_IN, fontweight="bold", zorder=6,
                ha="center" if dx == 0 else ("right" if dx < 0 else "left"),
                va="bottom" if dy > 3 else ("top" if dy < -3 else "center"),
                path_effects=[pe.withStroke(linewidth=1.6, foreground="white")])
for (x, y), (_, r) in zip(zip(sur.lon, sur.lat), sur.iterrows()):
    dx, dy = OFF.get(r.num, (4, -7))
    ax.annotate(r.num, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                fontsize=6.0, color="#1B4961", zorder=6,
                ha="center" if dx == 0 else ("right" if dx < 0 else "left"),
                va="bottom" if dy > 3 else ("top" if dy < -3 else "center"),
                path_effects=[pe.withStroke(linewidth=1.6, foreground="white")])

ax.set_xticks([])
ax.set_yticks([])
for sp in ("top", "right", "bottom", "left"):
    ax.spines[sp].set_visible(True)
    ax.spines[sp].set_linewidth(0.5)
    ax.spines[sp].set_color("#8C8C8C")

# scale bar 200 m, bottom left
lat_s = EXT[2] + (EXT[3] - EXT[2]) * 0.045
lon_s = EXT[0] + (EXT[1] - EXT[0]) * 0.045
dlon = 200 / 94500.0
ax.plot([lon_s, lon_s + dlon], [lat_s, lat_s], color="k", lw=1.8,
        solid_capstyle="butt", zorder=7,
        path_effects=[pe.withStroke(linewidth=3.0, foreground="white")])
ax.text(lon_s + dlon / 2, lat_s - (EXT[3] - EXT[2]) * 0.018, "200 m",
        ha="center", va="top", fontsize=6.0, zorder=7,
        path_effects=[pe.withStroke(linewidth=1.8, foreground="white")])

# Basemap attribution, inside the map itself.  Copernicus: "The copyright/
# attribution and distribution licences of such maps must be visible in the
# maps themselves", so this cannot live in the caption alone.
ax.text(EXT[1] - (EXT[1] - EXT[0]) * 0.012,
        EXT[2] + (EXT[3] - EXT[2]) * 0.012,
        "\u00a9 OpenStreetMap contributors", ha="right", va="bottom",
        fontsize=5.6, color="#4D4D4D", zorder=7,
        path_effects=[pe.withStroke(linewidth=1.6, foreground="white")])

# north arrow, top right
nx_ = EXT[1] - (EXT[1] - EXT[0]) * 0.055
ny_ = EXT[3] - (EXT[3] - EXT[2]) * 0.145
ax.annotate("", xy=(nx_, ny_ + (EXT[3] - EXT[2]) * 0.045),
            xytext=(nx_, ny_ - (EXT[3] - EXT[2]) * 0.045),
            arrowprops=dict(arrowstyle="-|>,head_width=0.14,head_length=0.26",
                            lw=0.6, color="k"), zorder=7)
ax.text(nx_, ny_ + (EXT[3] - EXT[2]) * 0.055, "N", ha="center", va="bottom",
        fontsize=6.2, zorder=7,
        path_effects=[pe.withStroke(linewidth=1.8, foreground="white")])

S.tag(ax, "a", x=-0.04, y=1.02)

# ================================================================== (b) spans
ax2 = fig.add_subplot(gs[0, 1])
o = d.sort_values(["kind", "t0"], ascending=[True, True]).reset_index(drop=True)
ypos = np.arange(len(o))[::-1]

# sampling cadence is coded by the line style of the span itself, so that the
# reader sees how densely each instrument reported without a separate column
LS = {"10 min": "solid", "on change": (0, (3.0, 1.5)), "24 h": (0, (1.0, 1.7))}
for i, r in o.iterrows():
    y = ypos[i]
    c = S.C_IN if r.kind == "sewer" else S.C_SURF
    cad = "10 min" if r.dt_med <= 15 else ("24 h" if r.dt_med >= 1000 else "on change")
    ax2.plot([r.t0, r.t1], [y, y], color=c, lw=1.3 if r.kind == "sewer" else 1.05,
             ls=LS[cad], solid_capstyle="butt", dash_capstyle="butt", zorder=3)
    ax2.plot([r.t0], [y], marker="o", ms=2.4, mfc=c, mec="none", zorder=4)
    ax2.plot([r.t1], [y], marker="|", ms=4.0, mec=c, mew=0.9, zorder=4)
    ax2.text(1.115, y, "{:,}".format(r.n), transform=ax2.get_yaxis_transform(),
             fontsize=5.8, va="center", ha="right", color="#333333")

NY = len(o)
ax2.set_yticks(ypos)
ax2.set_yticklabels(o.label, fontsize=6.2)
ax2.set_ylim(-0.9, NY + 2.6)
ax2.set_xlim(pd.Timestamp("2025-05-10"), pd.Timestamp("2026-10-20"))
ax2.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax2.tick_params(axis="x", labelsize=6.0)

ax2.axvline(pd.Timestamp("2025-09-11"), color="#333333", lw=0.6, ls=(0, (4, 2)), zorder=2)
ax2.text(pd.Timestamp("2025-09-08"), NY + 0.30, "archive begins\n11 Sep 2025",
         fontsize=5.8, color="#333333", ha="right", va="center", linespacing=1.25)

EV = [("2026-07-12", "Bavi  19.4 mm", NY + 0.30, "right", -0.012),
      ("2026-07-19", "19 Jul  164.6 mm", NY + 1.45, "center", 0.0),
      ("2026-08-10", "Typhoon Dolphin  243.2 mm", NY + 2.55, "left", 0.012)]
for t, lab, yt, ha, dxd in EV:
    tt = pd.Timestamp(t)
    ax2.axvline(tt, color="#8C8C8C", lw=0.5, ls=(0, (1.6, 2.0)), zorder=2)
    ax2.annotate(lab, xy=(tt + pd.Timedelta(days=dxd * 900), yt), fontsize=5.8,
                 color="#333333", ha=ha, va="center", zorder=6,
                 bbox=dict(fc="w", ec="none", pad=0.8))

ax2.text(1.115, NY + 0.15, "readings", transform=ax2.get_yaxis_transform(),
         fontsize=5.8, va="bottom", ha="right", color="#8C8C8C", style="italic")
# line-style key: the sampling cadence is encoded only by the line style, so
# the key has to sit on the same line as the panel label and be legible
for x0, lab, ls in ((0.015, "10 min", "solid"),
                    (0.300, "on change", (0, (3.0, 1.5))),
                    (0.620, "24 h", (0, (1.0, 1.7)))):
    ax2.plot([x0, x0 + 0.085], [1.055, 1.055], transform=ax2.transAxes,
             color="#333333", lw=1.2, ls=ls, solid_capstyle="butt",
             dash_capstyle="butt", clip_on=False, zorder=4)
    ax2.text(x0 + 0.100, 1.055, lab, transform=ax2.transAxes, fontsize=5.8,
             va="center", ha="left", color="#333333", clip_on=False)
S.tag(ax2, "b", x=-0.26, y=1.02)

if S.CAPTION:
    fig.text(0.032, 0.020,
             S.cap("Open circles: thirteen in-sewer ultrasonic instruments; filled squares: five "
                   "surface (buried) instruments. Positions come from the operator registry, which "
                   "is held on the BD-09 graticule, and are converted to WGS-84 to match the "
                   "basemap; they are drawn for location only: no result in this paper depends on "
                   "them. Dashed line: campus boundary, from the operator's drainage drawing. "
                   "Surface sites are labelled S1 to S5. In (b) "
                   "the line style gives the sampling cadence (key at the top), the filled circle "
                   "marks the first reading and the vertical bar the last. Site 03 (19,078 "
                   "readings, the second largest record) has no registry coordinate and appears in "
                   "(b) only. Basemap: \u00a9 OpenStreetMap contributors (ODbL 1.0), reduced to "
                   "roads, buildings, green space and water. "
                   "The three gauge-covered storms are dotted vertical lines.", 150),
             fontsize=6.1, ha="left", va="bottom", color="#333333", linespacing=1.4)

S.save(fig, "Fig2_site_networks", pdf_dpi=420)
