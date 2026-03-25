# queries.py — optimized for Streamlit dashboard
import pandas as pd
from db import run_query
import streamlit as st

# ============================================================
# KPIs — cached for performance
# ============================================================
@st.cache_data(ttl=3600)
def get_kpis():
    """Return main KPIs with preformatted values."""
    total_stops = run_query("SELECT COUNT(*) as cnt FROM traffic_stop")['cnt'].iloc[0]
    total_citations = run_query("SELECT COUNT(*) as cnt FROM violation_charge WHERE violation_type = 'CITATION'")['cnt'].iloc[0]
    total_warnings = run_query("SELECT COUNT(*) as cnt FROM violation_charge WHERE violation_type = 'WARNING'")['cnt'].iloc[0]
    total_arrests = run_query("SELECT COUNT(*) as cnt FROM search_enforcement WHERE search_outcome = 'Arrest'")['cnt'].iloc[0]
    total_searches = run_query("SELECT COUNT(*) as cnt FROM search_enforcement WHERE search_conducted = 1")['cnt'].iloc[0]
    total_accidents = run_query("SELECT COUNT(*) as cnt FROM incident_safety WHERE accident = 1")['cnt'].iloc[0]
    fatal_accidents = run_query("SELECT COUNT(*) as cnt FROM incident_safety WHERE fatal = 1")['cnt'].iloc[0]
    total_charges= run_query("SELECT COUNT(*) as cnt FROM violation_charge")['cnt'].iloc[0]
     # Most active district
    most_active_df = run_query("""
        SELECT district_number, COUNT(*) AS total_stops
        FROM traffic_stop
        WHERE district_number IS NOT NULL
        GROUP BY district_number
        ORDER BY total_stops DESC
        LIMIT 1
    """)
    most_active_district = most_active_df.iloc[0]['district_number']

    # Least active district
    least_active_df = run_query("""
        SELECT district_number, COUNT(*) AS total_stops
        FROM traffic_stop
        WHERE district_number IS NOT NULL
        GROUP BY district_number
        ORDER BY total_stops ASC
        LIMIT 1
    """)
    least_active_district = least_active_df.iloc[0]['district_number']

    # Top location
    top_location_df = run_query("""
        SELECT UPPER(TRIM(location_clean)) AS top_location, COUNT(*) AS total_stops
        FROM traffic_stop
        WHERE location_clean IS NOT NULL
        GROUP BY location_clean
        ORDER BY total_stops DESC
        LIMIT 1
    """)
    top_location = top_location_df.iloc[0]['top_location']

    


    repair_orders= total_charges-total_citations-total_warnings
    return {
        'total_stops': total_stops,
        'total_citations': total_citations,
        'total_warnings': total_warnings,
        'total_arrests': total_arrests,
        'total_searches': total_searches,
        'total_accidents': total_accidents,
        'fatal_accidents': fatal_accidents,
        'total_charges' : total_charges,
        'repair_orders' : repair_orders,
 
        # Top/least/most active
        'most_active_district': most_active_district,
        'least_active_district': least_active_district,
        'top_location': top_location,

        # precomputed rates
        'citation_rate_stop_level': round(total_citations / total_stops * 100, 1),
        'citation_rate_charge_level': round(total_citations / total_charges * 100, 1),
    	'warnings_rate_charge_level':round(total_warnings / total_charges * 100, 1),
        'repair_order_rate' : round(repair_orders / total_charges*100,1),
        'arrest_rate': round(total_arrests / total_stops * 100, 1),
        'search_rate': round(total_searches / total_stops * 100, 1),
        'fatality_rate': round(fatal_accidents / total_stops * 100, 2)
    }


# queries.py — add this helper at the top

