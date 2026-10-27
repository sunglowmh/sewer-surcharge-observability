# -*- coding: utf-8 -*-
"""
Fig. 7  The criterion and the archive's response   (RQ2, RQ3)
Fig. 9  Network centring: Omega independent of J, phi proportional to 1/J,
        and the vacant threshold band                                  (RQ4)

Inputs (authoritative, no recomputation of any reported number):
  outputs/p3a_obs_index.csv      12 threshold configurations: Omega, D_obs, alarms
  outputs/p3a_Omega_config.csv   same 12 configurations: readable / floor / below-thr
  outputs/p3a_J_segments.csv     13 instruments, well-depth segments

Canvas: 183 mm double column, Arial 7 pt, vector PDF (fonttype 42) + 600 dpi PNG.
"""
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import NullLocator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root, not the author's machine
OUT = os.path.join(ROOT, "figures")
os.makedirs(OUT, exist_ok=True)
MM = 1 / 25.4
W2 = 176 * MM        # HESS type area 177 mm (see figstyle.py)
W2_MAX = 177.0

# --------------------------------------------------------------------------- style
plt.rcParams.update({
    "font.family": "Arial",
    "mathtext.fontset": "custom",
    "mathtext.rm": "Arial",
    "mathtext.it": "Arial:italic",
    "mathtext.bf": "Arial:bold",
    "mathtext.default": "it",
    "font.size": 7,
    "axes.labelsize": 7.2,
    "xtick.labelsize": 6.6,
    "ytick.labelsize": 6.6,
    "legend.fontsize": 6.4,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.4,
    "ytick.major.size": 2.4,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "lines.linewidth": 0.8,
    "figure.dpi": 200,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})

C_IN, C_OUT = "#0072B2", "#E69F00"      # Omega > 1 / Omega <= 1
C_BAND = "#D8D8D8"
C_Y, C_B, C_R = "#EE854A", "#4878CF", "#B8B8B8"
C_GREY, C_GRID = "#5A5A5A", "#EBEBEB"

EN = {
    "867948079403574": "01 Chifeng Rd", "867948079405843": "02 Structure Lab",
    "863721076643276": "03 NW Bldg", "867948079405678": "04 Pumped chamber",
    "867948079409829": "05 Ocean Bldg", "867948079405785": "06 Aixiao Rd",
    "867948079405611": "07 Medical Bldg", "867948079405652": "08 Dewen Library",
    "867948079405165": "09 Gymnasium", "867948079409803": "10 Gate display",
    "867948079409621": "11 Tongwen Bldg", "867948079405546": "12 Cont. Educ.",
    "867948079407252": "13 Wenyuan Bldg",
}

# --------------------------------------------------------------------------- data
cfg = pd.read_csv(f"{ROOT}/outputs/p3a_Omega_config.csv", encoding="utf-8-sig")
ob = pd.read_csv(f"{ROOT}/outputs/p3a_obs_index.csv", encoding="utf-8-sig")
ob["dev"] = ob["dev"].astype(str)
cfg["k"] = cfg["thr"].round(2).astype(str) + "_" + cfg["J"].round(2).astype(str)
ob["k"] = ob["thr"].round(2).astype(str) + "_" + ob["Jp"].round(2).astype(str)
assert cfg["k"].is_unique and ob["k"].is_unique

# Row order is not decided here: Table 2 freezes it in table2_roworder.csv and
# this figure stacks the twelve lines in the same order, row 1 on top.  Any
# other sort would let "configuration 5" mean two different wells in the table
# and in the panel.
ro = pd.read_csv(f"{ROOT}/outputs/tables/table2_roworder.csv", encoding="utf-8-sig",
                 dtype={"dev": str})
ro["k"] = ro["thr"].round(2).astype(str) + "_" + ro["J"].round(2).astype(str)
assert len(ro) == 12 and ro["k"].is_unique
assert ro["No."].tolist() == list(range(1, 13))

d = ob.merge(cfg[["k", "n_read", "n_elev"]], on="k", how="left", validate="one_to_one")
d = d.merge(ro[["k", "No.", "dev"]].rename(columns={"dev": "dev_ro"}),
            on="k", how="left", validate="one_to_one")
assert d["No."].notna().all(), "a configuration in the figure is missing from Table 2"
assert d["dev_ro"].eq(d["dev"].astype(str)).all(), "device mismatch against Table 2"
d = d.sort_values("No.").reset_index(drop=True)
assert d["No."].tolist() == list(range(1, 13))
assert d["Omega"].is_monotonic_increasing
d["site"] = d["dev"].map(EN)
d["lab"] = d["site"] + " " + d["thr"].map(lambda v: f"{v:.2f}")
# row 1 at the top: the panel reads downward like the table does
d["y"] = len(d) - 1 - np.arange(len(d))

