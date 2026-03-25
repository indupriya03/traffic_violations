# utils/charts.py
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os



# ============================================================
# LIGHT THEME TEMPLATE
# ============================================================
LIGHT_TEMPLATE = dict(
    layout=go.Layout(
        paper_bgcolor = '#ffffff',
        plot_bgcolor  = '#f8f9fa',
        font          = dict(color='#1a1a1a', size=12),
        title         = dict(font=dict(color='#1a1a1a', size=16)),
        xaxis         = dict(
            gridcolor = '#e0e0e0',
            linecolor = '#e0e0e0',
            tickcolor = '#666666',
            tickfont  = dict(color='#666666'),
        ),
        yaxis         = dict(
            gridcolor = '#e0e0e0',
            linecolor = '#e0e0e0',
            tickcolor = '#666666',
            tickfont  = dict(color='#666666'),
        ),
        legend        = dict(
            bgcolor     = '#ffffff',
            bordercolor = '#e0e0e0',
            font        = dict(color='#1a1a1a'),
        ),
        colorway = [
            '#2196F3', '#4CAF50', '#F44336',
            '#9C27B0', '#FF9800', '#00BCD4',
        ],
    )
)

# ============================================================
# COLOR PALETTE
# ============================================================
COLORS = {
    'yellow' : '#FFC107',
    'purple' : '#9C27B0',
    'orange' : '#FF9800',
    'teal'   : '#00BCD4',
    'gray'   : '#9E9E9E',
    'blue'   : '#2196F3',
    'green'  : '#4CAF50',
    'red'    : '#F44336',

}

COLOR_SEQUENCE = list(COLORS.values())

# Use LIGHT_TEMPLATE as default
DARK_TEMPLATE = LIGHT_TEMPLATE  # alias for compatibility

# ============================================================
# HELPER
# ============================================================
def apply_theme(fig):
    fig.update_layout(
        **LIGHT_TEMPLATE['layout'].to_plotly_json()
    )
    return fig

# ============================================================
# CHART FUNCTIONS
# ============================================================
def bar_chart(df, x, y, title='',
              color=None, horizontal=False,
              color_sequence=None):
    colors = color_sequence or [COLORS['blue']]
    if horizontal:
        fig = px.bar(
            df, x=y, y=x,
            title=title,
            orientation='h',
            color=color,
            color_discrete_sequence=colors
        )
        fig.update_layout(yaxis=dict(autorange='reversed'))
    else:
        fig = px.bar(
            df, x=x, y=y,
            title=title,
            color=color,
            color_discrete_sequence=colors
        )
    return apply_theme(fig)

def line_chart(df, x, y, title='', color=None):
    fig = px.line(
        df, x=x, y=y,
        title=title,
        color=color,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    fig.update_traces(line=dict(width=2))
    return apply_theme(fig)

def pie_chart(df, names, values, title='', hole=0.4):
    fig = px.pie(
        df, names=names, values=values,
        title=title,
        hole=hole,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return apply_theme(fig)

def scatter_chart(df, x, y, title='',
                  color=None, size=None):
    fig = px.scatter(
        df, x=x, y=y,
        title=title,
        color=color,
        size=size,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    return apply_theme(fig)

def heatmap_chart(df, x, y, z, title=''):
    fig = px.density_heatmap(
        df, x=x, y=y, z=z,
        title=title,
        color_continuous_scale=[
            COLORS['blue'], COLORS['purple'], COLORS['red']
        ]
    )
    return apply_theme(fig)

# ===============================
# KPI CARD DESIGN
# ===============================


def kpi_card(title, value, delta=None, color="#2196F3"):
    st.markdown(f"""
    <div style="
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 10px;
        align-items: center;   /* centers text horizontally */
        text-align: center;    /* ensures multi-line text is centered */
        box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        white-space: nowrap;
        overflow: hidden;
        flex: 1;
        min-width: 0;
        min-height: 180px;
    ">
        <h4 style="margin:0; color:#555555; font-size:clamp(12px,1.2vw,16px);">{title}</h4>
        <h2 style="margin:5px 0; color:{color}; font-size:clamp(12px,1.5vw,22px);">{value}</h2>
        {f'<p style="margin:-2px; color:#555555; font-size:13px;">{delta}</p>' if delta else ""}
    </div>
    """, unsafe_allow_html=True)

# ===============================
#  MINI KPI CARD FOR SIDEBAR
# ===============================

def sidebar_kpi(title, value, icon="📌", text_color="black",bg_color="white"):
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(140deg, {bg_color}, #ADD8E6); /* gradient for modern look */
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2); /* soft shadow */
        margin-bottom: 12px;
        text-align: center;
        min-width: 0;
    ">
        <p style="margin:0; font-size:16px; color:{text_color}; font-weight:500;">{icon} {title}</p>
        <h3 style="margin:5px 0 0 0; color:{text_color}; font-size:18px; font-weight:600;">{value}</h3>
    </div>
    """, unsafe_allow_html=True)

# ===============================
#  RENDER SIDEBAR
# ===============================

def render_sidebar():
    st.markdown("""
    <style>
        /* Hide default page links */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Style custom page links */
        [data-testid="stSidebarContent"] a {
            color: #1a1a1a !important;
            text-decoration: none !important;
        }

        /* Page link button style */
        [data-testid="stPageLink"] > a {
            background-color: #f8f9fa !important;
            border: 0.5px solid #e0e0e0 !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            color: #1a1a1a !important;
            font-size: 14px !important;
            display: block !important;
            margin: 3px 0 !important;
        }

        [data-testid="stPageLink"] > a:hover {
            background-color: #e3f2fd !important;
            border-color: #2196F3 !important;
        }

        /* Active page highlight */
        [data-testid="stPageLink"][aria-current="page"] > a {
            background-color: #e3f2fd !important;
            border-color: #2196F3 !important;
            color: #2196F3 !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── Blue header card ───────────────────────────────────
    st.sidebar.markdown("""
    <div style="
        background-color: #2196F3;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    ">
        <div style="font-size:28px;">🚔</div>
        <h2 style="color:white; margin:4px 0 0; font-size:16px;
                   font-weight:600;">
            Traffic Violations
        </h2>
        <p style="color:#e3f2fd; margin:4px 0 0; font-size:11px;">
            Montgomery County, MD
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Navigation ─────────────────────────────────────────
    st.sidebar.markdown(
        "<p style='font-size:12px; color:#666; "
        "margin:8px 0 4px; font-weight:600;'>"
        "NAVIGATION</p>",
        unsafe_allow_html=True
    )

    pages = [
        ("app.py",                 "🏠", "Home"),
        ("pages/overview.py",      "📊", "Overview"),
        ("pages/temporal.py",      "📅", "Temporal"),
        ("pages/violations.py",    "⚖️", "Violations"),
        ("pages/geographic.py",    "🌆", "Geographic"),
        ("pages/vehicle.py",       "🚙", "Vehicle"),
        ("pages/search.py",        "🔍", "Search"),
        ("pages/demographics.py",  "👤", "Demographics"),
    ]

    for path, icon, label in pages:
        st.sidebar.page_link(
            path,
            label               = f"{icon} {label}",
            use_container_width = True,
        )

    # ── Footer ─────────────────────────────────────────────
    st.sidebar.divider()
    sidebar_kpi("Data", "2012 — 2025", icon="📅", text_color="#000000",bg_color="white")
    sidebar_kpi("Total Stops", "568,317", icon="🚗", text_color="#000000",bg_color="white")