# sewer-surcharge-observability

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23683481.svg)](https://doi.org/10.5281/zenodo.23683481)
[![code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![data: CC BY 4.0](https://img.shields.io/badge/data-CC--BY--4.0-lightgrey.svg)](outputs/LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](requirements.txt)

Reproducibility material for the manuscript *Where in-sewer level records stop
decides whether surcharge duration can be estimated*.

This repository holds **the derived tables from which every figure and table is
drawn, and the code that draws them**. It does not hold the raw level archive:
those are the operational records of a campus drainage network and remain with
the operator (see the Data availability statement of the paper). Everything the
paper claims can be recomputed from the files below — that is the point of the
paper, and this repository is where the claim is checked.

## Reproduce it

```
pip install -r requirements.txt     # numpy, pandas, matplotlib
python reproduce_all.py
```

`reproduce_all.py` redraws Figs. 1–9, regenerates Tables 1–3, recomputes `Omega`
from the published table, and then compares the six files it rewrote against the
hashes in `SHA256SUMS`. A silent change in any derived number therefore shows up
as `CHANGED`, not as a slightly different figure. Expected final line:
`PASS  every figure redrawn, every table and quantity byte-identical`.

Python 3.13 with three packages; no commercial software, no GIS stack. Each
script resolves `ROOT` from its own location, so a clone runs where it is
cloned. Figure PDFs are not checksummed: they carry a creation date and a font
subset, so their bytes move on every run even when the picture does not.

## What is where

| Paper item | Data | Code to rebuild it |
|---|---|---|
| Fig. 1 — where the window closes | none (drawn from `J`, `thr`, `D+B` only) | `code/fig1.py` |
| Fig. 2 — the two networks | `outputs/figdata/fig2_sites.csv`, `campus_outline.csv`, `basemap_osm.csv`, `basemap_campus.txt` | `code/fig2.py` |
| Fig. 3 — one instrument, three weeks | `outputs/figdata/fig3_{block,decomp,surface_day}.csv`, `outputs/p3a_precip_lock_blocks.csv` | `code/fig3.py` |
| Fig. 4 — dose and response | `outputs/p3a_dose_matrix.csv`, `p3a_dose_response_dual.csv` | `code/fig4.py` |
| Fig. 5 — blindness and the surface | `outputs/figdata/fig5_{status,trace,surface}.csv` | `code/fig5.py` |
| Fig. 6 — where the record stops | `outputs/figdata/fig6{a,b,c}_*.csv` | `code/fig6.py` |
| Figs. 7 and 9 — configurations, and `Omega` against `J` | `outputs/p3a_Omega_config.csv`, `p3a_obs_index.csv`, `p3a_J_segments.csv`, `outputs/tables/table2_roworder.csv` | `code/fig7_fig9.py` |
| Fig. 8 — the label is a function of one sign | `outputs/p3a_alarm_sign_flip.csv` | `code/fig8.py` |
| Table 1 — well-depth segments | `outputs/tables/table1_instruments.csv` | `code/make_tables.py` |
| Table 2 — threshold configurations | `outputs/tables/table2_configurations.csv` | `code/make_tables.py` |
| Table 3 — three treatments | `outputs/tables/table3_treatments.csv` | `code/make_tables.py` |

`outputs/tables/table2_roworder.csv` is the single source of the row order used
by Tables 2 and 3 and by Fig. 7. Renaming it or dropping a column stops
`fig7_fig9.py` on an assertion rather than producing a figure whose rows no
longer match the table — a failure that is intended.

## Which scripts run here, and which do not

| Scripts | Run from this repository | Why not |
|---|---|---|
| `fig1`–`fig8`, `fig7_fig9`, `make_tables` | yes | — |
| `fetch_basemap_osm.py` | only with network access | re-downloads the Fig. 2 basemap from OpenStreetMap; the extract is committed, so this is needed to refresh it, not to reproduce the figure |
| `p3a_obs_index.py` | yes | it recomputes `Omega`, `b_theta` and `Delta_obs` from the shipped `p3a_J_alarm_check.csv` and rewrites `outputs/p3a_obs_index*.csv`; `reproduce_all.py` checks that the rewrite is byte-identical |
| `prep_figdata.py` | no | rebuilds `outputs/figdata/` from the raw archive; its output is committed, so nothing downstream needs it |
| `p3a_lock_reclass_rain.py`, `p3a_recompute_r6.py`, `p3a_onset_lag_baserate.py`, `audit_J_registry.py` | no | recompute the quantities the text quotes from the registry exports and the alarm log; those exports stay with the operator. Their results are the `outputs/p3a_*.csv` committed here |

Those five are shipped so that they can be read, not run. `code/load_history.py`
is the archive loader; with no archive present it stops with a message that says
so, rather than an `ImportError` from somewhere inside pandas.

## What is deliberately absent

* The raw ten-minute level series, the registry originals (`.xlsx`) and the alarm
  log: operational records of the network operator, released only with the
  operator's written consent. The paper's Data availability statement says this
  and explains how to request access.
* `loc`, the platform's street address for each instrument, is dropped from
  `p3a_alarm_sign_flip.csv`. Nothing here reads it and the figures plot
  coordinates; an address is more than a reproduction needs. The alarm label
  text (`msg`) is kept, because Section 5 analyses it.
* The earlier AMap street raster behind Fig. 2(a). AMap tiles may not be
  redistributed, so the panel was redrawn from OpenStreetMap. What ships instead
  is `outputs/figdata/basemap_osm.csv`, a vector extract of roads, buildings,
  green space and water, with its attribution printed inside the map.
  `code/fetch_basemap_osm.py` regenerates it; the extract as shipped is a
  snapshot of the OpenStreetMap database taken on 2026-08-10.
* Model output and the `.docx` typesetting script: the paper reports no model
  number and the typesetting is not part of a reproduction.

## Licence and citation

Code (`code/`) is MIT — see `LICENSE`. Data (`outputs/`) is CC BY 4.0 — see
`outputs/LICENSE`. The licence covers the derived values, not the underlying
records. One file is not ours to license: `outputs/figdata/basemap_osm.csv` is
© OpenStreetMap contributors, ODbL 1.0, and is redistributed under that licence.
Machine-readable citation metadata is in `CITATION.cff`; cite the archived
version of record:

> Zheng, M., Jiang, S., Liu, C., and Zhang, K. (2026). *Derived tables and code
> for "Where in-sewer level records stop decides whether surcharge duration can
> be estimated"*, v1.0.0. Zenodo.
> https://doi.org/10.5281/zenodo.23683482

The badge above carries the concept DOI (`10.5281/zenodo.23683481`), which always
resolves to the newest version; the version DOI in the citation points at the
frozen v1.0.0 archive.

## Scope

One campus, thirteen instruments, twelve threshold configurations. The paper
supports a mechanism, not a frequency, and nothing here should be read as a
statement about other networks.
