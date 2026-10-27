"""Generate the three camera-ready tables (Table 1-3) for paper 3.

Reads only the frozen CSVs in outputs/ and asserts every number quoted in the
manuscript, so that a silent change in an upstream file aborts the build rather
than producing a plausible-looking table.

Outputs
-------
outputs/tables/table1_instruments.csv
outputs/tables/table2_configurations.csv
outputs/tables/table3_treatments.csv
outputs/tables/tables_body.md          (markdown bodies, no captions)
"""
from __future__ import annotations

import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
TAB = os.path.join(OUT, "tables")
os.makedirs(TAB, exist_ok=True)

D_WIN = 0.26  # blind window D+B, m

PREFIX_EN = {
    "01": "Chifeng Road",
    "02": "Structure Laboratory",
    "03": "Northwest Building",
    "04": "Pumped chamber (Int. Students Bldg 2)",
    "05": "Ocean Building",
    "06": "Aixiao Road",
    "07": "Medical Building",
    "08": "German Library",
    "09": "New Gymnasium",
    "10": "Main Gate",
    "11": "Tongwen Building",
    "12": "Continuing Education",
    "13": "Wenyuan Building",
}


def prefix(cn: str) -> str:
    """'01号赤峰路200号...' -> '01'; '9号新体育馆...' -> '09'."""
    head = cn.split("号")[0]
    return head.zfill(2)


def load():
    seg = pd.read_csv(f"{OUT}/p3a_J_segments.csv", dtype={"dev": str})
    geo = pd.read_csv(f"{OUT}/p3a_sensor_geometry.csv", dtype={"dev": str})
    om = pd.read_csv(f"{OUT}/p3a_Omega_config.csv")
    obs = pd.read_csv(f"{OUT}/p3a_obs_index.csv", dtype={"dev": str})
    r7 = pd.read_csv(f"{OUT}/p3a_r7_ratio.csv")
    sites = pd.read_csv(f"{OUT}/figdata/fig2_sites.csv", dtype={"dev": str})
    return seg, geo, om, obs, r7, sites


def build_table1(seg, geo, sites):
    cad = sites[sites.kind == "sewer"].set_index("dev")["dt_med"]
    rows = []
    for dev, g in seg[seg.keep].groupby("dev"):
        g = g.sort_values("t0")
        p = prefix(g.name.iloc[0])
        js = list(g.J)
        n = int(g.n.sum())
        row = {
            "No.": p,
            "Site": PREFIX_EN[p],
            "J (m)": " \u2192 ".join(f"{j:.2f}" for j in js),
            "Readings with burial": n,
            "Cadence (min)": int(round(cad.loc[dev])),
            "thr (m)": "",
            "b_theta (m)": "",
            "Omega": "",
        }
        # phi / h* use the effective (last) segment; 05's 0.70 m is flagged
        J_eff = js[-1]
        row["phi (%)"] = f"{100*D_WIN/J_eff:.1f}"
        row["h* (m)"] = f"{J_eff-D_WIN:.2f}"
        rows.append(row)
    t1 = pd.DataFrame(rows).set_index("No.")

    # attach the 12 configurations, matched on site prefix + well depth
    for _, c in t1.iterrows():
        pass
    return t1


