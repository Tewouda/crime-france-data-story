# Fewer thefts, more reported violence

**A data story on recorded crime in France, 2016–2025, built with Streamlit.**

Between 2016 and 2025 the crime that French police and gendarmerie *record* changed shape. Property crime fell: burglary −19%, vehicle theft −26% and violent theft −49% (rates per 1,000). Over the same period recorded violence against people rose: sexual violence +148%, domestic physical violence +120%, and fraud +74%. Sexual violence, domestic violence and fraud rose in **all 101 départements**. This app walks through that divergence, shows where it happens, and asks how much of it could come from victims reporting more often.

---

## 1. Story at a glance

| | |
|---|---|
| **Audience** | Local decision-makers (prefectures, départements, city councils) planning prevention and victim-support budgets; journalists and citizens reading crime statistics. |
| **Questions** | Q1 *What* changed, and in which direction? · Q2 *Where*: is it the same everywhere? · Q3 *Who* stands out (rankings, outliers, size effects)? · Q4 *Why*: how much could be explained by more reporting? |
| **Narrative pattern** | Before/after change over time, then regional comparison (map and small multiples), then rankings and distribution, then a what-if scenario. |
| **Key takeaways** | (1) Property crime is down and recorded violence against persons is up (+84% in counts). (2) The largest rises are in historically under-reported offences, and they accelerate after #MeToo (2017) and the Grenelle on domestic violence (2019). (3) The rise is nationwide, not only urban. (4) A doubling of the reporting rate would explain most of the rise in sexual violence, but not all of it. Only victimisation surveys can separate the two effects. |

The app is a single scrolling page with 6 chapters, linked from the sidebar:

1. **Why it matters**: hook, audience, questions, and the caveat that recorded crime is not the same as actual crime
2. **The big picture**: KPI header, family index chart (2016 = 100), change by indicator
3. **Where and who**: choropleth map (rate or change), regional small multiples, top/bottom N, distribution, size effect and outliers, département drill-down
4. **What if reporting changed?**: scenario sliders based on documented assumptions
5. **Data quality**: 10 automated checks, missingness, sparsity, cleaning steps, limitations, downloads
6. **Takeaways**: insights, implications, next steps, ethics

The full storyboard is in [`docs/storyboard.md`](docs/storyboard.md). The demo-video script is in [`docs/demo_video_script.md`](docs/demo_video_script.md).

---

## 2. Data

