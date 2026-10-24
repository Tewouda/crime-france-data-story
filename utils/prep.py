"""Cleaning, validation and feature engineering.

All functions are pure (DataFrame in -> DataFrame out) so they can be cached by
Streamlit and unit-tested from the command line (see scripts/validate_data.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from utils.constants import INDICATORS, OVERSEAS_REGIONS, PER_DWELLING, REGIONS

KEY = ["dep_code", "year", "indicator"]
RAW_COLUMNS = [
    "Code_departement", "Code_region", "annee", "indicateur", "unite_de_compte", "nombre",
    "taux_pour_mille", "insee_pop", "insee_pop_millesime", "insee_log", "insee_log_millesime",
]

# Overseas départements are absent from some geo sources; names are fixed here.
OVERSEAS_NAMES = {"971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion", "976": "Mayotte"}


# --------------------------------------------------------------------------- #
# Cleaning
# --------------------------------------------------------------------------- #
def clean(raw: pd.DataFrame, dep_names: dict[str, str]) -> pd.DataFrame:
    """Rename to English snake_case, add labels/families, recompute rates."""
    missing_cols = set(RAW_COLUMNS) - set(raw.columns)
    if missing_cols:
        raise ValueError(f"Unexpected schema, missing columns: {sorted(missing_cols)}")

    df = raw.rename(
        columns={
            "Code_departement": "dep_code", "Code_region": "region_code", "annee": "year",
            "indicateur": "indicator_fr", "unite_de_compte": "unit_fr", "nombre": "count",
            "taux_pour_mille": "rate_published", "insee_pop": "population",
            "insee_pop_millesime": "pop_vintage", "insee_log": "dwellings",
            "insee_log_millesime": "dwellings_vintage",
        }
    ).copy()

    df["dep_code"] = df["dep_code"].str.strip().str.upper().str.zfill(2)
    df["region_code"] = df["region_code"].str.strip().str.zfill(2)
    df["indicator_fr"] = df["indicator_fr"].str.strip()

    meta = pd.DataFrame.from_dict(
        INDICATORS, orient="index", columns=["indicator", "family", "unit", "is_sub"]
    )
    unknown = set(df["indicator_fr"]) - set(meta.index)
    if unknown:
        raise ValueError(f"Unknown indicators (update utils/constants.py): {sorted(unknown)}")
    df = df.join(meta, on="indicator_fr")

    names = {**dep_names, **OVERSEAS_NAMES}
    df["dep_name"] = df["dep_code"].map(names).fillna(df["dep_code"])
    df["region_name"] = df["region_code"].map(REGIONS)
    df["overseas"] = df["region_code"].isin(OVERSEAS_REGIONS)

    # Feature: the denominator actually used by SSMSI for the rate
    df["per_dwelling"] = df["indicator"].isin(PER_DWELLING)
    df["denominator"] = np.where(df["per_dwelling"], df["dwellings"], df["population"])
    df["rate"] = df["count"] / df["denominator"] * 1000

    ordered = [
        "dep_code", "dep_name", "region_code", "region_name", "overseas", "year",
        "indicator", "indicator_fr", "family", "unit", "is_sub", "count", "rate",
        "rate_published", "population", "pop_vintage", "dwellings", "dwellings_vintage",
        "denominator", "per_dwelling",
    ]
    return df[ordered].sort_values(KEY).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def quality_checks(raw: pd.DataFrame, df: pd.DataFrame, geo_codes: set[str]) -> pd.DataFrame:
    """Return one row per validation check: name, status, result, detail."""
    rows = []

    def add(name, ok, result, detail, warn=False):
        status = "Pass" if ok else ("Warning" if warn else "Fail")
        rows.append({"Check": name, "Status": status, "Result": result, "Why it matters": detail})

    n_missing = int(raw.isna().sum().sum())
    add("Missing values", n_missing == 0, f"{n_missing} missing cells out of {raw.size:,}",
        "Any gap would bias totals and rates.")

    n_dup_rows = int(raw.duplicated().sum())
    add("Duplicate rows", n_dup_rows == 0, f"{n_dup_rows} exact duplicates",
        "Duplicates would double-count offences.")

    n_dup_keys = int(df.duplicated(KEY).sum())
    add("Unique key (département × year × indicator)", n_dup_keys == 0,
        f"{n_dup_keys} duplicated keys", "Guarantees one value per cell of the panel.")

    n_dep, n_year, n_ind = df["dep_code"].nunique(), df["year"].nunique(), df["indicator"].nunique()
    expected = n_dep * n_year * n_ind
    add("Balanced panel", len(df) == expected,
        f"{len(df):,} rows = {n_dep} départements × {n_year} years × {n_ind} indicators",
        "No département/year silently missing from comparisons.")

    n_neg = int((df["count"] < 0).sum() + (df["denominator"] <= 0).sum())
    add("Valid ranges", n_neg == 0, f"{n_neg} negative counts or non-positive denominators",
        "Counts must be ≥ 0 and populations > 0.")

    diff = (df["rate"] - df["rate_published"]).abs()
    add("Rate recomputation", diff.max() < 1e-3,
        f"max |recomputed − published| = {diff.max():.1e} per 1,000",
        "Confirms we understood the denominators (population, or dwellings for burglary).")

    use = df[df["indicator_fr"] == "Usage de stupéfiants"].set_index(["dep_code", "year"])["count"]
    afd = df[df["indicator_fr"] == "Usage de stupéfiants (AFD)"].set_index(["dep_code", "year"])["count"]
    hors = df[df["indicator_fr"] == "Usage de stupéfiants (hors AFD)"].set_index(["dep_code", "year"])["count"]
    gap = int((use - afd - hors).abs().max())
    add("Sub-indicator consistency", gap == 0, f"Drug use = fixed fines + other, max gap {gap}",
        "Sub-indicators are excluded from totals to avoid double counting.")

    data_codes = set(df["dep_code"])
    unmatched = sorted(data_codes - geo_codes)
    add("Map join (data ↔ boundaries)", not unmatched,
        f"{len(data_codes) - len(unmatched)}/{len(data_codes)} départements matched"
        + (f"; unmatched: {', '.join(unmatched)}" if unmatched else ""),
        "Every département must appear on the map.")

    stale = df.loc[df["pop_vintage"] < df["year"] - 2, "dep_name"].unique()
    add("Population vintage", len(stale) == 0,
        f"2024–2025 rates use 2023 census population; stale vintage for: {', '.join(stale) or 'none'}",
        "Rates for recent years / Mayotte use an older population, so they are approximate.",
        warn=True)

    zero_share = (df.loc[~df["is_sub"], "count"] == 0).mean()
    add("Sparse cells", zero_share < 0.05, f"{zero_share:.1%} of main-indicator cells are zero",
        "Rare events (homicides) are volatile at département level.", warn=True)

    return pd.DataFrame(rows)


def missingness_table(raw: pd.DataFrame) -> pd.DataFrame:
    return (
        raw.isna().mean().mul(100).rename("missing_pct").rename_axis("column").reset_index()
    )


# --------------------------------------------------------------------------- #
# Feature engineering & aggregation
# --------------------------------------------------------------------------- #
def filter_scope(df: pd.DataFrame, regions: tuple[str, ...], include_overseas: bool) -> pd.DataFrame:
    out = df
    if regions:
        out = out[out["region_name"].isin(regions)]
    if not include_overseas:
        out = out[~out["overseas"]]
    return out


def aggregate_series(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Sum counts and denominators, then recompute the rate (never average rates)."""
    g = df.groupby(by, as_index=False, observed=True).agg(
        count=("count", "sum"), denominator=("denominator", "sum")
    )
    g["rate"] = g["count"] / g["denominator"] * 1000
    return g


