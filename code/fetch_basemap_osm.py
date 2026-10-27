# -*- coding: utf-8 -*-
"""Fetch the street/building/water layer for Fig. 2 (a) from OpenStreetMap.

The previous basemap was a raster tile mosaic from AMap: it could not be
redistributed, and the panel therefore had to be drawn without it in the
reproducibility repository.  This script replaces it with a vector extract of
the same footprint, which is ODbL and can ship.

Output: outputs/figdata/basemap_osm.csv, one row per vertex:

    cls,way_id,seq,lon,lat

`cls` is the drawing class (t1..t4 for roads, building, green, water, rail).
Coordinates are WGS-84, rounded to 1e-6 deg (about 0.1 m), which is two orders
of magnitude finer than the 10 m grid the analysis works on.

The extent is inherited from basemap_campus.txt, which is written on the GCJ-02
graticule (it framed an AMap mosaic).  It is converted to WGS-84 here, since
OSM is WGS-84.  Run with --print-only to see the query without fetching.
"""
import os
import sys
import csv
import json
import math
import urllib.parse
import urllib.request
import ssl

import certifi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "outputs", "figdata", "basemap_osm.csv")
EXT = os.path.join(ROOT, "outputs", "figdata", "basemap_campus.txt")

# overpass-api.de and most mirrors are unreachable from this machine (the
# tunnel returns 502 for the openstreetmap.org host family); the .fr instance
# answers and is worldwide.  overpass.osm.ch is kept as a fallback but serves
# Switzerland only, so it returns an empty extract for this bbox.
ENDPOINTS = ["https://overpass.openstreetmap.fr/api/interpreter",
             "https://overpass-api.de/api/interpreter"]
UA = "sewer-surcharge-observability/1.0 (Fig. 2 basemap; sunglowmh)"

_A = 6378245.0
_EE = 0.00669342162296594323
_X_PI = math.pi * 3000.0 / 180.0


def _tf_lat(x, y):
    r = (-100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y
         + 0.2 * math.sqrt(abs(x)))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    r += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return r


def _tf_lon(x, y):
    r = (300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y
         + 0.1 * math.sqrt(abs(x)))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    r += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return r


def wgs2gcj(lon, lat):
    dlat = _tf_lat(lon - 105.0, lat - 35.0)
    dlon = _tf_lon(lon - 105.0, lat - 35.0)
    rad = lat / 180.0 * math.pi
    magic = 1 - _EE * math.sin(rad) ** 2
    sq = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((_A * (1 - _EE)) / (magic * sq) * math.pi)
    dlon = (dlon * 180.0) / (_A / sq * math.cos(rad) * math.pi)
    return lon + dlon, lat + dlat


def gcj2wgs(lon, lat, n=6):
    """Inverse of wgs2gcj by fixed-point iteration (converges in 3 rounds)."""
    x, y = lon, lat
    for _ in range(n):
        gx, gy = wgs2gcj(x, y)
        x -= gx - lon
        y -= gy - lat
    return x, y


ROAD_TIER = {
    "motorway": "t1", "motorway_link": "t1", "trunk": "t1", "trunk_link": "t1",
    "primary": "t1", "primary_link": "t1",
    "secondary": "t2", "secondary_link": "t2",
    "tertiary": "t2", "tertiary_link": "t2",
    "unclassified": "t3", "residential": "t3", "living_street": "t3",
    "service": "t3", "road": "t3",
    "pedestrian": "t4", "footway": "t4", "path": "t4", "steps": "t4",
    "cycleway": "t4", "track": "t4", "corridor": "t4", "bridleway": "t4",
}
GREEN = {"grass", "forest", "meadow", "recreation_ground", "village_green",
         "cemetery", "orchard", "allotments"}
LEISURE = {"park", "pitch", "garden", "golf_course", "playground"}


def classify(tags):
    hw = tags.get("highway")
    if hw:
        return ROAD_TIER.get(hw, "t4")
    if tags.get("railway") in {"rail", "light_rail", "subway", "tram"}:
        return "rail"
    if tags.get("building"):
        return "building"
    if tags.get("natural") == "water" or tags.get("waterway") or tags.get("water"):
        return "water"
    if tags.get("landuse") in GREEN or tags.get("leisure") in LEISURE:
        return "green"
    return None


def query(bbox):
    s, w, n, e = bbox
    q = ("[out:json][timeout:120];"
         "(way[\"highway\"](%f,%f,%f,%f);"
         "way[\"railway\"](%f,%f,%f,%f);"
         "way[\"building\"](%f,%f,%f,%f);"
         "way[\"natural\"=\"water\"](%f,%f,%f,%f);"
         "way[\"waterway\"](%f,%f,%f,%f);"
         "way[\"landuse\"](%f,%f,%f,%f);"
         "way[\"leisure\"](%f,%f,%f,%f););out geom;"
         % ((s, w, n, e) * 7))
    return q


def fetch(q):
    ctx = ssl.create_default_context(cafile=certifi.where())
    last = None
    for url in ENDPOINTS:
        body = urllib.parse.urlencode({"data": q}).encode()
        req = urllib.request.Request(url, data=body, headers={"User-Agent": UA})
        try:
            r = urllib.request.urlopen(req, timeout=240, context=ctx)
            return json.loads(r.read().decode("utf-8"))
        except Exception as exc:                              # noqa: BLE001
            last = exc
            print("  %s failed: %s" % (url, exc))
    raise SystemExit("no endpoint answered: %s" % last)


def main():
    x0, x1, y0, y1 = [float(v) for v in open(EXT, encoding="utf-8").read().split()]
    sw = gcj2wgs(x0, y0)
    ne = gcj2wgs(x1, y1)
    bbox = (round(sw[1], 6), round(sw[0], 6), round(ne[1], 6), round(ne[0], 6))
    q = query(bbox)
    print("WGS-84 bbox  S=%.6f W=%.6f N=%.6f E=%.6f" % bbox)
    print("query %d chars" % len(q))
    if "--print-only" in sys.argv:
        print(q)
        return

    data = fetch(q)
    els = data.get("elements", [])
    print("elements: %d" % len(els))

    rows, per = [], {}
    for el in els:
        tags = el.get("tags", {})
        cls = classify(tags)
        if cls is None:
            continue
        g = el.get("geometry") or []
        if len(g) < 2:
            continue
        wid = el["id"]
        for k, pt in enumerate(g):
            rows.append((cls, wid, k, round(pt["lon"], 6), round(pt["lat"], 6)))
        per[cls] = per.get(cls, 0) + 1

    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["cls", "way_id", "seq", "lon", "lat"])
        w.writerows(rows)

    print("ways by class: " + ", ".join("%s %d" % kv for kv in sorted(per.items())))
    print("wrote %s (%d rows, %.1f kB)"
          % (OUT, len(rows), os.path.getsize(OUT) / 1024.0))
    print("attribution: © OpenStreetMap contributors, ODbL 1.0")


if __name__ == "__main__":
    main()
