# pages/6_search.py
import streamlit as st
import plotly.express as px
import pandas as pd
import queries as q
from filters import render_page_filters, build_where_clause
from utils.charts import COLORS, apply_theme, render_sidebar, kpi_card

st.set_page_config(
    page_title = "Search & Enforcement",
    page_icon  = "🔍",
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
st.title("🔍 Search & Enforcement")
st.caption("Search rates, contraband hit rates and arrest analysis")
st.divider()

# ============================================================
# FILTERS
# ============================================================
filters = render_page_filters(
    show_year               = True,
    show_time               = False,
    show_days               = False,
    show_district           = True,
    show_violation_type     = False,
    show_violation_category = False,
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
def load_search_kpis(where, params_tuple):
    params = dict(params_tuple)

    total_stops = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
    """, params=params)['cnt'].iloc[0]

    searches = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        {'AND' if where else 'WHERE'} se.search_conducted = 1
    """, params=params)['cnt'].iloc[0]

    arrests = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        {'AND' if where else 'WHERE'} se.search_outcome = 'Arrest'
    """, params=params)['cnt'].iloc[0]

    contraband = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        {'AND' if where else 'WHERE'} 
        se.search_disposition LIKE '%Contraband%'
    """, params=params)['cnt'].iloc[0]

    return {
        'total_stops'  : total_stops,
        'searches'     : searches,
        'arrests'      : arrests,
        'contraband'   : contraband,
        'search_rate'  : round(searches/total_stops*100, 1) \
                         if total_stops > 0 else 0,
        'arrest_rate'  : round(arrests/total_stops*100, 1) \
                         if total_stops > 0 else 0,
        'contraband_rate': round(contraband/searches*100, 1) \
                           if searches > 0 else 0,
    }

kpis = load_search_kpis(where, params_tuple)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("🚗 Total Stops",
             f"{kpis['total_stops']:,}",
             color=COLORS['blue'])
with col2:
    kpi_card("🔍 Searches",
             f"{kpis['searches']:,}",
             delta=f"{kpis['search_rate']}% search rate",
             color=COLORS['purple'])
with col3:
    kpi_card("⛓ Arrests",
             f"{kpis['arrests']:,}",
             delta=f"{kpis['arrest_rate']}% arrest rate",
             color=COLORS['red'])
with col4:
    kpi_card("📦 Contraband Hit Rate",
             f"{kpis['contraband_rate']}%",
             delta=f"{kpis['contraband']:,} searches",
             color=COLORS['orange'])

st.divider()

# ============================================================
# ROW 2 — Search reason + Search type
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_search_reason(where, params_tuple):
        return q.get_search_by_reason(where, dict(params_tuple))

    reason = load_search_reason(where, params_tuple)

    fig = px.bar(
        reason,
        x                       = 'total',
        y                       = 'search_reason',
        orientation             = 'h',
        title                   = '🔍 Search Reason Breakdown',
        color_discrete_sequence = [COLORS['blue']],
        text                    = 'total',
    )
    fig.update_traces(
        texttemplate = '%{text:,}',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title = 'Number of Searches',
        yaxis_title = '',
        yaxis       = dict(autorange='reversed'),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_search_type(where, params_tuple):
        return q.get_search_by_type(where, dict(params_tuple))

    stype = load_search_type(where, params_tuple)

    fig = px.pie(
        stype,
        names  = 'search_type',
        values = 'total',
        hole   = 0.4,
        title  = '🔍 Search Type Breakdown',
        color_discrete_sequence = list(COLORS.values()),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 3 — Search disposition + Search outcome
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_disposition(where, params_tuple):
        return q.get_search_by_disposition(where, dict(params_tuple))

    disposition = load_disposition(where, params_tuple)

    fig = px.bar(
        disposition,
        x                       = 'total',
        y                       = 'search_disposition',
        orientation             = 'h',
        title                   = '📦 Search Disposition',
        color_discrete_sequence = [COLORS['teal']],
        text                    = 'total',
    )
    fig.update_traces(
        texttemplate = '%{text:,}',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title = 'Number of Searches',
        yaxis_title = '',
        yaxis       = dict(autorange='reversed'),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_outcome(where, params_tuple):
        return q.get_search_by_outcome(where, dict(params_tuple))

    outcome = load_outcome(where, params_tuple)

    fig = px.pie(
        outcome,
        names  = 'search_outcome',
        values = 'total',
        hole   = 0.4,
        title  = '📋 Search Outcome',
        color  = 'search_outcome',
        color_discrete_map = {
            'Citation'       : COLORS['orange'],
            'Warning'        : COLORS['yellow'],
            'Arrest'         : COLORS['red'],
            'SERO'           : COLORS['teal'],
            'Not Applicable' : COLORS['gray'],
        }
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 4 — Search rate by district + Arrest type
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_search_district(where, params_tuple):
        return q.get_search_rate_by_district(where, dict(params_tuple))

    search_dist = load_search_district(where, params_tuple)
    search_dist['district_name'] = \
        search_dist['district_number'].map({
            1: '1 - Rockville',
            2: '2 - Bethesda',
            3: '3 - Silver Spring',
            4: '4 - Wheaton',
            5: '5 - Germantown',
            6: '6 - Gaithersburg',
        })

    fig = px.bar(
        search_dist.sort_values('search_rate'),
        x                      = 'search_rate',
        y                      = 'district_name',
        orientation            = 'h',
        title                  = '🌆 Search Rate by District (%)',
        color                  = 'search_rate',
        color_continuous_scale = ['#e3f2fd', '#2196F3'],
        text                   = 'search_rate',
    )
    fig.update_traces(
        texttemplate = '%{text}%',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title         = 'Search Rate %',
        yaxis_title         = '',
        coloraxis_showscale = False,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_arrest_type(where, params_tuple):
        return q.get_arrest_type_breakdown(where, dict(params_tuple))

    arrest_type = load_arrest_type(where, params_tuple)

    fig = px.bar(
        arrest_type,
        x                       = 'total',
        y                       = 'arrest_type_desc',
        orientation             = 'h',
        title                   = '🚔 Arrest Type Breakdown',
        color_discrete_sequence = [COLORS['purple']],
        text                    = 'total',
    )
    fig.update_traces(
        texttemplate = '%{text:,}',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title = 'Number of Stops',
        yaxis_title = '',
        yaxis       = dict(autorange='reversed'),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")