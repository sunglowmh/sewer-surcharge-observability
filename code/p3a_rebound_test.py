# -*- coding: utf-8 -*-
"""The rebound test: does the record come back as soon as the surface leaves the window?

`p3a_precip_lock_blocks.csv` locates eighteen blind blocks (maximal runs of readings at
the 0.25 m write-back).  The onset test in the manuscript asks only when a block starts.
This asks when it ends, and at what depth.

Why it discriminates.  The write-back value itself cannot: every mechanism that silences
an echo writes the same 0.25 m.  But the *return* is a measurement, not a write-back.  If
the echo fails because the surface sits inside the near field, the block must end the
moment the surface drops below 0.26 m, so the first readable value has to sit just above
the edge.  A block that ends for an independent reason (face dries, fouling clears, probe
resets) ends whenever that reason expires, at whatever depth the surface then holds.

Reported: for each block, the gap to the next reading, that reading's `burial`, and the
share of all readable readings that fall in the same band, which is the crude null.

  python .workbuddy/tools/p3a_rebound_test.py
  -> outputs/p3a_rebound_blocks.csv
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_history import load_all  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDGE = 0.26
BAND = (0.26, 0.35)
HORIZON_H = 6


def main():
    sonic, _ = load_all()
    s = sonic.dropna(subset=["burial"]).sort_values(["dev", "t"])

    blocks = pd.read_csv(os.path.join(ROOT, "outputs", "p3a_precip_lock_blocks.csv"),
                         encoding="utf-8-sig")
    blocks["t_start"] = pd.to_datetime(blocks["t_start"])
    blocks["t_end"] = pd.to_datetime(blocks["t_end"])

    rows = []
    for i, b in blocks.iterrows():
        after = s[(s.dev == str(b.dev)) & (s.t > b.t_end)].sort_values("t")
        nxt = after.iloc[0] if len(after) else None
        within = after[after.t <= b.t_end + pd.Timedelta(hours=HORIZON_H)]
        first_read = within[within.burial >= EDGE]
        rows.append(dict(
            block=i + 1,
            dev=str(b.dev),
            name=b["name"],
            event=b["event"],
            phase=b["phase"],
            t_end=b.t_end,
            gap_h=round((nxt.t - b.t_end).total_seconds() / 3600, 2) if nxt is not None else np.nan,
            next_burial=round(nxt.burial, 3) if nxt is not None else np.nan,
            first_readable=round(first_read.iloc[0].burial, 3) if len(first_read) else np.nan,
            # the band test runs on the next reading at whatever cadence the instrument
            # keeps; the six-hour column above is reported alongside because a daily
            # instrument's next reading is a day late, not a different quantity
            in_band=bool(nxt is not None and BAND[0] <= nxt.burial <= BAND[1]),
        ))

    out = pd.DataFrame(rows)
    path = os.path.join(ROOT, "outputs", "p3a_rebound_blocks.csv")
    out.to_csv(path, index=False, encoding="utf-8-sig")

    readable = s[s.burial >= EDGE]
    share_band = float(((readable.burial >= BAND[0]) & (readable.burial <= BAND[1])).mean())

    got = out.dropna(subset=["next_burial"])
    fast = got[got.gap_h <= HORIZON_H]
    print("blocks %d | with a following reading %d (%d of them within %d h)"
          % (len(out), len(got), len(fast), HORIZON_H))
    print("next value in [%.2f, %.2f]: %d of %d  (%d of %d within %d h)"
          % (BAND[0], BAND[1], got.in_band.sum(), len(got),
             fast.in_band.sum(), len(fast), HORIZON_H))
    print("null: %.2f%% of the %d readable readings sit in that band"
          % (100 * share_band, len(readable)))
    print("median next value %.3f m | overall median readable %.3f m"
          % (got.next_burial.median(), readable.burial.median()))
    print("wrote %s" % path)
    return out


if __name__ == "__main__":
    main()
