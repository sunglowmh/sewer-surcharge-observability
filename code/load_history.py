# -*- coding: utf-8 -*-
"""加载同济校园超声波/地埋式设备完整历史记录（2025-06 起），统一为长表。

用法：from load_history import load_all
"""
import os
import re
import zipfile
import datetime as dt
import pandas as pd

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "同济校园")
SONIC = os.path.join(BASE, "超声波设备")
BURIED = os.path.join(BASE, "地埋式设备")

if not os.path.isdir(BASE):
    # In the published repository this loader is shipped so that the scripts
    # that import it can be read, but the archive it reads stays with the
    # operator.  Say that here rather than failing later with a bare
    # FileNotFoundError from somewhere inside pandas.
    raise FileNotFoundError(
        "load_history: the raw level archive (%s) is not part of this "
        "reproducibility repository; see the Data availability statement of "
        "the paper. The derived tables the figures need are in outputs/."
        % BASE)


def read_xlsx(p):
    z = zipfile.ZipFile(p)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        s = z.read("xl/sharedStrings.xml").decode("utf8", "ignore")
        ss = ["".join(re.findall(r"<t[^>]*>(.*?)</t>", x, re.S)) for x in re.findall(r"<si>(.*?)</si>", s, re.S)]
    out = []
    for sn in [n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]:
        sh = z.read(sn).decode("utf8", "ignore")
        for r in re.findall(r"<row[^>]*>(.*?)</row>", sh, re.S):
            cells = {}
            for attr, body in re.findall(r"<c([^>]*)>(.*?)</c>", r, re.S):
                m = re.search(r'r="([A-Z]+)(\d+)"', attr)
                if not m:
                    continue
                v = re.findall(r"<v>(.*?)</v>", body)
                t = re.findall(r"<is>.*?<t[^>]*>(.*?)</t>", body, re.S)
                if t:
                    cells[m.group(1)] = t[0]
                elif v:
                    val = v[0]
                    cells[m.group(1)] = ss[int(val)] if 't="s"' in attr and ss and int(val) < len(ss) else val
            if cells:
                out.append(cells)
    return out


def _num(x):
    try:
        f = float(x)
        return f if f == f and abs(f) < 1e9 else None
    except Exception:
        return None


def _dt(x):
    if not x:
        return None
    s = str(x).strip()
    for fm in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return dt.datetime.strptime(s, fm)
        except Exception:
            pass
    return None


def _load_dir(d, kind):
    frames = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".xlsx") or "报警" in f or "参数" in f:
            continue
        rows = read_xlsx(os.path.join(d, f))
        if not rows:
            continue
        hdr = rows[0]
        inv = {k: v for k, v in hdr.items()}
        cols = {v: k for k, v in inv.items()}
        recs = []
        for r in rows[1:]:
            t = _dt(r.get(cols.get("更新时间", "B")))
            dev = r.get(cols.get("设备编号", "D"))
            if not t or not dev:
                continue
            rec = {
                "kind": kind,
                "file": f,
                "dev": dev,
                "name": r.get(cols.get("设备名称", "C"), ""),
                "t": t,
                "well": _num(r.get(cols.get("井下水深(m)", ""))),
                "burial": _num(r.get(cols.get("水位埋深(米)", ""))),
                "surf_mm": _num(r.get(cols.get("路面水深(毫米)", ""))),
                "cover": (r.get(cols.get("井盖状态", "")) or "").strip(),
                "soc": _num(r.get(cols.get("信号强度", ""))),
                "bat": _num(r.get(cols.get("电压(V)", ""))),
            }
            recs.append(rec)
        if recs:
            frames.append(pd.DataFrame(recs))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["dev", "t"]).sort_values(["dev", "t"])
    return df


def load_all():
    a = _load_dir(SONIC, "sonic")
    b = _load_dir(BURIED, "buried")
    return a, b


def load_alarms():
    out = []
    for d in (SONIC, BURIED):
        for f in os.listdir(d):
            if "报警" in f and f.endswith(".xlsx"):
                rows = read_xlsx(os.path.join(d, f))
                if not rows:
                    continue
                hdr = {v: k for k, v in rows[0].items()}
                for r in rows[1:]:
                    out.append({
                        "dev": r.get(hdr.get("设备编号", ""), ""),
                        "name": r.get(hdr.get("设备名称", ""), ""),
                        "type": r.get(hdr.get("报警类型", ""), ""),
                        "t": _dt(r.get(hdr.get("报警时间", ""), "")),
                        "msg": r.get(hdr.get("报警信息", ""), ""),
                    })
    return pd.DataFrame(out)


if __name__ == "__main__":
    a, b = load_all()
    print("sonic", a.shape, a.t.min(), a.t.max())
    print("buried", b.shape, b.t.min(), b.t.max())
    print(a.head(3).to_string())
    print(b.head(3).to_string())
