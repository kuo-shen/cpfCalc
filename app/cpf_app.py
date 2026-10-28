"""
CPF Fun Zone 🇸🇬 - an interactive Streamlit app built on cpf37.calculate_cpf.

Pure Python: no HTML, CSS or JavaScript is written anywhere in this app.
Run with:  uv run streamlit run cpf_app.py
"""

import random

import altair as alt
import pandas as pd
import streamlit as st
from streamlit import config as st_config

from cpf37 import calculate_cpf

OW_CEILING = 7400
PALETTE = {
    "Take-home pay": "#4ECDC4",
    "Your CPF": "#FF6B6B",
    "Employer CPF": "#FFD166",
}

# Theme palettes for the light/dark toggle (same keys as [theme] in config.toml)
THEMES = {
    "dark": {
        "base": "dark",
        "primaryColor": "#FF6B6B",
        "backgroundColor": "#0F1222",
        "secondaryBackgroundColor": "#1B2038",
        "textColor": "#F5F7FF",
    },
    "light": {
        "base": "light",
        "primaryColor": "#E8505B",
        "backgroundColor": "#FFFFFF",
        "secondaryBackgroundColor": "#F1F3FA",
        "textColor": "#1B1F3B",
    },
}


def apply_theme(mode: str) -> None:
    """Switch the app theme by updating Streamlit's theme config options.

    Note: this uses Streamlit's internal config module. The change applies to the
    whole running server (every open tab) and resets to config.toml on restart.
    """
    for option, value in THEMES[mode].items():
        st_config.set_option(f"theme.{option}", value)


st.set_page_config(page_title="CPF Fun Zone", page_icon="💰", layout="wide")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def money(x: float) -> str:
    return f"${x:,.2f}"


PERSONAS = [
    (25, "🐣", "Fresh Starter", "Every dollar saved now gets decades to compound. Great start!"),
    (35, "🚀", "Career Rocket", "Your salary is climbing and your CPF is riding along with it."),
    (45, "🏡", "Nest Builder", "Housing, family, future: your CPF is working hard for all three."),
    (55, "🦉", "Wise Saver", "Peak contribution years. Your future self says thank you!"),
    (60, "🌅", "Golden Approach", "Rates step down from 56. Retirement is on the horizon!"),
    (999, "🌴", "Silver Explorer", "Still contributing and still growing. Legend status."),
]

TREATS = {
    "☕ Kopi": 1.80,
    "🍗 Chicken rice": 5.00,
    "🧋 Bubble tea": 4.50,
    "🚇 MRT rides": 1.50,
}


def persona(age: int) -> tuple[str, str, str]:
    for limit, emoji, title, blurb in PERSONAS:
        if age <= limit:
            return emoji, title, blurb
    return PERSONAS[-1][1:]


def rates_for(age: int) -> tuple[float, float]:
    """Derive the rates straight from calculate_cpf so there is one source of truth."""
    r = calculate_cpf(100, age)
    return r["employee_share"] / 100, r["employer_share"] / 100


def bracket(age: int) -> str:
    return "55 and below" if age <= 55 else "56 to 60" if age <= 60 else "Above 60"


@st.cache_data
def project(start_age: int, salary: float, years: int, rate: float, raise_pct: float) -> pd.DataFrame:
    """Year-by-year CPF balance using calculate_cpf for every year's contributions."""
    rows, balance, contributed = [], 0.0, 0.0
    for y in range(years + 1):
        rows.append({"Age": start_age + y, "Balance": balance, "Contributed": contributed})
        if y == years:
            break
        yearly = calculate_cpf(salary, start_age + y)["total_contribution"] * 12
        balance = balance * (1 + rate) + yearly
        contributed += yearly
        salary *= 1 + raise_pct
    df = pd.DataFrame(rows)
    df["Interest earned"] = df["Balance"] - df["Contributed"]
    return df


# --------------------------------------------------------------------------
# Quiz state + callbacks (callbacks run before the page re-renders)
# --------------------------------------------------------------------------
def new_round() -> None:
    st.session_state.q_salary = random.randrange(1500, 12001, 100)
    st.session_state.q_age = random.randint(18, 65)
    st.session_state.q_answered = False
    st.session_state.q_feedback = None
    st.session_state.guess_input = 0.0


