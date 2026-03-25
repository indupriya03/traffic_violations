# filters.py
import streamlit as st
import queries as q


def init_filter_state(options):
    defaults = {
        'year_range'          : (int(min(options['years'])), int(max(options['years']))),
        'time_range'          : (0, 23),
        'days'                : options['days'],
        'districts'           : [int(d) for d in options['districts']],
        'violation_types'     : options['violation_types'],
        'violation_categories': options['violation_categories'],
        'vehicle_types'       : options['vehicle_types'],
        'location'            : "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    return defaults

# ============================================================
# LOAD FILTER OPTIONS
# ============================================================
@st.cache_data
def load_filter_options():
    return q.get_filter_options()

# ============================================================
# RESET FILTERS
# ============================================================
def reset_filters():
    for key in [
        'year_range', 'time_range', 'days',
        'districts', 'violation_types',
        'violation_categories', 'vehicle_types',
        'location'
    ]:
        if key in st.session_state:
            del st.session_state[key]
# ============================================================
# RENDER PAGE FILTERS
# ============================================================
def render_page_filters(
    show_year               = True,
    show_time               = True,
    show_days               = True,
    show_district           = True,
    show_violation_type     = True,
    show_violation_category = True,
    show_vehicle_type       = True,
    show_location           = True,
):
    options = load_filter_options()
    # ✅ Initialize state BEFORE widgets
    defaults = init_filter_state(options)
    # Reset button ABOVE expander
    col_title, col_reset = st.columns([5, 1])
    with col_title:
        st.markdown("#### 🔧 Filters")
    with col_reset:
        st.button(
            "🔄 Reset",
            use_container_width = True,
            on_click            = reset_filters,
        )

    with st.expander("Expand Filters", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            if show_year:
                st.slider(
                "📅 Year Range",
                min_value = int(min(options['years'])),
                max_value = int(max(options['years'])),
                value     = (2012, 2024),
                #key       = 'year_range',
            )  

            if show_time: 
                st.slider(
                "🕐 Hour of Day",
                min_value = 0,
                max_value = 23,
                value     = (0, 23),
                format    = "%d:00",
                #key       = 'time_range',
            )  

        with col2:
            if show_days:
                st.multiselect(
                "📆 Day of Week",
                options = options['days'],
                default = options['days'],
                #key     = 'days',
            )  
            if show_district:
                st.multiselect(
                "🌆 District",
                options     = [int(d) for d in options['districts']],
                default     = [int(d) for d in options['districts']],
                format_func = lambda x: {
                    1: '1 - Rockville',
                    2: '2 - Bethesda',
                    3: '3 - Silver Spring',
                    4: '4 - Wheaton',
                    5: '5 - Germantown',
                    6: '6 - Gaithersburg',
                }.get(x, str(x)),
                #key         = 'districts',
            )  
        with col3:
            if show_violation_type: 
                st.multiselect(
                "⚖️ Violation Type",
                options = options['violation_types'],
                default = options['violation_types'],
                key     = 'violation_types',
            )  

            if show_violation_category:
                st.multiselect(
                "📋 Violation Category",
                options = options['violation_categories'],
                default = options['violation_categories'],
                key     = 'violation_categories',
            )  

            if show_vehicle_type:
                st.multiselect(
                "🚙 Vehicle Type",
                options = options['vehicle_types'],
                default = options['vehicle_types'],
                key     = 'vehicle_types',
            )  
            if show_location:
                st.text_input(
                "📍 Location Search",
                placeholder = "e.g. SILVER SPRING",
                key         = 'location',
            )  

    return {
        'year_range'          : st.session_state.get('year_range', defaults['year_range']),
        'time_range'          : st.session_state.get('time_range', defaults['time_range']),
        'days'                : st.session_state.get('days', defaults['days']),
        'districts'           : st.session_state.get('districts', defaults['districts']),
        'violation_types'     : st.session_state.get('violation_types', defaults['violation_types']),
        'violation_categories': st.session_state.get('violation_categories', defaults['violation_categories']),
        'vehicle_types'       : st.session_state.get('vehicle_types', defaults['vehicle_types']),
        'location'            : st.session_state.get('location', ""),
    }
# ============================================================
# BUILD WHERE CLAUSE
# ============================================================
def build_where_clause(filters,
                        ts_alias='ts',
                        vc_alias='vc',
                        dv_alias='dv'):
    conditions = []
    params     = {}

    # Year range
    if filters.get('year_range'):
        conditions.append(
            f"YEAR({ts_alias}.stop_timestamp) "
            f"BETWEEN :year_from AND :year_to"
        )
        params['year_from'] = filters['year_range'][0]
        params['year_to']   = filters['year_range'][1]

    # Hour range
    if filters.get('time_range'):
        conditions.append(
            f"HOUR({ts_alias}.stop_timestamp) "
            f"BETWEEN :hour_from AND :hour_to"
        )
        params['hour_from'] = filters['time_range'][0]
        params['hour_to']   = filters['time_range'][1]

    # Days of week
    if filters.get('days') and len(filters['days']) < 7:
        placeholders = ', '.join(
            [f':day_{i}' for i in range(len(filters['days']))]
        )
        conditions.append(
            f"DAYNAME({ts_alias}.stop_timestamp) "
            f"IN ({placeholders})"
        )
        for i, day in enumerate(filters['days']):
            params[f'day_{i}'] = day

    # Districts
    if filters.get('districts') and \
       len(filters['districts']) < 6:
        placeholders = ', '.join(
            [f':dist_{i}' for i in range(len(filters['districts']))]
        )
        conditions.append(
            f"{ts_alias}.district_number IN ({placeholders})"
        )
        for i, dist in enumerate(filters['districts']):
            params[f'dist_{i}'] = dist

    # Violation types
    if filters.get('violation_types') and \
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
    if filters.get('violation_categories') and \
       len(filters['violation_categories']) < 20:
        placeholders = ', '.join(
            [f':vcat_{i}' for i in
             range(len(filters['violation_categories']))]
        )
        conditions.append(
            f"{vc_alias}.violation_category IN ({placeholders})"
        )
        for i, vc in enumerate(filters['violation_categories']):
            params[f'vcat_{i}'] = vc

    # Vehicle types
    if filters.get('vehicle_types') and \
       len(filters['vehicle_types']) < 10:
        placeholders = ', '.join(
            [f':veh_{i}' for i in range(len(filters['vehicle_types']))]
        )
        conditions.append(
            f"{dv_alias}.vehicle_category IN ({placeholders})"
        )
        for i, veh in enumerate(filters['vehicle_types']):
            params[f'veh_{i}'] = veh

    # Location search
    if filters.get('location'):
        conditions.append(
            f"{ts_alias}.location_clean LIKE :location"
        )
        params['location'] = \
            f"%{filters['location'].upper()}%"

    where = "WHERE " + " AND ".join(conditions) \
            if conditions else ""
    return where, params
