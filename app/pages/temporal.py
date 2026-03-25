# pages/2_temporal.py
import streamlit as st
import plotly.express as px
import queries as q
from filters import render_page_filters, build_where_clause
from utils.charts import COLORS, apply_theme, render_sidebar

st.set_page_config(
    page_title = "Temporal Analysis",
    page_icon  = "📅",
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
st.title("📅 Temporal Analysis")
st.caption("Traffic stop trends over time")
st.divider()

# ============================================================
# FILTERS
# ============================================================
filters = render_page_filters(
    show_year               = True,
    show_time               = True,
    show_days               = True,
    show_district           = False,
    show_violation_type     = False,
    show_violation_category = False,
    show_vehicle_type       = False,
    show_location           = False,
)
where, params = build_where_clause(filters)
params_tuple  = tuple(sorted(params.items()))

st.divider()



# ============================================================
# ROW 1 — Yearly trend
# ============================================================
st.subheader("📈 Stops by Year")

@st.cache_data
def load_yearly(where, params_tuple):
    return q.get_yearly_trend(where, dict(params_tuple))

yearly = load_yearly(where, params_tuple)
yearly = yearly[yearly['year'] <= 2024]

fig = px.bar(
    yearly,
    x                       = 'year',
    y                       = 'stops',
    title                   = 'Traffic Stops by Year',
    color_discrete_sequence = [COLORS['blue']],
)
fig.add_vline(
    x                     = 2020,
    line_dash             = 'dash',
    line_color            = COLORS['red'],
    annotation_text       = 'COVID-19',
    annotation_font_color = COLORS['red']
)
fig.update_layout(
    xaxis_title = 'Year',
    yaxis_title = 'Number of Stops',
)
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 2 — Monthly trend + Day of week
# ============================================================
col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_monthly(where, params_tuple):
        return q.get_monthly_trend(where, dict(params_tuple))

    monthly = load_monthly(where, params_tuple)
    monthly['month_year'] = (
        monthly['year'].astype(str) + '-' +
        monthly['month'].astype(str).str.zfill(2)
    )

    fig = px.line(
        monthly,
        x                       = 'month_year',
        y                       = 'stops',
        title                   = 'Monthly Trend',
        color_discrete_sequence = [COLORS['blue']],
    )
    fig.update_layout(
        xaxis_title      = 'Month',
        yaxis_title      = 'Number of Stops',
        xaxis_tickangle  = -45,
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    @st.cache_data
    def load_dow(where, params_tuple):
        return q.get_day_of_week(where, dict(params_tuple))

    dow = load_dow(where, params_tuple)

    fig = px.bar(
        dow,
        x                       = 'day_of_week',
        y                       = 'stops',
        title                   = 'Stops by Day of Week',
        color_discrete_sequence = [COLORS['teal']],
    )
    fig.update_layout(
        xaxis_title = 'Day',
        yaxis_title = 'Number of Stops',
    )
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 3 — Hourly trend
# ============================================================
st.subheader("🕐 Stops by Hour of Day")

@st.cache_data
def load_hourly(where, params_tuple):
    return q.get_hourly_trend(where, dict(params_tuple))

hourly = load_hourly(where, params_tuple)

fig = px.line(
    hourly,
    x                       = 'hour',
    y                       = 'stops',
    title                   = 'Stops by Hour of Day',
    color_discrete_sequence = [COLORS['purple']],
    markers                 = True,
)
fig.update_layout(
    xaxis_title  = 'Hour',
    yaxis_title  = 'Number of Stops',
    xaxis        = dict(tickmode='linear', dtick=1),
)

# Annotate peaks
fig.add_vline(x=8,  line_dash='dash', line_color=COLORS['orange'],
              annotation_text='Morning Peak',
              annotation_font_color=COLORS['orange'])
fig.add_vline(x=16, line_dash='dash', line_color=COLORS['green'],
              annotation_text='Evening Peak',
              annotation_font_color=COLORS['green'])
fig.add_vline(x=3,  line_dash='dash', line_color=COLORS['red'],
              annotation_text='DUI Peak',
              annotation_font_color=COLORS['red'])

apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# ROW 4 — Violation by hour heatmap
# ============================================================
st.subheader("🔥 Violation Category by Hour")

@st.cache_data
def load_violation_hour(where, params_tuple):
    return q.get_violation_by_hour(where, dict(params_tuple))

viol_hour = load_violation_hour(where, params_tuple)

fig = px.density_heatmap(
    viol_hour,
    x                      = 'hour',
    y                       = 'violation_category',
    z                       = 'total',
    title                   = 'Violation Category by Hour',
    color_continuous_scale  = ['#ffffff', '#2196F3', '#0D47A1'],
)
fig.update_layout(
    xaxis_title = 'Hour of Day',
    yaxis_title = 'Violation Category',
)
apply_theme(fig)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")