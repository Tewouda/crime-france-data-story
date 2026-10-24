"""Chapter 1 — Hook, audience, questions and caveats."""
import streamlit as st

from utils.constants import DATASET_PAGE, DATASET_VERSION


def render(ctx: dict) -> None:
    st.title("Fewer thefts, more reported violence")
    st.markdown(
        "#### What ten years of police and gendarmerie records say about crime in France (2016–2025)"
    )
    st.caption(
        f"Source: SSMSI – Ministère de l'Intérieur, [data.gouv.fr]({DATASET_PAGE}) · {DATASET_VERSION} · "
        "Licence Ouverte 2.0"
    )

    st.header("Why it matters", anchor="why-it-matters", divider="gray")
    st.markdown(
        "Every year France's police and gendarmerie record about **3.6 million** offences on the main "
        "crime indicators. Debates about “insecurity” often treat them as one number that goes up or "
        "down. **It doesn't.** Over the last decade the *kind* of crime that gets recorded has "
        "changed: theft, burglary and vandalism have **fallen**, while recorded violence against "
        "people, sexual violence and fraud have **risen sharply**. The question is whether that rise "
        "means more violence, more victims coming forward, or both."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("##### Audience")
        st.markdown(
            "- **Local decision-makers** (prefectures, *départements*, city councils) planning "
            "prevention and victim-support budgets\n"
            "- **Journalists & citizens** who want to read crime figures without jumping to conclusions"
        )
    with c2:
        st.markdown("##### Questions this story answers")
        st.markdown(
            "1. **What** changed between 2016 and 2025, and in which direction?\n"
            "2. **Where**: is the change the same in every *département* and region?\n"
            "3. **Who** stands out: highest rates, outliers, size effects?\n"
            "4. **Why**: how much of the rise could come from victims reporting more?"
        )
    with c3:
        st.markdown("##### How to read this app")
        st.markdown(
            "- Scroll top to bottom: each chapter opens with a **one-sentence headline**.\n"
            "- Use the **sidebar** to change the period, regions and focus indicator; "
            "all KPIs and charts update.\n"
            "- Hover any chart for exact values; open the **help tooltips and data tables** for the numbers."
        )

    st.warning(
        "**Recorded crime is not the same as actual crime.** These figures count offences that police "
        "and gendarmerie *recorded*. They depend on whether victims file a complaint (only about 12% of "
        "victims of sexual violence outside the household do, against 74% for burglary victims) and, "
        "for drug offences, on police activity. Read every increase as “more cases reach the police”, "
        "not automatically as “more crime”.",
    )
