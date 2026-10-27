#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R6 修正：逐井失明阈值 h* 的基准改为「实测井深 J_p」，并给出 burial 尺度的模型检验

问题
----
v1/v2 用 h* = maxdepth - 0.26，maxdepth 取自 CAD 模型最近节点。该取值在 9/12 口井上
比实测井深大 0.55-1.64 m，使 v2 的阈值系统性偏高（同文楼 1.37 -> 1.34 无碍，
但德文图书馆 1.82 -> 0.34、海洋楼 2.08 -> 0.44 是数量级变化）。

三条判据（互相独立）
------------------
[1] burial + well 逐台恒定（std = 0）⇒ 平台配置了一个井深常数 J_p，
    且 井下水深 ≡ J_p - burial（推导量，非独立观测）。
[2] 干井时超声应读到井底 ⇒ burial_max = 井深。
[3] burial 触底写回 0.250 时，报告水深必为 J_p - 0.25。

结论
----
h* = J_p - 0.26（水深口径，与平台报出的井下水深同基准）。
模型检验改在 burial 尺度：模型 burial = maxdepth - h_model。该式两个量同以模型井底为
零点，井底偏移自动抵消，故检验结果与 J_p 是否等于 maxdepth 无关。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "outputs")
sys.path.insert(0, HERE)

from load_history import load_all

B_STAR = 0.26
FLOOR = 0.2501


def seg_J(x):
    x = x.sort_values("t")
    J = (x.burial + x.well).round(2)
    brk = (J.diff().abs() > 0.02).cumsum()
    return [(float(s.J.median()), s.t.min(), s.t.max(), len(s)) for _, s in x.assign(J=J).groupby(brk)]


def floor_ceiling_ok(x, segs):
    """在每一段内部检验：burial 触底(0.250)时报告水深 == J_seg - 0.25。"""
    ok = True
    seen = False
    for jp, t0, t1, _ in segs:
        seg = x[(x.t >= t0) & (x.t <= t1)]
        fl = seg[(seg.burial - 0.25).abs() < 6e-4]
        if len(fl) == 0:
            continue
        seen = True
        ok = ok and bool(np.allclose(fl.well, jp - 0.25, atol=6e-3))
    return ok, seen


def pick_Jp(segs, bmax):
    """主导段；若 burial_max 越界则取不小于 burial_max 的最小段。"""
    dom = max(segs, key=lambda s: s[3])[0]
    if bmax <= dom + 0.006:
        return dom
    ok = sorted(s[0] for s in segs if s[0] >= bmax - 0.006)
    return ok[0] if ok else max(s[0] for s in segs)