def check_guess() -> None:
    ss = st.session_state
    if ss.q_answered:
        return
    answer = calculate_cpf(ss.q_salary, ss.q_age)["total_contribution"]
    guess = ss.guess_input
    error = abs(guess - answer) / answer
    ss.q_rounds += 1
    if error <= 0.02:
        ss.q_score += 3
        ss.q_streak += 1
        ss.q_celebrate = True
        ss.q_feedback = ("success", f"🎯 **BULLSEYE!** Spot on. The answer is **{money(answer)}**. +3 points")
    elif error <= 0.10:
        ss.q_score += 1
        ss.q_streak += 1
        ss.q_feedback = ("info", f"👌 **So close!** Within 10%. The answer is **{money(answer)}**. +1 point")
    else:
        ss.q_streak = 0
        direction = "high" if guess > answer else "low"
        ss.q_feedback = ("error", f"😅 **A bit too {direction}.** The answer is **{money(answer)}**. Streak reset!")
    ss.q_best = max(ss.q_best, ss.q_streak)
    ss.q_answered = True


if "q_salary" not in st.session_state:
    st.session_state.update(q_score=0, q_rounds=0, q_streak=0, q_best=0, q_celebrate=False)
    new_round()


# --------------------------------------------------------------------------
# Sidebar: inputs
# --------------------------------------------------------------------------
with st.sidebar:
    is_dark = st_config.get_option("theme.base") != "light"
    theme_label = "☀️ Switch to light mode" if is_dark else "🌙 Switch to dark mode"
    if st.button(theme_label, key="theme_toggle"):
        apply_theme("light" if is_dark else "dark")
        st.rerun()  # rerun so the browser receives the new theme
    st.header("🧑 About you")
    name = st.text_input("Your name", placeholder="e.g. Ah Boy", key="name")
    age = st.slider("Age", 16, 70, 30, key="age")
    salary = st.slider("Monthly salary", 0, 15000, 5000, step=100, format="$%d", key="salary")
    st.divider()
    emp_rate, er_rate = rates_for(age)
    st.markdown(f"**Your rates ({bracket(age)})**")
    st.markdown(f":red-badge[You {emp_rate:.0%}] :orange-badge[Employer {er_rate:.0%}]")
    st.caption(f"Ordinary Wage ceiling: {money(OW_CEILING)} per month")

result = calculate_cpf(salary, age)
emp, er, total = result["employee_share"], result["employer_share"], result["total_contribution"]
take_home = salary - emp
emoji, title, blurb = persona(age)


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.title("💰 :rainbow[CPF Fun Zone]")
st.caption("Singapore CPF contributions, made playful. Move the sliders in the sidebar and everything updates live.")

tab_calc, tab_grow, tab_game, tab_compare = st.tabs(
    ["🧮 My CPF", "📈 Grow My Nest Egg", "🎯 Guess the CPF", "⚖️ Compare & Explore"]
)

