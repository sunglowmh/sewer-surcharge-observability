# -*- coding: utf-8 -*-
"""Shared style for the P3 figure set (Fig. 1–9).

176 mm double column, Arial 7 pt, vector PDF with embedded TrueType (fonttype 42).

The column width is set from the HESS page, not chosen: page 216 x 283 mm, text
left edge measured at 19.4 mm on a published article and symmetric, so the type
area is ~177 mm.  Two earlier versions used 183 mm, which is the *Springer*
double column and 5-7 mm wider than Copernicus: Fig. 1 came out at 182.1 mm and
Figs. 3/4/5/7/8 at 176.7-178.0 mm, i.e. either over the type area or inside it by
less than a millimetre.  Production would have scaled them down to fit and taken
7 pt type to 6.8 pt with it.
mathtext is pinned to Arial so that Omega / theta / phi do not fall back to DejaVu.
"""
import math
import os
import textwrap
import matplotlib as mpl

mpl.use("Agg")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root, not the author's machine
FIGDIR = os.path.join(ROOT, "figures")
DATADIR = os.path.join(ROOT, "outputs", "figdata")
os.makedirs(FIGDIR, exist_ok=True)

MM = 1 / 25.4
W1 = 89 * MM
W15 = 120 * MM
W2 = 176 * MM        # HESS type area 177 mm, 1 mm rule margin
W2_MAX = 177.0       # mm; save() flags anything wider

# ---------------------------------------------------------------- captions
# Copernicus: "Figure captions should be included in the text file and not in
# the figure files."  The explanatory text was originally drawn on the canvas
# with fig.text(), which put a caption inside every figure file.  It is now
# behind a switch: the default output is the submission version, with no text
# on the canvas, and the caption lives in figures/*_captions.md and in the
# manuscript.  Set FIG_CAPTION=1 to draw them again for proof-reading.
CAPTION = os.environ.get("FIG_CAPTION", "0") == "1"

# ------------------------------------------------------------- coordinates
# The registry in 同济校园监测设备管理_设备编号_经纬度.xlsx is in BD-09 (the
# Baidu graticule): read as WGS84 or GCJ-02 it places the whole network 0.5-0.8
# km north-east of the campus, on the Siping-Rd / Guokang-Rd residential blocks.
# Converting BD-09 -> GCJ-02 puts all seventeen instruments back on the campus,
# with a residual of a few tens of metres, i.e. the accuracy with which the
# points were picked by hand.  AMap tiles are cut on the GCJ-02 graticule, so
# the figure is drawn in GCJ-02 throughout.  Nothing else in the paper uses
# these coordinates: 0.26, h*, Omega and phi are all in burial / registry units.
_A = 6378245.0
_EE = 0.00669342162296594323
_X_PI = math.pi * 3000.0 / 180.0


def bd2gcj(lon, lat):
    """BD-09 -> GCJ-02.  The standard polar form; exact to a few metres."""
    x, y = lon - 0.0065, lat - 0.0060
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * _X_PI)
    th = math.atan2(y, x) - 0.000003 * math.cos(x * _X_PI)
    return z * math.cos(th), z * math.sin(th)


def _tf_lat(x, y):
    r = (-100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y
         + 0.2 * math.sqrt(abs(x)))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    r += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return r


def _tf_lon(x, y):
    r = (300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y
         + 0.1 * math.sqrt(abs(x)))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    r += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return r


def wgs2gcj(lon, lat):
    """WGS84 -> GCJ-02.  Sub-metre over the campus."""
    dlat = _tf_lat(lon - 105.0, lat - 35.0)
    dlon = _tf_lon(lon - 105.0, lat - 35.0)
    rad = lat / 180.0 * math.pi
    magic = 1 - _EE * math.sin(rad) ** 2
    sq = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((_A * (1 - _EE)) / (magic * sq) * math.pi)
    dlon = (dlon * 180.0) / (_A / sq * math.cos(rad) * math.pi)
    return lon + dlon, lat + dlat


def gcj2wgs(lon, lat, n=6):
    """GCJ-02 -> WGS84, by fixed-point iteration on the forward transform.

    Needed because the registry is BD-09 and the basemap is OpenStreetMap,
    which is WGS84, while `wgs2gcj` only goes the other way.  Six rounds leave
    the residual below 1e-9 deg, four orders of magnitude finer than the 10 m
    grid the analysis works on.
    """
    x, y = lon, lat
    for _ in range(n):
        gx, gy = wgs2gcj(x, y)
        x -= gx - lon
        y -= gy - lat
    return x, y

