"""Run the data pipeline without the UI: clean, validate, export a processed parquet.

Usage:  python scripts/validate_data.py
Exit code is non-zero if any validation check fails (warnings are allowed).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from utils.constants import PROCESSED_DIR  # noqa: E402
from utils.io import department_names, load_data, load_geojson  # noqa: E402
from utils.prep import change_table, clean, national_series, quality_checks  # noqa: E402

if __name__ == "__main__":
    geo = load_geojson()
    raw = load_data()
    df = clean(raw, department_names(geo))
    checks = quality_checks(raw, df, {f["properties"]["code"] for f in geo["features"]})
    pd.set_option("display.width", 200, "display.max_colwidth", 90)
    print(checks[["Check", "Status", "Result"]].to_string(index=False))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "crime_departements_clean.parquet"
    df.to_parquet(out, index=False)
    print(f"\nSaved {len(df):,} clean rows -> {out}")

    chg = change_table(national_series(df), 2016, 2025)
    print("\nNational change in rate 2016 -> 2025 (%):")
    print(chg[["indicator", "pct_change"]].round(1).to_string(index=False))
    sys.exit(int(checks["Status"].eq("Fail").any()))
