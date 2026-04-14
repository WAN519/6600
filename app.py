import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Global GHG Emissions Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (light theme) ──────────────────────────────────────────────────
st.markdown("""
<style>
/* Metric cards */
[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px 20px;
}
[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 0.78rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a !important;
}

/* Tab styling */
[data-testid="stTabs"] button {
    font-weight: 600;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── Colour palette (works well on white background) ───────────────────────────
PALETTE = [
    "#2563eb",  # blue
    "#16a34a",  # green
    "#dc2626",  # red
    "#d97706",  # amber
    "#7c3aed",  # violet
    "#0891b2",  # cyan
    "#ea580c",  # orange
    "#0d9488",  # teal
    "#db2777",  # pink
    "#64748b",  # slate
]

COUNTRY_CANDIDATES  = ["Reference area", "REF_AREA", "Country", "LOCATION", "country"]
YEAR_CANDIDATES     = ["TIME_PERIOD", "Time period", "Year", "TIME", "year"]
EMISSION_CANDIDATES = ["OBS_VALUE", "Observation value", "Value", "Emissions", "value"]


def _find_col(columns, candidates):
    for c in candidates:
        if c in columns:
            return c
    return None


@st.cache_data
def load_data():
    df = pd.read_csv("OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,+.A.GHG._T.KG_CO2E_PS.csv")
    cols = df.columns.tolist()
    country_col  = _find_col(cols, COUNTRY_CANDIDATES)
    year_col     = _find_col(cols, YEAR_CANDIDATES)
    emission_col = _find_col(cols, EMISSION_CANDIDATES)

    if not all([country_col, year_col, emission_col]):
        raise KeyError(
            f"CSV column names did not match. Actual columns: {cols}\n"
            f"Match result: country={country_col}, year={year_col}, emission={emission_col}"
        )

    df = df[[country_col, year_col, emission_col]].copy()
    df.columns = ["Country", "Year", "Emissions"]
    df["Emissions"] = pd.to_numeric(df["Emissions"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df.dropna(subset=["Country", "Year", "Emissions"], inplace=True)
    df["Year"] = df["Year"].astype(int)
    return df


# ── Plotly light theme base ───────────────────────────────────────────────────
AXIS_STYLE = dict(
    gridcolor="#e2e8f0",
    zerolinecolor="#cbd5e1",
    tickfont=dict(size=11, color="#475569"),
)

CHART_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="Inter, system-ui, sans-serif", color="#334155"),
    title_font=dict(size=16, color="#0f172a"),
    legend=dict(
        bgcolor="#f8fafc",
        bordercolor="#e2e8f0",
        borderwidth=1,
        font=dict(size=12, color="#334155"),
    ),
    margin=dict(l=60, r=30, t=60, b=60),
)


# ── Main app ──────────────────────────────────────────────────────────────────
try:
    df = load_data()

    if df.empty:
        st.warning("The dataset is empty after loading. Please check the data file.")
        st.stop()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🌍 GHG Dashboard")
        st.markdown("---")
        st.markdown("**Filters**")

        all_countries = sorted(df["Country"].dropna().unique())
        default_countries = [c for c in ["Australia", "Canada", "Germany", "France", "United Kingdom"]
                             if c in all_countries]
        selected_countries = st.multiselect(
            "Countries",
            options=all_countries,
            default=default_countries if default_countries else all_countries[:5],
        )

        min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
        if min_year == max_year:
            year_range = (min_year, max_year)
            st.info(f"Data only contains year {min_year}")
        else:
            year_range = st.slider("Year Range", min_year, max_year, (min_year, max_year))

        st.markdown("---")
        st.caption("Data: OECD Air Emissions – GHG Inventories  \nUnit: kg CO₂e per person")

    # ── Filter data ───────────────────────────────────────────────────────────
    filtered_df = df[
        (df["Country"].isin(selected_countries)) &
        (df["Year"] >= year_range[0]) &
        (df["Year"] <= year_range[1])
    ].copy()
    filtered_df.dropna(subset=["Emissions"], inplace=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("# 🌍 Global Greenhouse Gas Emissions")
    st.markdown(
        f"Per-capita emissions · **{year_range[0]}** – **{year_range[1]}** · "
        f"{len(selected_countries)} countr{'y' if len(selected_countries)==1 else 'ies'} selected"
    )
    st.markdown("---")

    # ── KPI Metrics ───────────────────────────────────────────────────────────
    if not filtered_df.empty and filtered_df["Emissions"].notna().any():
        avg_emission = filtered_df["Emissions"].mean()
        valid = filtered_df.dropna(subset=["Emissions"])
        max_row = valid.loc[valid["Emissions"].idxmax()]
        min_row = valid.loc[valid["Emissions"].idxmin()]

        first_yr = filtered_df[filtered_df["Year"] == year_range[0]]["Emissions"].mean()
        last_yr  = filtered_df[filtered_df["Year"] == year_range[1]]["Emissions"].mean()
        trend_delta = None if pd.isna(first_yr) or pd.isna(last_yr) else round(last_yr - first_yr, 2)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Emissions (kg/person)", f"{avg_emission:,.1f}",
                  delta=f"{trend_delta:+.1f} vs {year_range[0]}" if trend_delta is not None else None,
                  delta_color="inverse")
        c2.metric("Highest Emitter", max_row["Country"],
                  delta=f"{max_row['Emissions']:,.0f} kg/person")
        c3.metric("Lowest Emitter", min_row["Country"],
                  delta=f"{min_row['Emissions']:,.0f} kg/person")
        c4.metric("Data Points", f"{len(filtered_df):,}")
    else:
        st.warning("No valid data for the current filters. Please adjust your selection.")

    st.markdown("")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["📈  Trend (Line Chart)", "📊  Comparison (Bar Chart)"])

    with tab1:
        if not filtered_df.empty:
            fig_line = go.Figure()
            countries = filtered_df["Country"].unique()

            for i, country in enumerate(countries):
                cdf = filtered_df[filtered_df["Country"] == country].sort_values("Year")
                colour = PALETTE[i % len(PALETTE)]
                fig_line.add_trace(go.Scatter(
                    x=cdf["Year"],
                    y=cdf["Emissions"],
                    name=country,
                    mode="lines+markers",
                    line=dict(width=2.5, color=colour),
                    marker=dict(size=6, color=colour,
                                line=dict(width=1.5, color="white")),
                    hovertemplate=(
                        f"<b>{country}</b><br>"
                        "Year: %{x}<br>"
                        "Emissions: <b>%{y:,.1f} kg CO₂e/person</b>"
                        "<extra></extra>"
                    ),
                ))

            fig_line.update_layout(
                **CHART_LAYOUT,
                title="Per-Capita GHG Emissions Over Time",
                xaxis=dict(
                    **AXIS_STYLE,
                    title="Year",
                    dtick=5,
                    rangeselector=dict(
                        bgcolor="#f1f5f9",
                        activecolor="#dbeafe",
                        bordercolor="#e2e8f0",
                        font=dict(color="#334155", size=11),
                        buttons=[
                            dict(count=10, label="10Y", step="year", stepmode="backward"),
                            dict(count=20, label="20Y", step="year", stepmode="backward"),
                            dict(step="all", label="All"),
                        ],
                        x=0, y=1.08,
                    ),
                    rangeslider=dict(visible=False),
                ),
                yaxis=dict(
                    **AXIS_STYLE,
                    title="Emissions (kg CO₂e/person)",
                ),
                hovermode="x unified",
            )

            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No data to display. Please adjust your filters.")

    with tab2:
        if not filtered_df.empty:
            bar_df = (
                filtered_df.groupby("Country")["Emissions"]
                .mean()
                .dropna()
                .reset_index()
                .sort_values("Emissions", ascending=True)
            )
            if not bar_df.empty:
                colours = [PALETTE[i % len(PALETTE)] for i in range(len(bar_df))]
                fig_bar = go.Figure(go.Bar(
                    x=bar_df["Emissions"],
                    y=bar_df["Country"],
                    orientation="h",
                    marker=dict(
                        color=colours,
                        line=dict(color="rgba(0,0,0,0)", width=0),
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Avg: <b>%{x:,.1f} kg CO₂e/person</b>"
                        "<extra></extra>"
                    ),
                    text=bar_df["Emissions"].apply(lambda v: f"{v:,.0f}"),
                    textposition="outside",
                    textfont=dict(color="#64748b", size=11),
                ))

                fig_bar.update_layout(
                    **CHART_LAYOUT,
                    title=f"Average Per-Capita Emissions · {year_range[0]}–{year_range[1]}",
                    xaxis=dict(
                        **AXIS_STYLE,
                        title="Avg Emissions (kg CO₂e/person)",
                    ),
                    yaxis=dict(
                        **AXIS_STYLE,
                        title="",
                    ),
                    showlegend=False,
                )

                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No data to display. Please adjust your filters.")
        else:
            st.info("No data to display. Please adjust your filters.")

    # ── Raw data expander ─────────────────────────────────────────────────────
    with st.expander("View Raw Data"):
        st.dataframe(
            filtered_df.sort_values(["Country", "Year"]),
            use_container_width=True,
            hide_index=True,
        )

    # ── Write-up ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📝 Project Write-up")

    with st.expander("1 · Research Question", expanded=True):
        st.markdown("""
This dashboard answers: **How have per-capita greenhouse gas emissions changed across OECD countries over time, and which countries emit the most per person?**

It uses per-capita figures (kg CO₂e/person) rather than absolute totals so that countries of different population sizes can be fairly compared.
        """)

    with st.expander("2 · Design Rationale"):
        st.markdown("""
**Visual encodings**

| Chart | Choice | Why |
|-------|--------|-----|
| Line chart | Position (x = year, y = emissions) + colour per country | Best channel for showing change over time; markers highlight individual data points where gaps may exist. |
| Horizontal bar chart | Bar length + sorted ascending | Rank is immediately readable; horizontal layout avoids rotating long country names. |
| Distinct colour palette | 10 perceptually separated hues | Colours remain distinguishable when multiple countries are selected simultaneously. |

**Interaction techniques**

- **Country filter & year slider** (sidebar) — focus on a subset without losing the full dataset.
- **Range selector buttons (10Y / 20Y / All)** — quick zoom on the line chart.
- **Unified hover tooltip** — shows all countries at once for a given year, making cross-country comparison easy.

**Alternatives considered**

- *Stacked area chart* — rejected because stacking distorts individual per-capita readings.
- *Vertical bar chart* — replaced with horizontal; country name labels overlapped when many countries were selected.
        """)

    with st.expander("3 · References & Data Sources"):
        st.markdown("""
**Data source**

OECD Air Emissions – Greenhouse Gas Inventories (`DSD_AIR_GHG@DF_AIR_GHG`), accessed April 2025.
Unit: kg CO₂-equivalent per person · Coverage: OECD member countries, annual.

[https://data-explorer.oecd.org/vis?df[ds]=DisseminateFinalDMZ&df[id]=DSD_AIR_GHG%40DF_AIR_GHG&df[ag]=OECD.ENV.EPI&dq=.A.GHG._T.KG_CO2E_PS&pd=2014%2C&to[TIME_PERIOD]=false](https://data-explorer.oecd.org/vis?df[ds]=DisseminateFinalDMZ&df[id]=DSD_AIR_GHG%40DF_AIR_GHG&df[ag]=OECD.ENV.EPI&dq=.A.GHG._T.KG_CO2E_PS&pd=2014%2C&to[TIME_PERIOD]=false)

**Tools**

- [Streamlit](https://docs.streamlit.io) — web app framework
- [Plotly](https://plotly.com/python/) — interactive charts (`plotly.graph_objects`)
- [pandas](https://pandas.pydata.org) — data processing
        """)

    with st.expander("4 · Development Process"):
        st.markdown("""
**Estimated time: ~4.5 people-hours**

| Phase | Hours |
|-------|-------|
| Data exploration & cleaning | 0.5 h |
| Initial prototype | 1.0 h |
| Visual redesign (theme, palette, layout) | 1.5 h |
| Interaction & KPI improvements | 1.0 h |
| Write-up | 0.5 h |

**What took the most time?**

The visual redesign took the longest. Switching from Plotly Express to `graph_objects` was necessary to control line width, marker style, and the unified hover tooltip, but required rewriting each chart from scratch. Keeping the custom CSS consistent across Streamlit's internal component structure was also time-consuming.
        """)

except FileNotFoundError:
    st.error("Error: Data file not found. Please ensure the CSV file is in the same folder as app.py.")
except KeyError as e:
    st.error(f"CSV column mismatch. Details:\n\n{e}")
