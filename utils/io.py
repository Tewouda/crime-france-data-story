"""Data ingestion: download with caching + checksum verification, then load."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import requests

from utils.constants import (
    DATASET_LICENSE,
    DATASET_LICENSE_URL,
    DATASET_PAGE,
    DATASET_PRODUCER,
    DATASET_TITLE,
    DATASET_VERSION,
    SOURCES,
)

LICENSE_TEXT = (
    f"Data: “{DATASET_TITLE}”, {DATASET_PRODUCER}, {DATASET_VERSION}. "
    f"Published on data.gouv.fr ({DATASET_PAGE}) under the {DATASET_LICENSE} "
    f"({DATASET_LICENSE_URL}). Département boundaries: france-geojson (G. David), "
    "derived from IGN/INSEE open data, Licence Ouverte. Code: MIT licence."
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_and_cache(key: str, force: bool = False, timeout: int = 120) -> Path:
    """Return the local path of source `key`, downloading it only if missing.

    The pinned checksum guarantees that everybody runs the analysis on exactly
    the same bytes; a mismatch is reported instead of silently accepted.
    """
    src = SOURCES[key]
    path: Path = src["path"]
    if path.exists() and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(src["url"], timeout=timeout)
    resp.raise_for_status()
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(resp.content)
    digest = sha256(tmp)
    if digest != src["sha256"]:
        tmp.unlink()
        raise ValueError(
            f"Checksum mismatch for {key}: expected {src['sha256']}, got {digest}. "
            "The upstream file has changed; update SOURCES in utils/constants.py deliberately."
        )
    tmp.replace(path)
    return path


def load_data() -> pd.DataFrame:
    """Load the raw départemental CSV exactly as published (French decimals, ';')."""
    path = fetch_and_cache("crime_dep")
    return pd.read_csv(
        path,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        dtype={"Code_departement": str, "Code_region": str},
    )


def _simplify_ring(ring: list, ndigits: int = 2) -> list:
    """Round coordinates (~1 km, invisible at national scale) and drop consecutive duplicates.

    Shrinks the boundary payload sent to the browser from 3.7 MB to under 1 MB.
    """
    out = []
    for x, y in ring:
        pt = [round(x, ndigits), round(y, ndigits)]
        if not out or out[-1] != pt:
            out.append(pt)
    if out and out[0] != out[-1]:
        out.append(out[0])
    return out


def _signed_area(ring: list) -> float:
    """Shoelace formula on lon/lat; > 0 means counter-clockwise."""
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:])) / 2


def _rewind(poly: list) -> list:
    """Plotly's d3-geo expects clockwise exterior rings and counter-clockwise holes;
    with the opposite winding a département is drawn as 'the whole globe minus it'."""
    out = []
    for i, ring in enumerate(poly):
        ccw = _signed_area(ring) > 0
        out.append(ring[::-1] if (ccw if i == 0 else not ccw) else ring)
    return out


# Inset boxes (lon_min, lat_min, size in degrees) west of mainland France for overseas
# départements, so the map stays zoomed on France. Insets are NOT to scale.
OVERSEAS_INSETS = {
    "971": (-9.0, 47.0, 1.4),  # Guadeloupe
    "972": (-9.0, 45.4, 1.4),  # Martinique
    "973": (-9.0, 43.6, 1.6),  # Guyane
    "974": (-9.0, 42.0, 1.4),  # La Réunion
    "976": (-9.0, 40.4, 1.4),  # Mayotte
}


def _inset(polys: list, box: tuple[float, float, float]) -> list:
    pts = [p for poly in polys for ring in poly for p in ring]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    bx, by, size = box
    k = size / max(x1 - x0, y1 - y0)
    return [[[[round(bx + (x - x0) * k, 3), round(by + (y - y0) * k, 3)] for x, y in ring]
             for ring in poly] for poly in polys]


def load_geojson() -> dict:
    path = fetch_and_cache("geojson")
    geo = json.loads(Path(path).read_text(encoding="utf-8"))
    for feat in geo["features"]:
        g = feat["geometry"]
        code = feat["properties"]["code"]
        ndigits = 3 if code in OVERSEAS_INSETS else 2  # small islands are enlarged: keep detail
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        simplified = []
        for poly in polys:
            rings = [_simplify_ring(r, ndigits) for r in poly]
            if len(rings[0]) >= 4:  # drop islets that collapse to a point
                simplified.append(_rewind([r for r in rings if len(r) >= 4]))
        if code in OVERSEAS_INSETS:
            simplified = _inset(simplified, OVERSEAS_INSETS[code])
        g["type"], g["coordinates"] = "MultiPolygon", simplified
    return geo


def department_names(geo: dict) -> dict[str, str]:
    return {f["properties"]["code"]: f["properties"]["nom"] for f in geo["features"]}