# --------------------------------------------------------------------------
# Tab 1: Calculator
# --------------------------------------------------------------------------
with tab_calc:
    greet = f"{name}, you're" if name else "You're"
    st.subheader(f"{emoji} {greet} a **{title}**")
    st.write(blurb)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏠 Take-home pay", money(take_home), f"-{money(emp)} to CPF", delta_color="off", border=True)
    c2.metric("🙋 Your share", money(emp), f"{emp_rate:.0%} of wages", delta_color="off", border=True)
    c3.metric("🏢 Employer share", money(er), "Bonus from the boss!", border=True)
    c4.metric("🏦 Total into CPF", money(total), f"{money(total * 12)} a year", delta_color="off", border=True)

    left, right = st.columns([3, 2], gap="large")

    with left, st.container(border=True):
        st.markdown(f"#### 🍩 Your total package: {money(salary + er)}")
        if salary == 0:
            st.info("Slide your salary above $0 to bake the donut! 🍩")
        else:
            donut_df = pd.DataFrame(
                {"Part": list(PALETTE), "Amount": [take_home, emp, er]}
            )
            donut = (
                alt.Chart(donut_df)
                .mark_arc(innerRadius=80, cornerRadius=8, padAngle=0.02)
                .encode(
                    theta="Amount:Q",
                    color=alt.Color(
                        "Part:N",
                        scale=alt.Scale(domain=list(PALETTE), range=list(PALETTE.values())),
                        legend=alt.Legend(orient="bottom", title=None),
                    ),
                    tooltip=["Part", alt.Tooltip("Amount:Q", format="$,.2f")],
                )
                .properties(height=340)
            )
            st.altair_chart(donut)

    with right:
        with st.container(border=True):
            st.markdown("#### 🧱 Wage ceiling meter")
            st.progress(
                min(salary / OW_CEILING, 1.0),
                text=f"{money(min(salary, OW_CEILING))} of {money(OW_CEILING)} counts for CPF",
            )
            if salary > OW_CEILING:
                st.info(f"🚧 Ceiling reached! {money(salary - OW_CEILING)} of your pay is CPF-free.")
            else:
                st.success(f"📏 {money(OW_CEILING - salary)} to go before you hit the ceiling.")

        with st.container(border=True):
            st.markdown("#### 🛍️ Your monthly CPF in treats")
            treat = st.segmented_control("Pick a treat", list(TREATS), default="☕ Kopi", key="treat") or "☕ Kopi"
            count = int(total // TREATS[treat])
            icon = treat.split()[0]
            st.markdown(f"## {icon} × {count:,}")
            st.caption(f"That's how many {treat.split(' ', 1)[1].lower()} your monthly CPF could buy (at {money(TREATS[treat])} each).")
            st.write(icon * min(count, 40) + (" …" if count > 40 else ""))

    if st.button("🎈 Celebrate my savings!", type="primary"):
        st.balloons()
        st.toast(f"{money(total * 12)} a year into your future. Shiok! 🎉", icon="🥳")


# --------------------------------------------------------------------------
# Tab 2: Projection
# --------------------------------------------------------------------------
with tab_grow:
    st.subheader("📈 Watch your CPF snowball")
    g1, g2, g3 = st.columns(3)
    years = g1.slider("Years to project", 1, 45, 30, key="years")
    rate = g2.slider("Average interest rate", 2.5, 5.0, 3.5, step=0.1, format="%.1f%%", key="rate") / 100
    raise_pct = g3.slider("Yearly pay rise", 0.0, 8.0, 3.0, step=0.5, format="%.1f%%", key="raise") / 100

    df = project(age, float(salary), years, rate, raise_pct)
    final = df.iloc[-1]

    m1, m2, m3 = st.columns(3)
    m1.metric(f"🏦 Balance at age {int(final['Age'])}", money(final["Balance"]), border=True)
    m2.metric("💵 You + employer put in", money(final["Contributed"]), border=True)
    m3.metric("✨ Free money from interest", money(final["Interest earned"]), border=True)

    long_df = df.melt(id_vars="Age", value_vars=["Contributed", "Interest earned"], var_name="Source", value_name="Amount")
    area = (
        alt.Chart(long_df)
        .mark_area(opacity=0.85, interpolate="monotone")
        .encode(
            x=alt.X("Age:Q", axis=alt.Axis(format="d")),
            y=alt.Y("Amount:Q", stack=True, axis=alt.Axis(format="$,.0s"), title="CPF balance"),
            color=alt.Color(
                "Source:N",
                scale=alt.Scale(domain=["Contributed", "Interest earned"], range=["#FF6B6B", "#A78BFA"]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["Age", "Source", alt.Tooltip("Amount:Q", format="$,.0f")],
        )
        .properties(height=380)
    )
    st.altair_chart(area)

    st.markdown("##### 🏅 Milestones")
    cols = st.columns(4)
    for col, (target, medal) in zip(cols, [(100_000, "🥉"), (250_000, "🥈"), (500_000, "🥇"), (1_000_000, "🏆")]):
        hit = df[df["Balance"] >= target]
        with col:
            if hit.empty:
                st.markdown(f"🔒 **{money(target)[:-3]}**  \nNot yet. Keep going!")
            else:
                st.markdown(f"{medal} **{money(target)[:-3]}**  \nReached at age **{int(hit.iloc[0]['Age'])}**")
    st.caption(
        "Simplified fun projection: one blended interest rate, no withdrawals, "
        "and contributions use the rates from cpf37.py for every age."
    )


# --------------------------------------------------------------------------
# Tab 3: Game
# --------------------------------------------------------------------------
with tab_game:
    ss = st.session_state
    if ss.q_celebrate:
        st.balloons()
        ss.q_celebrate = False

    st.subheader("🎯 Guess the CPF!")
    st.write("Guess the **total** monthly CPF (employee + employer). Within 2% = 3 points, within 10% = 1 point.")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("⭐ Score", ss.q_score, border=True)
    s2.metric("🎲 Rounds", ss.q_rounds, border=True)
    s3.metric("🔥 Streak", ss.q_streak, border=True)
    s4.metric("🏆 Best streak", ss.q_best, border=True)

    with st.container(border=True):
        st.markdown(f"### 🧑 A **{ss.q_age}-year-old** earns **{money(ss.q_salary)}** a month.")
        with st.expander("💡 Need a hint?"):
            st.markdown(
                "- Only the first **$7,400** counts (the wage ceiling)\n"
                "- **55 and below:** 20% employee + 17% employer = **37%**\n"
                "- **56 and above:** 15% employee + 14% employer = **29%**"
            )
        with st.form("guess_form"):
            st.number_input("Your guess ($)", min_value=0.0, step=10.0, format="%.2f", key="guess_input")
            st.form_submit_button("🔒 Lock in my answer", on_click=check_guess, disabled=ss.q_answered, type="primary")

        if ss.q_feedback:
            kind, msg = ss.q_feedback
            getattr(st, kind)(msg)
            breakdown = calculate_cpf(ss.q_salary, ss.q_age)
            st.caption(
                f"Breakdown: employee {money(breakdown['employee_share'])} + employer "
                f"{money(breakdown['employer_share'])} on {money(min(ss.q_salary, OW_CEILING))} of wages."
            )
            st.button("➡️ Next challenge", on_click=new_round)


# --------------------------------------------------------------------------
# Tab 4: Compare & explore
# --------------------------------------------------------------------------
with tab_compare:
    st.subheader("⚔️ Head-to-head")
    a, vs, b = st.columns([5, 1, 5])
    people = []
    for col, label, default_age, default_sal in [(a, "A", 30, 5000), (b, "B", 58, 8000)]:
        with col, st.container(border=True):
            pname = st.text_input("Name", value=f"Player {label}", key=f"p{label}_name")
            page = st.number_input("Age", 16, 100, default_age, key=f"p{label}_age")
            psal = st.number_input("Monthly salary ($)", 0, 100_000, default_sal, step=100, key=f"p{label}_sal")
            pres = calculate_cpf(psal, page)
            st.metric("Total CPF / month", money(pres["total_contribution"]))
            people.append((pname, pres["total_contribution"]))
    vs.markdown("## 🆚")
    (n1, t1), (n2, t2) = people
    if t1 == t2:
        st.info("🤝 It's a tie! Perfectly balanced, as all things should be.")
    else:
        winner, loser, diff = (n1, n2, t1 - t2) if t1 > t2 else (n2, n1, t2 - t1)
        st.success(f"🏆 **{winner}** saves {money(diff)} more per month than {loser} ({money(diff * 12)} a year)!")

    st.divider()
    st.subheader("🔬 Explore the rules")
    e1, e2 = st.columns(2, gap="large")

    with e1, st.container(border=True):
        st.markdown(f"#### 🎂 Same salary ({money(salary)}), different ages")
        age_df = pd.DataFrame(
            [{"Age": x, "Total CPF": calculate_cpf(salary, x)["total_contribution"], "Bracket": bracket(x)} for x in range(16, 71)]
        )
        bars = (
            alt.Chart(age_df)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("Age:O", axis=alt.Axis(values=list(range(20, 71, 5)), labelAngle=0)),
                y=alt.Y("Total CPF:Q", axis=alt.Axis(format="$,.0f")),
                color=alt.Color(
                    "Bracket:N",
                    scale=alt.Scale(domain=["55 and below", "56 to 60", "Above 60"], range=["#4ECDC4", "#FFD166", "#A78BFA"]),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
                opacity=alt.condition(alt.datum.Age == age, alt.value(1.0), alt.value(0.55)),
                tooltip=["Age", alt.Tooltip("Total CPF:Q", format="$,.2f"), "Bracket"],
            )
            .properties(height=320)
        )
        st.altair_chart(bars)
        st.caption("Your current age is highlighted. Notice the step down at 56!")

    with e2, st.container(border=True):
        st.markdown(f"#### 💸 Same age ({age}), different salaries")
        sal_df = pd.DataFrame(
            [{"Salary": s, "Total CPF": calculate_cpf(s, age)["total_contribution"]} for s in range(0, 15001, 250)]
        )
        line = (
            alt.Chart(sal_df)
            .mark_line(color="#FF6B6B", strokeWidth=3)
            .encode(
                x=alt.X("Salary:Q", axis=alt.Axis(format="$,.0f")),
                y=alt.Y("Total CPF:Q", axis=alt.Axis(format="$,.0f")),
                tooltip=[alt.Tooltip("Salary:Q", format="$,.0f"), alt.Tooltip("Total CPF:Q", format="$,.2f")],
            )
        )
        ceiling = alt.Chart(pd.DataFrame({"x": [OW_CEILING]})).mark_rule(color="#FFD166", strokeDash=[6, 4]).encode(x="x:Q")
        you = alt.Chart(pd.DataFrame({"Salary": [salary], "Total CPF": [total]})).mark_point(
            size=180, filled=True, color="#4ECDC4"
        ).encode(x="Salary:Q", y="Total CPF:Q")
        st.altair_chart((line + ceiling + you).properties(height=320))
        st.caption("The yellow line is the $7,400 ceiling: earn more and CPF stops growing. The teal dot is you.")
