# pages/7_demographics.py
import streamlit as st
import plotly.express as px
import pandas as pd
import queries as q
from filters import render_page_filters, build_where_clause
from utils.charts import COLORS, apply_theme, render_sidebar, kpi_card

st.set_page_config(
    page_title = "Demographics Analysis",
    page_icon  = "👤",
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
st.title("👤 Demographics Analysis")
st.caption("Race and gender analysis of traffic stops")
st.divider()

# ============================================================
# FILTERS
# ============================================================
filters = render_page_filters(
    show_year               = True,
    show_time               = False,
    show_days               = False,
    show_district           = True,
    show_violation_type     = True,
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
def load_demo_kpis(where, params_tuple):
    params = dict(params_tuple)

    total = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
    """, params=params)['cnt'].iloc[0]

    top_race = q.run_query(f"""
        SELECT dv.race, COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.race != 'UNKNOWN'
        GROUP BY dv.race
        ORDER BY cnt DESC
        LIMIT 1
    """, params=params)

    male_stops = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        {'AND' if where else 'WHERE'} dv.gender = 'M'
    """, params=params)['cnt'].iloc[0]

    female_stops = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        {'AND' if where else 'WHERE'} dv.gender = 'F'
    """, params=params)['cnt'].iloc[0]

    return {
        'total'       : total,
        'top_race'    : top_race['race'].iloc[0] \
                        if len(top_race) > 0 else 'N/A',
        'male_stops'  : male_stops,
        'female_stops': female_stops,
        'male_pct'    : round(male_stops/total*100, 1) \
                        if total > 0 else 0,
        'female_pct'  : round(female_stops/total*100, 1) \
                        if total > 0 else 0,
    }

kpis = load_demo_kpis(where, params_tuple)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("🚗 Total Stops",
             f"{kpis['total']:,}",
             color=COLORS['blue'])
with col2:
    kpi_card("Most Stopped Ethnicity",
             kpis['top_race'],
             color=COLORS['purple'])
with col3:
    kpi_card("👨 Male Stops",
             f"{kpis['male_stops']:,}",
             delta=f"{kpis['male_pct']}% of stops",
             color=COLORS['teal'])
with col4:
    kpi_card("👩 Female Stops",
             f"{kpis['female_stops']:,}",
             delta=f"{kpis['female_pct']}% of stops",
             color=COLORS['orange'])

st.divider()

# ============================================================
# ROW 2 — Stops by race + Stops by gender
# ============================================================
col1, col2 = st.columns([2, 1])

with col1:
    @st.cache_data
    def load_race(where, params_tuple):
        return q.get_stops_by_race(where, dict(params_tuple))

    race = load_race(where, params_tuple)

    fig = px.bar(
        race,
        x                       = 'stops',
        y                       = 'race',
        orientation             = 'h',
        title                   = '👤 Stops by Ethnicity',
        color_discrete_sequence = [COLORS['blue']],
        text                    = 'stops',
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

with col2:
    @st.cache_data
    def load_gender(where, params_tuple):
        return q.get_stops_by_gender(where, dict(params_tuple))

    gender = load_gender(where, params_tuple)

    fig = px.pie(
        gender,
        names  = 'gender',
        values = 'stops',
        hole   = 0.4,
        title  = '👤 Stops by Gender',
        color  = 'gender',
        color_discrete_map = {
            'M' : COLORS['blue'],
            'F' : COLORS['orange'],
            'U' : COLORS['gray'],
        }
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 3 — Search rate by race + Arrest rate by race
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_search_race(where, params_tuple):
        return q.get_search_rate_by_race(where, dict(params_tuple))

    search_race = load_search_race(where, params_tuple)

    fig = px.bar(
        search_race.sort_values('search_rate'),
        x                      = 'search_rate',
        y                      = 'race',
        orientation            = 'h',
        title                  = '🔍 Search Rate by Ethnicity (%)',
        color                  = 'search_rate',
        color_continuous_scale = ['#e3f2fd', '#2196F3'],
        text                   = 'search_rate',
    )
    # Average line
    avg = search_race['search_rate'].mean()
    fig.add_vline(
        x                     = avg,
        line_dash             = 'dash',
        line_color            = COLORS['red'],
        annotation_text       = f'Avg: {avg:.1f}%',
        annotation_font_color = COLORS['red'],
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
    def load_arrest_race(where, params_tuple):
        return q.get_arrest_rate_by_race(where, dict(params_tuple))

    arrest_race = load_arrest_race(where, params_tuple)

    fig = px.bar(
        arrest_race.sort_values('arrest_rate'),
        x                      = 'arrest_rate',
        y                      = 'race',
        orientation            = 'h',
        title                  = '⛓ Arrest Rate by Ethnicity (%)',
        color                  = 'arrest_rate',
        color_continuous_scale = ['#fff3e0', '#F44336'],
        text                   = 'arrest_rate',
    )
    avg = arrest_race['arrest_rate'].mean()
    fig.add_vline(
        x                     = avg,
        line_dash             = 'dash',
        line_color            = COLORS['red'],
        annotation_text       = f'Avg: {avg:.1f}%',
        annotation_font_color = COLORS['red'],
    )
    fig.update_traces(
        texttemplate = '%{text}%',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title         = 'Arrest Rate %',
        yaxis_title         = '',
        coloraxis_showscale = False,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 4 — Search rate by gender + Violation by race
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_search_gender(where, params_tuple):
        return q.get_search_rate_by_gender(where, dict(params_tuple))

    search_gender = load_search_gender(where, params_tuple)

    fig = px.bar(
        search_gender,
        x                      = 'gender',
        y                      = 'search_rate',
        title                  = '🔍 Search Rate by Gender (%)',
        color                  = 'gender',
        color_discrete_map     = {
            'M': COLORS['blue'],
            'F': COLORS['orange'],
        },
        text                   = 'search_rate',
    )
    fig.update_traces(
        texttemplate = '%{text}%',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title = 'Gender',
        yaxis_title = 'Search Rate %',
        showlegend  = False,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_violation_race(where, params_tuple):
        return q.get_violation_by_race(where, dict(params_tuple))

    viol_race = load_violation_race(where, params_tuple)

    # Top violation per race
    top_per_race = (
        viol_race.groupby('race')
        .apply(lambda x: x.nlargest(1, 'total'))
        .reset_index(drop=True)
    )

    fig = px.bar(
        top_per_race,
        x                       = 'race',
        y                       = 'total',
        color                   = 'violation_category',
        title                   = '⚖️ Top Violation by Ethnicity',
        color_discrete_sequence = list(COLORS.values()),
        text                    = 'violation_category',
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title = 'Race',
        yaxis_title = 'Number of Charges',
        showlegend  = True,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 5 — Race x Gender heatmap
# ============================================================
st.subheader("🔥 Search Rate by Race and Gender")

@st.cache_data
def load_race_gender(where, params_tuple):
    return q.get_search_rate_race_gender(where, dict(params_tuple))

race_gender = load_race_gender(where, params_tuple)

fig = px.density_heatmap(
    race_gender,
    x                      = 'gender',
    y                       = 'race',
    z                       = 'search_rate',
    title                   = '🔥 Search Rate by Ethnicity and Gender (%)',
    color_continuous_scale  = ['#ffffff', '#2196F3', '#0D47A1'],
    text_auto               = True,
)
fig.update_layout(
    xaxis_title = 'Gender',
    yaxis_title = 'Race',
)
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")