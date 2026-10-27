# outputs/

Derived tables. Nothing here is a raw record.

* `tables/` — machine-readable versions of Tables 1-3, and `table2_roworder.csv`,
  the single source of the row order used by Tables 2 and 3 and by Fig. 7.
* `figdata/` — the exact inputs of Figs. 2, 3, 5, 6 and 8. Two of them are short
  level extracts (`fig3_block.csv`, `fig5_trace.csv`), plotted as they are.
* `p3a_*.csv` — the quantities the text quotes: `Omega` per configuration, the
  criterion depth, the blindness classification against the rainfall record, the
  duration ratios of Table 3, and the onset-lag and dose matrices.
* `p3a_alarm_sign_flip.csv` — the 305 alarm records behind Fig. 8: the alarm
  time, the current value, the threshold, and the label the platform assigned.
  The label text is analysed in Section 5 (result R8), so it is published; the
  platform's street address for each instrument (`loc`) is not, and is dropped.
* `figdata/basemap_osm.csv` — the vector extract behind Fig. 2(a): roads,
  buildings, green space and water as coordinate sequences, one row per vertex.
  It is © OpenStreetMap contributors, ODbL 1.0, and is the only file here that
  is not ours to license; `figdata/basemap_campus.txt` is the four-number frame
  it was cut to.
* `p3a_J_registry.csv`, `p3a_J_verdict.csv`, `p3a_J_alarm_check.csv` — the
  reconstruction of the well depth `J` and its step dates (Section 4.5).

`SHA256SUMS` and `MANIFEST.csv` in the repository root cover every file here.
Licence: CC BY 4.0 (see `LICENSE` in this directory), except
`figdata/basemap_osm.csv`, which is ODbL 1.0.
