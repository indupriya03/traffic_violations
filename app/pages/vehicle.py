# pages/5_vehicle.py
import streamlit as st
import plotly.express as px
import pandas as pd
import queries as q
from filters import render_page_filters, build_where_clause
from utils.charts import COLORS, apply_theme, render_sidebar, kpi_card

st.set_page_config(
    page_title = "Vehicle Analysis",
    page_icon  = "🚙",
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
st.title("🚙 Vehicle Analysis")
st.caption("Vehicle make, model, color and age analysis")
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
    show_vehicle_type       = True,
    show_location           = False,
)
where, params = build_where_clause(filters)
params_tuple  = tuple(sorted(params.items()))

st.divider()

# ============================================================
# ROW 1 — KPIs
# ============================================================
@st.cache_data
def load_vehicle_kpis(where, params_tuple):
    params = dict(params_tuple)

    total = q.run_query(f"""
        SELECT COUNT(DISTINCT ts.stop_id) as cnt
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
    """, params=params)['cnt'].iloc[0]

    top_make = q.run_query(f"""
        SELECT dv.make, COUNT(*) as cnt
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.make != 'UNKNOWN'
        GROUP BY dv.make
        ORDER BY cnt DESC
        LIMIT 1
    """, params=params)

    top_color = q.run_query(f"""
        SELECT dv.color, COUNT(*) as cnt
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.color != 'UNKNOWN'
        GROUP BY dv.color
        ORDER BY cnt DESC
        LIMIT 1
    """, params=params)

    avg_age = q.run_query(f"""
        SELECT ROUND(AVG(
            YEAR(ts.stop_timestamp) - dv.year
        ), 1) as avg_age
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.year IS NOT NULL
        AND YEAR(ts.stop_timestamp) - dv.year BETWEEN 0 AND 30
    """, params=params)

    return {
        'total'    : total,
        'top_make' : top_make['make'].iloc[0] \
                     if len(top_make) > 0 else 'N/A',
        'top_color': top_color['color'].iloc[0] \
                     if len(top_color) > 0 else 'N/A',
        'avg_age'  : avg_age['avg_age'].iloc[0] \
                     if len(avg_age) > 0 else 0,
    }

kpis = load_vehicle_kpis(where, params_tuple)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("🚗 Total Stops",
             f"{kpis['total']:,}",
             color=COLORS['blue'])
with col2:
    kpi_card("🏆 Top Make",
             kpis['top_make'],
             color=COLORS['teal'])
with col3:
    kpi_card("🎨 Top Color",
             kpis['top_color'],
             color=COLORS['purple'])
with col4:
    kpi_card("📅 Avg Vehicle Age",
             f"{kpis['avg_age']} years",
             color=COLORS['orange'])

st.divider()

# ============================================================
# ROW 2 — Top makes + Top colors
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_makes(where, params_tuple):
        return q.get_top_makes(where, dict(params_tuple))

    makes = load_makes(where, params_tuple)

    fig = px.bar(
        makes,
        x                       = 'stops',
        y                       = 'make',
        orientation             = 'h',
        title                   = '🏆 Top 15 Vehicle Makes',
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
    def load_colors(where, params_tuple):
        return q.get_top_colors(where, dict(params_tuple))

    colors_df = load_colors(where, params_tuple)

    # Map color names to actual colors
    color_map = {
        'BLACK'        : '#212121',
        'WHITE'        : '#F5F5F5',
        'SILVER'       : '#9E9E9E',
        'GRAY'         : '#757575',
        'RED'          : '#F44336',
        'BLUE'         : '#2196F3',
        'GREEN'        : '#4CAF50',
        'GOLD'         : '#FFC107',
        'DARK BLUE'    : '#0D47A1',
        'MAROON'       : '#B71C1C',
        'TAN'          : '#D2B48C',
        'LIGHT BLUE'   : '#90CAF9',
        'DARK GREEN'   : '#1B5E20',
        'BEIGE'        : '#F5F5DC',
        'BROWN'        : '#795548',
        'YELLOW'       : '#FFEB3B',
        'ORANGE'       : '#FF9800',
        'BRONZE'       : '#CD7F32',
        'PURPLE'       : '#9C27B0',
        'CREAM'        : '#FFFDD0',
    }

    fig = px.bar(
        colors_df,
        x     = 'stops',
        y     = 'color',
        orientation = 'h',
        title = '🎨 Stops by Vehicle Color',
        color = 'color',
        color_discrete_map = color_map,
        text  = 'stops',
    )
    fig.update_traces(
        texttemplate = '%{text:,}',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title  = 'Number of Stops',
        yaxis_title  = '',
        yaxis        = dict(autorange='reversed'),
        showlegend   = False,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 3 — Vehicle category + Vehicle age
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_category(where, params_tuple):
        return q.get_vehicle_category(where, dict(params_tuple))

    category = load_category(where, params_tuple)

    fig = px.pie(
        category.head(8),
        names  = 'vehicle_category',
        values = 'stops',
        hole   = 0.4,
        title  = '🚗 Vehicle Category Breakdown',
        color_discrete_sequence = list(COLORS.values()),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_age(where, params_tuple):
        return q.get_vehicle_age(where, dict(params_tuple))

    age = load_age(where, params_tuple)

    fig = px.bar(
        age,
        x                       = 'vehicle_age',
        y                       = 'stops',
        title                   = '📅 Vehicle Age at Time of Stop',
        color_discrete_sequence = [COLORS['teal']],
    )
    # Shade age groups
    fig.add_vrect(
        x0=-0.5, x1=3.5,
        fillcolor=COLORS['green'],
        opacity=0.1,
        annotation_text='New (0-3)',
        annotation_font_color=COLORS['green'],
        line_width=0,
    )
    fig.add_vrect(
        x0=3.5, x1=9.5,
        fillcolor=COLORS['orange'],
        opacity=0.1,
        annotation_text='Mid (4-9)',
        annotation_font_color=COLORS['orange'],
        line_width=0,
    )
    fig.add_vrect(
        x0=9.5, x1=30.5,
        fillcolor=COLORS['red'],
        opacity=0.1,
        annotation_text='Older (10+)',
        annotation_font_color=COLORS['red'],
        line_width=0,
    )
    fig.update_layout(
        xaxis_title = 'Vehicle Age (Years)',
        yaxis_title = 'Number of Stops',
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 4 — Accident rate by make
# ============================================================
@st.cache_data
def load_accident_rate(where, params_tuple):
    return q.get_accident_rate_by_make(where, dict(params_tuple))

accident = load_accident_rate(where, params_tuple)

fig = px.bar(
    accident.sort_values('accident_rate'),
    x                      = 'accident_rate',
    y                      = 'make',
    orientation            = 'h',
    title                  = '🚨 Accident Rate by Vehicle Make (%)',
    color                  = 'accident_rate',
    color_continuous_scale = ['#2196F3', '#F44336'],
    text                   = 'accident_rate',
)
fig.update_traces(
    texttemplate = '%{text}%',
    textposition = 'outside'
)
fig.update_layout(
    xaxis_title         = 'Accident Rate %',
    yaxis_title         = '',
    yaxis               = dict(autorange='reversed'),
    coloraxis_showscale = False,
)
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")