# integrity checks — the figure must not be drawn if any of these fail
assert len(d) == 12
assert int((d.Omega <= 1).sum()) == 5 and int((d.Omega > 1).sum()) == 7
assert d.loc[d.Omega <= 1, "n_elev"].sum() == 0
assert (d.loc[d.Omega > 1, "n_elev"] >= 1).all()
assert d.loc[d.Omega <= 1, "n"].sum() == 90 and d["n"].sum() == 305
assert np.allclose(d.Omega, (d.Jp - d.thr) / 0.26, atol=0.002)

NB = 5                      # rows with Omega <= 1, i.e. Table 2 rows 1-5 (drawn on top)
NROW = len(d)
Y_HI = NROW - 1 + 0.55      # 11.55
Y_LO = -0.55
BAND = (NROW - NB - 0.5, Y_HI)   # 6.5 .. 11.55
assert (d.loc[d.Omega <= 1, "y"] >= BAND[0]).all()
assert (d.loc[d.Omega > 1, "y"] <= BAND[0]).all()


def decorate(ax, grid=True):
    ax.set_ylim(Y_LO, Y_HI)
    ax.axhspan(BAND[0], BAND[1], color=C_BAND, alpha=0.5, lw=0, zorder=0.3)
    if grid:
        for yy in range(NROW):
            ax.axhline(yy, color=C_GRID, lw=0.45, zorder=0.6)


def tag(ax, s, x=-0.03, y=1.02):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=8, fontweight="bold",
            va="bottom", ha="right")


# =========================================================================== FIG 7
fig = plt.figure(figsize=(W2, 94 * MM))
gs = GridSpec(1, 3, figure=fig, width_ratios=[1.00, 1.00, 1.20], wspace=0.15,
              left=0.180, right=0.988, top=0.885, bottom=0.150)
axA = fig.add_subplot(gs[0])
axB = fig.add_subplot(gs[1], sharey=axA)
axC = fig.add_subplot(gs[2], sharey=axA)

