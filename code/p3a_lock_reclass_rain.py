#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P3 · 用降水（外部判据）重建「降水期失明 / 非降水期锁定」二分

为什么必须重建
--------------
旧判据「连续锁定 ≥20 条 或 跨度 ≥6 h ⇒ 故障」是**纯长度阈值**，与物理无关：
  - 同文楼 0719 的真实物理失明持续 8 h40m（模型显示该节点 burial ≤0.26 到 23:59）
  - 却在旧判据下被判为"故障"，164 条记录全部从事件期样本中剔除
  ⇒ 恰好把最严重的物理失明删掉了，R3/R6 的样本被系统性掏空

新判据（三层，全部独立于 burial）
--------------------------------
  1. 降水活跃期 Aprs = ∪[降雨开始, 降雨结束 + LAG]，LAG = 6 h（管网退水滞后）
  2. 锁定记录落在 Aprs 内 ⇒ 降水期锁定（候选物理失明）
  3. 落在 Aprs 外 ⇒ 非降水期锁定（无降雨驱动，物理上不可能由水位上涨造成）
  4. 无雨量数据覆盖的时段 ⇒ 未判定（不并入任何一类，不参与统计）

这样 R1 从"按长度猜"变成"按是否下雨判"，且判据可以写进 Methods。

附带产出
--------
  - 降水期锁定的方向判定（涨水 / 退水）
  - 两类的记录数、块数、总时长
  - 三场事件的累计雨量（巴威仅 19.4 mm）
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_history import load_all, read_xlsx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "outputs")
BASE = os.path.join(ROOT, "同济校园", "监测数据")
LOCK = 0.2501
LAG_H = 6.0           # 雨止后管网继续退水的滞后
RAIN_DRIVE_MM = 5.0   # 块起点前 3 h 累计降雨超过此值 ⇒ 降雨驱动（水位上涨段）
RAIN_FILES = {
    "0719暴雨": "20260719暴雨/雨量计数据-20260719.xlsx",
    "巴威":     "202609台风巴威(7.11-7.13)/雨量计数据-2026-0711-0713.xlsx",
    "白海豚":   "2026台风白海豚（8.09-8.11)/雨量计数据-2026-0809-0811.xlsx",
}


def parse_rain(path):
    rows = read_xlsx(path)
    out = []
    for r in rows[1:]:
        a = r.get("A")
        if a is None:
            continue
        sa = str(a).strip()
        try:
            if len(sa) < 8 and sa.replace(".", "").replace("-", "").isdigit():
                ser = float(a)
                frac = float(r.get("B", 0) or 0)
                t = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(ser)) + pd.Timedelta(days=frac)
            else:
                t = pd.Timestamp(sa)
        except Exception:
            continue
        v = None
        for k in (("C", "D") if len(sa) < 8 else ("B",)):
            if k in r:
                try:
                    v = float(r[k]); break
                except Exception:
                    pass
        if v is not None:
            out.append((t, v))
    d = pd.DataFrame(out, columns=["t", "mm"]).sort_values("t").reset_index(drop=True)
    return d


def active_periods(rain, lag_h=LAG_H, min_gap_h=3.0):
    """把 >0 的降雨样本合并成降雨段，每段右扩 lag_h，返回 [(a,b,rain_mm)]"""
    w = rain[rain.mm > 0].copy()
    if len(w) == 0:
        return [], 0.0
    w = w.sort_values("t").reset_index(drop=True)
    segs, s = [], 0
    for i in range(1, len(w)):
        if (w.t[i] - w.t[i - 1]).total_seconds() / 3600 > min_gap_h:
            segs.append((s, i - 1)); s = i
    segs.append((s, len(w) - 1))
    out = []
    for a, b in segs:
        t0 = w.t[a]; t1 = w.t[b] + pd.Timedelta(hours=lag_h)
        out.append((t0, t1, float(w.mm[a:b + 1].sum())))
    # 合并重叠
    out.sort()
    merged = []
    for a, b, mm in out:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b), merged[-1][2] + mm)
        else:
            merged.append((a, b, mm))
    return merged, float(w.mm.sum())


