# pages/1_overview.py
import streamlit as st
import plotly.express as px
import pandas as pd
import queries as q
from utils.charts import COLORS, apply_theme, kpi_card, render_sidebar
st.set_page_config(
    page_title = "Overview",
    page_icon  = "📊",
    layout     = "wide",
)

render_sidebar()
# ============================================================
# LIGHT THEME CSS
# ============================================================
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    h1, h2, h3 { color: #1a1a1a !important; }
    hr { border-color: #e0e0e0 !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# PAGE HEADER
# ============================================================
st.title("📊 Overview")
st.caption("High level summary of traffic stops")
st.divider()



# ============================================================
# ROW 1 — Yearly trend + Violation type
# ============================================================
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📅 Stops by Year")
    
    @st.cache_data
    def load_yearly():
        return q.get_yearly_trend()

    yearly = load_yearly()
    yearly = yearly[yearly['year'] <= 2024]

    fig = px.bar(
        yearly, x='year', y='stops', title = 'Traffic Stops by Year', 
        color_discrete_sequence=[COLORS['blue']],
    )
    
    fig.add_vline(
        x=2020, line_dash='dash',
        line_color=COLORS['red'],
        annotation_text='COVID-19',
        annotation_font_color=COLORS['red']
    )
    fig.update_layout(
        xaxis_title = 'Year',
        yaxis_title = 'Number of Stops',
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⚖️ Violation Type")

    @st.cache_data
    def load_violation_type():
        return q.get_violation_type()

    vtype = load_violation_type()

    fig = px.pie(
        vtype,
        names  = 'violation_type',
        title  = 'Violation Type Breakdown',
        values = 'total',
        hole   = 0.4,
        color = 'violation_type',
        color_discrete_map = {
        'CITATION' : '#F44336',
        'WARNING'  : '#FF9800',
        'ESERO'    : '#2196F3',
        'SERO'     : '#9E9E9E',
        }    
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 2 — Top violations + Citation rate
# ============================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Top Violation Categories")

    @st.cache_data
    def load_violations():
        return q.get_violation_category()

    violations = load_violations()

    fig = px.bar(
        violations.head(10),
        x                        = 'total',
        y                        = 'violation_category',
        orientation              = 'h',
        color_discrete_sequence  = [COLORS['blue']],
        title                   = '📋 Top Violation Categories'
    )
    fig.update_layout(
        xaxis_title = 'Number of Charges',
        yaxis_title = '',
        yaxis       = dict(autorange='reversed'),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Citation Rate by Category")

    @st.cache_data
    def load_citation_rate():
        return q.get_citation_rate()

    citation = load_citation_rate()

    fig = px.bar(
        citation.sort_values('citation_rate'),
        x                       = 'citation_rate',
        y                       = 'violation_category',
        orientation             = 'h',
        color                   = 'citation_rate',
        color_continuous_scale  = ['#2196F3', '#4CAF50'],
        title                  = '📊 Citation Rate by Category (%)',

    )
    fig.add_vline(
        x                      = 80,
        line_dash              = 'dash',
        line_color             = COLORS['red'],
        annotation_text        = '80%',
        annotation_font_color  = COLORS['red']
    )
    fig.update_layout(
        xaxis_title          = 'Citation Rate %',
        yaxis_title          = '',
        yaxis                = dict(autorange='reversed'),
        coloraxis_showscale  = False,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 3 — District breakdown + Safety overview
# ============================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌆 Stops by District")

    @st.cache_data
    def load_district():
        return q.get_stops_by_district()

    district = load_district()
    district['district_name'] = district['district_number'].map({
        1: '1 - Rockville',
        2: '2 - Bethesda',
        3: '3 - Silver Spring',
        4: '4 - Wheaton',
        5: '5 - Germantown',
        6: '6 - Gaithersburg',
    })

    fig = px.bar(
        district,
        x                       = 'district_name',
        y                       = 'stops',
        color_discrete_sequence = [COLORS['teal']],
        title                   = '🌆 Stops by District',

    )
    fig.update_layout(
        xaxis_title      = 'District',
        yaxis_title      = 'Number of Stops',
        xaxis_tickangle  = -15,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🛡️ Safety Overview")

    @st.cache_data
    def load_safety():
        return q.get_safety_overview()

    safety = load_safety().iloc[0]

    safety_df = pd.DataFrame({
        'Category' : [
            'Accidents', 'Belt Violations',
            'Injuries', 'Property Damage', 'Fatalities'
        ],
        'Count' : [
            int(safety['accidents']),
            int(safety['belt_violations']),
            int(safety['injuries']),
            int(safety['property_damage']),
            int(safety['fatalities']),
        ]
    })

    fig = px.bar(
        safety_df,
        x                       = 'Count',
        y                       = 'Category',
        orientation             = 'h',
        color                   = 'Count',
        color_continuous_scale  = ['#2196F3', '#F44336'],
        title                  = '🛡️ Safety Overview',

    )
    fig.update_layout(
        xaxis_title         = 'Count',
        yaxis_title         = '',
        coloraxis_showscale = False,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")