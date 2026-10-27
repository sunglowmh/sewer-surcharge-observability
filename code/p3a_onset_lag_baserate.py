#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审稿意见 A-1(c) 与 A-3(b) 所需的两项计算。

A-3(b) 基准率：在降水覆盖期内，"前 3 h 累计 >= 5 mm" 的时间占比 p。
        与 16/18 个失明块起于涨水段对照。分母取 Aprs（块的采样框架），
        另给全雨量覆盖时段的值作为上界参考。

A-1(c) 判别检验（N3）：若失明是近场衰减，块起点应在雨强峰附近但晚于降雨开始
        （井要充水时间）；若是溅水/凝结/泡沫，块起点应紧随首次降水（lag ≈ 0）。
        逐块给出：
          lag_onset  = t_start - 该场降雨段首个湿样本
          lag_peak   = t_start - 该场降雨段 10 min 雨强峰
          i_onset    = 起点所在 10 min 的雨量
        "该场降雨段" 用与 Aprs 相同的分段规则（>=3 h 无雨即断开），
        以避免 §4.3 已指出的"白海豚两个雨峰相隔 22 h"问题。

输出：
  outputs/p3a_onset_lag.csv        逐块
  outputs/p3a_onset_baserate.csv   基准率 p 的两种口径
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "outputs")
BASE = os.path.join(ROOT, "同济校园", "监测数据")
sys.path.insert(0, HERE)

from p3a_lock_reclass_rain import parse_rain, active_periods, RAIN_FILES, RAIN_DRIVE_MM, LAG_H

# ---------------------------------------------------------------- rainfall
EV = {}
for ev, rel in RAIN_FILES.items():
    r = parse_rain(os.path.join(BASE, rel))
    EV[ev] = r

# 降雨段（断开规则 >=3 h 无雨），不带 6 h 右扩
BURSTS = {}          # ev -> [(t0, t1, mm, peak_t, peak_mm)]
for ev, r in EV.items():
    w = r[r.mm > 0].sort_values("t").reset_index(drop=True)
    segs, s = [], 0
    for i in range(1, len(w)):
        if (w.t[i] - w.t[i - 1]).total_seconds() / 3600 > 3.0:
            segs.append((s, i - 1))
            s = i
    segs.append((s, len(w) - 1))
    lst = []
    for a, b in segs:
        sl = r[(r.t >= w.t[a]) & (r.t <= w.t[b])]
        r10 = sl.set_index("t").mm.resample("10min").sum()
        r10 = r10[r10.index >= w.t[a]]
        pk = r10.idxmax() if len(r10) else pd.NaT
        lst.append((w.t[a], w.t[b], float(w.mm[a:b + 1].sum()), pk, float(r10.max())))
    BURSTS[ev] = lst


def aprs_of(r):
    segs, _ = active_periods(r)
    return segs


def ant3(rain, t):
    """t 之前 3 h（含 t 所在 10 min 格）累计降雨"""
    a = t - pd.Timedelta(hours=3)
    s = rain[(rain.t > a) & (rain.t <= t)]
    return float(s.mm.sum())


# ---------------------------------------------------- A-3(b): base rate p
rows = []
for ev, r in EV.items():
    segs = aprs_of(r)
    idx = pd.date_range(r.t.min().floor("10min"), r.t.max().ceil("10min"), freq="10min")
    grid = pd.DataFrame({"t": idx})
    grid["ant3"] = [ant3(r, t) for t in grid.t]
    grid["in_aprs"] = [any(a <= t <= b for a, b, _ in segs) for t in grid.t]
    grid["wet"] = grid.t.map(lambda t: float(r[(r.t > t - pd.Timedelta(minutes=10)) & (r.t <= t)].mm.sum()))
    sub = grid[grid.in_aprs]
    rows.append(dict(
        ev=ev,
        n_bins_covered=len(grid),
        n_bins_aprs=len(sub),
        p_aprs=float((sub.ant3 >= RAIN_DRIVE_MM).mean()) if len(sub) else np.nan,
        p_covered=float((grid.ant3 >= RAIN_DRIVE_MM).mean()),
        aprs_h=sum((b - a).total_seconds() / 3600 for a, b, _ in segs),
        covered_h=len(grid) / 6.0,
    ))