# ------------------------------------------------------------------ palette
C_IN = "#0072B2"        # Omega > 1 / observable
C_OUT = "#E69F00"       # Omega <= 1 / not estimable
C_BAND = "#D8D8D8"      # blind window fill
C_Y = "#EE854A"         # platform label: above threshold
C_B = "#4878CF"         # platform label: level has receded
C_R = "#B8B8B8"         # platform label: fault family
C_SURF = "#2E6E8E"      # surface network
C_RAIN = "#9EC9E2"
C_GREY = "#5A5A5A"
C_GRID = "#EBEBEB"
C_ALERT = "#B2182B"     # impossible / zero cell

EN = {
    "867948079403574": "01 Chifeng Rd",
    "867948079405843": "02 Structure Lab",
    "863721076643276": "03 NW Bldg",
    "867948079405678": "04 Pumped chamber",
    "867948079409829": "05 Ocean Bldg",
    "867948079405785": "06 Aixiao Rd",
    "867948079405611": "07 Medical Bldg",
    "867948079405652": "08 Dewen Library",
    "867948079405165": "09 Gymnasium",
    "867948079409803": "10 Gate display",
    "867948079409621": "11 Tongwen Bldg",
    "867948079405546": "12 Cont. Educ.",
    "867948079407252": "13 Wenyuan Bldg",
}
# surface instruments (地埋式)
EN_SURF = {
    "863342076635699": "S1 Chifeng Rd",
    "863342076635152": "S2 Gymnasium",
    "863342076635186": "S3 Auditorium",
    "863342076635095": "S4 Ruian Bldg",
    "869158077679187": "S5 Surveying",
}


def apply():
    mpl.rcParams.update({
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
        "legend.frameon": False,
        "legend.handlelength": 1.4,
        "legend.handletextpad": 0.5,
        "legend.labelspacing": 0.28,
        "legend.borderpad": 0.0,
    })


def tag(ax, s, x=-0.16, y=1.04, fs=8):
    """Lowercase bold panel label, placed outside the axes on the top-left."""
    ax.text(x, y, s, transform=ax.transAxes, fontsize=fs, fontweight="bold",
            va="bottom", ha="left")


def bare(ax, keep=("left", "bottom")):
    for sp in ("top", "right", "left", "bottom"):
        if sp not in keep:
            ax.spines[sp].set_visible(False)


def cap(text, width=146):
    """Hard-wrap a caption so that it stays inside the 176 mm column; savefig with
    bbox_inches='tight' silently widens the canvas otherwise."""
    return "\n".join(textwrap.wrap(" ".join(text.split()), width))


def save(fig, name, pdf_dpi=None):
    """Write pdf/png/svg; if a target is locked by a viewer, write beside it and
    report instead of failing the whole figure. Also reports the final size so that
    a caption running past the right margin cannot pass unnoticed.

    pdf_dpi only matters for figures that carry a raster panel: the PDF backend
    resamples every image to savefig.dpi, so at the default 600 dpi a 70 mm
    basemap is embedded at 1650 px and the file runs to ~2 MB. Passing a lower
    value keeps the raster at the resolution it was built at."""
    try:
        bb = fig.get_tightbbox(fig.canvas.get_renderer())
        w, h = bb.width * 25.4, bb.height * 25.4
        print("size %.1f x %.1f mm%s" % (w, h, "   <-- OVER WIDTH" if w > W2_MAX else ""))
    except Exception as exc:                                   # pragma: no cover
        print("size unknown:", exc)
    for ext in ("pdf", "png", "svg"):
        p = os.path.join(FIGDIR, "%s.%s" % (name, ext))
        dpi = 600 if ext == "png" else (pdf_dpi if ext == "pdf" else None)
        try:
            fig.savefig(p, dpi=dpi)
        except PermissionError:
            q = os.path.join(FIGDIR, "_new_%s.%s" % (name, ext))
            fig.savefig(q, dpi=dpi)
            print("LOCKED %s -> wrote %s" % (p, q))
    print("saved", name)
