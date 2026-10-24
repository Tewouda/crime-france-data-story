"""Chapter 2 — KPIs and national trends (the 'great divergence')."""
import pandas as pd
import streamlit as st

from utils import viz
from utils.constants import FAMILY_HELP
from utils.prep import change_table, dept_snapshot, family_index


def _kpis(ctx: dict, nat: pd.DataFrame, snap: pd.DataFrame) -> None:
    ind, y0, y1, unit = ctx["indicator"], ctx["y0"], ctx["y1"], ctx["unit_label"]
    s = nat[nat["indicator"] == ind].set_index("year")
    rate0, rate1 = s.loc[y0, "rate"], s.loc[y1, "rate"]
    cnt0, cnt1 = s.loc[y0, "count"], s.loc[y1, "count"]
    rising = int((snap["pct_change"] > 0).sum())
    top = snap.sort_values("rate_end").iloc[-1]

    main = nat[(~nat["is_sub"])]
    persons = main[main["family"] == "Violence against persons"].groupby("year")["count"].sum()
    total = main.groupby("year")["count"].sum()
    share0, share1 = persons[y0] / total[y0] * 100, persons[y1] / total[y1] * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(f"{ind} · {y1}", f"{cnt1:,.0f}", f"{(cnt1 / cnt0 - 1) * 100:+.1f}% vs {y0}",
              delta_color="inverse", help="Number recorded by police and gendarmerie in the selection.")
    c2.metric(f"Rate {unit}", f"{rate1:.2f}", f"{(rate1 / rate0 - 1) * 100:+.1f}% vs {y0}",
              delta_color="inverse", help="Rate removes the effect of population growth.")
    c3.metric("Départements where the rate rose", f"{rising} / {len(snap)}",
              help=f"Rate in {y1} higher than in {y0}.")
    c4.metric(f"Highest rate · {y1}", f"{top['dep_name']}",
              f"{top['ratio_to_scope']:.1f}× the average", delta_color="off")
    c5.metric("Violence against persons, share of all records", f"{share1:.1f}%",
              f"{share1 - share0:+.1f} pts vs {y0}", delta_color="inverse",
              help="Share of victims of violence among all main indicators (counts, mixed units).")


def render(ctx: dict) -> None:
    y0, y1, nat = ctx["y0"], ctx["y1"], ctx["nat"]
    nat_p = nat[nat["year"].between(y0, y1)]
    fam = family_index(ctx["scope"][ctx["scope"]["year"].between(y0, y1)], y0)
    chg = change_table(nat, y0, y1)
    snap = dept_snapshot(ctx["scope"], ctx["indicator"], y0, y1)

    st.header("The big picture", anchor="the-big-picture", divider="gray")
    f_end = fam[fam["year"] == y1].set_index("family")["index"]
    persons = f_end.get("Violence against persons", float("nan")) - 100
    prop = f_end.get("Property crime", float("nan")) - 100
    st.subheader(
        f"In {ctx['scope_label']}, recorded violence against persons changed by {persons:+.0f}% "
        f"between {y0} and {y1}, while property crime changed by {prop:+.0f}%."
    )
    st.caption(f"Key figures for the focus indicator **{ctx['indicator']}** in {ctx['scope_label']} "
               "(change the indicator in the sidebar).")
    _kpis(ctx, nat_p, snap)

    st.markdown("")
    left, right = st.columns([1.35, 1])
    with left:
        viz.show(
            viz.family_index_chart(fam, y0),
            f"Line chart of five crime families indexed to {y0} = 100. Violence against persons and fraud "
            f"climb well above 100 by {y1}, while property crime and violent theft fall below 100; "
            "all families dip in 2020 during the COVID-19 lockdowns.",
        )
        with st.expander("What is in each family?"):
            for k, v in FAMILY_HELP.items():
                st.markdown(f"- **{k}**: {v}")
    with right:
        viz.show(
            viz.change_bar(chg, y0, y1),
            f"Horizontal bars of the change in rate per 1,000 between {y0} and {y1} for each indicator. "
            "Red bars (increases) are led by sexual violence, domestic violence and fraud; blue bars "
            "(decreases) by violent theft, armed robbery and vehicle theft.",
        )

    st.info(
        "**Reading the divergence.** Thefts and burglaries are well reported (insurance requires a "
        "complaint), so their decline is likely real. The steepest rises are in offences that were "
        "historically **under-reported**, sexual and domestic violence, and they accelerate after "
        "#MeToo (2017) and the national *Grenelle* on domestic violence (2019). Drug-use figures jump "
        "after fixed fines (AFD) were introduced in Sept. 2020: they measure **police activity** more than "
        "drug consumption.",
    )
    with st.expander("Data table: rates per indicator"):
        t = chg.rename(columns={"rate_start": f"Rate {y0} (‰)", "rate_end": f"Rate {y1} (‰)",
                                "count_start": f"Count {y0}", "count_end": f"Count {y1}",
                                "pct_change": "Change (%)"})
        st.dataframe(t, hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.2f") for c in t.columns
                                    if "Rate" in c or "Change" in c})
