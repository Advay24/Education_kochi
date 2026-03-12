"""
Kochi Education Survey Dashboard
==================================
Interactive dashboard for exploring Education survey data across Kochi wards.
Data: Education-Ward_Level.xlsx + Education_Schools.xlsx
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings("ignore")

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kochi Education Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── THEME / CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #f0f6f0; }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #006400 0%, #004d99 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,100,0,0.3);
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border-left: 5px solid #006400;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    .kpi-card .value { font-size: 2rem; font-weight: 700; color: #006400; }
    .kpi-card .label { font-size: 0.78rem; color: #555; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-card.blue { border-left-color: #004d99; }
    .kpi-card.blue .value { color: #004d99; }
    .kpi-card.orange { border-left-color: #e67e22; }
    .kpi-card.orange .value { color: #e67e22; }
    .kpi-card.purple { border-left-color: #8e44ad; }
    .kpi-card.purple .value { color: #8e44ad; }
    
    /* Insight Box */
    .insight-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #e3f2fd 100%);
        border: 1px solid #006400;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        font-size: 0.88rem;
        line-height: 1.6;
        color: #1a1a2e;
    }
    .insight-box strong { color: #006400; }
    
    /* Section headers */
    .section-header {
        border-bottom: 3px solid #006400;
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
        color: #004d00;
        font-size: 1.2rem;
        font-weight: 700;
    }
    
    /* Sidebar */
    .css-1d391kg { background-color: #003300 !important; }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #e8f5e9;
        border-radius: 8px 8px 0 0;
        color: #006400;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #006400 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # ── Ward Level ──
    ward_df = pd.read_excel("Education-Ward_Level.xlsx", sheet_name="Education-Ward Level_Final")
    ward_df.columns = [
        "ward_num", "ward_name", "anganwadi_count", "anganwadi_enroll_total",
        "anganwadi_boys", "anganwadi_girls", "anganwadi_own_building",
        "vhs_present", "tuition_centres", "study_abroad_centres",
        "higher_ed_institutions", "special_schools"
    ]
    ward_df["ward_num"] = pd.to_numeric(ward_df["ward_num"], errors="coerce")
    for col in ["anganwadi_count","anganwadi_enroll_total","anganwadi_boys",
                "anganwadi_girls","anganwadi_own_building","tuition_centres",
                "study_abroad_centres","higher_ed_institutions"]:
        ward_df[col] = pd.to_numeric(ward_df[col], errors="coerce").fillna(0)
    ward_df["gender_parity"] = ward_df.apply(
        lambda r: round(r["anganwadi_girls"]/r["anganwadi_enroll_total"]*100, 1)
        if r["anganwadi_enroll_total"] > 0 else np.nan, axis=1
    )
    ward_df["vhs_present"] = ward_df["vhs_present"].str.strip().str.title()
    ward_df["special_schools"] = ward_df["special_schools"].str.strip().str.title()

    # ── Schools ──
    sch = pd.read_excel("Education_Schools.xlsx", sheet_name="Education_Schools_Final")
    # Standardise key columns
    sc = pd.DataFrame()
    sc["ward_num"]      = pd.to_numeric(sch["1. Ward number."], errors="coerce")
    sc["ward_name"]     = sch["Ward Name"].str.strip().str.title()
    sc["school_name"]   = sch["2.Name of the School"].str.strip()
    sc["lat"]           = pd.to_numeric(sch["_3.Geolocation of the School_latitude"], errors="coerce")
    sc["lon"]           = pd.to_numeric(sch["_3.Geolocation of the School_longitude"], errors="coerce")
    sc["board"]         = sch["4.Type of school board."].str.strip()
    sc["school_type"]   = sch["5. Type of School"].str.strip()   # Govt/Aided/Private
    sc["school_level"]  = sch["6. What type of school?"].str.strip()
    sc["students_male"] = pd.to_numeric(sch["7. Number of Male students"], errors="coerce").fillna(0)
    sc["students_female"]= pd.to_numeric(sch["8. Number of Female students"], errors="coerce").fillna(0)
    sc["students_total"]= pd.to_numeric(sch["9. Total Number of students"], errors="coerce")
    sc["teachers"]      = pd.to_numeric(sch["10. Number of teachers"], errors="coerce").fillna(0)
    sc["classrooms"]    = pd.to_numeric(sch["11. Number of classrooms"], errors="coerce").fillna(0)
    sc["smart_cls"]     = pd.to_numeric(sch["12. Number of smart classrooms"], errors="coerce").fillna(0)
    sc["computers"]     = pd.to_numeric(sch["13. Number of computers are provided for students"], errors="coerce").fillna(0)
    sc["washrooms"]     = pd.to_numeric(sch["14. Number of Washrooms/toilets"], errors="coerce").fillna(0)
    sc["playground"]    = sch["15. Do these schools have a playground?"].str.strip()
    sc["facilities"]    = sch[" 16. Facilities in the school."].fillna("").astype(str)
    sc["school_buses"]  = pd.to_numeric(sch["20. Number of School buses "], errors="coerce").fillna(0)
    sc["dist_public_transport"] = pd.to_numeric(
        sch["21. Distance to the nearest public transport from the main gate (in Km)"], errors="coerce")
    sc["dist_higher_ed"] = pd.to_numeric(
        sch["22. Distance of the school from the nearest next higher education center (in Km)"], errors="coerce")

    # Transport modes (student)
    for mode in ["Bus","Metro","Walking","Cycling","Ride- hailing services(Ola, Uber, Rapido, etc.)","Personal Vehicle","School Bus","Others"]:
        col_src = f"18. What modes of transportation do students use to reach educational institutions?/{mode}"
        col_dst = f"stu_{mode.split()[0].lower().replace('-','')}"
        if col_src in sch.columns:
            sc[col_dst] = sch[col_src].apply(lambda x: 1 if str(x).strip().lower() in ["1","yes","true"] else 0)

    # Transport modes (teacher)
    for mode in ["Bus","Metro","Walking","Cycling","Personal Vehicle","School Bus","Others"]:
        col_src = f"19. What modes of transportation do teachers use to reach educational institutions?/{mode}"
        col_dst = f"tch_{mode.split()[0].lower()}"
        if col_src in sch.columns:
            sc[col_dst] = sch[col_src].apply(lambda x: 1 if str(x).strip().lower() in ["1","yes","true"] else 0)

    # Fix obvious GPS errors (lat outside Kerala range ~8.2–12.8, lon ~74.8–77.4)
    sc.loc[(sc["lat"] < 8.2) | (sc["lat"] > 12.8), ["lat","lon"]] = np.nan
    sc.loc[(sc["lon"] < 74.8) | (sc["lon"] > 77.4), ["lat","lon"]] = np.nan

    # Fix obvious distance outliers (>50 km → set NaN)
    sc.loc[sc["dist_public_transport"] > 50, "dist_public_transport"] = np.nan

    # Derived metrics
    sc["students_total"] = sc["students_total"].fillna(sc["students_male"] + sc["students_female"])
    sc["student_teacher_ratio"] = sc.apply(
        lambda r: round(r["students_total"]/r["teachers"], 1) if r["teachers"] > 0 else np.nan, axis=1)
    sc["smart_cls_pct"] = sc.apply(
        lambda r: round(r["smart_cls"]/r["classrooms"]*100, 1) if r["classrooms"] > 0 else 0, axis=1)
    sc["computers_per_student"] = sc.apply(
        lambda r: round(r["computers"]/r["students_total"], 3) if r["students_total"] > 0 else 0, axis=1)

    # Facility score (0-10)
    sc["facility_score"] = (
        (sc["playground"] == "Yes").astype(int) * 2 +
        (sc["smart_cls"] >= 5).astype(int) * 2 +
        (sc["computers"] >= 10).astype(int) * 1.5 +
        (sc["washrooms"] >= 5).astype(int) * 1 +
        sc["facilities"].str.contains("library|computer|lab|playground|sport|music|art", case=False).astype(int) * 1 +
        sc["facilities"].str.contains("transport|canteen|hostel", case=False).astype(int) * 0.5 +
        (sc["school_buses"] > 0).astype(int) * 1
    )

    # KMeans clustering on ward level
    cluster_features = ["anganwadi_count","anganwadi_enroll_total","tuition_centres",
                        "higher_ed_institutions","study_abroad_centres"]
    wf = ward_df[cluster_features].fillna(0)
    scaler = StandardScaler()
    wf_scaled = scaler.fit_transform(wf)
    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    ward_df["cluster"] = km.fit_predict(wf_scaled)
    cluster_labels = {0:"Basic Coverage", 1:"Developing", 2:"Well-Served"}
    # Assign labels based on mean anganwadi_enroll_total per cluster
    c_means = ward_df.groupby("cluster")["anganwadi_enroll_total"].mean().sort_values()
    label_map = {c_means.index[0]: "Basic Coverage", c_means.index[1]: "Developing", c_means.index[2]: "Well-Served"}
    ward_df["cluster_label"] = ward_df["cluster"].map(label_map)

    return ward_df, sc


ward_df, school_df = load_data()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#006400,#004d99);padding:1rem;border-radius:10px;color:white;text-align:center;margin-bottom:1rem;'>
        <h2 style='margin:0;font-size:1.3rem;'>🎓 Kochi Education</h2>
        <p style='margin:0;font-size:0.75rem;opacity:0.8;'>Survey Dashboard 2025</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Filters")

    all_wards = sorted(ward_df["ward_name"].dropna().unique().tolist())
    selected_wards = st.multiselect(
        "Ward(s)", options=all_wards, default=all_wards,
        help="Select one or more wards"
    )
    if not selected_wards:
        selected_wards = all_wards

    all_boards = sorted(school_df["board"].dropna().unique().tolist())
    selected_boards = st.multiselect("School Board", options=all_boards, default=all_boards)
    if not selected_boards:
        selected_boards = all_boards

    all_types = sorted(school_df["school_type"].dropna().unique().tolist())
    selected_types = st.multiselect("School Type", options=all_types, default=all_types)
    if not selected_types:
        selected_types = all_types

    all_levels = sorted(school_df["school_level"].dropna().unique().tolist())
    selected_levels = st.multiselect("School Level", options=all_levels, default=all_levels)
    if not selected_levels:
        selected_levels = all_levels

    playground_filter = st.radio("Playground", ["All", "Yes", "No"], horizontal=True)

    st.markdown("---")
    smart_min, smart_max = st.slider(
        "Smart Classrooms Range", 0, int(school_df["smart_cls"].max()), (0, int(school_df["smart_cls"].max()))
    )
    dist_max = st.slider(
        "Max Distance to Public Transport (km)", 0.0, 10.0, 10.0, 0.1
    )

    st.markdown("---")
    st.markdown("""<div style='font-size:0.72rem;color:#555;'>
    ⚠️ <b>Data Notes:</b><br>
    • Wards 37 & 41: Anganwadis closed<br>
    • Ward 63: Data unavailable<br>
    • Pre-2025 delimitation boundaries<br>
    • 22 wards surveyed, 48 schools
    </div>""", unsafe_allow_html=True)

# ─── APPLY FILTERS ────────────────────────────────────────────────────────────
w_filt = ward_df[ward_df["ward_name"].isin(selected_wards)]

s_filt = school_df[
    school_df["ward_name"].str.title().isin([w.title() for w in selected_wards]) &
    school_df["board"].isin(selected_boards) &
    school_df["school_type"].isin(selected_types) &
    school_df["school_level"].isin(selected_levels) &
    (school_df["smart_cls"] >= smart_min) &
    (school_df["smart_cls"] <= smart_max) &
    (school_df["dist_public_transport"].isna() | (school_df["dist_public_transport"] <= dist_max))
]
if playground_filter != "All":
    s_filt = s_filt[s_filt["playground"] == playground_filter]

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class='main-header'>
    <h1>🎓 Kochi Education Survey Dashboard</h1>
    <p>Comprehensive analysis of education infrastructure across Kochi Corporation wards • Survey 2025</p>
</div>
""", unsafe_allow_html=True)

