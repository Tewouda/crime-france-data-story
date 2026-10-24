"""Chapter 4 — What-if: how much of the rise could be explained by more reporting?"""
import streamlit as st

from utils import viz
from utils.constants import REPORTING_RATES

VICTIM_INDICATORS = [
    "Sexual violence",
    "Domestic physical violence",
    "Non-domestic physical violence",
    "Fraud & payment fraud",
    "Residential burglary",
]


def render(ctx: dict) -> None:
    y0, y1, nat = ctx["y0"], ctx["y1"], ctx["nat"]
    st.header("What if reporting changed?", anchor="what-if-reporting-changed", divider="gray")
    st.markdown(
        "Recorded numbers combine two things: **how many offences happen** and **how many victims "
        "go to the police**. With the simple identity "
        "`recorded = actual victims × reporting rate`, a change in recorded figures splits into "
        "`(1 + recorded change) = (1 + actual change) × (1 + reporting change)`. "
        "The data cannot tell us the reporting change, so **you choose the assumption** and see what it implies."
    )

    default = ctx["indicator"] if ctx["indicator"] in VICTIM_INDICATORS else "Sexual violence"
    c1, c2 = st.columns([1, 1.6])
    with c1:
        ind = st.selectbox("Indicator", VICTIM_INDICATORS, index=VICTIM_INDICATORS.index(default),
                           key="whatif_indicator")
        s = nat[nat["indicator"] == ind].set_index("year")
        recorded = (s.loc[y1, "count"] / s.loc[y0, "count"] - 1) * 100
        reporting = st.slider(
            f"Assumed change in the share of victims who report, {y0} → {y1} (%)",
            min_value=-50, max_value=200, value=min(100, max(0, 5 * round(recorded / 10))), step=5,
            help="Example: +50% means the reporting rate went from 12% to 18%.",
        )
        implied = ((1 + recorded / 100) / (1 + reporting / 100) - 1) * 100
        if abs(implied) < 0.5:
            implied = 0.0  # display "+0%" rather than "-0%"
        st.metric(f"Recorded change ({ind})", f"{recorded:+.0f}%")
        st.metric("Implied change in actual victimisation", f"{implied:+.0f}%",
                  help="Under your reporting assumption, with everything else constant.")
        st.caption(
            f"Break-even: if reporting rose by **{recorded:+.0f}%**, the actual number of victims "
            "would be unchanged. Any smaller increase in reporting implies a real rise."
        )
    with c2:
        viz.show(
            viz.whatif_chart(recorded, reporting, implied),
            f"Three horizontal bars: recorded change of {recorded:+.0f}% for {ind}, the assumed reporting "
            f"change of {reporting:+.0f}%, and the implied change in actual victimisation of {implied:+.0f}%.",
        )

    if ind in REPORTING_RATES:
        base = REPORTING_RATES[ind]
        st.markdown(f"##### Order of magnitude of unrecorded cases · {ind}, {y1}")
        k1, k2, k3 = st.columns(3)
        rate = k1.slider("Assumed reporting rate (%)", 5, 100, int(base * 100), 1,
                         help=f"Survey reference (Cadre de vie et sécurité 2011–2018): {base:.0%}.") / 100
        rec = s.loc[y1, "count"]
        k2.metric("Recorded", f"{rec:,.0f}")
        k3.metric("Estimated total victims", f"{rec / rate:,.0f}",
                  f"{rec / rate - rec:,.0f} never reach the police", delta_color="off")
        st.caption(
            "Survey reporting rates are national averages for 2011–2018 and refer to slightly different "
            "definitions; this is an order-of-magnitude illustration, not an estimate of prevalence."
        )
    st.info(
        "**Takeaway.** For sexual and domestic violence, a large part of the rise is compatible with "
        "victims reporting more, which is itself a policy goal. But unless reporting more than doubled, "
        "the data are also consistent with a real increase. Only victimisation surveys can separate the two.",
    )
