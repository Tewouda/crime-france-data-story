"""Chapter 6 — Takeaways, implications and next steps."""
import streamlit as st

from utils.io import LICENSE_TEXT
from utils.prep import change_table, family_index


def render(ctx: dict) -> None:
    y0, y1, nat, scope = ctx["y0"], ctx["y1"], ctx["nat"], ctx["scope"]
    chg = change_table(nat, y0, y1).set_index("indicator")["pct_change"]
    fam = family_index(scope[scope["year"].between(y0, y1)], y0)
    f = fam[fam["year"] == y1].set_index("family")["index"] - 100

    def p(ind):
        return f"{chg.get(ind, float('nan')):+.0f}%"

    st.header("Takeaways", anchor="takeaways", divider="gray")
    st.subheader(f"{ctx['scope_label']}, {y0}→{y1}: the crime that gets recorded has shifted from property to people.")

    c1, c2 = st.columns(2)
    with c1:
        st.success(
            "**Key insights**\n\n"
            f"1. **Two opposite trends.** Violence against persons {f.get('Violence against persons', 0):+.0f}% and "
            f"fraud {f.get('Fraud', 0):+.0f}%, versus property crime {f.get('Property crime', 0):+.0f}% and violent "
            f"theft {f.get('Violent theft', 0):+.0f}% (counts).\n"
            f"2. **Biggest rises** in historically under-reported offences: sexual violence {p('Sexual violence')}, "
            f"domestic violence {p('Domestic physical violence')} (rates).\n"
            f"3. **Biggest falls** in street and vehicle crime: violent theft {p('Violent theft without weapon')}, "
            f"armed robbery {p('Armed robbery')}, vehicle theft {p('Vehicle theft')}.\n"
            "4. **Everywhere, not just in cities**: between 2016 and 2025 the sexual-violence, domestic-violence "
            "and fraud rates rose in **all 101 départements**. Levels still differ (top vs bottom decile "
            "1.4–2.8× depending on the indicator): overseas départements lead for physical violence and "
            "homicides, Paris for sexual violence, fraud and drug use.\n"
            "5. **Reporting matters**: a doubling of the reporting rate would be enough to explain most of "
            "the recorded rise in sexual violence; we cannot rule either explanation out."
        )
    with c2:
        st.info(
            "**Implications**\n\n"
            "- **For local decision-makers:** more cases reaching the police means more demand for victim "
            "support, investigators specialised in intra-family and sexual violence, and court capacity. "
            "Budget for the *recorded* trend, even if part of it is better reporting.\n"
            "- **For journalists:** never report “crime is up” as one number. Separate property crime "
            "(down) from violence (up), and mention reporting effects.\n"
            "- **For prevention policy:** falling burglary and vehicle theft suggest that target-hardening "
            "works; fraud, now mostly online, needs national rather than local responses.\n\n"
            "**Next steps**\n\n"
            "- Join the *Cadre de vie et sécurité* / *Vécu et ressenti en matière de sécurité* victimisation "
            "surveys to estimate reporting rates directly.\n"
            "- Go down to commune level (also on data.gouv.fr) to separate urban from rural effects.\n"
            "- Add socio-economic covariates (INSEE density, poverty rate, tourism) for a multivariate model."
        )

    st.markdown("##### Ethics & transparency")
    st.markdown(
        "- Data are **aggregated** at département level (the smallest, Lozère, has about 76,000 "
        "inhabitants), so no individual can be identified; SSMSI already suppresses small communes.\n"
        "- The app shows **associations, not causes**; contextual events are annotations, not explanations.\n"
        "- Rates use the population where the offence was recorded; tourist areas and city centres are "
        "inflated by visitors (e.g. Paris).\n"
        "- All code, assumptions (reporting rates, outlier threshold) and checks are documented in the README."
    )
    st.divider()
    st.caption(LICENSE_TEXT)
