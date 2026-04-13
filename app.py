import streamlit as st
import pandas as pd
import plotly.express as px

# 设置页面配置
st.set_page_config(page_title="全球温室气体排放仪表盘", layout="wide")


# 加载数据集
@st.cache_data
def load_data():
    # 读取 CSV 文件
    df = pd.read_csv('OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,+.A.GHG._T.KG_CO2E_PS.csv')
    # 清洗列名和必要的数据转换
    df = df[['Reference area', 'Time period', 'Observation value']].copy()
    df.columns = ['Country', 'Year', 'Emissions']
    return df


try:
    df = load_data()

    # --- 侧边栏交互设置 ---
    st.sidebar.header("筛选选项")

    # 国家多选
    all_countries = sorted(df['Country'].unique())
    selected_countries = st.sidebar.multiselect(
        "选择国家/地区",
        options=all_countries,
        default=['Australia', 'Canada', 'Germany', 'France', 'United Kingdom']
    )

    # 年份范围滑块
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.sidebar.slider("选择时间范围", min_year, max_year, (min_year, max_year))

    # 过滤数据
    filtered_df = df[
        (df['Country'].isin(selected_countries)) &
        (df['Year'] >= year_range[0]) &
        (df['Year'] <= year_range[1])
        ]

    # --- 主界面布局 ---
    st.title("🌍 温室气体排放交互式可视化")
    st.markdown(
        f"本应用根据作业 5 要求构建，旨在探索 **{year_range[0]} - {year_range[1]}** 期间各国的人均温室气体排放量。")

    # 关键指标卡片 (Metrics)
    col1, col2, col3 = st.columns(3)
    if not filtered_df.empty:
        avg_emission = filtered_df['Emissions'].mean()
        max_country = filtered_df.loc[filtered_df['Emissions'].idxmax(), 'Country']
        col1.metric("平均排放量 (kg/人)", f"{avg_emission:.2f}")
        col2.metric("选定范围最高排放国家", max_country)
        col3.metric("选定记录数", len(filtered_df))

    # 图表展示
    tab1, tab2 = st.tabs(["趋势图 (Line Chart)", "分布对比 (Bar Chart)"])

    with tab1:
        st.subheader("人均排放量随时间的变化趋势")
        fig_line = px.line(
            filtered_df,
            x="Year",
            y="Emissions",
            color="Country",
            markers=True,
            labels={"Emissions": "排放量 (kg CO2e/人)", "Year": "年份"},
            title="年度排放趋势"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        st.subheader("各国排放量横向对比")
        # 取选定范围内每个国家的平均值进行对比
        bar_df = filtered_df.groupby('Country')['Emissions'].mean().reset_index()
        fig_bar = px.bar(
            bar_df,
            x="Country",
            y="Emissions",
            color="Country",
            labels={"Emissions": "平均排放量 (kg CO2e/人)"},
            title=f"选定年份区间内各国的平均排放水平"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # 显示原始数据
    with st.expander("查看过滤后的原始数据表"):
        st.dataframe(filtered_df, use_container_width=True)

except FileNotFoundError:
    st.error("错误：未找到数据集文件。请确保 CSV 文件与 app.py 在同一文件夹内。")