# ─── KPI ROW ──────────────────────────────────────────────────────────────────
total_students = int(s_filt["students_total"].sum())
total_anganwadi = int(w_filt["anganwadi_count"].sum())
avg_gpi = w_filt["gender_parity"].mean()
avg_facility = s_filt["facility_score"].mean()
total_schools = len(s_filt)
total_teachers = int(s_filt["teachers"].sum())

c1, c2, c3, c4, c5, c6 = st.columns(6)
def kpi(col, val, label, cls=""):
    col.markdown(f"""
    <div class='kpi-card {cls}'>
        <div class='value'>{val}</div>
        <div class='label'>{label}</div>
    </div>""", unsafe_allow_html=True)

kpi(c1, len(selected_wards), "Wards Selected")
kpi(c2, total_anganwadi, "Anganwadis", "blue")
kpi(c3, f"{total_students:,}", "School Students", "orange")
kpi(c4, total_teachers, "Teachers", "blue")
kpi(c5, f"{avg_gpi:.1f}%" if not np.isnan(avg_gpi) else "N/A", "Avg Girls % (Anganwadi)", "purple")
kpi(c6, f"{avg_facility:.1f}/10", "Avg Facility Score")

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Ward Comparison",
    "🗺️ School Map",
    "🏫 Facility Analyzer",
    "🚌 Transport & Equity",
    "📈 Correlations & Clusters",
    "💡 Insight Generator"
])

