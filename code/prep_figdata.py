# -*- coding: utf-8 -*-
"""为 Fig.1–2、3–6、8 准备绘图数据（一次性落盘，绘图脚本只读 CSV）。

输出到 outputs/figdata/：
  fig2_sites.csv        13 井下 + 5 地表：经纬度、记录数、起止、中位采样间隔
  fig3_decomp.csv       量程下界读数的层级分解计数
  fig3_block.csv        赤峰路 2025-11 逐条 burial 与逐日地表有水比例
  fig5_peak.csv         0719 14:00–17:00 逐 10 min：井下锁定比例 / 地表有水比例 / 峰值
  fig6a_minburial.csv   每台「非 0.250 的最小 burial」
  fig6b_excursion.csv   5 条 burial<0.25 的前/本/后三点
  fig6c_hist.csv        burial 落在 (0.25, 0.35] 的直方图（0.01 m 分箱）
  fig8_config.csv       每条配置 floor-thr、在写回值条数、标签分布
"""
import os
import re
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from load_history import load_all  # noqa: E402
import figstyle as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "figdata")
os.makedirs(OUT, exist_ok=True)

FLOOR = 0.2501   # 固件写回值上界（burial <= 0.2501 记为落在写回值）


def site_no(name):
    """'11号同文楼大门口' -> '11' ; '测绘与地理学院地埋式05' -> 'S5'."""
    m = re.match(r"^\s*(\d+)\s*号", str(name))
    if m:
        return "%02d" % int(m.group(1))
    m = re.search(r"地埋式\s*(\d+)", str(name)) or re.search(r"(\d+)\s*号地埋式", str(name))
    if m:
        return "S%d" % int(m.group(1))
    return "?"


def save(df, name):
    p = os.path.join(OUT, name)
    df.to_csv(p, index=False, encoding="utf-8-sig")
    print("saved %-22s %5d rows" % (name, len(df)))


son, bur = load_all()
son["dev"] = son.dev.astype(str)

# ---------------------------------------------------------------- Fig. 2
loc = pd.read_csv(os.path.join(ROOT, "outputs", "P3_设备落点_SWMM节点.csv"), encoding="utf-8-sig")
loc["dev"] = loc.dev.astype(str)

rows = []
for kind, df in (("sewer", son), ("surface", bur)):
    for dev, g in df.groupby("dev"):
        g = g.sort_values("t")
        dt = g.t.diff().dt.total_seconds().div(60).dropna()
        m = loc[loc.dev == dev]
        lon = m.lon.iloc[0] if len(m) else np.nan
        lat = m.lat.iloc[0] if len(m) else np.nan
        # the registry is BD-09; tiles are GCJ-02; the figure is drawn in GCJ-02
        glon, glat = (S.bd2gcj(lon, lat) if np.isfinite(lon) else (np.nan, np.nan))
        nm = (g.name.iloc[0] if "name" in g else "")
        rows.append(dict(
            dev=dev, kind=kind, num=site_no(nm), name=nm,
            lon_bd=lon, lat_bd=lat, lon_gcj=glon, lat_gcj=glat,
            n=len(g), t0=g.t.min(), t1=g.t.max(),
            dt_med=float(dt.median()) if len(dt) else np.nan,
        ))
sites = pd.DataFrame(rows)
save(sites.sort_values(["kind", "num"]), "fig2_sites.csv")

# ---------------------------------------------------------------- Fig. 3
# (a) 层级分解
recl = pd.read_csv(os.path.join(ROOT, "outputs", "p3a_lock_reclass_by_dev.csv"), encoding="utf-8-sig")
recl["dev"] = recl.dev.astype(str)
tot = int(recl.total.sum())
precip = int(recl.precip.sum())
nodata = int(recl.no_data.sum())
no_rain = int(recl.no_rain.sum())
cf = int(recl.loc[recl.dev == "867948079403574", "no_data"].iloc[0])

# 赤峰路单块：取该台最长连续锁定段（数据驱动，不写死日期）
cfd = son[(son.dev == "867948079403574") & son.burial.notna()].sort_values("t").reset_index(drop=True)
cv = (cfd.burial <= FLOOR).values
_runs, _s = [], None
for _i, _v in enumerate(cv):
    if _v and _s is None:
        _s = _i
    elif not _v and _s is not None:
        _runs.append((_s, _i - 1))
        _s = None