| | |
|---|---|
| **Dataset** | *Bases statistiques communale, départementale et régionale de la délinquance enregistrée par la police et la gendarmerie nationales*, **départemental file (DEP)** |
| **Producer** | SSMSI, the statistical service of the French Ministry of the Interior |
| **Portal** | data.gouv.fr: <https://www.data.gouv.fr/datasets/bases-statistiques-communale-departementale-et-regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales> |
| **Pinned file** | `donnee-dep-data.gouv-2025-geographie2026-produit-le2026-06-25.csv` (July 2026 release), SHA-256 `05fd70cb…22b1` |
| **Licence** | Licence Ouverte / Open Licence v2.0 (Etalab), which allows reuse with attribution |
| **Size** | 18,180 rows × 11 columns (2 MB): 101 départements × 10 years (2016–2025) × 18 indicators |
| **Boundaries** | `departements-avec-outre-mer.geojson` from [france-geojson](https://github.com/gregoiredavid/france-geojson) (IGN/INSEE derived, Licence Ouverte) |
| **Documentation** | Official methodology PDF in `data/raw/ssmsi_documentation_juillet2026.pdf` |

All links and checksums are listed in [`DATA_SOURCES.md`](DATA_SOURCES.md).

**Data dictionary (raw → clean)**

| Raw column | Clean column | Meaning |
|---|---|---|
| `Code_departement` | `dep_code` | INSEE département code (text: `01`, `2A`, `971`) |
| `Code_region` | `region_code` → `region_name` | INSEE region code (2016 regions) |
| `annee` | `year` | Year in which the offence was **recorded** |
| `indicateur` | `indicator_fr` → `indicator`, `family` | One of 18 indicators, translated and grouped into 5 families |
| `unite_de_compte` | `unit` | Counting unit: victims, offences, vehicles, persons charged |
| `nombre` | `count` | Number recorded (place of commission; place of residence for fraud) |
| `taux_pour_mille` | `rate_published` | Published rate per 1,000 inhabitants (per 1,000 dwellings for burglary) |
| `insee_pop`, `insee_log` | `population`, `dwellings` → `denominator` | Census population and dwellings used as denominator |
| `*_millesime` | `pop_vintage`, `dwellings_vintage` | Census year of the denominator |
| (derived) | `rate` | Recomputed rate = count / denominator × 1,000 |

---

## 3. Quick start

Requires Python 3.12 or later.

```bash
# 1. install pinned dependencies (a virtual environment is recommended)
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. (optional) download / verify the data; the app also does this on first run
python scripts/download_data.py

# 3. (optional) run the cleaning and validation pipeline headlessly
python scripts/validate_data.py

# 4. launch the app on http://localhost:8501
streamlit run app.py
```

With `make`: `make install`, `make data`, `make validate`, `make run`.

The raw files are included in `data/raw/` so the app works offline. If they are deleted, `utils/io.fetch_and_cache()` downloads them again from the pinned URLs and refuses any file whose SHA-256 differs.

### Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repository.
2. On <https://share.streamlit.io>, choose **New app**, select the repo and branch, and set the main file to `app.py`.
3. Under *Advanced settings*, choose Python 3.12. `requirements.txt` is picked up automatically.

---

## 4. Project structure

```
app.py                     # entry point: page config, cached loading, sidebar filters, story order
sections/
  intro.py                 # Ch.1 hook, audience, questions, caveats
  overview.py              # Ch.2 KPIs, family index, change by indicator
  deep_dives.py            # Ch.3 map, small multiples, rankings, distribution, outliers, drill-down
  whatif.py                # Ch.4 reporting-rate scenario
  data_quality.py          # Ch.5 validation checks, missingness, sparsity, downloads
  conclusions.py           # Ch.6 insights, implications, next steps, ethics
utils/
  constants.py             # sources + checksums, labels, families, colours, assumptions
  io.py                    # fetch_and_cache(), load_data(), load_geojson(), licence text
  prep.py                  # cleaning, validation checks, feature engineering, aggregations
  viz.py                   # all Plotly charts, shared template, alt-text helper
scripts/
  download_data.py         # download + checksum verification
  validate_data.py         # headless pipeline: checks + processed parquet export
data/raw/                  # pinned source files (CSV, GeoJSON, methodology PDF)
data/processed/            # generated parquet (not required to run the app)
docs/                      # storyboard and demo-video script
.streamlit/config.toml     # theme (accessible light palette)
requirements.txt, Makefile, runtime.txt
```

---

## 5. Methods

### Cleaning
- Parse the CSV with `;` separator, decimal comma and BOM-safe UTF-8. Codes are kept as text so `01`, `2A`/`2B` and `971` survive.
- Rename columns to English snake_case. Translate the 18 indicators and map them to 5 families: *Violence against persons*, *Violent theft*, *Property crime*, *Drug offences*, *Fraud*.
- Join département names from the boundary file (with fixed names for the 5 overseas départements) and region names from INSEE codes.

### Validation (`utils/prep.quality_checks`, shown in the app)
| Check | Result |
|---|---|
| Missing values | 0 / 199,980 cells |
| Exact duplicate rows | 0 |
| Unique key département × year × indicator | 0 duplicates |
| Balanced panel | 18,180 = 101 × 10 × 18 |
| Valid ranges (counts ≥ 0, denominators > 0) | OK |
| Rate recomputation vs published rate | max abs. diff 8.2e-05 per 1,000 |
| Sub-indicator consistency (drug use = fixed fines + other) | exact |
| Map join | 101 / 101 départements matched |
| Population vintage | **Warning**: 2024–2025 use the 2023 census and Mayotte uses 2017 throughout |
| Sparse cells | 0.4% zeros (homicides mostly) |

### Feature engineering
- **Rates are never averaged.** Every aggregate (region, national, filtered selection) sums counts and denominators, then divides.
- Family index: summed counts, base year = 100. Drug-use sub-indicators are excluded to avoid double counting.
- Per département: % change in rate, **OLS trend** (% of period mean per year), **ratio to the selection average**, and a **robust z-score** of log-rates (median/MAD). Outlier means |z| > 2.5.
- Size effect: least-squares fit of the rate on log10(population), with Pearson r reported.

### What-if assumptions (chapter 4)
- Identity: `recorded = actual victims × reporting rate`, so `(1 + recorded change) = (1 + actual change) × (1 + reporting change)`.
- The reporting change is **chosen by the user**; the data cannot identify it.
- Baseline reporting rates come from the *Cadre de vie et sécurité* survey (2011–2018 average), as quoted in the SSMSI methodology: **12%** for sexual violence outside the household and **74%** for burglary. They are used only as an order-of-magnitude illustration.

---

## 6. Limitations & ethics

- **Recorded ≠ committed.** The figures depend on reporting propensity and, for drug offences, on police activity. Fixed fines for drug use (AFD) began in Sept. 2020.
- **Year of recording ≠ year of the facts.** Old sexual-violence cases recorded late inflate recent years.
- **Definition change.** Physical violence was redefined in July 2025 (domestic / non-domestic, including minors) and back-cast by SSMSI to 2016.
- **Fraud** is counted at the victim's place of residence; the other indicators use the place of the offence.
- **Denominators.** Resident population does not capture visitors, which inflates rates in Paris and tourist areas. 2024–2025 rates use the 2023 population. Mayotte's population is uncertain.
- **Small numbers.** Homicides and attempted homicides are rare at département level, so their % changes are noisy.
- **Privacy.** All data are aggregates; the smallest unit has about 76,000 inhabitants (Lozère), so there is no re-identification risk.
- **No causal claims.** Events (#MeToo, Grenelle, COVID-19) are context annotations, not explanations.

---

## 7. Accessibility, UX and performance

- Every chart is followed by a **text description** (alt text). Axes carry units, and every mark has a hover tooltip.
- **Validated colour palette** (blue / orange / aqua / yellow / magenta). Diverging scales run blue (decrease), grey (stable), red (increase). Colour is never the only cue: values are printed on bars, and the line chart is labelled directly.
- The light theme is set in `.streamlit/config.toml` with high-contrast text.
- `@st.cache_data` is used for loading, cleaning and validation and for each filter scope. `@st.cache_resource` holds the boundary file, which is simplified (3.7 MB → under 1 MB) and has its overseas départements repositioned as insets.
- All controls live in the sidebar except the map toggle, Top-N slider, drill-down selector and what-if sliders, which sit next to the chart they drive.

---

## 8. Credits

- Data © SSMSI / Ministère de l'Intérieur, Licence Ouverte 2.0. Boundaries © IGN/INSEE via france-geojson, Licence Ouverte.
- Code: MIT licence.
- Built with Streamlit, pandas, NumPy and Plotly.
