# app.py

# ============================================================
# 1. PAGE CONFIG — must be first!
# ============================================================
import streamlit as st
import queries as q
from utils.charts import kpi_card, COLORS, sidebar_kpi

st.set_page_config(
    page_title            = "Traffic Violations",
    page_icon             = "🚔",
    layout                = "wide",
    initial_sidebar_state = "expanded",
)


# ============================================================
# 2. CSS — second
# ============================================================
st.markdown("""
<style>
    .nav-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin: 5px 0;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
    }
    .nav-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    .nav-card h3 {
        margin: 0;
        font-size: 16px;
    }
    .nav-card p {
        margin: 5px 0 0 0;
        font-size: 13px;
        color: #555555;
    }
    /* Push page nav down */
    [data-testid="stSidebarNav"] {
        padding-top: 0px;
        margin-top: 10px;
    }

    /* Style page nav links */
    [data-testid="stSidebarNav"] a {
        color: #1a1a1a !important;
        font-size: 14px;
    }

    [data-testid="stSidebarNav"] a:hover {
        background-color: #e3f2fd !important;
        border-radius: 5px;
    }
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    h1, h2, h3 { color: #1a1a1a !important; }
    hr { border-color: #e0e0e0 !important; }
    
    
</style>

""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. SIDEBAR — third
# ============================================================
with st.sidebar:

    # 🚔 TOP CARD (now truly at the top)
    st.sidebar.markdown("""
    <div style="
        background: linear-gradient(140deg, #42a5f5, #1e88e5); /* nice blue gradient */
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 8px 8px 12px rgba(0,0,0,0.2); /* soft shadow */
    ">
        <h1 style="color:white; margin:0; font-size:22px;">🚔 Traffic Violations</h1>
        <p style="color:#e3f2fd; margin:8px 0 0 0; font-size:14px;">
            Montgomery County, MD
        </p>
    </div>
    """, unsafe_allow_html=True)

    #  CUSTOM NAVIGATION
    st.markdown("### 📌 Navigation")

    st.page_link("app.py", label="🏠 Home")
    st.page_link("pages/overview.py",label="📊 Overview")
    st.page_link("pages/temporal.py", label="📊 Temporal Analysis")
    st.page_link("pages/violations.py", label="🚗 Violation Analysis")
    st.page_link("pages/geographic.py",label="📍 Geographic Analysis")
    st.page_link("pages/vehicle.py",label="🚗 Vehicle Analysis")
    st.page_link("pages/search.py",label="🔍 Search Analysis")
    st.page_link("pages/demographics.py",label="👥 Demographics Analysis")


    st.divider()

sidebar_kpi("Data", "2012 — 2025", icon="📅", text_color="#000000",bg_color="white")
sidebar_kpi("Total Stops", "568,317", icon="🚗", text_color="#000000",bg_color="white")

# ============================================================
# 4. HOME PAGE CONTENT — fourth
# ============================================================
st.title("🚔 Montgomery County Traffic Violations")
st.caption("Interactive dashboard for traffic stop analysis — 2012 to 2025")
st.divider()

# KPIs
@st.cache_data
def load_kpis():
    return q.get_kpis()

kpis = load_kpis()

# KPIs section
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    kpi_card(
        "🚗 Total Stops",  
        f"{kpis['total_stops']:,}",  delta=" "
    )

with col2:
    kpi_card(
        "📋 Citations",    
        f"{kpis['total_citations']:,}",
        delta=f"{kpis['citation_rate_stop_level']:.1f}% of stops",
        color="blue"  # neutral, professional
    )
with col3:
    kpi_card(
        "⚠️ Warnings",
        f"{kpis['total_warnings']:,}", 
    )
    
with col4:
    kpi_card(
        "🔍 Searches",     
        f"{kpis['total_searches']:,}",
        delta=f"{kpis['search_rate']:.1f}%"
    )
with col5:
    kpi_card(
        "⛓ Arrests",      
        f"{kpis['total_arrests']:,}",
        delta=f"{kpis['arrest_rate']:.1f}%"
    )
with col6:
    kpi_card(
        "💀 Fatalities",   
        f"{kpis['fatal_accidents']:,}",
        delta=f"{kpis['fatality_rate']:.2f}%"    
    )

st.divider()


# -----------------------------
# Homepage nav cards
# -----------------------------
# Replace nav cards section in app.py

st.subheader("📌 Dashboard Pages")

# Row 1 — 4 cards
col1, col2, col3, col4 = st.columns(4)

pages_row1 = [
    ("pages/overview.py",   "📊", "Overview",   "KPIs and summary statistics",        "Summary"),
    ("pages/Temporal.py",   "📅", "Temporal",   "Trends over time",                   "Trends"),
    ("pages/Violations.py", "⚖️", "Violations", "Citation and warning analysis",       "Analysis"),
    ("pages/Geographic.py", "🌆", "Geographic", "Hotspots, districts and locations",   "Map"),
]

for col, (path, icon, title, desc, badge) in zip(
    [col1, col2, col3, col4], pages_row1
):
    with col:
        st.markdown(f"""
        <div style="
            background:#ffffff;
            border: 0.5px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px 16px;
            min-height: 130px;
        ">
            <div style="font-size:24px">{icon}</div>
            <h3 style="font-size:14px; font-weight:600;
                       color:#1a1a1a; margin:8px 0 4px;">{title}</h3>
            <p style="font-size:12px; color:#666666; margin:0">{desc}</p>
            <span style="
                display:inline-block;
                font-size:11px;
                padding:2px 8px;
                border-radius:99px;
                margin-top:8px;
                background:#e3f2fd;
                color:#1565c0;
            ">{badge}</span>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(path, label=f"Open {title}",
                     use_container_width=True)

st.write("")

# Row 2 — 3 cards
col5, col6, col7 = st.columns(3)

pages_row2 = [
    ("pages/Vehicle.py",      "🚙", "Vehicle",      "Make, model, color and age",        "Vehicle"),
    ("pages/Search.py",       "🔍", "Search",        "Search rates, contraband, arrests",  "Enforcement"),
    ("pages/Demographics.py", "👤", "Demographics",  "Race and gender stop analysis",      "Demographics"),
]

for col, (path, icon, title, desc, badge) in zip(
    [col5, col6, col7], pages_row2
):
    with col:
        st.markdown(f"""
        <div style="
            background:#ffffff;
            border: 0.5px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px 16px;
            min-height: 130px;
        ">
            <div style="font-size:24px">{icon}</div>
            <h3 style="font-size:14px; font-weight:600;
                       color:#1a1a1a; margin:8px 0 4px;">{title}</h3>
            <p style="font-size:12px; color:#666666; margin:0">{desc}</p>
            <span style="
                display:inline-block;
                font-size:11px;
                padding:2px 8px;
                border-radius:99px;
                margin-top:8px;
                background:#e3f2fd;
                color:#1565c0;
            ">{badge}</span>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(path, label=f"Open {title}",
                     use_container_width=True)
# Footer
st.divider()
st.caption("Montgomery County Traffic Violations | 2012 - 2025")