# --- (a) position on the criterion -------------------------------------------
decorate(axA)
axA.axvline(1.0, color="k", lw=0.9, zorder=2)
axA.plot(d.Omega, d.y, "o", ms=4.0, mfc="k", mec="k", mew=0.6, zorder=3)
axA.set_xlim(0.30, 1.62)
axA.set_yticks(d.y.tolist())
axA.set_yticklabels(d.lab.tolist())
axA.set_xticks([0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
axA.set_xlabel(r"$\Omega \;=\; b_\theta \,/\, (D+B)$")
axA.text(1.575, (BAND[0] + BAND[1]) / 2, r"$\Omega\leq1$   (5 of 12)", rotation=90,
         fontsize=6.3, color=C_GREY, ha="center", va="center", zorder=5)
tag(axA, "a", x=-0.62)

# --- (b) what the archive then records ---------------------------------------
decorate(axB, grid=True)
axB.set_xscale("symlog", linthresh=1.0, linscale=1.45)
axB.axvline(1.0, color=C_GREY, lw=0.6, ls=(0, (2.5, 2)), zorder=1)
axB.plot(d.n_elev, d.y, "o", ms=4.0, mfc=C_IN, mec="k", mew=0.6, zorder=4)
axB.set_xlim(-0.28, 62)
axB.set_xticks([0, 1, 2, 5, 10, 20, 50])
axB.set_xticklabels(["0", "1", "2", "5", "10", "20", "50"])
axB.xaxis.set_minor_locator(NullLocator())
axB.set_xlabel(r"readings below $b_\theta$   ($n$)")
axB.text(15, (BAND[0] + BAND[1]) / 2, "0 of 5", fontsize=7, color=C_OUT,
         fontweight="bold", ha="left", va="center")
axB.text(15, BAND[0] - 0.6, "7 of 7 $\\geq$ 1", fontsize=7, color=C_IN,
         fontweight="bold", ha="left", va="center")
tag(axB, "b", x=-0.06)

# --- (c) what the platform logged --------------------------------------------
decorate(axC, grid=True)
left = np.zeros(len(d))
for col, c in (("yellow", C_Y), ("blue", C_B), ("red", C_R)):
    axC.barh(d.y, d[col], left=left, height=0.60, color=c, edgecolor="none", zorder=3)
    left = left + d[col].values
axC.set_xlim(0, 132)
axC.set_xticks([0, 25, 50, 75, 100])
axC.set_xlabel(r"alarms logged   ($n$)")
_y70 = d.loc[(d.yellow + d.blue + d.red) == 70, "y"]
assert len(_y70) == 1, "the 70-alarm configuration is no longer unique"
axC.text(72, float(_y70.iloc[0]), "70", fontsize=7, ha="left", va="center",
         fontweight="bold")

xb = 108
axC.plot([xb, xb], [BAND[0] + 0.08, BAND[1] - 0.08], color="k", lw=0.7, clip_on=False)
for yy in (BAND[0] + 0.08, BAND[1] - 0.08):
    axC.plot([xb - 2.0, xb], [yy, yy], color="k", lw=0.7, clip_on=False)
axC.text(xb + 2.2, (BAND[0] + BAND[1]) / 2, "90", fontsize=7.6, fontweight="bold",
         va="center", ha="left")
hc = [Patch(fc=C_Y, ec="none", label="above threshold"),
      Patch(fc=C_B, ec="none", label="receded"),
      Patch(fc=C_R, ec="none", label="fault")]
axC.legend(handles=hc, loc="lower right", bbox_to_anchor=(1.02, 0.0), frameon=False,
           handlelength=1.1, handleheight=0.8, handletextpad=0.4, borderpad=0.0,
           labelspacing=0.25)
tag(axC, "c", x=-0.06)

for ax in (axB, axC):
    ax.tick_params(axis="y", length=0)
    plt.setp(ax.get_yticklabels(), visible=False)

for ext in ("pdf", "png", "svg"):
    fig.savefig(os.path.join(OUT, f"Fig7_Omega_criterion.{ext}"), format=ext)
_bb = fig.get_tightbbox(fig.canvas.get_renderer())
print("Fig7 size %.1f x %.1f mm%s" % (_bb.width * 25.4, _bb.height * 25.4,
      "   <-- OVER WIDTH" if _bb.width * 25.4 > W2_MAX else ""))
plt.close(fig)

# =========================================================================== FIG 9
seg = pd.read_csv(f"{ROOT}/outputs/p3a_J_segments.csv", encoding="utf-8-sig")
seg["dev"] = seg["dev"].astype(str)
seg = seg[seg["keep"]]
seg = seg[~((seg.dev == "867948079409829") & np.isclose(seg.J, 0.70))]  # erroneous segment
dj = seg.drop_duplicates(["dev", "J"])[["dev", "J"]].copy()
dj["site"] = dj["dev"].map(EN)
dj["phi"] = 0.26 / dj["J"] * 100.0
assert len(dj) == 17 and dj["dev"].nunique() == 13   # 18 segments, less the rejected 0.70 m one
assert abs(dj.phi.max() - 47.27) < 0.05 and abs(dj.phi.min() - 9.63) < 0.05

fig = plt.figure(figsize=(W2, 96 * MM))
gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 0.34], width_ratios=[1, 1],
              hspace=0.75, wspace=0.30, left=0.068, right=0.945, top=0.905, bottom=0.105)

# --- (a) Omega against well depth --------------------------------------------
axA = fig.add_subplot(gs[0, 0])
levels = sorted(d.Omega.unique())
for om in levels:
    axA.axhline(om, color=C_GRID, lw=0.7, ls=(0, (1.8, 2.2)), zorder=0)
axA.axhline(1.0, color="k", lw=0.9, zorder=1)
for dev, g in d.groupby("dev"):
    if g.Jp.nunique() == 1 and len(g) > 1:
        axA.plot([g.Jp.iloc[0]] * 2, [g.Omega.min(), g.Omega.max()],
                 color=C_GREY, lw=0.7, zorder=2, solid_capstyle="round")
