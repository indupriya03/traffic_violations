# pages/3_violations.py
import streamlit as st
import plotly.express as px
import pandas as pd
import queries as q
from filters import render_page_filters, build_where_clause
from utils.charts import COLORS, apply_theme, render_sidebar, kpi_card

st.set_page_config(
    page_title = "Violations Analysis",
    page_icon  = "⚖️",
    layout     = "wide",
)

# ============================================================
# CSS
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
# SIDEBAR
# ============================================================
render_sidebar()

# ============================================================
# PAGE HEADER
# ============================================================
st.title("⚖️ Violations Analysis")
st.caption("Citation, warning and violation category analysis")
st.divider()

# ============================================================
# FILTERS
# ============================================================
filters = render_page_filters(
    show_year               = True,
    show_time               = True,
    show_days               = True,
    show_district           = True,
    show_violation_type     = True,
    show_violation_category = True,
    show_vehicle_type       = False,
    show_location           = False,
)
where, params = build_where_clause(filters)
params_tuple  = tuple(sorted(params.items()))

st.divider()

# ============================================================
# ROW 1 — KPIs
# ============================================================
@st.cache_data
def load_kpis():
    return q.get_kpis()

kpis = load_kpis()
col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card(
        "📋 Total Charges",
        f"{kpis['total_charges']:,}",   # fixed typo!
        color=COLORS['blue']
    )

with col2:
    kpi_card(
        "🔴 Citations",
        f"{kpis['total_citations']:,}",
        delta=f"{kpis['citation_rate_charge_level']:.1f}%",
        color=COLORS['red']
    )

with col3:
    kpi_card(
        "🟠 Warnings",
        f"{kpis['total_warnings']:,}",
        delta=f"{kpis['warnings_rate_charge_level']:.1f}%",
        color=COLORS['orange']
    )

with col4:
    kpi_card(
        "🔵 Repair Orders",
        f"{kpis['repair_orders']:,}",
        delta=f"{kpis['repair_order_rate']:.1f}%",
        color=COLORS['teal']
    )

st.divider()

# ============================================================
# ROW 2 — Top violations + Violation type pie
# ============================================================
col1, col2 = st.columns([2, 1])

with col1:
    @st.cache_data
    def load_violations(where, params_tuple):
        return q.get_violation_category(where, dict(params_tuple))

    violations = load_violations(where, params_tuple)

    fig = px.bar(
        violations.head(10),
        x                       = 'total',
        y                       = 'violation_category',
        orientation             = 'h',
        title                   = '📋 Top Violation Categories',
        color_discrete_sequence = [COLORS['blue']],
    )
    fig.update_layout(
        xaxis_title = 'Number of Charges',
        yaxis_title = '',
        yaxis       = dict(autorange='reversed'),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_vtype(where, params_tuple):
        return q.get_violation_type(where, dict(params_tuple))

    vtype = load_vtype(where, params_tuple)

    fig = px.pie(
        vtype,
        names  = 'violation_type',
        values = 'total',
        hole   = 0.4,
        title  = '⚖️ Violation Type Breakdown',
        color  = 'violation_type',
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
# ROW 3 — Citation rate by category
# ============================================================
@st.cache_data
def load_citation_rate(where, params_tuple):
    return q.get_citation_rate(where, dict(params_tuple))

citation = load_citation_rate(where, params_tuple)

fig = px.bar(
    citation.sort_values('citation_rate'),
    x                      = 'citation_rate',
    y                      = 'violation_category',
    orientation            = 'h',
    title                  = '📊 Citation Rate by Category (%)',
    color                  = 'citation_rate',
    color_continuous_scale = ['#2196F3', '#F44336'],
    text                   = 'citation_rate',
)
fig.add_vline(
    x                     = 80,
    line_dash             = 'dash',
    line_color            = COLORS['red'],
    annotation_text       = '80% threshold',
    annotation_font_color = COLORS['red']
)
fig.update_traces(texttemplate='%{text}%', textposition='outside')
fig.update_layout(
    xaxis_title         = 'Citation Rate %',
    yaxis_title         = '',
    yaxis               = dict(autorange='reversed'),
    coloraxis_showscale = False,
)
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 4 — Violations by district + Violations by hour
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_violation_district(where, params_tuple):
        return q.get_violation_by_district(where, dict(params_tuple))

    viol_dist = load_violation_district(where, params_tuple)

    # Get top violation per district
    top_per_district = (
        viol_dist.groupby('district_number')
        .apply(lambda x: x.nlargest(1, 'total'))
        .reset_index(drop=True)
    )
    top_per_district['district_name'] = \
        top_per_district['district_number'].map({
            1: '1-Rockville',
            2: '2-Bethesda',
            3: '3-Silver Spring',
            4: '4-Wheaton',
            5: '5-Germantown',
            6: '6-Gaithersburg',
        })

    fig = px.bar(
        top_per_district,
        x                       = 'district_name',
        y                       = 'total',
        color                   = 'violation_category',
        title                   = '🌆 Top Violation by District',
        color_discrete_sequence = list(COLORS.values()),
    )
    fig.update_layout(
        xaxis_title     = 'District',
        yaxis_title     = 'Number of Charges',
        xaxis_tickangle = -15,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_violation_hour(where, params_tuple):
        return q.get_violation_by_hour(where, dict(params_tuple))

    viol_hour = load_violation_hour(where, params_tuple)

    # Top violation per hour
    top_per_hour = (
        viol_hour.groupby('hour')
        .apply(lambda x: x.nlargest(1, 'total'))
        .reset_index(drop=True)
    )

    fig = px.bar(
        top_per_hour,
        x                       = 'hour',
        y                       = 'total',
        color                   = 'violation_category',
        title                   = '🕐 Top Violation by Hour',
        color_discrete_sequence = list(COLORS.values()),
    )
    fig.update_layout(
        xaxis_title = 'Hour of Day',
        yaxis_title = 'Number of Charges',
        xaxis       = dict(tickmode='linear', dtick=1),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")