def main():
    son, _ = load_all()
    son["dev"] = son["dev"].astype(str).str.strip()
    son["t"] = pd.to_datetime(son["t"], errors="coerce")
    for c in ("well", "burial"):
        son[c] = pd.to_numeric(son[c], errors="coerce")
    g0 = son.dropna(subset=["burial", "well"])

    geo = pd.read_csv(os.path.join(OUT, "p3a_blind_depth_threshold.csv"), dtype={"dev": str})
    geo["dev"] = geo.dev.str.strip()
    geo = geo[~geo["name"].astype(str).str.contains("地埋式")]

    rows = []
    for _, r in geo.iterrows():
        x = g0[g0.dev == r.dev]
        segs = seg_J(x)
        bmax = float(x.burial.max())
        Jp = pick_Jp(segs, bmax)
        M = float(r.maxdepth)
        ceil_ok, ceil_seen = floor_ceiling_ok(x, segs)
        dead = bool(x.burial.nunique() <= 2)
        rows.append(dict(
            dev=r.dev, name=r["name"], node=r.new_node, dist_m=round(float(r.reg_dist_m), 2),
            n=len(x), Jp=round(Jp, 3), n_regime=len([s for s in segs if s[3] >= 5]),
            burial_max=round(bmax, 3), reaches_bottom=bool(abs(bmax - Jp) <= 6e-3),
            h_star=round(Jp - B_STAR, 3), blind_share=round(B_STAR / Jp, 4),
            n_floor=int((x.burial <= FLOOR).sum()), ceiling_ok=ceil_ok, ceiling_seen=ceil_seen,
            dead=dead,
            cad_maxdepth=round(M, 3), dJ=round(Jp - M, 3),
            regimes="; ".join(f"{s[0]:.2f}[{s[1]:%Y-%m-%d}~{s[2]:%Y-%m-%d},n={s[3]}]"
                              for s in segs if s[3] >= 5),
        ))
    tab = pd.DataFrame(rows).sort_values("h_star")
    tab.to_csv(os.path.join(OUT, "p3a_r6_threshold.csv"), index=False, encoding="utf-8-sig")

    W = 104
    print("=" * W)
    print("[判据 2] 干井时 burial_max 是否等于 J_p")
    hit = tab[tab.reaches_bottom & ~tab.dead]
    print(f"  精确相等: {len(hit)} 台 — " + "; ".join(f"{r['name'][:7]}={r.burial_max:.2f}" for _, r in hit.iterrows()))
    print(f"  从未干到井底: {int((~tab.reaches_bottom).sum())} 台 — "
          + "; ".join(f"{r['name'][:7]}{r.burial_max:.2f}<{r.Jp:.2f}" for _, r in tab[~tab.reaches_bottom].iterrows()))

    print("\n[判据 3] burial 触底(0.250)时报告水深是否 = J_seg - 0.25（逐段检验）")
    seen = tab[tab.ceiling_seen]
    print(f"  成立 {int(seen.ceiling_ok.sum())}/{len(seen)} 台（有触底记录的设备）")
    bad = seen[~seen.ceiling_ok]
    if len(bad):
        print("  不成立: " + "; ".join(f"{r['name'][:7]} n={r.n_floor}" for _, r in bad.iterrows()))

    print("\n[判据 4] 配置改动是否造成报告水深的整体平移（同 burial 下换一个井深）")
    for _, r in tab.iterrows():
        if r.n_regime > 1:
            print(f"  {r['name'][:12]:14s} {r.regimes}")

    print("\n" + "=" * W)
    print("[结果] 逐井失明阈值 h* = J_p - 0.26（按 h* 升序）")
    s = tab.assign(dev=lambda d: d.dev.str[-4:])[
        ["dev", "name", "Jp", "h_star", "blind_share", "cad_maxdepth", "dJ", "burial_max", "n_floor", "dead"]]
    s["blind_share"] = (100 * s.blind_share).round(1)
    s["dead"] = s.dead.map({True: "DEAD", False: ""})
    print(s.to_string(index=False))
    live = tab[~tab.dead]
    print(f"\n  h* 范围      : {live.h_star.min():.2f} ~ {live.h_star.max():.2f} m（中位 {live.h_star.median():.2f}，n={len(live)}）")
    print(f"  盲带占井深   : {100*live.blind_share.min():.1f}% ~ {100*live.blind_share.max():.1f}%"
          f"（中位 {100*live.blind_share.median():.1f}%）—— 绝对宽度恒为 0.26 m")
    print(f"  CAD ΔJ       : {tab.dJ.min():.2f} ~ {tab.dJ.max():.2f} m；|ΔJ|<=0.15 仅 {int((tab.dJ.abs()<=0.15).sum())}/{len(tab)} 台")
    print(f"  旧阈值->新阈值（|ΔJ|>0.15 的井，前 6 台）:")
    for _, r in tab[tab.dJ.abs() > 0.15].head(6).iterrows():
        print(f"    {r['name'][:10]:12s} {r.cad_maxdepth-0.26:.2f} -> {r.h_star:.2f}  (Δ {r.h_star-(r.cad_maxdepth-0.26):+.2f})")

    # ---------------- 模型检验：burial 尺度 ----------------
    S = pd.read_csv(os.path.join(OUT, "p3a_0719_model_series.csv"))
    S["t"] = pd.to_datetime(S["t"])
    MAP = {"867948079409621": ("node_5465", "同文楼"), "867948079405843": ("node_4857", "结构实验室"),
           "867948079403574": ("node_3498", "赤峰路")}

    print("\n" + "=" * W)
    print("[模型检验] 0719 实测：模型 burial 是否在观测到的失明时段 <= 0.26")
    recs = []
    for dev, (nd, lab) in MAP.items():
        m = S[S.node == nd].sort_values("t").reset_index(drop=True)
        md = float(m.maxdepth.iloc[0])
        m["b"] = md - m.h_model
        x = son[son.dev == dev].sort_values("t").dropna(subset=["burial"])
        day = x[(x.t >= "2026-07-19 12:00") & (x.t <= "2026-07-20 06:00")]
        lock_t = day[day.burial <= FLOOR].t
        if len(lock_t) == 0:
            continue
        first_lock, last_lock = lock_t.min(), lock_t.max()
        before = day[(day.t < first_lock) & (day.burial > 0.30)]
        after = day[(day.t > last_lock) & (day.burial > 0.30)]
        blind = m[m.b <= B_STAR]
        onset = blind.t.min() if len(blind) else pd.NaT
        # 模型连续失明块
        idx = blind.index.to_numpy()
        if len(idx):
            brk = np.where(np.diff(idx) > 1)[0]
            a0 = np.r_[idx[0], idx[brk + 1]]
            e0 = np.r_[idx[brk], idx[-1]]
            dur = int((e0 - a0 + 1).max())
            off = m.loc[e0[np.argmax(e0 - a0)], "t"]
        else:
            dur, off = 0, pd.NaT
        recs.append(dict(dev=dev[-6:], label=lab, node=nd,
                         obs_before=str(before.t.max())[11:16] if len(before) else "",
                         obs_before_b=round(float(before.burial.iloc[-1]), 2) if len(before) else np.nan,
                         obs_first_lock=str(first_lock)[11:16],
                         obs_last_lock=str(last_lock)[11:16],
                         obs_after=str(after.t.min())[11:16] if len(after) else "",
                         obs_after_b=round(float(after.burial.iloc[0]), 2) if len(after) else np.nan,
                         mdl_onset=str(onset)[11:16] if pd.notna(onset) else "未越阈",
                         mdl_recover=str(off)[11:16] if pd.notna(off) else "",
                         mdl_blind_min=dur,
                         mdl_b_at_first_lock=round(float(m.loc[(m.t - first_lock).abs().idxmin(), "b"]), 3),
                         mdl_b_at_last_lock=round(float(m.loc[(m.t - last_lock).abs().idxmin(), "b"]), 3)))
        r = recs[-1]
        print(f"\n  {lab} ({nd})  maxdepth={md:.2f}")
        print(f"    观测: 末次有效 {r['obs_before']} b={r['obs_before_b']} → 首次写回 {r['obs_first_lock']} "
              f"→ 末次写回 {r['obs_last_lock']} → 首次恢复 {r['obs_after']} b={r['obs_after_b']}")
        print(f"    模型: 越阈 {r['mdl_onset']}，连续失明 {dur} min（{dur/60:.1f} h），结束 {r['mdl_recover']}")
        print(f"    写回时刻模型 burial: 首次 {r['mdl_b_at_first_lock']}，末次 {r['mdl_b_at_last_lock']}（阈值 0.26）")
    ck = pd.DataFrame(recs)
    ck.to_csv(os.path.join(OUT, "p3a_r6_model_check.csv"), index=False, encoding="utf-8-sig")
    print("\n  -> outputs/p3a_r6_threshold.csv, outputs/p3a_r6_model_check.csv")


if __name__ == "__main__":
    main()
