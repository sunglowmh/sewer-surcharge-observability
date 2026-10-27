# -*- coding: utf-8 -*-
"""可观测性指数 Ω 与 Δ_obs 的**时间正确**主表（v2，修正 v1 的 J 混用 bug）。

v1（`p3a_r7_delta_obs.py` 第 5 段）用 `Jl`（该台**最后**一段 J）去配**所有**阈值：
  同文楼 thr=0.90 只在 2026-07-03~07-07（当时 J=1.20）生效，
  却被配上 J=1.60 ⇒ b_θ 由 0.30 抬到 0.70 ⇒ Δ_obs 由 +0.04 抬到 +0.44。
这正是 E2 要消灭的那类错误，只是换了一层皮。本版改为：
  **每条阈值只配「该阈值实际生效期间」的 J**，J 由该阈值下的报警记录反推（floor + 0.25）。

产出
  outputs/p3a_obs_index.csv   (dev, thr) 级：J_p, b_θ, Ω, Δ_obs, 报警数, 各色数, 在写回值条数
  outputs/p3a_obs_index_bydev.csv  设备级：Ω 跨度、φ=(D+B)/J、h*=J−0.26
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DB = 0.26
FW = 0.25

al = pd.read_csv(os.path.join(OUT, "p3a_J_alarm_check.csv"))
al["Jp"] = (al.floor + FW).round(2)          # 该阈值生效期间平台的 J
al["b_th"] = (al.Jp - al.thr).round(2)
al["Omega"] = (al.b_th / DB).round(3)
al["D_obs"] = (al.b_th - DB).round(2)

g = (al.groupby(["dev", "name", "thr", "Jp", "b_th", "Omega", "D_obs"])
       .agg(n=("cur", "size"), at_floor=("at_floor", "sum"),
            yellow=("colour", lambda s: int((s == "yellow").sum())),
            blue=("colour", lambda s: int((s == "blue").sum())),
            red=("colour", lambda s: int((s == "red").sum())),
            t0=("t", "min"), t1=("t", "max"))
       .reset_index()
       .sort_values("Omega"))
g["estimable"] = np.where(g.Omega > 1, "可估计", "不可估计")
g.to_csv(os.path.join(OUT, "p3a_obs_index.csv"), index=False, encoding="utf-8-sig")
# 同内容覆盖旧主表（v1 用 J_late 配所有阈值，已作废），加版本列防误引
g.assign(version="v2_time_matched").to_csv(
    os.path.join(OUT, "p3a_delta_obs.csv"), index=False, encoding="utf-8-sig")

# ---- 设备级：Ω 跨度 + φ + h* ----
# J 取论文 §4.4a 已核定的值（三条判据：分段恒定 / 干井 burial_max / 触底报 J−0.25）。
# 不取「最后一段」：海洋楼最后一段 0.70 已被物理反证（cur 1.34 > 0.70）作废；
# 也不取「条数最多段」：继教 1.30 段更长，但干井与报警都指向 1.40。
J_VALID = {
    "867948079405652": 0.55,   # 08 德文图书馆
    "867948079405546": 1.40,   # 12 继教
    "867948079405785": 1.30,   # 06 爱校路
    "867948079405611": 1.45,   # 07 医学楼
    "867948079409621": 1.60,   # 11 同文楼
    "867948079409829": 1.60,   # 05 海洋楼
    "867948079405165": 1.75,   # 09 新体育馆
    "867948079405843": 1.95,   # 02 结构实验室
    "867948079405678": 1.90,   # 04 泵水池
    "867948079407252": 2.25,   # 13 文远楼
    "867948079403574": 2.70,   # 01 赤峰路
}
rows = []
for dev, sub in g.groupby("dev"):
    J = float(J_VALID.get(str(dev), np.nan))
    rows.append(dict(dev=dev, name=sub.name.iloc[0], J=J,
                     h_star=round(J - DB, 2),
                     phi=round(DB / J * 100, 1) if J and J > 0 else np.nan,
                     Omega_min=sub.Omega.min(), Omega_max=sub.Omega.max(),
                     n_cfg=len(sub), n_neg=int((sub.Omega <= 1).sum()),
                     alarms=sub.n.sum(), alarms_neg=sub[sub.Omega <= 1].n.sum()))
B = pd.DataFrame(rows).sort_values("phi", ascending=False)
B.to_csv(os.path.join(OUT, "p3a_obs_index_bydev.csv"), index=False, encoding="utf-8-sig")

pd.set_option("display.width", 240, "display.max_columns", 40)
print("=== (dev, thr) 级：可观测性指数 Ω（12 条阈值配置） ===")
print(g[["name", "thr", "Jp", "b_th", "Omega", "D_obs", "estimable",
         "n", "at_floor", "yellow", "blue", "red"]].to_string(index=False))
neg = g[g.Omega <= 1]
pos = g[g.Omega > 1]
print()
print(f"配置总数 {len(g)}：Ω>1 {len(pos)} 条（Δ_obs {pos.D_obs.min():+.2f}~{pos.D_obs.max():+.2f}，报警 {pos.n.sum()}）")
print(f"           Ω≤1 {len(neg)} 条（Δ_obs {neg.D_obs.min():+.2f}~{neg.D_obs.max():+.2f}，报警 {neg.n.sum()}）")
print(f"           Ω≤1 中：蓝 {neg.blue.sum()} / 黄 {neg.yellow.sum()} / 红 {neg.red.sum()} / 落在写回值 {neg.at_floor.sum()}")
print(f"Ω 全局范围 {g.Omega.min()}~{g.Omega.max()}，中位 {g.Omega.median():.2f}")
print(f"Δ_obs 全局范围 {g.D_obs.min():+.2f}~{g.D_obs.max():+.2f}")
print()
print("=== 设备级：φ = (D+B)/J ===")
print(B[["name", "J", "h_star", "phi", "Omega_min", "Omega_max", "n_cfg", "n_neg"]].to_string(index=False))
print()
print(f"φ 范围 {B.phi.min()}%~{B.phi.max()}%，倍数 {B.phi.max()/B.phi.min():.1f}×")
