# pages/4_geographic.py
import streamlit as st
import plotly.express as px
import pandas as pd
import queries as q
from filters import render_page_filters, build_where_clause
from utils.charts import COLORS, apply_theme, render_sidebar, kpi_card

st.set_page_config(
    page_title = "Geographic Analysis",
    page_icon  = "🌆",
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
st.title("🌆 Geographic Analysis")
st.caption("Traffic stop hotspots, districts and locations")
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
    show_location           = True,
)
where, params = build_where_clause(filters)
params_tuple  = tuple(sorted(params.items()))

st.divider()

# ============================================================
# ROW 1 — KPIs
# ============================================================
DISTRICT_MAP = {
    1: 'Rockville',
    2: 'Bethesda',
    3: 'Silver Spring',
    4: 'Wheaton',
    5: 'Germantown',
    6: 'Gaithersburg',
}
@st.cache_data
def load_kpis():
    return q.get_kpis()

kpis = load_kpis()

col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card(
        "🚗 Total Stops",
        f"{kpis['total_stops']:,}",
    )

with col2:
    kpi_card(
        "📍 Top Location",
        kpis['top_location'],
        
    )

with col3:
    kpi_card(
        "🧊 Least Active District",
        DISTRICT_MAP.get(kpis['least_active_district']),    )

with col4:
    kpi_card(
        "🌆 Busiest District",
        DISTRICT_MAP.get(kpis['most_active_district']),
       
    )
st.divider()

# ============================================================
# ROW 2 — Stops by district + Location type
# ============================================================
col1, col2 = st.columns([2, 1])

with col1:
    @st.cache_data
    def load_district(where, params_tuple):
        return q.get_stops_by_district(where, dict(params_tuple))

    district = load_district(where, params_tuple)
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
        title                   = '🌆 Stops by District',
        color                   = 'stops',
        color_continuous_scale  = ['#e3f2fd', '#2196F3'],
        text                    = 'stops',
    )
    fig.update_traces(
        texttemplate = '%{text:,}',
        textposition = 'outside'
    )
    fig.update_layout(
        xaxis_title         = 'District',
        yaxis_title         = 'Number of Stops',
        xaxis_tickangle     = -15,
        coloraxis_showscale = False,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_loc_type(where, params_tuple):
        return q.get_stops_by_loc_type(where, dict(params_tuple))

    loc_type = load_loc_type(where, params_tuple)

    fig = px.pie(
        loc_type,
        names  = 'loc_type',
        values = 'stops',
        hole   = 0.4,
        title  = '📍 Location Type',
        color_discrete_sequence = [
            COLORS['blue'],
            COLORS['teal'],
            COLORS['purple'],
        ]
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 3 — Citation rate by district
# ============================================================
@st.cache_data
def load_citation_district(where, params_tuple):
    return q.get_citation_rate_by_district(where, dict(params_tuple))

citation_dist = load_citation_district(where, params_tuple)
citation_dist['district_name'] = citation_dist['district_number'].map({
    1: '1 - Rockville',
    2: '2 - Bethesda',
    3: '3 - Silver Spring',
    4: '4 - Wheaton',
    5: '5 - Germantown',
    6: '6 - Gaithersburg',
})

fig = px.bar(
    citation_dist.sort_values('citation_rate'),
    x                      = 'citation_rate',
    y                      = 'district_name',
    orientation            = 'h',
    title                  = '📊 Citation Rate by District (%)',
    color                  = 'citation_rate',
    color_continuous_scale = ['#2196F3', '#F44336'],
    text                   = 'citation_rate',
)
fig.update_traces(
    texttemplate = '%{text}%',
    textposition = 'outside'
)
fig.update_layout(
    xaxis_title         = 'Citation Rate %',
    yaxis_title         = '',
    coloraxis_showscale = False,
)
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 4 — Top hotspot locations
# ============================================================
st.subheader("🔥 Top 20 Hotspot Locations")

@st.cache_data
def load_top_locations(where, params_tuple):
    return q.get_top_locations(where, dict(params_tuple))

locations = load_top_locations(where, params_tuple)

fig = px.bar(
    locations,
    x                       = 'stops',
    y                       = 'location_clean',
    orientation             = 'h',
    title                   = '📍 Top 20 Hotspot Locations',
    color_discrete_sequence = [COLORS['teal']],
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
    height      = 600,
)
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 5 — Map
# ============================================================
st.subheader("🗺️ Stop Locations Map")

@st.cache_data
def load_hotspots(where, params_tuple):
    return q.get_hotspots(where, dict(params_tuple))

hotspots = load_hotspots(where, params_tuple)
hotspots = hotspots.dropna(subset=['latitude', 'longitude'])

if len(hotspots) > 0:
    fig = px.scatter_mapbox(
        hotspots,
        lat             = 'latitude',
        lon             = 'longitude',
        size            = 'stops',
        color           = 'stops',
        color_continuous_scale = ['#e3f2fd', '#2196F3', '#0D47A1'],
        size_max        = 20,
        zoom            = 10,
        title           = '🗺️ Traffic Stop Density Map',
        mapbox_style    = 'carto-positron',
        hover_data      = {'stops': True},
    )
    fig.update_layout(
        height              = 500,
        coloraxis_showscale = True,
        margin              = dict(l=0, r=0, t=40, b=0),
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No location data available for selected filters")

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")