def main():
    pd.set_option("display.width", 240)
    son, _ = load_all()
    son["dev"] = son["dev"].astype(str).str.strip()
    son["t"] = pd.to_datetime(son["t"], errors="coerce")
    son["burial"] = pd.to_numeric(son["burial"], errors="coerce")
    son = son.dropna(subset=["dev", "t", "burial"]).sort_values(["dev", "t"]).reset_index(drop=True)
    son["cens"] = son["burial"] <= LOCK

    print("=" * 96)
    print("0  雨量：三场事件的降水活跃期")
    print("=" * 96)
    cov = []      # [(a,b,event,tot_mm)] 有雨量数据的时段（用于区分"无雨"与"无数据"）
    PEAK = {}     # 事件 → 全程最大 10 min 雨量时刻（仅参考）
    RAIN10 = {}   # 事件 → 10 min 雨量序列
    for ev, rel in RAIN_FILES.items():
        r = parse_rain(os.path.join(BASE, rel))
        segs, tot = active_periods(r)
        r10 = r.set_index("t").mm.resample("10min").sum().dropna()
        RAIN10[ev] = r10
        PEAK[ev] = r10.idxmax() if len(r10) else pd.NaT
        print(f"\n{ev}: n={len(r)} 累计 {tot:.1f} mm  {r.t.min()} ~ {r.t.max()}")
        print(f"   10 min 峰值 {r10.max():.1f} mm @ {PEAK[ev]:%m-%d %H:%M}")
        for a, b, mm in segs:
            print(f"   活跃期 {a:%m-%d %H:%M} → {b:%m-%d %H:%M}  (段内雨量 {mm:.1f} mm)")
            cov.append((r.t.min(), r.t.max(), ev, tot))
        globals().setdefault("APRS", []).extend([(a, b, ev) for a, b, _ in segs])

    APRS = globals()["APRS"]

    def classify(t):
        for a, b, ev in APRS:
            if a <= t <= b:
                return "precip", ev
        for a, b, ev in [(c[0], c[1], c[2]) for c in cov]:
            if a <= t <= b:
                return "no_rain", ev
        return "no_data", None
    print("\n" + "=" * 96)
    print("1  锁定记录的降水分类（逐台）")
    print("=" * 96)
    lock = son[son.cens].copy()
    cls = [classify(t) for t in lock.t]
    lock["cls"] = [c[0] for c in cls]
    lock["ev"] = [c[1] for c in cls]
    tab = lock.groupby(["dev", "cls"]).size().unstack(fill_value=0)
    for c in ("precip", "no_rain", "no_data"):
        if c not in tab:
            tab[c] = 0
    tab = tab[["precip", "no_rain", "no_data"]]
    nm = son.groupby("dev")["name"].first().str[:14]
    tab.insert(0, "name", nm)
    tab["total"] = tab[["precip", "no_rain", "no_data"]].sum(axis=1)
    tab["pct_precip"] = (100 * tab.precip / tab.total.replace(0, np.nan)).round(1)
    print(tab.to_string())
    print(f"\n合计: 降水期 {tab.precip.sum()} / 非降水期 {tab.no_rain.sum()} / 无数据 {tab.no_data.sum()}"
          f"  = 总 {tab.total.sum()}")
    tab.to_csv(os.path.join(OUT, "p3a_lock_reclass_by_dev.csv"), encoding="utf-8-sig")

    print("\n" + "=" * 96)
    print("2  非降水期锁定的时间结构（应是故障，且应集中在无雨的日子）")
    print("=" * 96)
    nr = lock[lock.cls == "no_rain"].copy()
    if len(nr):
        nr["day"] = nr.t.dt.date
        dd = nr.groupby("day").size().sort_values(ascending=False)
        print(f"非降水期锁定 {len(nr)} 条，跨 {len(dd)} 天；前 8 天：")
        for d, n in dd.head(8).items():
            sub = nr[nr.day == d]
            print(f"   {d}  {n:5d} 条  含 {sub.dev.nunique()} 台")

    print("\n" + "=" * 96)
    print("3  降水期锁定的块结构与方向（块 = 同类连续记录）")
    print("=" * 96)
    rows = []
    for dev, x in son.groupby("dev"):
        x = x.reset_index(drop=True)
        cl = [classify(t) for t in x.t]
        x["cls"] = [c[0] for c in cl]
        x["cls_ev"] = [c[1] for c in cl]
        # 块 = 「降水活跃期」∧「锁定」的连续记录（缺一不可）
        mask = ((x.cls == "precip") & x.cens).values
        runs, s0 = [], None
        for i, v in enumerate(mask):
            if v and s0 is None:
                s0 = i
            elif not v and s0 is not None:
                runs.append((s0, i - 1)); s0 = None
        if s0 is not None:
            runs.append((s0, len(mask) - 1))
        if not runs:
            continue
        for a, b in runs:
            # 方向证据 1：块起点相对雨峰的位置（外部判据，不依赖 burial）
            ev_here = x.cls_ev.iloc[a]
            pk = PEAK.get(ev_here, pd.NaT)
            dt_pk = (x.t.iloc[a] - pk).total_seconds() / 60 if pk == pk else np.nan
            # 判据：块起点前 3 h 的累计降雨（多峰事件下比"距全局峰"稳健）
            rr = RAIN10.get(ev_here)
            r3 = np.nan
            if rr is not None:
                w3 = rr[(rr.index >= x.t.iloc[a] - pd.Timedelta(hours=3)) & (rr.index < x.t.iloc[a])]
                r3 = float(w3.sum())
            if r3 != r3:
                phase = "unknown"
            elif r3 >= RAIN_DRIVE_MM:
                phase = "rain-driven"     # 降雨驱动：水位处于上涨段
            else:
                phase = "rain-quiet"      # 降雨已停：退水段仍承压
            # 方向证据 2：块起点前 180 min 的 burial 斜率（内部判据，稀疏时缺失）
            t0 = x.t.iloc[a]
            w = x[(x.t >= t0 - pd.Timedelta(minutes=180)) & (x.t < t0)]
            sl = np.nan
            if len(w) >= 3 and (w.t.iloc[-1] - w.t.iloc[0]).total_seconds() > 1200:
                hrs = (w.t - w.t.iloc[0]).dt.total_seconds().values / 3600.0
                sl = float(np.polyfit(hrs, w.burial.values, 1)[0])
            if sl != sl:
                slope_lab = "na"
            elif sl < -0.05:
                slope_lab = "rising"
            elif sl > 0.05:
                slope_lab = "receding"
            else:
                slope_lab = "flat"
            gaps = x.t.iloc[a:b + 1].diff().dt.total_seconds().div(60).dropna()
            post = x.burial.iloc[b + 1:b + 6]
            post_m = float(post.median()) if len(post) else np.nan
            rows.append(dict(
                dev=dev, name=str(x["name"].iloc[0])[:14], event=ev_here,
                t_start=x.t.iloc[a], t_end=x.t.iloc[b], n=b - a + 1,
                dur_h=round((x.t.iloc[b] - x.t.iloc[a]).total_seconds() / 3600, 2),
                max_gap_min=round(float(gaps.max()), 0) if len(gaps) else 0.0,
                dt_peak_min=round(dt_pk, 0) if dt_pk == dt_pk else np.nan,
                rain_prev3h_mm=round(r3, 2) if r3 == r3 else np.nan,
                phase=phase,
                slope_before=round(sl, 3) if sl == sl else np.nan,
                slope_dir=slope_lab,
                burial_post=round(post_m, 3) if post_m == post_m else np.nan,
                recovered=bool(post_m == post_m and post_m > 0.3),
            ))
    blk = pd.DataFrame(rows).sort_values("t_start")
    blk.to_csv(os.path.join(OUT, "p3a_precip_lock_blocks.csv"), index=False, encoding="utf-8-sig")
    print(blk.to_string(index=False))
    print(f"\n降水期锁定块 {len(blk)} 个，{int(blk.n.sum())} 条")
    print("\n[方向判据] 块起点前 3 h 累计降雨（外部判据，>=%.0f mm 记为降雨驱动）：" % RAIN_DRIVE_MM)
    print(blk.groupby("phase").agg(n_seg=("dev", "size"), n_rec=("n", "sum"),
                                   dur_h=("dur_h", "sum")).to_string())
    print("\n[方向证据 2] 块起点前 180 min 的 burial 斜率：")
    print(blk.groupby("slope_dir").agg(n_seg=("dev", "size"), n_rec=("n", "sum"),
                                       dur_h=("dur_h", "sum")).to_string())
    n = len(blk)
    dv = blk.phase == "rain-driven"
    print(f"\n降雨驱动块: {int(dv.sum())}/{n} = {dv.sum()/max(n,1):.1%}（段计数）")
    print(f"记录加权: {int(blk[dv].n.sum())}/{int(blk.n.sum())} = {blk[dv].n.sum()/max(blk.n.sum(),1):.1%}")
    print(f"时长加权: {blk[dv].dur_h.sum():.2f}/{blk.dur_h.sum():.2f} h "
          f"= {blk[dv].dur_h.sum()/max(blk.dur_h.sum(),1e-9):.1%}")
    print(f"\n内部空档 > 60 min 的块（其 dur_h 不可用于时长统计）："
          f"{int((blk.max_gap_min > 60).sum())}/{n}")

    print("\n" + "=" * 96)
    print("4  剂量-响应矩阵：设备 × 事件（台时口径，仅活跃期）")
    print("=" * 96)
    print("关键：只有采样密集（≥10 min）的格才可比；稀疏格（>60 min）标记为不可用")
    mat = []
    for ev in RAIN_FILES:
        segs = [s for s in APRS if s[2] == ev]
        a = min(s[0] for s in segs); b = max(s[1] for s in segs)
        tot = [c[3] for c in cov if c[2] == ev][0]
        w = son[(son.t >= a) & (son.t <= b)]
        for dev, x in w.groupby("dev"):
            x = x.sort_values("t")
            cell = x.assign(bin=x.t.dt.floor("10min")).groupby("bin").cens.max()
            step = float(np.median(np.diff(x.t.values).astype("timedelta64[m]").astype(float))) if len(x) > 1 else np.nan
            mat.append(dict(ev=ev, rain_mm=round(tot, 1), dev=dev[-6:],
                            name=str(x["name"].iloc[0])[:13], n=len(x), n_cell=len(cell),
                            step=round(step, 0) if step == step else np.nan,
                            f_cell=round(float(cell.mean()), 4),
                            usable=bool(step == step and step <= 60 and len(x) >= 8)))
    M = pd.DataFrame(mat)
    M.to_csv(os.path.join(OUT, "p3a_dose_matrix.csv"), index=False, encoding="utf-8-sig")
    for ev, g in M.groupby("ev", sort=False):
        print(f"\n--- {ev}  ({g.rain_mm.iloc[0]} mm)")
        print(g.sort_values(["usable", "f_cell"], ascending=[False, False])
              [[ "name", "n", "n_cell", "step", "f_cell", "usable"]].to_string(index=False))
    print("\n可用格（密集采样）汇总：")
    u = M[M.usable]
    print(u.groupby(["ev", "rain_mm"]).f_cell.agg(["size", "mean", "min", "max"]).round(3).to_string())


if __name__ == "__main__":
    main()
