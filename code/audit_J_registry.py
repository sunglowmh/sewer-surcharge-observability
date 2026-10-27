# -*- coding: utf-8 -*-
"""E2：核定 `J`（井深）——判据是「J 随时间分段恒定，在检修日跳变」。

输出
  outputs/p3a_J_registry.csv        每台设备：J 的取值段（起止时间、条数、值）
  outputs/p3a_J_verdict.csv         每台设备：采纳的 J（末段值）、跳变日、是否与报警表自洽
  outputs/p3a_delta_obs.csv         Δ_obs = (J − thr) − 0.26 逐台（R7 主表）
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_history import load_all, load_alarms  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
D_BLIND = 0.26

sonic, buried = load_all()
s = sonic[sonic.well.notna() & sonic.burial.notna()].copy()
s["J"] = (s.burial + s.well).round(2)

# ---------------- 1. J 的取值段 ----------------
rows = []
for dev, g in s.groupby("dev"):
    g = g.sort_values("t")
    j = g.J.values
    t = g.t.values
    # 跳变点：与上一段值相差 ≥ 0.05
    segs, s0 = [], 0
    for i in range(1, len(j)):
        if abs(j[i] - j[i - 1]) >= 0.05:
            segs.append((s0, i - 1, j[s0]))
            s0 = i
    segs.append((s0, len(j) - 1, j[s0]))
    for k, (a, b, v) in enumerate(segs):
        rows.append(dict(dev=dev, name=g.name.iloc[0], seg=k, J=v,
                         n=b - a + 1, t0=t[a], t1=t[b]))
Jseg = pd.DataFrame(rows)
Jseg.to_csv(os.path.join(OUT, "p3a_J_registry.csv"), index=False, encoding="utf-8-sig")

# ---------------- 2. 报警表反推 J（cur + 0.25），逐次 ----------------
al = load_alarms()
import re
al["cur"] = al.msg.str.extract(r"当前值[^\d\-]*(-?\d+\.?\d*)").astype(float)
al["thr"] = al.msg.str.extract(r"阈值[^\d\-]*(-?\d+\.?\d*)").astype(float)
als = al[al.dev.isin(sonic.dev.unique())].dropna(subset=["cur"]).copy()
als["J_alarm"] = (als.cur + 0.25).round(2)

verdict = []
for dev, g in s.groupby("dev"):
    seg = Jseg[Jseg.dev == dev].sort_values("seg")
    J_last = seg.J.iloc[-1]
    nseg = len(seg)
    chg = "" if nseg == 1 else str(seg.t0.iloc[1])[:10]
    aa = als[als.dev == dev]
    J_alm = sorted(aa.J_alarm.round(1).value_counts().to_dict().items(), key=lambda x: -x[1])
    J_alm_top = J_alm[0][0] if J_alm else np.nan
    verdict.append(dict(dev=dev, name=seg.name.iloc[0], n_seg=nseg,
                        J_early=seg.J.iloc[0], J_late=J_last, change_day=chg,
                        n_alarm=len(aa), J_from_alarm=J_alm_top,
                        alarm_matches_late=(abs(J_alm_top - J_last) < 0.02) if J_alm else None))
V = pd.DataFrame(verdict).sort_values(["n_alarm", "dev"], ascending=[False, True])
V.to_csv(os.path.join(OUT, "p3a_J_verdict.csv"), index=False, encoding="utf-8-sig")

# ---------------- 3. Δ_obs 主表 ----------------
# thr 取报警表里该台出现最多的阈值；无报警的台用平台配置（框架 §4.4）
THR_CONFIG = {
    "867948079409621": 1.40,  # 11 同文楼
    "867948079403574": 2.40,  # 01 赤峰路
    "867948079405843": 1.60,  # 02 结构实验室
    "867948079405678": 1.70,  # 04 泵水池
    "867948079405546": 1.00,  # 12 继教
    "867948079405165": 2.60,  # 09 新体育馆
    "867948079409829": 1.50,  # 05 海洋楼
    "867948079405611": 1.10,  # 07 医学楼
    "867948079405785": 1.10,  # 06 爱校路
    "867948079407252": 2.00,  # 13 文远楼
    "867948079405652": 1.30,  # 08 德文图书馆
    "863721076643276": 1.20,  # 03 西北二楼
    "867948079409803": 1.50,  # 10 大门口
}
drows = []
for _, r in V.iterrows():
    thr = THR_CONFIG.get(r.dev, np.nan)
    J = r.J_late
    b_th = J - thr if pd.notna(thr) else np.nan
    d = b_th - D_BLIND if pd.notna(b_th) else np.nan
    drows.append(dict(dev=r.dev, name=r["name"], J=J, thr=thr, b_th=round(b_th, 2) if pd.notna(b_th) else np.nan,
                      D_obs=round(d, 2) if pd.notna(d) else np.nan,
                      side="可读数（Δ>0）" if d > 0 else "结构上恒零（Δ≤0）",
                      floor_val=round(J - 0.25, 2), n_alarm=r.n_alarm,
                      J_early=r.J_early, changed=r.n_seg > 1))
D = pd.DataFrame(drows).sort_values("D_obs", ascending=False)
D.to_csv(os.path.join(OUT, "p3a_delta_obs.csv"), index=False, encoding="utf-8-sig")

# ---------------- 打印 ----------------
pd.set_option("display.width", 200, "display.max_columns", 40)
print("=== J 取值段（分段数 >1 的台） ===")
print(Jseg[Jseg.dev.isin(Jseg.groupby("dev").size()[lambda x: x > 1].index)].to_string(index=False))
print("\n=== J 核定结论 ===")
print(V.to_string(index=False))
print("\n=== Δ_obs 主表 ===")
print(D.to_string(index=False))
print("\n=== 汇总 ===")
print("Δ>0（可读数）:", int((D.D_obs > 0).sum()), "台;  Δ≤0（恒零）:", int((D.D_obs <= 0).sum()), "台")
print("J 曾被改过的台:", int(D.changed.sum()), "台")