if _s is not None:
    _runs.append((_s, len(cv) - 1))
_ra, _rb = max(_runs, key=lambda r: r[1] - r[0])
block_n = int(_rb - _ra + 1)
block_t0, block_t1 = cfd.t.iloc[_ra], cfd.t.iloc[_rb]
print("  block: %s -> %s  n=%d  %.2f d" % (block_t0, block_t1, block_n,
                                            (block_t1 - block_t0).total_seconds() / 86400))

decomp = pd.DataFrame([
    dict(level=0, label="floor readings", value=tot, parent=""),
    dict(level=1, label="rainfall-active period", value=precip, parent="floor readings"),
    dict(level=1, label="outside gauge coverage", value=nodata + no_rain, parent="floor readings"),
    dict(level=2, label="Chifeng Road (site 01)", value=cf, parent="outside gauge coverage"),
    dict(level=3, label="one 21-day block", value=block_n, parent="Chifeng Road (site 01)"),
    dict(level=2, label="residual", value=nodata + no_rain - cf, parent="outside gauge coverage"),
])
save(decomp, "fig3_decomp.csv")
print("  check: total", tot, "= precip", precip, "+ outside", nodata + no_rain)
print("  Chifeng block", block_n, "of", cf)

# (b) 赤峰路 2025-11 逐条 burial + 逐日地表有水比例
w = son[(son.dev == "867948079403574") & (son.t >= "2025-10-25") & (son.t <= "2025-12-05")].sort_values("t")
blk = pd.DataFrame(dict(
    t=w.t, burial=w.burial.fillna(np.nan),
    cens=(w.burial.notna() & (w.burial <= FLOOR)),
))
s = bur[(bur.t >= "2025-10-25") & (bur.t <= "2025-12-05")].copy()
s["d"] = s.t.dt.floor("D")
day = s.groupby("d").surf_mm.agg(lambda x: float((x > 0).mean() * 100)).rename("wet_pct").reset_index()
save(blk, "fig3_block.csv")
save(day, "fig3_surface_day.csv")

# ---------------------------------------------------------------- Fig. 5
t0, t1 = pd.Timestamp("2026-07-19 14:00"), pd.Timestamp("2026-07-19 17:00")
b = son[(son.t >= t0) & (son.t < t1) & son.burial.notna()].copy()
b["bin"] = b.t.dt.floor("10min")
bb = b.groupby(["dev", "bin"]).agg(cens=("burial", lambda x: (x <= FLOOR).any())).reset_index()
g = bb.groupby("bin").cens.agg(["sum", "size"]).reset_index()
g["lock_pct"] = g["sum"] / g["size"] * 100
sf = bur[(bur.t >= t0) & (bur.t < t1)].copy()
sf["bin"] = sf.t.dt.floor("10min")
ss = sf.groupby("bin").agg(wet=("surf_mm", lambda x: (x > 0).mean() * 100),
                           peak=("surf_mm", "max")).reset_index()
pk = g.merge(ss, on="bin", how="left").sort_values("bin")
save(pk, "fig5_peak.csv")
print("  peak cells: locked %d/%d = %.1f%%" % (g["sum"].sum(), g["size"].sum(),
                                               g["sum"].sum() / g["size"].sum() * 100))
print("  surface wet %d/%d = %.1f%%  peak %.0f mm" % ((sf.surf_mm > 0).sum(), len(sf),
                                                      (sf.surf_mm > 0).mean() * 100, sf.surf_mm.max()))


# ---------------------------------------------------------------- Fig. 5 trace
t0 = pd.Timestamp("2026-07-19 09:00")
t1 = pd.Timestamp("2026-07-20 02:00")
tr = son[(son.dev == "867948079409621") & (son.t >= t0) & (son.t <= t1) &
         son.burial.notna()][["t", "burial"]].copy()
