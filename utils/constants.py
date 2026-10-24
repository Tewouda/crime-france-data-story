"""Project-wide constants: data sources, labels, colours and documented assumptions.

Everything that could change the numbers shown in the app lives here, so the
analysis is deterministic and every assumption is reviewable in one place.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# --------------------------------------------------------------------------- #
# Data sources (pinned to the exact files used, with SHA-256 checksums)
# --------------------------------------------------------------------------- #
DATASET_TITLE = (
    "Bases statistiques communale, départementale et régionale de la délinquance "
    "enregistrée par la police et la gendarmerie nationales"
)
DATASET_PAGE = (
    "https://www.data.gouv.fr/datasets/bases-statistiques-communale-departementale-et-"
    "regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales"
)
DATASET_PRODUCER = "SSMSI – Ministère de l'Intérieur (statistical service for internal security)"
DATASET_LICENSE = "Licence Ouverte / Open Licence v2.0 (Etalab)"
DATASET_LICENSE_URL = "https://www.etalab.gouv.fr/licence-ouverte-open-licence/"
DATASET_VERSION = "July 2026 release (data 2016–2025, 2026 geography, produced 2026-06-25)"

_BASE = (
    "https://static.data.gouv.fr/resources/bases-statistiques-communale-departementale-et-"
    "regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales"
)
SOURCES = {
    "crime_dep": {
        "url": f"{_BASE}/20260709-120038/donnee-dep-data.gouv-2025-geographie2026-produit-le2026-06-25.csv",
        # Stable data.gouv.fr permalink (always points to the latest version of the resource)
        "permalink": "https://www.data.gouv.fr/fr/datasets/r/2b27a675-e3bf-41ef-a852-5fb9ab483967",
        "path": RAW_DIR / "dep.csv",
        "sha256": "05fd70cbfe72f694826a8431630aa798071ab1f653b61fafbfc90a816b0122b1",
    },
    "documentation": {
        "url": f"{_BASE}/20260709-120136/fichier-metadonnees-data-gouv-geographie-delinquance-juillet2026.pdf",
        "path": RAW_DIR / "ssmsi_documentation_juillet2026.pdf",
        "sha256": "b409750fa411754884b616bdfcb2a1e6c8b554d4693b9e590ccae01e61c29945",
    },
    "geojson": {
        # Département boundaries (IGN Admin Express derived, overseas départements
        # repositioned next to mainland France). Licence Ouverte.
        "url": "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-avec-outre-mer.geojson",
        "path": RAW_DIR / "departements.geojson",
        "sha256": "0c331e85eef244d8014f68a4c256bb732e28776aceec53ddf849624f2eb6c163",
    },
}

# --------------------------------------------------------------------------- #
# Indicators: French label -> (English label, family, unit, is_sub_indicator)
# --------------------------------------------------------------------------- #
INDICATORS = {
    "Homicides": ("Homicides", "Violence against persons", "victims", False),
    "Tentatives d'homicide": ("Attempted homicides", "Violence against persons", "victims", False),
    "Violences physiques intrafamiliales": ("Domestic physical violence", "Violence against persons", "victims", False),
    "Violences physiques hors cadre familial": ("Non-domestic physical violence", "Violence against persons", "victims", False),
    "Violences sexuelles": ("Sexual violence", "Violence against persons", "victims", False),
    "Vols avec armes": ("Armed robbery", "Violent theft", "offences", False),
    "Vols violents sans arme": ("Violent theft without weapon", "Violent theft", "offences", False),
    "Vols sans violence contre des personnes": ("Non-violent theft from persons", "Property crime", "victims heard", False),
    "Cambriolages de logement": ("Residential burglary", "Property crime", "offences", False),
    "Vols de véhicule": ("Vehicle theft", "Property crime", "vehicles", False),
    "Vols dans les véhicules": ("Theft from vehicles", "Property crime", "vehicles", False),
    "Vols d'accessoires sur véhicules": ("Theft of vehicle parts", "Property crime", "vehicles", False),
    "Destructions et dégradations volontaires": ("Criminal damage & vandalism", "Property crime", "offences", False),
    "Usage de stupéfiants": ("Drug use", "Drug offences", "suspects", False),
    "Usage de stupéfiants (AFD)": ("Drug use – fixed fines (AFD)", "Drug offences", "suspects", True),
    "Usage de stupéfiants (hors AFD)": ("Drug use – excl. fixed fines", "Drug offences", "suspects", True),
    "Trafic de stupéfiants": ("Drug trafficking", "Drug offences", "suspects", False),
    "Escroqueries et fraudes aux moyens de paiement": ("Fraud & payment fraud", "Fraud", "victims", False),
}
# Rates are per 1,000 dwellings for burglary, per 1,000 inhabitants otherwise (SSMSI convention)
PER_DWELLING = {"Residential burglary"}

FAMILIES = [
    "Violence against persons",
    "Violent theft",
    "Property crime",
    "Drug offences",
    "Fraud",
]
FAMILY_HELP = {
    "Violence against persons": "Homicides, attempted homicides, domestic and non-domestic physical violence, sexual violence (victims).",
    "Violent theft": "Armed robbery and violent theft without a weapon (offences).",
    "Property crime": "Non-violent theft, burglary, vehicle-related theft, criminal damage.",
    "Drug offences": "Drug use and trafficking (persons charged). Driven largely by police activity.",
    "Fraud": "Fraud and payment-means fraud (victims, counted at place of residence).",
}

DEFAULT_INDICATOR = "Sexual violence"

# --------------------------------------------------------------------------- #
# Geography
# --------------------------------------------------------------------------- #
REGIONS = {
    "11": "Île-de-France", "24": "Centre-Val de Loire", "27": "Bourgogne-Franche-Comté",
    "28": "Normandie", "32": "Hauts-de-France", "44": "Grand Est", "52": "Pays de la Loire",
    "53": "Bretagne", "75": "Nouvelle-Aquitaine", "76": "Occitanie", "84": "Auvergne-Rhône-Alpes",
    "93": "Provence-Alpes-Côte d'Azur", "94": "Corse", "01": "Guadeloupe", "02": "Martinique",
    "03": "Guyane", "04": "La Réunion", "06": "Mayotte",
}
OVERSEAS_REGIONS = {"01", "02", "03", "04", "06"}

# --------------------------------------------------------------------------- #
# Colours (validated categorical palette, light theme; see README "Accessibility")
# --------------------------------------------------------------------------- #
FAMILY_COLORS = {
    "Violence against persons": "#2a78d6",  # blue
    "Violent theft": "#eb6834",             # orange
    "Property crime": "#1baf7a",            # aqua
    "Drug offences": "#eda100",             # yellow
    "Fraud": "#e87ba4",                     # magenta
}
SEQ_SCALE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
# Diverging: blue = decrease, grey = stable, red = increase
DIV_SCALE = [[0.0, "#1c5cab"], [0.25, "#86b6ef"], [0.5, "#f0efec"], [0.75, "#ee8f8e"], [1.0, "#b42b2b"]]
INCREASE_COLOR = "#d03b3b"
DECREASE_COLOR = "#2a78d6"
NATIONAL_COLOR = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
INK = "#0b0b0b"
INK_2 = "#52514e"
SURFACE = "#fcfcfb"

# --------------------------------------------------------------------------- #
# Story annotations (contextual events, not causal claims)
# --------------------------------------------------------------------------- #
EVENTS = [
    (2017, "#MeToo (Oct. 2017)"),
    (2019, "Grenelle on domestic<br>violence (autumn 2019)"),
    (2020, "COVID-19 lockdowns"),
]

# --------------------------------------------------------------------------- #
# What-if assumptions (documented in README)
# Share of victims who file a complaint, from the national victimisation survey
# "Cadre de vie et sécurité" 2011–2018 average, as quoted in the SSMSI documentation.
# --------------------------------------------------------------------------- #
REPORTING_RATES = {
    "Sexual violence": 0.12,      # sexual violence outside the household
    "Residential burglary": 0.74,
}

RANDOM_SEED = 42  # no sampling is performed; kept for reproducibility conventions
