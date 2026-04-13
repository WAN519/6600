import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Global Greenhouse Gas Emissions Dashboard", layout="wide")

COUNTRY_CANDIDATES  = ['Reference area', 'REF_AREA', 'Country', 'LOCATION', 'country']
YEAR_CANDIDATES     = ['TIME_PERIOD', 'Time period', 'Year', 'TIME', 'year']
EMISSION_CANDIDATES = ['OBS_VALUE', 'Observation value', 'Value', 'Emissions', 'value']


def _find_col(columns, candidates):
    for c in candidates:
        if c in columns:
            return c
    return None


@st.cache_data
def load_data():
    df = pd.read_csv('OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,+.A.GHG._T.KG_CO2E_PS.csv')

    cols = df.columns.tolist()
    country_col  = _find_col(cols, COUNTRY_CANDIDATES)
    year_col     = _find_col(cols, YEAR_CANDIDATES)
    emission_col = _find_col(cols, EMISSION_CANDIDATES)

    if not all([country_col, year_col, emission_col]):
        missing = {
            'Country column': country_col,
            'Year column':    year_col,
            'Emissions column': emission_col,
        }
        raise KeyError(
            f"CSV column names did not match. Actual columns: {cols}\n"
            f"Match result: {missing}"
        )

    df = df[[country_col, year_col, emission_col]].copy()
    df.columns = ['Country', 'Year', 'Emissions']

    df['Emissions'] = pd.to_numeric(df['Emissions'], errors='coerce')
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df.dropna(subset=['Country', 'Year', 'Emissions'], inplace=True)
    df['Year'] = df['Year'].astype(int)

    return df


try:
    df = load_data()

    if df.empty:
        st.warning("The dataset is empty after loading. Please check the data file.")
        st.stop()

    # --- Sidebar ---
    st.sidebar.header("Filters")

    all_countries = sorted(df['Country'].dropna().unique())
    default_countries = [c for c in ['Australia', 'Canada', 'Germany', 'France', 'United Kingdom']
                         if c in all_countries]
    selected_countries = st.sidebar.multiselect(
        "Select Countries",
        options=all_countries,
        default=default_countries if default_countries else all_countries[:5]
    )

    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    if min_year == max_year:
        year_range = (min_year, max_year)
        st.sidebar.info(f"Data only contains year {min_year}")
    else:
        year_range = st.sidebar.slider("Select Year Range", min_year, max_year, (min_year, max_year))

    filtered_df = df[
        (df['Country'].isin(selected_countries)) &
        (df['Year'] >= year_range[0]) &
        (df['Year'] <= year_range[1])
    ].copy()

    filtered_df.dropna(subset=['Emissions'], inplace=True)

    # --- Main Layout ---
    st.title("🌍 Global Greenhouse Gas Emissions Dashboard")
    st.markdown(
        f"This app visualises per-capita greenhouse gas emissions from **{year_range[0]}** to **{year_range[1]}**.")

    col1, col2, col3 = st.columns(3)
    if not filtered_df.empty and filtered_df['Emissions'].notna().any():
        avg_emission = filtered_df['Emissions'].mean()
        valid_emissions = filtered_df.dropna(subset=['Emissions'])
        max_idx = valid_emissions['Emissions'].idxmax()
        max_country = valid_emissions.loc[max_idx, 'Country']
        col1.metric("Avg Emissions (kg/person)", f"{avg_emission:.2f}")
        col2.metric("Highest Emitter (selected)", max_country)
        col3.metric("Records Selected", len(filtered_df))
    else:
        st.warning("No valid data for the current filters. Please adjust your selection.")

    tab1, tab2 = st.tabs(["Trend (Line Chart)", "Comparison (Bar Chart)"])

    with tab1:
        st.subheader("Per-Capita Emissions Over Time")
        if not filtered_df.empty:
            fig_line = px.line(
                filtered_df,
                x="Year",
                y="Emissions",
                color="Country",
                markers=True,
                labels={"Emissions": "Emissions (kg CO2e/person)", "Year": "Year"},
                title="Annual Emissions Trend"
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No data to display. Please adjust your filters.")

    with tab2:
        st.subheader("Average Emissions by Country")
        if not filtered_df.empty:
            bar_df = filtered_df.groupby('Country')['Emissions'].mean().dropna().reset_index()
            if not bar_df.empty:
                fig_bar = px.bar(
                    bar_df,
                    x="Country",
                    y="Emissions",
                    color="Country",
                    labels={"Emissions": "Avg Emissions (kg CO2e/person)"},
                    title="Average Emissions by Country for Selected Period"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No data to display. Please adjust your filters.")
        else:
            st.info("No data to display. Please adjust your filters.")

    with st.expander("View Raw Data"):
        st.dataframe(filtered_df, use_container_width=True)

except FileNotFoundError:
    st.error("Error: Data file not found. Please make sure the CSV file is in the same folder as app.py.")
except KeyError as e:
    st.error(f"CSV column mismatch. Details:\n\n{e}")