tr["cens"] = tr.burial <= FLOOR
sf2 = bur[(bur.t >= t0) & (bur.t <= t1)].copy()
sf2["b10"] = sf2.t.dt.floor("10min")
ss2 = sf2.groupby("b10").agg(wet=("surf_mm", lambda x: (x > 0).mean() * 100),
                             peak=("surf_mm", "max"),
                             k=("surf_mm", lambda x: int((x > 0).sum())),
                             n=("surf_mm", "size")).reset_index()
tr.to_csv(os.path.join(OUT, "fig5_trace.csv"), index=False, encoding="utf-8-sig")
ss2.to_csv(os.path.join(OUT, "fig5_surface.csv"), index=False, encoding="utf-8-sig")
print("saved fig5_trace.csv %d rows; fig5_surface.csv %d rows" % (len(tr), len(ss2)))

# ------------------------------------------------- Fig. 5 status grid
w0, w1 = pd.Timestamp("2026-07-19 12:00"), pd.Timestamp("2026-07-20 00:00")
b5 = son[(son.t >= w0) & (son.t < w1) & son.burial.notna()].copy()
b5["bin"] = b5.t.dt.floor("10min")
g5 = b5.groupby(["dev", "bin"]).agg(
    f=("burial", lambda x: float((x <= FLOOR).mean())), n=("burial", "size")).reset_index()
save(g5, "fig5_status.csv")

# ---------------------------------------------------------------- Fig. 6
x = son[son.burial.notna()].copy()
rows = []
for dev, gg in x.groupby("dev"):
    nf = gg.loc[gg.burial > FLOOR, "burial"]
    rows.append(dict(dev=dev, name=gg.name.iloc[0],
                     min_nonfloor=float(nf.min()) if len(nf) else np.nan,
                     n=len(gg), n_floor=int((gg.burial <= FLOOR).sum()),
                     dt_med=float(gg.t.diff().dt.total_seconds().div(60).median())))
mb = pd.DataFrame(rows)
save(mb.sort_values("min_nonfloor"), "fig6a_minburial.csv")
print(mb.sort_values("min_nonfloor")[["name", "min_nonfloor", "n", "n_floor"]].to_string(index=False))

low = x[x.burial < 0.25].sort_values("t")
rows = []
for _, r in low.iterrows():
    gg = x[x.dev == r.dev].sort_values("t").reset_index(drop=True)
    i = gg.index[gg.t == r.t][0]
    rows.append(dict(dev=r.dev, name=r.name, t=r.t, cur=r.burial,
                     prev=(gg.burial.iloc[i - 1] if i > 0 else np.nan),
                     nxt=(gg.burial.iloc[i + 1] if i + 1 < len(gg) else np.nan)))
ex = pd.DataFrame(rows)
save(ex, "fig6b_excursion.csv")
print(ex[["name", "t", "prev", "cur", "nxt"]].to_string(index=False))

mid = x[(x.burial > FLOOR) & (x.burial <= 0.35)]
edges = np.arange(0.250, 0.351, 0.010)
h, _ = np.histogram(mid.burial, bins=edges)
hist = pd.DataFrame(dict(lo=edges[:-1], hi=edges[1:], n=h))
hist["n_dev"] = [int(mid[(mid.burial > a) & (mid.burial <= b)].dev.nunique())
                 for a, b in zip(edges[:-1], edges[1:])]
save(hist, "fig6c_hist.csv")
print("  mid-band n=%d dev=%d" % (len(mid), mid.dev.nunique()))

# ---------------------------------------------------------------- Fig. 8
a = pd.read_csv(os.path.join(ROOT, "outputs", "p3a_J_alarm_check.csv"), encoding="utf-8-sig")
a["dev"] = a.dev.astype(str)
a["d"] = (a.floor - a.thr).round(3)
cfg = (a.groupby(["dev", "name", "thr", "J", "side", "d"])
        .agg(n=("cur", "size"),
             at_floor=("at_floor", "sum"),
             yellow=("colour", lambda s: int((s == "yellow").sum())),
             blue=("colour", lambda s: int((s == "blue").sum())),
             red=("colour", lambda s: int((s == "red").sum())))
        .reset_index().sort_values("d"))
save(cfg, "fig8_config.csv")
print(cfg.to_string(index=False))
print("at floor total", int(cfg.at_floor.sum()), "of", int(cfg.n.sum()))