def _build_joins(where):
    """Auto detect which joins are needed based on WHERE clause"""
    joins = []
    if not where:
        return ''
    if 'vc.' in where:
        joins.append(
            "JOIN violation_charge vc ON ts.stop_id = vc.stop_id"
        )
    if 'dv.' in where:
        joins.append(
            "JOIN driver_vehicle dv ON ts.stop_id = dv.stop_id"
        )
    if 'se.' in where:
        joins.append(
            "JOIN search_enforcement se ON ts.stop_id = se.stop_id"
        )
    if 'ins.' in where:
        joins.append(
            "JOIN incident_safety ins ON ts.stop_id = ins.stop_id"
        )
    return '\n'.join(joins)

# ============================================================
# ROW 1 — Yearly trend (Temporal)
# ============================================================
@st.cache_data(ttl=3600)
def get_yearly_trend(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        return run_query("""
            SELECT 
                YEAR(stop_timestamp) as year,
                COUNT(*)             as stops
            FROM traffic_stop
            GROUP BY YEAR(stop_timestamp)
            ORDER BY year
        """)
    return run_query(f"""
        SELECT 
            YEAR(ts.stop_timestamp)    as year,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        {_build_joins(where)}
        {where}
        GROUP BY YEAR(ts.stop_timestamp)
        ORDER BY year
    """, params=params)
# ============================================================
# ROW 2 — Monthly trend + Day of week (Temporal)
# ============================================================
@st.cache_data(ttl=3600)
def get_monthly_trend(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        return run_query("""
            SELECT 
                YEAR(stop_timestamp)  as year,
                MONTH(stop_timestamp) as month,
                COUNT(*)              as stops
            FROM traffic_stop
            GROUP BY YEAR(stop_timestamp), MONTH(stop_timestamp)
            ORDER BY year, month
        """)
    return run_query(f"""
        SELECT 
            YEAR(ts.stop_timestamp)    as year,
            MONTH(ts.stop_timestamp)   as month,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        {_build_joins(where)}
        {where}
        GROUP BY YEAR(ts.stop_timestamp), MONTH(ts.stop_timestamp)
        ORDER BY year, month
    """, params=params)


@st.cache_data(ttl=3600)
def get_day_of_week(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        df = run_query("""
            SELECT 
                DAYNAME(stop_timestamp) as day_of_week,
                COUNT(*)                as stops
            FROM traffic_stop
            GROUP BY DAYNAME(stop_timestamp)
        """)
    else:
        df = run_query(f"""
            SELECT 
                DAYNAME(ts.stop_timestamp) as day_of_week,
                COUNT(DISTINCT ts.stop_id) as stops
            FROM traffic_stop ts
            {_build_joins(where)}
            {where}
            GROUP BY DAYNAME(ts.stop_timestamp)
        """, params=params)
    day_order = ['Monday','Tuesday','Wednesday',
                 'Thursday','Friday','Saturday','Sunday']
    df['day_of_week'] = pd.Categorical(
        df['day_of_week'], categories=day_order, ordered=True
    )
    return df.sort_values('day_of_week')
# ============================================================
# ROW 3 — Hourly trend (Temporal)
# ============================================================
@st.cache_data(ttl=3600)
def get_hourly_trend(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        return run_query("""
            SELECT 
                HOUR(stop_timestamp) as hour,
                COUNT(*)             as stops
            FROM traffic_stop
            GROUP BY HOUR(stop_timestamp)
            ORDER BY hour
        """)
    return run_query(f"""
        SELECT 
            HOUR(ts.stop_timestamp)    as hour,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        {_build_joins(where)}
        {where}
        GROUP BY HOUR(ts.stop_timestamp)
        ORDER BY hour
    """, params=params)

# ============================================================
# ROW 4 — Violation by hour heatmap (Temporal)
# ============================================================
@st.cache_data(ttl=3600)
def get_violation_by_hour(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)

    # No filters → simple, fast query
    if not where or not where.strip():
        return run_query("""
            SELECT
                HOUR(ts.stop_timestamp) as hour,
                vc.violation_category,
                COUNT(*) as total
            FROM traffic_stop ts
            JOIN violation_charge vc ON ts.stop_id = vc.stop_id
            GROUP BY HOUR(ts.stop_timestamp), vc.violation_category
            ORDER BY hour, total DESC
        """)

    # With filters → join only necessary tables dynamically
    joins = _build_joins(where)

    query = f"""
        SELECT
            HOUR(ts.stop_timestamp) as hour,
            vc.violation_category,
            COUNT(DISTINCT ts.stop_id) as total
        FROM traffic_stop ts
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {joins}
        {where}
        GROUP BY HOUR(ts.stop_timestamp), vc.violation_category
        ORDER BY hour, total DESC
    """

    return run_query(query, params=params)



# ============================================================
# ROW 2 — Top violations + Violation type pie (Violation)
# ============================================================
@st.cache_data(ttl=3600)
def get_violation_category(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        return run_query("""
            SELECT 
                violation_category,
                COUNT(*) as total
            FROM violation_charge
            GROUP BY violation_category
            ORDER BY total DESC
        """)
    return run_query(f"""
        SELECT 
            vc.violation_category,
            COUNT(*) as total
        FROM violation_charge vc
        JOIN traffic_stop ts ON vc.stop_id = ts.stop_id
        {where}
        GROUP BY vc.violation_category
        ORDER BY total DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_violation_type(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        return run_query("""
            SELECT violation_type, COUNT(*) as total
            FROM violation_charge
            GROUP BY violation_type
            ORDER BY total DESC
        """)
    return run_query(f"""
        SELECT 
            vc.violation_type,
            COUNT(*) as total
        FROM violation_charge vc
        JOIN traffic_stop ts ON vc.stop_id = ts.stop_id
        {where}
        GROUP BY vc.violation_type
        ORDER BY total DESC
    """, params=params)


# ============================================================
# ROW 3 — Citation rate by category
# ============================================================

@st.cache_data(ttl=3600)
def get_citation_rate(where='', params=None):
    return run_query(f"""
        SELECT
            vc.violation_category,
            SUM(CASE WHEN vc.violation_type = 'CITATION' THEN 1 ELSE 0 END) as citations,
            SUM(CASE WHEN vc.violation_type = 'WARNING'  THEN 1 ELSE 0 END) as warnings,
            COUNT(*) as total,
            ROUND(
                SUM(CASE WHEN vc.violation_type = 'CITATION' THEN 1 ELSE 0 END) /
                COUNT(*) * 100, 1
            ) as citation_rate
        FROM traffic_stop ts
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        WHERE vc.violation_type IN ('CITATION', 'WARNING')
        {('AND ' + where.replace('WHERE ', '')) if where else ''}
        GROUP BY vc.violation_category
        ORDER BY citation_rate DESC
    """, params=params)

# ============================================================
# ROW 4 — Violations by district + Violations by hour
# ============================================================
@st.cache_data(ttl=3600)
def get_violation_by_district(where='', params=None):
    return run_query(f"""
        SELECT
            ts.district_number,
            vc.violation_category,
            COUNT(*) as total
        FROM traffic_stop ts
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND ts.district_number IS NOT NULL
        GROUP BY ts.district_number, vc.violation_category
        ORDER BY ts.district_number, total DESC
    """, params=params)





@st.cache_data(ttl=3600)
def get_stops_by_district(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        return run_query("""
            SELECT
                district_number,
                COUNT(*) as stops
            FROM traffic_stop
            WHERE district_number IS NOT NULL
            GROUP BY district_number
            ORDER BY district_number
        """)
    return run_query(f"""
        SELECT
            ts.district_number,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        {_build_joins(where)}
        {where}
        AND ts.district_number IS NOT NULL
        GROUP BY ts.district_number
        ORDER BY ts.district_number
    """, params=params)




@st.cache_data(ttl=3600)
def get_top_makes(where='', params=None):
    return run_query(f"""
        SELECT
            dv.make,
            COUNT(*) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.make != 'UNKNOWN'
        GROUP BY dv.make
        ORDER BY stops DESC
        LIMIT 15
    """, params=params)

@st.cache_data(ttl=3600)
def get_top_colors(where='', params=None):
    if isinstance(params, tuple):
        params = dict(params)
    if not where or not where.strip():
        return run_query("""
            SELECT color, COUNT(*) as stops
            FROM driver_vehicle
            WHERE color != 'UNKNOWN'
            GROUP BY color
            ORDER BY stops DESC
        """)
    return run_query(f"""
        SELECT
            dv.color,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM driver_vehicle dv
        {_build_joins(where)}
        {where}
        AND dv.color != 'UNKNOWN'
        GROUP BY dv.color
        ORDER BY stops DESC
    """, params=params)


@st.cache_data(ttl=3600)
def get_stops_by_race(where='', params=None):
    return run_query(f"""
        SELECT
            dv.race,
            COUNT(*) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.race != 'UNKNOWN'
        GROUP BY dv.race
        ORDER BY stops DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_rate_by_district(where='', params=None):
    return run_query(f"""
        SELECT
            ts.district_number,
            ROUND(SUM(se.search_conducted) / COUNT(*) * 100, 1) as search_rate
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        JOIN driver_vehicle     dv ON ts.stop_id = dv.stop_id
        {where}
        AND ts.district_number IS NOT NULL
        GROUP BY ts.district_number
        ORDER BY search_rate DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_stops_by_loc_type(where='', params=None):
    return run_query(f"""
        SELECT
            ts.loc_type,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        {where}
        AND ts.loc_type IS NOT NULL
        GROUP BY ts.loc_type
        ORDER BY stops DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_citation_rate_by_district(where='', params=None):
    return run_query(f"""
        SELECT
            ts.district_number,
            COUNT(*) as total,
            SUM(CASE WHEN vc.violation_type = 'CITATION'
                THEN 1 ELSE 0 END) as citations,
            ROUND(
                SUM(CASE WHEN vc.violation_type = 'CITATION'
                    THEN 1 ELSE 0 END) /
                COUNT(*) * 100, 1
            ) as citation_rate
        FROM traffic_stop ts
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        {where}
        AND ts.district_number IS NOT NULL
        GROUP BY ts.district_number
        ORDER BY citation_rate DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_top_locations(where='', params=None):
    return run_query(f"""
        SELECT
            ts.location_clean,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        {where}
        GROUP BY ts.location_clean
        ORDER BY stops DESC
        LIMIT 20
    """, params=params)

@st.cache_data(ttl=3600)
def get_hotspots(where='', params=None):
    return run_query(f"""
        SELECT
            ts.latitude,
            ts.longitude,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        {where}
        AND ts.latitude  IS NOT NULL
        AND ts.longitude IS NOT NULL
        GROUP BY ts.latitude, ts.longitude
        ORDER BY stops DESC
        LIMIT 500
    """, params=params)

@st.cache_data(ttl=3600)
def get_vehicle_category(where='', params=None):
    return run_query(f"""
        SELECT
            dv.vehicle_category,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.vehicle_category != 'UNKNOWN'
        GROUP BY dv.vehicle_category
        ORDER BY stops DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_vehicle_age(where='', params=None):
    return run_query(f"""
        SELECT
            YEAR(ts.stop_timestamp) - dv.year as vehicle_age,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.year IS NOT NULL
        AND YEAR(ts.stop_timestamp) - dv.year BETWEEN 0 AND 30
        GROUP BY vehicle_age
        ORDER BY vehicle_age
    """, params=params)

@st.cache_data(ttl=3600)
def get_accident_rate_by_make(where='', params=None):
    return run_query(f"""
        SELECT
            dv.make,
            COUNT(DISTINCT ts.stop_id)  as total,
            SUM(ins.accident) as accidents,
            ROUND(
                SUM(ins.accident) /
                COUNT(DISTINCT ts.stop_id) * 100, 1
            ) as accident_rate
        FROM traffic_stop ts
        JOIN driver_vehicle   dv  ON ts.stop_id = dv.stop_id
        JOIN incident_safety  ins ON ts.stop_id = ins.stop_id
        JOIN violation_charge vc  ON ts.stop_id = vc.stop_id
        {where}
        AND dv.make != 'UNKNOWN'
        GROUP BY dv.make
        HAVING total > 1000
        ORDER BY accident_rate DESC
        LIMIT 15
    """, params=params)

@st.cache_data(ttl=3600)
def get_top_makes(where='', params=None):
    return run_query(f"""
        SELECT
            dv.make,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.make != 'UNKNOWN'
        GROUP BY dv.make
        ORDER BY stops DESC
        LIMIT 15
    """, params=params)

@st.cache_data(ttl=3600)
def get_top_colors(where='', params=None):
    return run_query(f"""
        SELECT
            dv.color,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.color != 'UNKNOWN'
        GROUP BY dv.color
        ORDER BY stops DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_by_reason(where='', params=None):
    return run_query(f"""
        SELECT
            se.search_reason,
            COUNT(DISTINCT ts.stop_id) as total
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND se.search_reason != 'Not Applicable'
        GROUP BY se.search_reason
        ORDER BY total DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_by_type(where='', params=None):
    return run_query(f"""
        SELECT
            se.search_type,
            COUNT(DISTINCT ts.stop_id) as total
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND se.search_type != 'NOT APPLICABLE'
        GROUP BY se.search_type
        ORDER BY total DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_by_disposition(where='', params=None):
    return run_query(f"""
        SELECT
            se.search_disposition,
            COUNT(DISTINCT ts.stop_id) as total
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND se.search_disposition != 'Not Applicable'
        GROUP BY se.search_disposition
        ORDER BY total DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_by_outcome(where='', params=None):
    return run_query(f"""
        SELECT
            se.search_outcome,
            COUNT(DISTINCT ts.stop_id) as total
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND se.search_outcome != 'Not Applicable'
        GROUP BY se.search_outcome
        ORDER BY total DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_rate_by_district(where='', params=None):
    return run_query(f"""
        SELECT
            ts.district_number,
            ROUND(
                SUM(se.search_conducted) /
                COUNT(DISTINCT ts.stop_id) * 100, 1
            ) as search_rate
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND ts.district_number IS NOT NULL
        GROUP BY ts.district_number
        ORDER BY search_rate DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_arrest_type_breakdown(where='', params=None):
    return run_query(f"""
        SELECT
            se.arrest_type_desc,
            COUNT(DISTINCT ts.stop_id) as total
        FROM traffic_stop ts
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        GROUP BY se.arrest_type_desc
        ORDER BY total DESC
        LIMIT 10
    """, params=params)

@st.cache_data(ttl=3600)
def get_stops_by_race(where='', params=None):
    return run_query(f"""
        SELECT
            dv.race,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.race != 'UNKNOWN'
        GROUP BY dv.race
        ORDER BY stops DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_stops_by_gender(where='', params=None):
    return run_query(f"""
        SELECT
            dv.gender,
            COUNT(DISTINCT ts.stop_id) as stops
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.gender IN ('M', 'F')
        GROUP BY dv.gender
        ORDER BY stops DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_rate_by_race(where='', params=None):
    return run_query(f"""
        SELECT
            dv.race,
            COUNT(DISTINCT ts.stop_id)       as total,
            SUM(se.search_conducted)         as searches,
            ROUND(
                SUM(se.search_conducted) /
                COUNT(DISTINCT ts.stop_id) * 100, 1
            ) as search_rate
        FROM traffic_stop ts
        JOIN driver_vehicle     dv ON ts.stop_id = dv.stop_id
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.race != 'UNKNOWN'
        GROUP BY dv.race
        ORDER BY search_rate DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_arrest_rate_by_race(where='', params=None):
    return run_query(f"""
        SELECT
            dv.race,
            COUNT(DISTINCT ts.stop_id) as total,
            SUM(CASE WHEN se.search_outcome = 'Arrest'
                THEN 1 ELSE 0 END)     as arrests,
            ROUND(
                SUM(CASE WHEN se.search_outcome = 'Arrest'
                    THEN 1 ELSE 0 END) /
                COUNT(DISTINCT ts.stop_id) * 100, 1
            ) as arrest_rate
        FROM traffic_stop ts
        JOIN driver_vehicle     dv ON ts.stop_id = dv.stop_id
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.race != 'UNKNOWN'
        GROUP BY dv.race
        ORDER BY arrest_rate DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_rate_by_gender(where='', params=None):
    return run_query(f"""
        SELECT
            dv.gender,
            COUNT(DISTINCT ts.stop_id)       as total,
            SUM(se.search_conducted)         as searches,
            ROUND(
                SUM(se.search_conducted) /
                COUNT(DISTINCT ts.stop_id) * 100, 1
            ) as search_rate
        FROM traffic_stop ts
        JOIN driver_vehicle     dv ON ts.stop_id = dv.stop_id
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.gender IN ('M', 'F')
        GROUP BY dv.gender
        ORDER BY search_rate DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_violation_by_race(where='', params=None):
    return run_query(f"""
        SELECT
            dv.race,
            vc.violation_category,
            COUNT(DISTINCT ts.stop_id) as total
        FROM traffic_stop ts
        JOIN driver_vehicle   dv ON ts.stop_id = dv.stop_id
        JOIN violation_charge vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.race != 'UNKNOWN'
        GROUP BY dv.race, vc.violation_category
        ORDER BY dv.race, total DESC
    """, params=params)

@st.cache_data(ttl=3600)
def get_search_rate_race_gender(where='', params=None):
    return run_query(f"""
        SELECT
            dv.race,
            dv.gender,
            ROUND(
                SUM(se.search_conducted) /
                COUNT(DISTINCT ts.stop_id) * 100, 1
            ) as search_rate
        FROM traffic_stop ts
        JOIN driver_vehicle     dv ON ts.stop_id = dv.stop_id
        JOIN search_enforcement se ON ts.stop_id = se.stop_id
        JOIN violation_charge   vc ON ts.stop_id = vc.stop_id
        {where}
        AND dv.race   != 'UNKNOWN'
        AND dv.gender IN ('M', 'F')
        GROUP BY dv.race, dv.gender
        ORDER BY dv.race, dv.gender
    """, params=params)

@st.cache_data(ttl=3600)
def build_where_clause(filters,
                        ts_alias='ts',
                        vc_alias='vc',
                        dv_alias='dv'):
    conditions = []
    params     = {}

    # Year range
    conditions.append(
        f"YEAR({ts_alias}.stop_timestamp) BETWEEN :year_from AND :year_to"
    )
    params['year_from'] = filters['year_range'][0]
    params['year_to']   = filters['year_range'][1]

    # Hour range
    conditions.append(
        f"HOUR({ts_alias}.stop_timestamp) BETWEEN :hour_from AND :hour_to"
    )
    params['hour_from'] = filters['time_range'][0]
    params['hour_to']   = filters['time_range'][1]

    # Days of week
    if filters['days'] and len(filters['days']) < 7:
        placeholders = ', '.join(
            [f':day_{i}' for i in range(len(filters['days']))]
        )
        conditions.append(
            f"DAYNAME({ts_alias}.stop_timestamp) IN ({placeholders})"
        )
        for i, day in enumerate(filters['days']):
            params[f'day_{i}'] = day

    # Districts
    if filters['districts'] and len(filters['districts']) < 6:
        placeholders = ', '.join(
            [f':dist_{i}' for i in range(len(filters['districts']))]
        )
        conditions.append(
            f"{ts_alias}.district_number IN ({placeholders})"
        )
        for i, dist in enumerate(filters['districts']):
            params[f'dist_{i}'] = dist

    # Violation types
    if filters['violation_types'] and \
       len(filters['violation_types']) < 4:
        placeholders = ', '.join(
            [f':vtype_{i}' for i in range(len(filters['violation_types']))]
        )
        conditions.append(
            f"{vc_alias}.violation_type IN ({placeholders})"
        )
        for i, vt in enumerate(filters['violation_types']):
            params[f'vtype_{i}'] = vt

    # Violation categories
    if filters['violation_categories'] and \
       len(filters['violation_categories']) < 20:
        placeholders = ', '.join(
            [f':vcat_{i}' for i in range(len(filters['violation_categories']))]
        )
        conditions.append(
            f"{vc_alias}.violation_category IN ({placeholders})"
        )
        for i, vc in enumerate(filters['violation_categories']):
            params[f'vcat_{i}'] = vc

    # Vehicle types
    if filters['vehicle_types'] and \
       len(filters['vehicle_types']) < 10:
        placeholders = ', '.join(
            [f':veh_{i}' for i in range(len(filters['vehicle_types']))]
        )
        conditions.append(
            f"{dv_alias}.vehicle_category IN ({placeholders})"
        )
        for i, veh in enumerate(filters['vehicle_types']):
            params[f'veh_{i}'] = veh

    # Location
    if filters['location']:
        conditions.append(
            f"{ts_alias}.location_clean LIKE :location"
        )
        params['location'] = f"%{filters['location'].upper()}%"

    where = "WHERE " + " AND ".join(conditions) \
            if conditions else ""
    return where, params


# ============================================================
# Safety Overview
# ============================================================
@st.cache_data(ttl=3600)
def get_safety_overview():
    return run_query("""
        SELECT
            SUM(accident) as accidents,
            SUM(belts) as belt_violations,
            SUM(personal_injury) as injuries,
            SUM(property_damage) as property_damage,
            SUM(fatal) as fatalities
        FROM incident_safety
    """)

# ============================================================
# Filter Options
# ============================================================
@st.cache_data(ttl=3600)
def get_filter_years():
    return run_query("""
        SELECT DISTINCT YEAR(stop_timestamp) as year
        FROM traffic_stop
        ORDER BY year
    """)['year'].tolist()

@st.cache_data(ttl=3600)
def get_filter_districts():
    return run_query("""
        SELECT DISTINCT district_number
        FROM traffic_stop
        WHERE district_number IS NOT NULL
        ORDER BY district_number
    """)['district_number'].tolist()

@st.cache_data(ttl=3600)
def get_filter_violation_types():
    return run_query("""
        SELECT DISTINCT violation_type
        FROM violation_charge
        WHERE violation_type IS NOT NULL
        ORDER BY violation_type
    """)['violation_type'].tolist()

@st.cache_data(ttl=3600)
def get_filter_violation_categories():
    return run_query("""
        SELECT DISTINCT violation_category
        FROM violation_charge
        WHERE violation_category IS NOT NULL
        ORDER BY violation_category
    """)['violation_category'].tolist()

@st.cache_data(ttl=3600)
def get_filter_vehicle_types():
    return run_query("""
        SELECT DISTINCT vehicle_category
        FROM driver_vehicle
        WHERE vehicle_category IS NOT NULL
        AND vehicle_category != 'UNKNOWN'
        ORDER BY vehicle_category
    """)['vehicle_category'].tolist()

@st.cache_data(ttl=3600)
def get_filter_locations():
    return run_query("""
        SELECT DISTINCT location_clean
        FROM traffic_stop
        WHERE location_clean IS NOT NULL
        ORDER BY location_clean
        LIMIT 1000
    """)['location_clean'].tolist()

@st.cache_data(ttl=3600)
def get_filter_days():
    return [
        'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]

@st.cache_data(ttl=3600)
def get_filter_options():
    return {
        'days'                : get_filter_days(),
        'years'               : get_filter_years(),
        'districts'           : get_filter_districts(),
        'violation_types'     : get_filter_violation_types(),      # ← missing
        'violation_categories': get_filter_violation_categories(), # ← missing
        'vehicle_types'       : get_filter_vehicle_types(),        # ← missing
        'locations'           : get_filter_locations(),            # ← missing
    }