COLORS = {
    "green": "#006400", "blue": "#004d99", "light_green": "#28a745",
    "orange": "#e67e22", "red": "#c0392b", "purple": "#8e44ad", "teal": "#17a589"
}

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — WARD COMPARISON
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-header'>Ward-Level Overview</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        fig = px.bar(
            w_filt.sort_values("anganwadi_enroll_total", ascending=False),
            x="ward_name", y="anganwadi_enroll_total",
            color="cluster_label",
            color_discrete_map={"Well-Served":"#006400","Developing":"#004d99","Basic Coverage":"#e67e22"},
            labels={"ward_name":"Ward","anganwadi_enroll_total":"Total Enrolled","cluster_label":"Cluster"},
            title="Anganwadi Enrollment by Ward",
            text_auto=True
        )
        fig.update_layout(xaxis_tickangle=-40, plot_bgcolor="white", height=380,
                          legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.bar(
            w_filt.sort_values("tuition_centres", ascending=False),
            x="ward_name",
            y=["tuition_centres","higher_ed_institutions","study_abroad_centres"],
            barmode="group",
            labels={"value":"Count","variable":"Category","ward_name":"Ward"},
            title="Education Support Centres by Ward",
            color_discrete_sequence=["#006400","#004d99","#e67e22"]
        )
        fig2.update_layout(xaxis_tickangle=-40, plot_bgcolor="white", height=380,
                           legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)
    
    with col_c:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Boys", x=w_filt["ward_name"],
                              y=w_filt["anganwadi_boys"], marker_color="#004d99"))
        fig3.add_trace(go.Bar(name="Girls", x=w_filt["ward_name"],
                              y=w_filt["anganwadi_girls"], marker_color="#e91e8c"))
        fig3.update_layout(barmode="stack", title="Gender Distribution – Anganwadi Enrollment",
                           xaxis_tickangle=-40, plot_bgcolor="white", height=350,
                           legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        # Anganwadis with own building vs total
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Total Anganwadis", x=w_filt["ward_name"],
                              y=w_filt["anganwadi_count"], marker_color="#c8e6c9"))
        fig4.add_trace(go.Bar(name="Own Building", x=w_filt["ward_name"],
                              y=w_filt["anganwadi_own_building"], marker_color="#006400"))
        fig4.update_layout(barmode="overlay", title="Anganwadis: Own Building vs Total",
                           xaxis_tickangle=-40, plot_bgcolor="white", height=350,
                           legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig4, use_container_width=True)

    # VHS & Special Schools table
    st.markdown("<div class='section-header'>Special Facilities per Ward</div>", unsafe_allow_html=True)
    tbl = w_filt[["ward_name","vhs_present","special_schools","anganwadi_count",
                  "tuition_centres","higher_ed_institutions","cluster_label"]].copy()
    tbl.columns = ["Ward","VHS Present","Special Schools","Anganwadis",
                   "Tuition Centres","Higher Ed","Cluster"]
    st.dataframe(tbl.set_index("Ward"), use_container_width=True, height=300)