def national_series(df: pd.DataFrame) -> pd.DataFrame:
    return aggregate_series(df, ["indicator", "family", "is_sub", "year"])


def family_index(df: pd.DataFrame, base_year: int) -> pd.DataFrame:
    """Index (base year = 100) of summed counts per family, main indicators only."""
    fam = df[~df["is_sub"]].groupby(["family", "year"], as_index=False)["count"].sum()
    base = fam[fam["year"] == base_year].set_index("family")["count"]
    fam["index"] = fam["count"] / fam["family"].map(base) * 100
    return fam


def change_table(nat: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    """Percentage change in rate between y0 and y1 for every main indicator."""
    main = nat[~nat["is_sub"]]
    p = main.pivot_table(index=["indicator", "family"], columns="year", values=["rate", "count"])
    out = pd.DataFrame(
        {
            "rate_start": p[("rate", y0)],
            "rate_end": p[("rate", y1)],
            "count_start": p[("count", y0)],
            "count_end": p[("count", y1)],
        }
    ).reset_index()
    out["pct_change"] = (out["rate_end"] / out["rate_start"] - 1) * 100
    out.loc[out["count_start"] == 0, "pct_change"] = np.nan
    return out.sort_values("pct_change")


def dept_snapshot(df: pd.DataFrame, indicator: str, y0: int, y1: int) -> pd.DataFrame:
    """One row per département for `indicator`: level, change, trend, outlier flag."""
    d = df[(df["indicator"] == indicator) & df["year"].between(y0, y1)]
    wide = d.pivot_table(index=["dep_code", "dep_name", "region_name", "overseas"],
                         columns="year", values=["rate", "count"])
    snap = pd.DataFrame(
        {
            "rate_start": wide[("rate", y0)],
            "rate_end": wide[("rate", y1)],
            "count_start": wide[("count", y0)],
            "count_end": wide[("count", y1)],
        }
    ).reset_index()
    snap["pct_change"] = (snap["rate_end"] / snap["rate_start"] - 1) * 100
    snap.loc[snap["rate_start"] == 0, "pct_change"] = np.nan

    # Linear trend (OLS on all years in range), expressed as % of the period mean per year
    years = np.arange(y0, y1 + 1)
    rates = wide["rate"][list(years)].to_numpy()
    if len(years) >= 3:
        slope = np.polyfit(years, rates.T, 1)[0]
        snap["trend_pct_per_year"] = slope / rates.mean(axis=1) * 100
    else:
        snap["trend_pct_per_year"] = np.nan

    total = d[d["year"] == y1]
    nat_rate = total["count"].sum() / total["denominator"].sum() * 1000
    snap["ratio_to_scope"] = snap["rate_end"] / nat_rate
    # Robust z-score on log rates (rates are right-skewed)
    lr = np.log(snap["rate_end"].where(snap["rate_end"] > 0))
    mad = (lr - lr.median()).abs().median() * 1.4826
    snap["robust_z"] = (lr - lr.median()) / mad if mad else 0.0
    snap["outlier"] = snap["robust_z"].abs() > 2.5
    snap["population"] = (
        df[(df["year"] == y1) & (df["indicator"] == indicator)].set_index("dep_code")["population"]
        .reindex(snap["dep_code"]).to_numpy()
    )
    return snap


def dept_profile(df: pd.DataFrame, dep_code: str, year: int, scope_nat: pd.DataFrame) -> pd.DataFrame:
    """Ratio of a département's rate to the scope average, for every main indicator."""
    d = df[(df["dep_code"] == dep_code) & (df["year"] == year) & ~df["is_sub"]][
        ["indicator", "family", "rate", "count"]
    ]
    n = scope_nat[(scope_nat["year"] == year)][["indicator", "rate"]].rename(columns={"rate": "ref_rate"})
    out = d.merge(n, on="indicator")
    out["ratio"] = out["rate"] / out["ref_rate"]
    return out.sort_values("ratio")


def scatter_fit(x: pd.Series, y: pd.Series) -> dict:
    """Least-squares fit of y on log10(x); returns slope, intercept and Pearson r."""
    mask = (x > 0) & y.notna()
    lx, yy = np.log10(x[mask]), y[mask]
    slope, intercept = np.polyfit(lx, yy, 1)
    r = float(np.corrcoef(lx, yy)[0, 1])
    return {"slope": float(slope), "intercept": float(intercept), "r": r, "n": int(mask.sum())}