def main():
    seg, geo, om, obs, r7, sites = load()

    # ---------- shared keys ----------
    om = om.assign(pre=om.name.map(prefix))
    obs = obs.assign(pre=obs.name.map(prefix)).rename(columns={"Jp": "J"})
    r7 = r7.assign(pre=r7.name.map(prefix))
    key = ["pre", "thr", "J"]
    assert len(om) == 12 and len(obs) == 12 and len(r7) == 12
    for a, b, nm in ((om, obs, "obs"), (om, r7, "r7")):
        ma = set(map(tuple, a[key].values))
        mb = set(map(tuple, b[key].values))
        assert ma == mb, f"key mismatch with {nm}: {ma ^ mb}"

    # ---------- Table 2 ----------
    # Row order is the order of the frozen CSV (Omega ascending); the same order
    # and the same 1..12 identifiers are used in Table 3, so a configuration can
    # be read across the two tables.
    t2 = om.merge(obs[key + ["dev", "yellow", "blue", "red"]], on=key, validate="1:1")
    t2["Judgement"] = t2["est"].map({"可估计": "estimable", "不可估计": "not estimable"})
    assert (t2.n_elev == 0).sum() == 5, "expected five configurations with zero exceedances"
    lo = t2.Omega <= 1
    assert t2.loc[lo, "yellow"].sum() + t2.loc[lo, "blue"].sum() + t2.loc[lo, "red"].sum() == 90
    assert t2.yellow.sum() + t2.blue.sum() + t2.red.sum() == 305
    assert t2.loc[lo, "n_read"].sum() == 9578
    assert t2.loc[~lo, "n_read"].sum() == 13494
    assert t2.loc[~lo, "n_elev"].sum() == 71
    assert t2.Omega.min().round(3) == 0.385 and t2.Omega.max().round(3) == 1.538
    assert abs(t2.Omega.median() - 1.154) < 1e-9

    # Note 1 of Table 2: the twelve threshold configurations do not map onto twelve
    # well-depth segments. Three pairs (1/6, 2/7, 4/11) sit on one segment each and are
    # distinguished only by threshold, so the rows cover 9 of the 18 segments of Table 1
    # and the readings of the six shared-segment rows are counted twice.
    row_seg = pd.Series(list(zip(t2.pre, t2.J.round(2))), index=t2.index)
    seg_rows = row_seg.value_counts()
    assert len(seg_rows) == 9, f"expected 9 segments, got {len(seg_rows)}"
    assert (seg_rows > 1).sum() == 3 and seg_rows[seg_rows > 1].sum() == 6, seg_rows.tolist()
    dup_read = int(t2.n_read.sum() - t2.groupby(row_seg).n_read.max().sum())
    dup_lock = int(t2.n_lock.sum() - t2.groupby(row_seg).n_lock.max().sum())
    assert (dup_read, dup_lock) == (4229, 2), (dup_read, dup_lock)

    def b_(v, cond):
        return f"**{v:,}**" if cond else f"{v:,}"

    t2["No."] = range(1, len(t2) + 1)
    t2o = pd.DataFrame({
        "No.": t2["No."],
        "Site": [f"{p} {PREFIX_EN[p]}" for p in t2.pre],
        "thr (m)": t2.thr.map(lambda v: f"{v:.2f}"),
        "J (m)": t2.J.map(lambda v: f"{v:.2f}"),
        "b_theta (m)": t2.b_th.map(lambda v: f"{v:.2f}"),
        "Omega": [f"**{v:.3f}**" if v <= 1 else f"{v:.3f}" for v in t2.Omega],
        "Delta_obs (m)": t2.D_obs.map(lambda v: f"{v:+.2f}"),
        "Readable": t2.n_read.map(lambda v: f"{v:,}"),
        "At floor": t2.n_lock.map(lambda v: f"{v:,}"),
        "Below thr": t2.n_elev.map(lambda v: f"**0**" if v == 0 else f"{v}"),
        "Y": t2.yellow, "B": t2.blue, "R": t2.red,
        "Criterion": t2.Judgement,
    })
    t2o.to_csv(f"{TAB}/table2_configurations.csv", index=False)

    # ---------- Table 2 row order (single source for table and figure) ----------
    # Fig. 7 draws one horizontal line per configuration and must stack them in
    # exactly this order, otherwise "row 5 of Table 2" and "the fifth line of
    # Fig. 7" name different configurations.  The order is frozen here once and
    # read back by fig7_fig9.py; it is never re-derived from a sort inside the
    # plotting script (an earlier version sorted on the alarm count as a
    # tie-breaker, which silently disagreed with the table inside three Omega
    # groups).
    roworder = pd.DataFrame({
        "No.": t2["No."],
        "pre": t2.pre,
        "thr": t2.thr,
        "J": t2.J,
        "Omega": t2.Omega,
        "dev": t2.dev.astype(str),
    })
    assert roworder["No."].tolist() == list(range(1, 13))
    assert roworder["Omega"].is_monotonic_increasing, "row order must follow Omega"
    roworder.to_csv(f"{TAB}/table2_roworder.csv", index=False)

    # ---------- Table 1 ----------
    # One row per well-depth segment, because J is a segmented quantity and a
    # device with a changed J cannot be described by a single row. The segment
    # J = 0.70 m at the Ocean Building is retained but flagged: it is physically
    # impossible (a reading of 1.34 m exceeds J) and is excluded from phi and h*.
    cad = sites[sites.kind == "sewer"].set_index("dev")["dt_med"]
    INVALID = {("05", 0.70)}
    t1 = []
    for _, r in seg[seg.keep].sort_values(["dev", "t0"]).iterrows():
        p = prefix(r["name"])
        cfgs = t2[(t2.pre == p) & (abs(t2.J - r.J) < 1e-9)]
        d = pd.Timestamp(r.t1).strftime("%d %b %Y")
        bad = (p, round(float(r.J), 2)) in INVALID
        t1.append({
            "No.": p + ("\u2020" if bad else ""),
            "Site": PREFIX_EN[p],
            "J (m)": f"{r.J:.2f}",
            "From": pd.Timestamp(r.t0).strftime("%d %b %Y"),
            "Until": d,
            "_from": pd.Timestamp(r.t0).strftime("%d %b %Y"),
            "thr (m)": " / ".join(f"{v:.2f}" for v in cfgs.thr) if len(cfgs) else "\u2014",
            "b_theta (m)": " / ".join(f"{v:.2f}" for v in cfgs.b_th) if len(cfgs) else "\u2014",
            "Omega": " / ".join(f"{v:.3f}" for v in cfgs.Omega) if len(cfgs) else "\u2014",
            "phi (%)": f"{100*D_WIN/r.J:.1f}",
            "h* (m)": f"{r.J-D_WIN:.2f}",
            "Cadence (min)": int(round(cad.loc[r.dev])),
            "Readings with burial": int(r.n),
        })
    t1o = pd.DataFrame(t1)
    # Sort on the *instrument number* and then on the segment start date, not on
    # the instrument number and then on the printed J: the J column is a string,
    # so "1.90" sorts before "2.00" and the pumped chamber's two segments come out
    # in the wrong order.  The build must not depend on how a number is printed.
    t1o["_k"] = t1o["No."].str.rstrip("\u2020").astype(int)
    t1o["_t"] = pd.to_datetime(t1o["_from"], format="%d %b %Y")
    t1o = (t1o.sort_values(["_k", "_t"])
              .drop(columns=["_k", "_t", "_from"]).reset_index(drop=True))
    assert t1o["No."].str.rstrip("\u2020").is_monotonic_increasing, "Table 1 must run 01..13"
    t1o.to_csv(f"{TAB}/table1_instruments.csv", index=False)

    # sanity: phi range and the two ends quoted in 5.3 / 6.4
    ph = t1o["phi (%)"].astype(float).values
    valid = t1o["No."].str.endswith("\u2020") == False
    ph_v = ph[valid]
    assert abs(ph_v.min() - 9.6) < 0.05 and abs(ph_v.max() - 47.3) < 0.05, (ph_v.min(), ph_v.max())
    # 13 devices + 04, 05(daggers), 11, 12, 08 split = 18 rows
    assert len(t1o) == 18, len(t1o)

    # ---------- Table 3 ----------
    # r7 rows are in the same order as om; assert that before numbering
    assert all(abs(a_.J - b_.J) < 1e-9 and a_.thr == b_.thr and a_.pre == b_.pre
               for a_, b_ in zip(r7.itertuples(), om.itertuples()))
    t3 = r7.copy().reset_index(drop=True)
    t3["No."] = t2["No."].values
    t3["cap_ratio"] = t3.D3_24 / t3.D3_6
    t3o = pd.DataFrame({
        "No.": t3["No."],
        "Site": [PREFIX_EN[p] for p in t3.pre],
        "thr (m)": t3.thr.map(lambda v: f"{v:.2f}"),
        "Omega": t3.Omega.map(lambda v: f"{v:.3f}"),
        "D1 (h)": t3.D1_6.map(lambda v: f"{v:.2f}"),
        "D2 (h)": t3.D2_6.map(lambda v: f"{v:.2f}"),
        "D3 (h)": t3.D3_6.map(lambda v: f"{v:.2f}" if pd.notna(v) else "\u2014"),
        "D2/D1": t3.R21_6.map(lambda v: f"{v:.2f}" if pd.notna(v) else "\u2014"),
        "D3 cap 24 h / 6 h": t3.cap_ratio.map(
            lambda v: f"{v:.2f}" if pd.notna(v) and v > 0 else "\u2014"),
        "Span (h)": t3.span_h.map(lambda v: f"{v:.0f}" if pd.notna(v) else "\u2014"),
        "Median gap (h)": t3.med_gap_h.map(lambda v: f"{v:.2f}"),
    })
    t3o.to_csv(f"{TAB}/table3_treatments.csv", index=False)

    # ---------- assertions quoted in the text ----------
    pos = t3o["D2/D1"].replace("\u2014", None).dropna().astype(float)
    assert abs(pos.min() - 1.00) < 1e-9 and abs(pos.max() - 8.67) < 1e-9, pos.tolist()
    assert abs(pos.median() - 2.00) < 1e-9
    # the range quoted in 6.3 is over the seven configurations whose estimate exists
    cap = t3.loc[t3.D1_6 > 0, "cap_ratio"].dropna()
    assert abs(cap.min() - 1.08) < 5e-3 and abs(cap.max() - 4.00) < 5e-3, cap.tolist()

    def md(df):
        head = "| " + " | ".join(df.columns) + " |"
        sep = "|" + "|".join(["---"] * len(df.columns)) + "|"
        body = "\n".join(
            "| " + " | ".join(str(v) for v in r) + " |" for r in df.values
        )
        return f"{head}\n{sep}\n{body}"

    with open(f"{TAB}/tables_body.md", "w", encoding="utf-8") as fh:
        for nm, df in (("Table 1", t1o), ("Table 2", t2o), ("Table 3", t3o)):
            fh.write(f"### {nm}\n\n{md(df)}\n\n")

    print("OK  ->", TAB)
    print("Table 1 rows", len(t1o), "| Table 2 rows", len(t2o), "| Table 3 rows", len(t3o))
    print("D2/D1 range", pos.min(), pos.max(), "median", pos.median())
    print(md(t1o))
    print()
    print(md(t2o))
    print()
    print(md(t3o))


if __name__ == "__main__":
    main()