# ═══════════════════════════════════════════════════════════════════
# TAB 2 — SCHOOL MAP
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-header'>School Locations – Interactive Map</div>", unsafe_allow_html=True)
    st.caption("📍 Click any marker for full school details. Colour = School Type.")

    map_df = s_filt.dropna(subset=["lat","lon"]).copy()

    # Build folium map centred on Kochi
    m = folium.Map(location=[9.97, 76.28], zoom_start=12,
                   tiles="CartoDB positron")

    type_colors = {"Government":"green", "Aided":"blue", "Private":"red"}

    for _, row in map_df.iterrows():
        color = type_colors.get(row["school_type"], "gray")
        popup_html = f"""
        <div style='min-width:220px;font-size:13px;'>
            <b style='color:#006400;'>{row['school_name']}</b><br>
            <b>Ward:</b> {row['ward_name']} ({int(row['ward_num']) if not pd.isna(row['ward_num']) else 'N/A'})<br>
            <b>Board:</b> {row['board']} | <b>Type:</b> {row['school_type']}<br>
            <b>Level:</b> {row['school_level']}<br>
            <hr style='margin:4px 0;'>
            <b>Students:</b> {int(row['students_total']) if not pd.isna(row['students_total']) else 'N/A'}
            (♂{int(row['students_male'])} ♀{int(row['students_female'])})<br>
            <b>Teachers:</b> {int(row['teachers'])} | <b>S:T Ratio:</b> {row['student_teacher_ratio']}<br>
            <b>Classrooms:</b> {int(row['classrooms'])} | <b>Smart:</b> {int(row['smart_cls'])}<br>
            <b>Computers:</b> {int(row['computers'])} | <b>Washrooms:</b> {int(row['washrooms'])}<br>
            <b>Playground:</b> {row['playground']} | <b>Buses:</b> {int(row['school_buses'])}<br>
            <b>Dist. Public Transport:</b> {row['dist_public_transport']} km<br>
            <b>Dist. Higher Ed:</b> {row['dist_higher_ed']} km<br>
            <b>Facility Score:</b> {row['facility_score']:.1f}/10<br>
            <b>Facilities:</b> {row['facilities'][:80]}...
        </div>"""
        
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=row["school_name"]
        ).add_to(m)

    # Legend
    legend_html = """
    <div style='position:fixed;bottom:30px;right:30px;z-index:1000;background:white;
                padding:10px;border-radius:8px;border:1px solid #ccc;font-size:12px;'>
        <b>School Type</b><br>
        🟢 Government<br>🔵 Aided<br>🔴 Private
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=None, height=500, returned_objects=[])

    st.markdown("---")
    st.subheader(f"📋 Schools in Selection ({len(s_filt)} schools)")
    display_cols = ["school_name","ward_name","board","school_type","school_level",
                    "students_total","teachers","smart_cls","facility_score","playground","dist_public_transport"]
    st.dataframe(
        s_filt[display_cols].rename(columns={
            "school_name":"School","ward_name":"Ward","board":"Board",
            "school_type":"Type","school_level":"Level","students_total":"Students",
            "teachers":"Teachers","smart_cls":"Smart Cls","facility_score":"Facility Score",
            "playground":"Playground","dist_public_transport":"Dist. PT (km)"
        }).set_index("School"),
        use_container_width=True, height=350
    )


# ═══════════════════════════════════════════════════════════════════
# TAB 3 — FACILITY ANALYZER
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Facility & Infrastructure Analysis</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Smart classroom availability breakdown
        s_filt2 = s_filt.copy()
        s_filt2["smart_band"] = pd.cut(s_filt2["smart_cls"], bins=[-1,0,5,10,100],
                                        labels=["0 (None)","1–5","6–10","10+"])
        smart_counts = s_filt2["smart_band"].value_counts().sort_index()
        fig_sc = px.pie(values=smart_counts.values, names=smart_counts.index,
                        title="Smart Classroom Distribution",
                        color_discrete_sequence=["#e74c3c","#e67e22","#3498db","#006400"])
        fig_sc.update_traces(textposition="inside", textinfo="percent+label")
        fig_sc.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig_sc, use_container_width=True)

    with col2:
        # Facility score by school type
        fig_fs = px.box(s_filt, x="school_type", y="facility_score",
                        color="school_type",
                        color_discrete_map={"Government":"#006400","Aided":"#004d99","Private":"#e67e22"},
                        title="Facility Score Distribution by School Type",
                        labels={"school_type":"Type","facility_score":"Facility Score (0–10)"})
        fig_fs.update_layout(height=340, showlegend=False, plot_bgcolor="white")
        st.plotly_chart(fig_fs, use_container_width=True)

    col3, col4 = st.columns(2)
    
    with col3:
        # Scatter: distance vs enrollment
        scatter_df = s_filt.dropna(subset=["dist_public_transport","students_total"])
        fig_sc2 = px.scatter(scatter_df,
                             x="dist_public_transport", y="students_total",
                             color="school_type", size="facility_score",
                             hover_name="school_name",
                             labels={"dist_public_transport":"Distance to Public Transport (km)",
                                     "students_total":"Total Students",
                                     "school_type":"Type"},
                             title="Enrollment vs Distance to Public Transport",
                             color_discrete_map={"Government":"#006400","Aided":"#004d99","Private":"#e67e22"})
        fig_sc2.update_layout(height=350, plot_bgcolor="white")
        st.plotly_chart(fig_sc2, use_container_width=True)

    with col4:
        # Stacked bar: playground by board
        pg_board = s_filt.groupby(["board","playground"]).size().reset_index(name="count")
        fig_pg = px.bar(pg_board, x="board", y="count", color="playground",
                        barmode="stack",
                        color_discrete_map={"Yes":"#006400","No":"#e74c3c"},
                        title="Playground Availability by Board",
                        labels={"board":"Board","count":"Number of Schools"})
        fig_pg.update_layout(height=350, plot_bgcolor="white",
                              legend=dict(orientation="h",y=1.05))
        st.plotly_chart(fig_pg, use_container_width=True)

    # Heatmap: facilities across wards
    st.markdown("<div class='section-header'>Infrastructure Heatmap by Ward</div>", unsafe_allow_html=True)
    ward_agg = s_filt.groupby("ward_name").agg(
        avg_smart_cls=("smart_cls","mean"),
        avg_computers=("computers","mean"),
        avg_washrooms=("washrooms","mean"),
        avg_facility_score=("facility_score","mean"),
        pct_playground=("playground", lambda x: (x=="Yes").mean()*100),
        total_students=("students_total","sum"),
        school_count=("school_name","count")
    ).reset_index()
    
    heat_cols = ["avg_smart_cls","avg_computers","avg_washrooms","avg_facility_score","pct_playground"]
    heat_labels = ["Avg Smart Cls","Avg Computers","Avg Washrooms","Facility Score","% Playground"]
    if len(ward_agg) > 0:
        heat_data = ward_agg.set_index("ward_name")[heat_cols]
        # Normalise 0-1
        heat_norm = (heat_data - heat_data.min()) / (heat_data.max() - heat_data.min() + 1e-9)
        fig_heat = px.imshow(heat_norm.T,
                             labels=dict(x="Ward", y="Metric", color="Score (Normalised)"),
                             x=heat_norm.index.tolist(),
                             y=heat_labels,
                             color_continuous_scale="YlGn",
                             title="Normalised Infrastructure Metrics Heatmap")
        fig_heat.update_layout(height=300)
        st.plotly_chart(fig_heat, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 4 — TRANSPORT & EQUITY
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Transport Modes & Gender Equity</div>", unsafe_allow_html=True)

    # Student transport modes
    stu_mode_cols = {
        "stu_bus": "Bus", "stu_metro": "Metro", "stu_walking": "Walking",
        "stu_cycling": "Cycling", "stu_ride-": "Ride-Hailing",
        "stu_personal": "Personal Vehicle", "stu_school": "School Bus"
    }
    tch_mode_cols = {
        "tch_bus": "Bus", "tch_metro": "Metro", "tch_walking": "Walking",
        "tch_cycling": "Cycling", "tch_personal": "Personal Vehicle",
        "tch_school": "School Bus"
    }

    # Find which cols exist
    stu_existing = {k:v for k,v in stu_mode_cols.items() 
                    if any(c.startswith(k) for c in s_filt.columns)}
    tch_existing = {k:v for k,v in tch_mode_cols.items() 
                    if any(c.startswith(k) for c in s_filt.columns)}

    col1, col2 = st.columns(2)
    
    with col1:
        stu_sums = {}
        for prefix, label in stu_existing.items():
            matched = [c for c in s_filt.columns if c.startswith(prefix)]
            if matched:
                stu_sums[label] = s_filt[matched[0]].sum()
        if stu_sums:
            fig_stu = px.bar(
                x=list(stu_sums.keys()), y=list(stu_sums.values()),
                labels={"x":"Mode","y":"Schools Reporting"},
                title="Student Transport Modes (Schools Reporting Each)",
                color=list(stu_sums.keys()),
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_stu.update_layout(height=360, plot_bgcolor="white", showlegend=False)
            st.plotly_chart(fig_stu, use_container_width=True)

    with col2:
        tch_sums = {}
        for prefix, label in tch_existing.items():
            matched = [c for c in s_filt.columns if c.startswith(prefix)]
            if matched:
                tch_sums[label] = s_filt[matched[0]].sum()
        if tch_sums:
            fig_tch = px.bar(
                x=list(tch_sums.keys()), y=list(tch_sums.values()),
                labels={"x":"Mode","y":"Schools Reporting"},
                title="Teacher Transport Modes (Schools Reporting Each)",
                color=list(tch_sums.keys()),
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_tch.update_layout(height=360, plot_bgcolor="white", showlegend=False)
            st.plotly_chart(fig_tch, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Gender equity in schools
        gender_df = s_filt.copy()
        gender_df["female_pct"] = gender_df.apply(
            lambda r: r["students_female"]/r["students_total"]*100
            if r["students_total"] > 0 else np.nan, axis=1)
        fig_gen = px.histogram(gender_df.dropna(subset=["female_pct"]),
                               x="female_pct", nbins=15,
                               color_discrete_sequence=["#e91e8c"],
                               labels={"female_pct":"Female Student %"},
                               title="Distribution of Female Student % Across Schools")
        fig_gen.add_vline(x=50, line_dash="dash", line_color="#006400",
                          annotation_text="Parity line", annotation_position="top right")
        fig_gen.update_layout(height=350, plot_bgcolor="white")
        st.plotly_chart(fig_gen, use_container_width=True)

    with col4:
        # Distance distribution
        dist_df = s_filt.dropna(subset=["dist_public_transport"])
        fig_dist = px.histogram(dist_df, x="dist_public_transport", nbins=20,
                                color="school_type",
                                color_discrete_map={"Government":"#006400","Aided":"#004d99","Private":"#e67e22"},
                                labels={"dist_public_transport":"Distance to Public Transport (km)"},
                                title="Distribution of Distance to Public Transport")
        fig_dist.update_layout(height=350, plot_bgcolor="white",
                               legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig_dist, use_container_width=True)

    # Radar chart per board
    st.markdown("<div class='section-header'>Infrastructure Radar by Board</div>", unsafe_allow_html=True)
    board_agg = s_filt.groupby("board").agg(
        Smart_Cls=("smart_cls_pct","mean"),
        Computers_per_100=("computers_per_student", lambda x: x.mean()*100),
        Facility_Score=("facility_score","mean"),
        Student_Teacher_Ratio_inv=("student_teacher_ratio", lambda x: 50/x.mean() if x.mean()>0 else 0),
        Playground_Pct=("playground", lambda x: (x=="Yes").mean()*100)
    ).reset_index()
    
    categories = ["Smart_Cls","Computers_per_100","Facility_Score","Student_Teacher_Ratio_inv","Playground_Pct"]
    cat_labels = ["Smart Cls %","Comp/100 Students","Facility Score","Inverse S:T Ratio","Playground %"]
    
    fig_radar = go.Figure()
    colors_radar = ["#006400","#004d99","#e67e22","#8e44ad","#17a589"]
    for i, row in board_agg.iterrows():
        vals = [row.get(c, 0) for c in categories]
        vals_norm = [min(v/max(board_agg[c].max(), 1e-9)*10, 10) for v, c in zip(vals, categories)]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_norm + [vals_norm[0]],
            theta=cat_labels + [cat_labels[0]],
            fill="toself",
            name=row["board"],
            line_color=colors_radar[i % len(colors_radar)],
            opacity=0.6
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,10])),
        title="Infrastructure Profile by School Board (Normalised 0–10)",
        height=400
    )
    st.plotly_chart(fig_radar, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 5 — CORRELATIONS & CLUSTERS
# ═══════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-header'>Statistical Correlations & Ward Clustering</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        # Ward cluster scatter
        fig_cl = px.scatter(w_filt,
                            x="tuition_centres", y="higher_ed_institutions",
                            color="cluster_label", size="anganwadi_enroll_total",
                            hover_name="ward_name",
                            color_discrete_map={"Well-Served":"#006400","Developing":"#004d99","Basic Coverage":"#e67e22"},
                            title="Ward Clusters: Tuition Centres vs Higher Ed Institutions",
                            labels={"tuition_centres":"Tuition Centres","higher_ed_institutions":"Higher Ed Institutions"})
        fig_cl.update_layout(height=400, plot_bgcolor="white")
        st.plotly_chart(fig_cl, use_container_width=True)

    with col2:
        # Correlation heatmap (school metrics)
        corr_cols = ["students_total","teachers","classrooms","smart_cls","computers",
                     "facility_score","dist_public_transport","dist_higher_ed"]
        corr_labels = ["Students","Teachers","Classrooms","Smart Cls","Computers",
                       "Facility Score","Dist PT","Dist Higher Ed"]
        corr_df = s_filt[corr_cols].dropna()
        if len(corr_df) > 3:
            corr_mat = corr_df.corr()
            fig_corr = px.imshow(corr_mat,
                                 x=corr_labels, y=corr_labels,
                                 color_continuous_scale="RdBu_r",
                                 zmin=-1, zmax=1,
                                 title="Correlation Matrix – School Metrics",
                                 text_auto=".2f")
            fig_corr.update_layout(height=400)
            st.plotly_chart(fig_corr, use_container_width=True)

    col3, col4 = st.columns(2)
    
    with col3:
        # Anganwadi own building vs enrollment
        fig_ab = px.scatter(w_filt,
                            x="anganwadi_own_building", y="anganwadi_enroll_total",
                            color="vhs_present", text="ward_name",
                            color_discrete_map={"Yes":"#006400","No":"#e74c3c"},
                            title="Own Buildings vs Enrollment (Anganwadi)",
                            labels={"anganwadi_own_building":"Own Buildings",
                                    "anganwadi_enroll_total":"Total Enrolled",
                                    "vhs_present":"VHS Present"})
        fig_ab.update_traces(textposition="top center", textfont_size=9)
        fig_ab.update_layout(height=380, plot_bgcolor="white")
        st.plotly_chart(fig_ab, use_container_width=True)

    with col4:
        # Smart classrooms vs enrollment (by school type)
        fig_sm = px.scatter(s_filt.dropna(subset=["students_total"]),
                            x="smart_cls", y="students_total",
                            color="school_type", trendline="ols",
                            hover_name="school_name",
                            color_discrete_map={"Government":"#006400","Aided":"#004d99","Private":"#e67e22"},
                            title="Smart Classrooms vs Total Enrollment",
                            labels={"smart_cls":"Smart Classrooms","students_total":"Total Students"})
        fig_sm.update_layout(height=380, plot_bgcolor="white",
                             legend=dict(orientation="h",y=1.05))
        st.plotly_chart(fig_sm, use_container_width=True)

    # Analysis Summary text
    st.markdown("---")
    st.markdown("<div class='section-header'>📋 Key Statistical Findings</div>", unsafe_allow_html=True)
    
    avg_smart_no_pg = s_filt[s_filt["playground"]=="No"]["smart_cls"].mean()
    avg_smart_pg = s_filt[s_filt["playground"]=="Yes"]["smart_cls"].mean()
    avg_stu_no_pg = s_filt[s_filt["playground"]=="No"]["students_total"].mean()
    avg_stu_pg = s_filt[s_filt["playground"]=="Yes"]["students_total"].mean()
    
    stats_html = f"""
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:1rem;'>
    <div class='insight-box'>
        <strong>📐 Smart Classrooms & Enrollment</strong><br>
        Schools with ≥10 smart classrooms have <b>{s_filt[s_filt['smart_cls']>=10]['students_total'].mean():.0f}</b> avg students
        vs <b>{s_filt[s_filt['smart_cls']<10]['students_total'].mean():.0f}</b> for schools with fewer.
        Correlation coefficient: <b>{s_filt[['smart_cls','students_total']].dropna().corr().iloc[0,1]:.2f}</b>
    </div>
    <div class='insight-box'>
        <strong>🏟️ Playground & Infrastructure</strong><br>
        Schools <i>with</i> playgrounds avg <b>{avg_smart_pg:.1f}</b> smart classrooms vs 
        <b>{avg_smart_no_pg:.1f}</b> without. Average enrollment: 
        <b>{avg_stu_pg:.0f}</b> vs <b>{avg_stu_no_pg:.0f}</b> students.
    </div>
    <div class='insight-box'>
        <strong>🏛️ Ward Cluster Breakdown</strong><br>
        <b>Well-Served:</b> {len(w_filt[w_filt['cluster_label']=='Well-Served'])} wards | 
        <b>Developing:</b> {len(w_filt[w_filt['cluster_label']=='Developing'])} wards | 
        <b>Basic Coverage:</b> {len(w_filt[w_filt['cluster_label']=='Basic Coverage'])} wards
    </div>
    <div class='insight-box'>
        <strong>🎓 Government vs Private Facility</strong><br>
        Avg facility score — Government: <b>{s_filt[s_filt['school_type']=='Government']['facility_score'].mean():.1f}</b> | 
        Aided: <b>{s_filt[s_filt['school_type']=='Aided']['facility_score'].mean():.1f}</b> | 
        Private: <b>{s_filt[s_filt['school_type']=='Private']['facility_score'].mean():.1f}</b>
    </div>
    </div>"""
    st.markdown(stats_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 6 — INSIGHT GENERATOR
# ═══════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("<div class='section-header'>💡 Insight Generator – Live Analysis</div>", unsafe_allow_html=True)
    st.caption("Insights update automatically based on your sidebar filter selections.")

    # ── Compute live insights from filtered data ──
    insights = []

    n_wards = len(selected_wards)
    n_schools = len(s_filt)
    total_stu = s_filt["students_total"].sum()
    total_stu_w = w_filt["anganwadi_enroll_total"].sum()

    # 1. Gender parity
    girls_pct = (s_filt["students_female"].sum() / s_filt["students_total"].sum() * 100) if s_filt["students_total"].sum() > 0 else 0
    insights.append({
        "icon": "⚧",
        "title": "Gender Parity in Schools",
        "body": f"Across <b>{n_schools}</b> selected schools, <b>{girls_pct:.1f}%</b> of students are female "
                f"({s_filt['students_female'].sum():.0f} girls vs {s_filt['students_male'].sum():.0f} boys). "
                + ("This indicates female under-representation. Focus on Aided schools for equity programmes." 
                   if girls_pct < 45 else 
                   "This is near parity (45–55%) — an encouraging sign of gender-inclusive education." 
                   if 45 <= girls_pct <= 55 else 
                   "Female students outnumber males in this selection — potentially girls-only institutions included.")
    })

    # 2. Smart classrooms
    pct_no_smart = (s_filt["smart_cls"] == 0).mean() * 100
    insights.append({
        "icon": "🖥️",
        "title": "Smart Classroom Access Gap",
        "body": f"<b>{pct_no_smart:.0f}%</b> of selected schools have <b>zero smart classrooms</b>. "
                f"Schools with ≥10 smart classrooms average <b>{s_filt[s_filt['smart_cls']>=10]['students_total'].mean():.0f}</b> "
                f"students vs <b>{s_filt[s_filt['smart_cls']<10]['students_total'].mean():.0f}</b> for others — "
                "suggesting better-resourced schools also attract higher enrollment."
    })

    # 3. Playground & transport
    no_pg = s_filt[s_filt["playground"] == "No"]
    walk_col = [c for c in s_filt.columns if c.startswith("stu_walk")]
    if walk_col and len(no_pg) > 0:
        pct_walk_nopg = no_pg[walk_col[0]].mean() * 100
        insights.append({
            "icon": "🏟️",
            "title": "Playground-Deficient Schools & Transport",
            "body": f"<b>{len(no_pg)}</b> schools lack playgrounds. Among these, "
                    f"<b>{pct_walk_nopg:.0f}%</b> report walking as a student transport mode. "
                    f"Average distance to public transport: <b>{no_pg['dist_public_transport'].mean():.2f} km</b>. "
                    "These schools may benefit from infrastructure investment to improve both facilities and access."
        })

    # 4. Tuition centres vs higher ed
    high_tution = w_filt[w_filt["tuition_centres"] >= 3]
    zero_tution = w_filt[w_filt["tuition_centres"] == 0]
    if len(high_tution) > 0 and len(zero_tution) > 0:
        ratio = high_tution["higher_ed_institutions"].mean() / max(zero_tution["higher_ed_institutions"].mean(), 0.1)
        enroll_ratio = high_tution["anganwadi_enroll_total"].mean() / max(zero_tution["anganwadi_enroll_total"].mean(), 0.1)
        insights.append({
            "icon": "📚",
            "title": "Tuition Centres & Higher Education Correlation",
            "body": f"Wards with ≥3 tuition centres (<b>{len(high_tution)} wards</b>) have on average "
                    f"<b>{ratio:.1f}×</b> more higher education institutions and "
                    f"<b>{enroll_ratio:.1f}×</b> higher Anganwadi enrollment than wards with zero tuition centres "
                    f"(<b>{len(zero_tution)} wards</b>). This suggests education clustering in certain wards."
        })

    # 5. VHS access
    vhs_wards = w_filt[w_filt["vhs_present"]=="Yes"]
    no_vhs_wards = w_filt[w_filt["vhs_present"]=="No"]
    insights.append({
        "icon": "🏫",
        "title": "Vocational Higher Secondary (VHS) Coverage",
        "body": f"<b>{len(vhs_wards)}</b> of {n_wards} selected wards have VHS schools; "
                f"<b>{len(no_vhs_wards)}</b> do not. Wards without VHS: "
                f"<b>{', '.join(no_vhs_wards['ward_name'].tolist()) or 'None'}</b>. "
                "Students in non-VHS wards may face barriers to vocational education access."
    })

    # 6. Distance to transport
    far_schools = s_filt[s_filt["dist_public_transport"] > 0.5]
    pct_far = len(far_schools) / max(len(s_filt), 1) * 100
    bus_col = [c for c in s_filt.columns if c.startswith("stu_bus")]
    personal_col = [c for c in s_filt.columns if c.startswith("stu_personal")]
    if bus_col and personal_col and len(far_schools) > 0:
        pct_personal_far = far_schools[personal_col[0]].mean() * 100
        insights.append({
            "icon": "🚌",
            "title": "Distance & Personal Vehicle Dependency",
            "body": f"<b>{pct_far:.0f}%</b> of selected schools are >0.5 km from public transport. "
                    f"Among these, <b>{pct_personal_far:.0f}%</b> report personal vehicle use by students. "
                    f"Average facility score for these schools: <b>{far_schools['facility_score'].mean():.1f}/10</b> "
                    f"vs <b>{s_filt[s_filt['dist_public_transport']<=0.5]['facility_score'].mean():.1f}/10</b> for well-connected schools."
        })

    # 7. Special schools
    special_wards = w_filt[w_filt["special_schools"]=="Yes"]
    no_special_wards = w_filt[w_filt["special_schools"]=="No"]
    insights.append({
        "icon": "♿",
        "title": "Special School Availability",
        "body": f"<b>{len(special_wards)}</b> wards have special schools "
                f"({', '.join(special_wards['ward_name'].tolist()) or 'None'}). "
                f"<b>{len(no_special_wards)}</b> wards lack special education facilities. "
                "Children with disabilities in underserved wards may need to travel to neighbouring wards for support."
    })

    # 8. CBSE private profile
    cbse_private = s_filt[(s_filt["board"]=="CBSE") & (s_filt["school_type"]=="Private")]
    state_govt = s_filt[(s_filt["board"]=="State") & (s_filt["school_type"]=="Government")]
    if len(cbse_private) > 0 and len(state_govt) > 0:
        insights.append({
            "icon": "🏆",
            "title": "CBSE Private vs State Government Comparison",
            "body": f"CBSE Private schools (<b>{len(cbse_private)}</b>): "
                    f"avg <b>{cbse_private['computers_per_student'].mean():.3f}</b> computers/student, "
                    f"facility score <b>{cbse_private['facility_score'].mean():.1f}/10</b>, "
                    f"S:T ratio <b>{cbse_private['student_teacher_ratio'].mean():.0f}:1</b>. "
                    f"State Government schools (<b>{len(state_govt)}</b>): "
                    f"avg <b>{state_govt['computers_per_student'].mean():.3f}</b> computers/student, "
                    f"facility score <b>{state_govt['facility_score'].mean():.1f}/10</b>, "
                    f"S:T ratio <b>{state_govt['student_teacher_ratio'].mean():.0f}:1</b>."
        })

    # 9. Cluster insight
    cluster_summary = w_filt.groupby("cluster_label").agg(
        wards=("ward_name","count"),
        avg_enrollment=("anganwadi_enroll_total","mean"),
        avg_tuition=("tuition_centres","mean"),
        avg_higher_ed=("higher_ed_institutions","mean")
    ).reset_index()
    if len(cluster_summary) > 0:
        best = cluster_summary.loc[cluster_summary["avg_enrollment"].idxmax()]
        insights.append({
            "icon": "🗺️",
            "title": "Ward Education Cluster Analysis",
            "body": f"KMeans clustering (k=3) identified <b>3 ward types</b>: "
                    + " | ".join([f"<b>{r['cluster_label']}</b>: {r['wards']} wards, avg enrollment {r['avg_enrollment']:.0f}"
                                  for _, r in cluster_summary.iterrows()])
                    + f". Top cluster '<b>{best['cluster_label']}</b>' averages "
                    f"{best['avg_tuition']:.1f} tuition centres and {best['avg_higher_ed']:.1f} higher-ed institutions per ward."
        })

    # 10. Study abroad & higher ed
    study_abroad_wards = w_filt[w_filt["study_abroad_centres"] > 0]
    insights.append({
        "icon": "✈️",
        "title": "Study Abroad & International Education Access",
        "body": f"<b>{len(study_abroad_wards)}</b> wards have study-abroad counselling centres "
                f"(avg <b>{w_filt['study_abroad_centres'].mean():.1f}</b> per ward). "
                "Wards with study-abroad centres tend to also have higher tuition centre counts, "
                f"suggesting concentrated education services in specific zones: "
                f"{', '.join(study_abroad_wards['ward_name'].tolist()) or 'None in selection'}."
    })

    # ── Display insights ──
    cols_ins = st.columns(2)
    for i, ins in enumerate(insights):
        with cols_ins[i % 2]:
            st.markdown(f"""
            <div class='insight-box'>
                <b>{ins['icon']} {ins['title']}</b><br>
                {ins['body']}
            </div>""", unsafe_allow_html=True)

    # ── What-If Generator ──
    st.markdown("---")
    st.markdown("<div class='section-header'>🤔 What-If Question Generator</div>", unsafe_allow_html=True)
    
    whatif_templates = [
        ("Select Ward Fort Kochi + filter Anganwadis",
         f"Ward Fort Kochi has {int(ward_df[ward_df['ward_name']=='Fort Kochi']['anganwadi_count'].values[0]) if 'Fort Kochi' in ward_df['ward_name'].values else 'N/A'} Anganwadis, "
         f"with {int(ward_df[ward_df['ward_name']=='Fort Kochi']['anganwadi_own_building'].values[0]) if 'Fort Kochi' in ward_df['ward_name'].values else 'N/A'} in own buildings. "
         "Gender split is 60% boys, 40% girls in Anganwadis — below the equity target."),
        ("Filter schools with <10 smart classrooms",
         f"These {len(s_filt[s_filt['smart_cls']<10])} schools average {s_filt[s_filt['smart_cls']<10]['students_total'].mean():.0f} students "
         f"vs {s_filt[s_filt['smart_cls']>=10]['students_total'].mean():.0f} for schools with ≥10 smart classrooms."),
        ("Choose 'No Playground' schools",
         f"{len(s_filt[s_filt['playground']=='No'])} schools lack playgrounds. "
         f"Their average distance to public transport is {s_filt[s_filt['playground']=='No']['dist_public_transport'].mean():.2f} km."),
        ("Compare wards with ≥3 tuition centres vs 0",
         f"Wards with ≥3 tuition centres: avg {w_filt[w_filt['tuition_centres']>=3]['higher_ed_institutions'].mean():.1f} higher-ed vs "
         f"{w_filt[w_filt['tuition_centres']==0]['higher_ed_institutions'].mean():.1f} for wards with none."),
        ("Select Special Schools + gender filter",
         f"Special school wards: {', '.join(w_filt[w_filt['special_schools']=='Yes']['ward_name'].tolist()) or 'None in selection'}. "
         f"School-level female ratio: {girls_pct:.1f}% in current selection."),
        ("Set distance to public transport >0.5 km",
         f"{len(s_filt[s_filt['dist_public_transport']>0.5])} schools are >0.5 km from public transport. "
         f"Average facility score: {s_filt[s_filt['dist_public_transport']>0.5]['facility_score'].mean():.1f}/10."),
        ("Cluster by VHS presence",
         f"Wards WITH VHS: avg enrollment {w_filt[w_filt['vhs_present']=='Yes']['anganwadi_enroll_total'].mean():.0f}. "
         f"Wards WITHOUT VHS: {w_filt[w_filt['vhs_present']=='No']['anganwadi_enroll_total'].mean():.0f}. "
         "VHS presence correlates with higher overall education activity."),
        ("Toggle all CBSE Private schools",
         f"CBSE Private ({len(s_filt[(s_filt['board']=='CBSE')&(s_filt['school_type']=='Private')])} schools): "
         f"avg {s_filt[(s_filt['board']=='CBSE')&(s_filt['school_type']=='Private')]['computers_per_student'].mean():.3f} computers/student, "
         f"facility score {s_filt[(s_filt['board']=='CBSE')&(s_filt['school_type']=='Private')]['facility_score'].mean():.1f}/10."),
        ("Analyze Government schools in high-enrollment wards",
         f"Government schools ({len(s_filt[s_filt['school_type']=='Government'])}): "
         f"avg S:T ratio {s_filt[s_filt['school_type']=='Government']['student_teacher_ratio'].mean():.0f}:1, "
         f"avg smart classrooms {s_filt[s_filt['school_type']=='Government']['smart_cls'].mean():.1f}."),
        ("Examine ICSE vs CBSE infrastructure",
         f"ICSE ({len(s_filt[s_filt['board']=='ICSE'])} schools): facility score {s_filt[s_filt['board']=='ICSE']['facility_score'].mean():.1f}/10. "
         f"CBSE ({len(s_filt[s_filt['board']=='CBSE'])} schools): facility score {s_filt[s_filt['board']=='CBSE']['facility_score'].mean():.1f}/10."),
    ]

    for q, a in whatif_templates:
        with st.expander(f"❓ If I {q}…"):
            st.markdown(f"<div class='insight-box'>📊 <b>Then I can derive:</b><br>{a}</div>",
                        unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:1rem;color:#888;font-size:0.75rem;margin-top:2rem;
            border-top:1px solid #ddd;'>
    Kochi Education Survey Dashboard • Data: Education-Ward_Level.xlsx + Education_Schools.xlsx • 
    Survey 2025 | Built with Streamlit + Plotly + Folium
</div>""", unsafe_allow_html=True)