br = pd.DataFrame(rows)
br.loc[len(br)] = dict(
    ev="pooled",
    n_bins_covered=br.n_bins_covered.sum(),
    n_bins_aprs=br.n_bins_aprs.sum(),
    p_aprs=br.n_bins_aprs.mul(br.p_aprs).sum() / br.n_bins_aprs.sum(),
    p_covered=br.n_bins_covered.mul(br.p_covered).sum() / br.n_bins_covered.sum(),
    aprs_h=br.aprs_h.sum(),
    covered_h=br.covered_h.sum(),
)
br.to_csv(os.path.join(OUT, "p3a_onset_baserate.csv"), index=False, encoding="utf-8-sig")
print("=" * 92)
print("A-3(b)  基准率 p = P(前 3 h >= 5 mm | 降水覆盖期)")
print("=" * 92)
print(br.round(4).to_string(index=False))

# ------------------------------------------------- A-1(c): onset lag test
blk = pd.read_csv(os.path.join(OUT, "p3a_precip_lock_blocks.csv"), encoding="utf-8-sig")
blk["t_start"] = pd.to_datetime(blk.t_start)
out = []
for _, r in blk.iterrows():
    ev = r.event
    cand = [b for b in BURSTS[ev] if b[0] - pd.Timedelta(hours=6) <= r.t_start <= b[1] + pd.Timedelta(hours=6)]
    if not cand:
        cand = [min(BURSTS[ev], key=lambda b: abs((b[0] - r.t_start).total_seconds()))]
    b = min(cand, key=lambda b: abs((b[0] - r.t_start).total_seconds()))
    t0, t1, tot, pk, pkm = b
    rain = EV[ev]
    i_on = float(rain[(rain.t > r.t_start - pd.Timedelta(minutes=10)) & (rain.t <= r.t_start)].mm.sum())
    out.append(dict(
        dev=r.dev, name=r["name"], event=ev, t_start=r.t_start, n=r.n, dur_h=r.dur_h,
        rain_prev3h_mm=r.rain_prev3h_mm, phase=r.phase,
        burst_onset=t0, burst_mm=round(tot, 1),
        lag_onset_min=round((r.t_start - t0).total_seconds() / 60, 0),
        burst_peak=pk, peak_mm=round(pkm, 1),
        lag_peak_min=round((r.t_start - pk).total_seconds() / 60, 0) if pd.notna(pk) else np.nan,
        i_onset_mm=round(i_on, 1),
        burial_post=r.burial_post,
    ))
lag = pd.DataFrame(out).sort_values(["event", "t_start"])
lag.to_csv(os.path.join(OUT, "p3a_onset_lag.csv"), index=False, encoding="utf-8-sig")
print()
print("=" * 92)
print("A-1(c)  块起点相对降雨段起点与雨强峰的滞时（分钟；负值=早于）")
print("=" * 92)
print(lag[["name", "event", "t_start", "n", "phase", "burst_mm", "lag_onset_min",
           "peak_mm", "lag_peak_min", "i_onset_mm"]].to_string(index=False))

rd = lag[lag.phase == "rain-driven"]
print()
print("降水驱动块 n=%d" % len(rd))
for c in ("lag_onset_min", "lag_peak_min", "i_onset_mm"):
    print("  %-14s min %6.0f  med %6.0f  max %6.0f" % (c, rd[c].min(), rd[c].median(), rd[c].max()))
print("  lag_onset <= 0 (未晚于降雨开始): %d" % int((rd.lag_onset_min <= 0).sum()))
print("  lag_onset <= 10 min (首个 10 min 内): %d" % int((rd.lag_onset_min <= 10).sum()))
print("  lag_onset >= 20 min: %d" % int((rd.lag_onset_min >= 20).sum()))
print("  lag_peak < 0 (早于雨强峰): %d  |  >0: %d" % (
    int((rd.lag_peak_min < 0).sum()), int((rd.lag_peak_min > 0).sum())))
print("  起点 10 min 雨量 > 0 的块: %d" % int((rd.i_onset_mm > 0).sum()))