axA.plot(d.Jp, d.Omega, "o", ms=4.2, mfc="k", mec="k", mew=0.6, zorder=3)
axA.set_xlim(0.35, 2.92)
axA.set_ylim(0.26, 1.70)
axA.set_xticks([0.5, 1.0, 1.5, 2.0, 2.5])
axA.set_yticks([0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
axA.set_xlabel(r"well depth $J$   (m)")
axA.set_ylabel(r"$\Omega = b_\theta\,/\,(D+B)$")
axA.text(0.37, 1.045, r"$\Omega=1$", fontsize=6.2, ha="left", va="bottom", color="k")

axR = axA.twinx()
axR.set_ylim(axA.get_ylim())
axR.set_yticks(levels)
axR.set_yticklabels([f"{0.26*v:.2f}" for v in levels], fontsize=6.2, color=C_GREY)
axR.set_ylabel(r"$b_\theta$  (m)", fontsize=6.8, color=C_GREY, labelpad=2)
axR.tick_params(axis="y", colors=C_GREY, length=2.0, width=0.5)
axR.spines["right"].set_visible(True)
axR.spines["right"].set_linewidth(0.5)
axR.spines["right"].set_color(C_GREY)
axR.spines["top"].set_visible(False)

axA.annotate("one instrument,\nseveral states", xy=(1.30, 0.86), xytext=(1.74, 0.56),
             fontsize=6.3, ha="left", va="center", color=C_GREY, linespacing=1.15,
             arrowprops=dict(arrowstyle="-", lw=0.55, color=C_GREY,
                             shrinkA=2, shrinkB=2))
tag(axA, "a", x=-0.135)

# --- (b) the same window, priced per well ------------------------------------
axB = fig.add_subplot(gs[0, 1])
xx = np.linspace(0.52, 2.78, 200)
axB.plot(xx, 0.26 / xx * 100, color=C_GREY, lw=0.6, ls=(0, (3, 2)), zorder=1)
axB.plot(dj.J, dj.phi, "o", ms=4.0, mfc=C_IN, mec="k", mew=0.6, zorder=3)
for jj, txt, off, ha in [(0.55, "08 Dewen Library", (7, 1), "left"),
                         (2.70, "01 Chifeng Rd", (-6, -3), "right")]:
    r = dj[dj.J == jj].iloc[0]
    axB.annotate(txt, xy=(r.J, r.phi), xytext=off, textcoords="offset points",
                 fontsize=5.9, ha=ha, va="center", color=C_GREY)
axB.set_xlim(0.35, 2.92)
axB.set_ylim(0, 58)
axB.set_xticks([0.5, 1.0, 1.5, 2.0, 2.5])
axB.set_yticks([0, 10, 20, 30, 40, 50])
axB.set_xlabel(r"well depth $J$   (m)")
axB.set_ylabel(r"$\varphi = (D+B)\,/\,J$   (%)")
axB.text(0.975, 0.935, "4.9$\\times$ range", transform=axB.transAxes, fontsize=7,
         ha="right", va="top", fontweight="bold")
axB.text(0.975, 0.845, "9.6 – 47.3 %", transform=axB.transAxes, fontsize=6.4,
         ha="right", va="top", color=C_GREY)
tag(axB, "b", x=-0.16)

# --- (c) the vacant band -----------------------------------------------------
axC = fig.add_subplot(gs[1, :])
centres = np.round(np.arange(0.10, 0.401, 0.05), 2)
counts = np.array([int(np.isclose(d.b_th, c).sum()) for c in centres])
assert counts.sum() == 12 and counts[3] == 0          # bin straddling 0.26 m is empty
axC.axvspan(0.205, 0.295, color=C_BAND, alpha=0.6, lw=0, zorder=0)
cols = [C_OUT if c <= 0.20 else C_IN for c in centres]
axC.bar(centres, counts, width=0.042, color=cols, edgecolor="k", linewidth=0.5, zorder=3)
axC.axvline(0.26, color="k", lw=0.9, ls=(0, (4, 2)), zorder=4)
axC.set_xlim(0.045, 0.455)
axC.set_ylim(0, 5.2)
axC.set_yticks([0, 1, 2, 3])
axC.set_xticks([0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45])
axC.set_xticklabels(["0.05", "0.10", "0.15", "0.20", "0.25", "0.30", "0.35", "0.40", "0.45"])
axC.set_xlabel(r"threshold depth below cover, $b_\theta$   (m, 0.05 m grid)")
axC.set_ylabel("configurations")
axC.text(0.198, 4.42, "vacant band\n0.21 – 0.29 m", fontsize=6.5, ha="right",
         va="center", color=C_GREY, linespacing=1.25)
axC.text(0.25, 0.14, "0", fontsize=6.4, ha="center", va="bottom", color=C_GREY)
axC.text(0.268, 3.62, r"$D+B$ = 0.26 m", fontsize=6.6, ha="left", va="center")
hc = [Patch(fc=C_OUT, ec="k", lw=0.5, label=r"$\Omega\leq1$"),
      Patch(fc=C_IN, ec="k", lw=0.5, label=r"$\Omega>1$")]
axC.legend(handles=hc, loc="upper right", bbox_to_anchor=(1.005, 1.22), ncol=2,
           frameon=False, handlelength=1.1, handleheight=0.8, handletextpad=0.4,
           columnspacing=1.4, borderpad=0.0)
tag(axC, "c", x=-0.048, y=0.94)

for ext in ("pdf", "png", "svg"):
    fig.savefig(os.path.join(OUT, f"Fig9_network_centring.{ext}"), format=ext)
_bb = fig.get_tightbbox(fig.canvas.get_renderer())
print("Fig9 size %.1f x %.1f mm%s" % (_bb.width * 25.4, _bb.height * 25.4,
      "   <-- OVER WIDTH" if _bb.width * 25.4 > W2_MAX else ""))
plt.close(fig)

print("counts per bin", dict(zip(centres, counts)))
print("saved:", sorted(os.listdir(OUT)))
