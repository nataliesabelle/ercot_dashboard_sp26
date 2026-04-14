"""
ERCOT Large Electronic Load Dashboard
Policy/research decision-support tool focused on data centers, AI, and crypto mining in ERCOT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ERCOT Large Electronic Load Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main background */
.main { background-color: #0f1117; }
[data-testid="stAppViewContainer"] { background-color: #0f1117; }
[data-testid="stSidebar"] { background-color: #1a1d27; }

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1e2130, #252840);
    border: 1px solid #333660;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
    margin-bottom: 8px;
}
.metric-card .metric-value {
    font-size: 1.8em;
    font-weight: 700;
    color: #4fc3f7;
    line-height: 1.1;
}
.metric-card .metric-label {
    font-size: 0.78em;
    color: #9ea3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

/* Status pills */
.pill-operational { background: #1b4332; color: #52b788; border-radius: 12px; padding: 2px 10px; font-size:0.78em; font-weight:600; }
.pill-approved { background: #1a3a5c; color: #74b9ff; border-radius: 12px; padding: 2px 10px; font-size:0.78em; font-weight:600; }
.pill-early { background: #3d2b00; color: #ffd166; border-radius: 12px; padding: 2px 10px; font-size:0.78em; font-weight:600; }
.pill-unknown { background: #2d1f3d; color: #bd93f9; border-radius: 12px; padding: 2px 10px; font-size:0.78em; font-weight:600; }

/* Section headers */
.section-header {
    font-size: 1.1em;
    font-weight: 700;
    color: #e0e3f0;
    border-bottom: 2px solid #333660;
    padding-bottom: 6px;
    margin-bottom: 12px;
}
/* Disclaimer banner */
.disclaimer {
    background: #1a1c2e;
    border-left: 4px solid #f39c12;
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 0.82em;
    color: #ccc;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── Data Loading ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_projects():
    df = pd.read_csv(DATA_DIR / "projects.csv")
    df["owner_tentative"] = df["owner_tentative"].astype(bool)
    df["in_service_year"] = pd.to_numeric(df["in_service_year"], errors="coerce").fillna(2030).astype(int)
    return df

@st.cache_data
def load_queue():
    return pd.read_csv(DATA_DIR / "queue_categories.csv")

@st.cache_data
def load_transmission():
    with open(DATA_DIR / "transmission_backbone.json") as f:
        return json.load(f)

projects_df = load_projects()
queue_df = load_queue()
tx_data = load_transmission()

# ── Color maps ────────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "Operational":            "#52b788",   # green
    "Under Review-Advancing": "#74b9ff",   # blue
    "To Be Operational":      "#ffd166",   # amber
    "Unknown":                "#bd93f9",   # purple
}
SECTOR_COLORS = {
    "AI / Data Center":   "#4fc3f7",
    "Crypto Mining":      "#ff7675",
    "Other LEL":          "#a29bfe",
}

# ── Sidebar: Filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ ERCOT Large Load")
    st.markdown("### 🗓 Year Slider")
    year_val = st.slider(
        "Show projects in service by:",
        min_value=2024, max_value=2030, value=2026, step=1,
        help="A project appears when its expected in-service year ≤ slider year. Projects with no public ISD default to 2030."
    )

    st.markdown("---")
    st.markdown("### 🔎 Project Filters")

    status_opts = ["All"] + sorted(projects_df["status_simple"].unique().tolist())
    status_filter = st.multiselect(
        "Status",
        options=status_opts[1:],
        default=status_opts[1:],
        help="Filter by simplified project status"
    )

    sector_opts = sorted(projects_df["sector"].unique().tolist())
    sector_filter = st.multiselect(
        "Sector / Type",
        options=sector_opts,
        default=sector_opts,
    )

    all_owners = sorted(projects_df["owner_display"].unique().tolist())
    owner_filter = st.multiselect(
        "Owner / Developer",
        options=all_owners,
        default=all_owners,
        help="* = tentative / inferred ownership"
    )

    mw_min, mw_max = int(projects_df["requested_mw"].min()), int(projects_df["requested_mw"].max())
    mw_range = st.slider(
        "Requested MW range",
        min_value=mw_min, max_value=mw_max,
        value=(mw_min, mw_max),
    )

    st.markdown("---")
    st.markdown("### 🗺 Map Overlays")
    show_backbone = st.checkbox("Current 345-kV backbone", value=True)
    show_765 = st.checkbox("765-kV conceptual layer", value=False)
    show_substations = st.checkbox("Key substations / hubs", value=True)

    st.markdown("---")
    st.markdown("### 📊 Context Chart")
    queue_chart_year = st.selectbox(
        "Queue chart year",
        options=sorted(queue_df["year"].unique().tolist()),
        index=4,  # 2026
    )

    st.markdown("---")
    st.markdown(
        "<div style='color:#6c7a89; font-size:0.75em;'>Data sources: ERCOT March 2026 TAC Report, "
        "ERCOT Dec 2024 Constraints Report, Oracle/OpenAI Stargate Fact Sheet, "
        "EIA Oct 2024, public news sources. See README for full citations.</div>",
        unsafe_allow_html=True
    )

# ── Apply Filters ─────────────────────────────────────────────────────────────
# For summary panels: apply year filter
filtered = projects_df[projects_df["in_service_year"] <= year_val].copy()

# For map: all projects (no year filter, but respect other filters for consistency)
map_data = projects_df.copy()

# Status, sector, owner, MW filters (applied to both)
if status_filter:
    filtered = filtered[filtered["status_simple"].isin(status_filter)]
    map_data = map_data[map_data["status_simple"].isin(status_filter)]
if sector_filter:
    filtered = filtered[filtered["sector"].isin(sector_filter)]
    map_data = map_data[map_data["sector"].isin(sector_filter)]
if owner_filter:
    filtered = filtered[filtered["owner_display"].isin(owner_filter)]
    map_data = map_data[map_data["owner_display"].isin(owner_filter)]
filtered = filtered[
    (filtered["requested_mw"] >= mw_range[0]) &
    (filtered["requested_mw"] <= mw_range[1])
]
map_data = map_data[
    (map_data["requested_mw"] >= mw_range[0]) &
    (map_data["requested_mw"] <= mw_range[1])
]

filtered["status_display"] = np.where(
    filtered["status_simple"] == "operational",
    "Operational",
    np.where(
        (filtered["status_simple"] == "under review-advancing") &
        (filtered["in_service_year"] <= year_val),
        "To Be Operational",
        np.where(
            filtered["status_simple"] == "under review-advancing",
            "Under Review-Advancing",
            "Unknown"
        )
    )
)

map_data["status_display"] = np.where(
    map_data["status_simple"] == "operational",
    "Operational",
    np.where(
        (map_data["status_simple"] == "under review-advancing") &
        (map_data["in_service_year"] <= year_val),
        "To Be Operational",
        np.where(
            map_data["status_simple"] == "under review-advancing",
            "Under Review-Advancing",
            "Unknown"
        )
    )
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#e0e3f0; font-size:1.7em; margin-bottom:4px;'>"
    "⚡ ERCOT Large Electronic Load Dashboard</h1>"
    "<div style='color:#9ea3b8; font-size:0.9em; margin-bottom:8px;'>"
    "Data centers · AI · Crypto mining · Large Electronic Loads · ERCOT-processed projects 2024 onward · "
    "Policy &amp; research decision-support tool</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='disclaimer'>⚠️ This is a prototype policy-research dashboard, not an engineering-grade contingency simulator. "
    "Ownership marked with <b>*</b> is inferred from public sources and marked tentative. "
    "Transmission layers are conceptual — not exact geometry. See README for full data methodology.</div>",
    unsafe_allow_html=True
)

# ── Summary Metrics Row ───────────────────────────────────────────────────────
total_mw = filtered["requested_mw"].sum()
n_projects = len(filtered)
status_counts = filtered["status_display"].value_counts().to_dict()

col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)

def metric_card(col, value, label):
    col.markdown(
        f"<div class='metric-card'>"
        f"<div class='metric-value'>{value}</div>"
        f"<div class='metric-label'>{label}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

metric_card(col_m1, f"{total_mw:,.0f}", "Total Req. MW")
metric_card(col_m2, f"{total_mw/1000:.1f} GW", "Total Req. GW")
metric_card(col_m3, str(n_projects), "Visible Projects")
metric_card(col_m4, str(status_counts.get("Operational", 0)), "Operational")
metric_card(col_m5, str(status_counts.get("Under Review-Advancing", 0)), "Under Review-Advancing")
metric_card(col_m6, str(status_counts.get("To Be Operational", 0)), "To Be Operational")

# ── Main Layout: Map + Right Panel ────────────────────────────────────────────
map_col, right_col = st.columns([3, 1], gap="medium")

with map_col:
    st.markdown(f"<div class='section-header'>📍 ERCOT Large Electronic Load Map — All Projects (Status as of {year_val})</div>", unsafe_allow_html=True)

    # Build map figure
    fig_map = go.Figure()

    # ── Transmission: current 345-kV backbone ────────────────────────────────
    if show_backbone:
        for corr in tx_data["current_backbone"]["corridors"]:
            lats = [p[0] for p in corr["path"]]
            lons = [p[1] for p in corr["path"]]
            color = "#4a90d9" if corr["voltage_kv"] >= 345 else "#2e5fa3"
            dash = "solid"
            width = 2 if corr["voltage_kv"] >= 345 else 1.5
            fig_map.add_trace(go.Scattergeo(
                lat=lats, lon=lons,
                mode="lines",
                line=dict(color=color, width=width, dash=dash),
                name=f"{corr['voltage_kv']}kV: {corr['name']}",
                legendgroup="backbone",
                legendgrouptitle_text="345-kV Backbone (current)",
                showlegend=True,
                hovertemplate=f"<b>{corr['name']}</b><br>{corr['voltage_kv']} kV<br>{corr['notes']}<extra></extra>",
            ))

    # ── Transmission: 765-kV conceptual ──────────────────────────────────────
    if show_765:
        for corr in tx_data["conceptual_765kv"]["corridors"]:
            lats = [p[0] for p in corr["path"]]
            lons = [p[1] for p in corr["path"]]
            fig_map.add_trace(go.Scattergeo(
                lat=lats, lon=lons,
                mode="lines",
                line=dict(color="#ff6b6b", width=3, dash="dash"),
                name=f"[CONCEPTUAL] {corr['name']}",
                legendgroup="765kv",
                legendgrouptitle_text="765-kV (CONCEPTUAL)",
                showlegend=True,
                hovertemplate=f"<b>{corr['name']}</b><br>765 kV CONCEPTUAL<br>{corr['notes']}<extra></extra>",
            ))

    # ── Substations ───────────────────────────────────────────────────────────
    if show_substations:
        subs = tx_data["major_substations"]
        fig_map.add_trace(go.Scattergeo(
            lat=[s["lat"] for s in subs],
            lon=[s["lon"] for s in subs],
            mode="markers+text",
            marker=dict(
                symbol="diamond",
                size=8,
                color="#f1c40f",
                line=dict(color="#333", width=1),
            ),
            text=[s["name"] for s in subs],
            textposition="top center",
            textfont=dict(size=8, color="#f1c40f"),
            name="Key Substations / Hubs",
            legendgroup="substations",
            showlegend=True,
            hovertemplate="<b>%{text}</b><extra></extra>",
        ))

    # ── Project Points ────────────────────────────────────────────────────────
    if not map_data.empty:
        # Scale marker size by MW (log scale, bounded)
        mw_vals = map_data["requested_mw"].values
        # Size: 10–50 based on log MW
        log_mw = np.log10(np.clip(mw_vals, 25, 10000))
        sizes = 10 + (log_mw - np.log10(25)) / (np.log10(10000) - np.log10(25)) * 40

        # Color by status
        marker_colors = map_data["status_display"].map(STATUS_COLORS).fillna("#ccc").tolist()

        # Hover text
        hover_parts = []
        for _, row in map_data.iterrows():
            owner_str = row["owner_display"]
            if row["owner_tentative"] and not owner_str.endswith("*"):
                owner_str = owner_str + "*"
            status_label = row["status_display"]
            loc = row["city"] if pd.notna(row["city"]) and row["city"] != "unknown" else ""
            county = row["county"] if pd.notna(row["county"]) and row["county"] != "unknown" else ""
            location_str = ", ".join(filter(None, [loc, f"{county} Co."]))
            notes_str = row["notes"] if pd.notna(row["notes"]) and str(row["notes"]) != "nan" else ""
            hover_parts.append(
                f"<b>{row['project_name']}</b><br>"
                f"Owner: {owner_str}<br>"
                f"Sector: {row['sector']}<br>"
                f"Requested: <b>{row['requested_mw']:,} MW</b><br>"
                f"Status: {status_label}<br>"
                f"In-service: {row['in_service_year']}<br>"
                f"Location: {location_str if location_str else 'unknown'}<br>"
                f"<i style='font-size:0.9em;color:#aaa'>{notes_str[:120] + '...' if len(str(notes_str)) > 120 else notes_str}</i>"
            )

        fig_map.add_trace(go.Scattergeo(
            lat=map_data["latitude"].tolist(),
            lon=map_data["longitude"].tolist(),
            mode="markers",
            marker=dict(
                size=sizes.tolist(),
                color=marker_colors,
                opacity=0.88,
                line=dict(color="white", width=0.7),
            ),
            text=map_data["project_name"].tolist(),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_parts,
            name="Projects",
            showlegend=False,
        ))

        # Add legend manually via invisible scatter per status
        for status, color in STATUS_COLORS.items():
            label_map = {
                "Operational": "🟢 Operational",
                "Under Review-Advancing": "🔵 Under Review-Advancing",
                "To Be Operational": "🟡 To Be Operational",
                "Unknown": "🟣 Unknown",
            }
            if status in map_data["status_display"].values:
                fig_map.add_trace(go.Scattergeo(
                    lat=[None], lon=[None],
                    mode="markers",
                    marker=dict(size=12, color=color, line=dict(color="white", width=0.7)),
                    name=label_map.get(status, status),
                    legendgroup="projects",
                    legendgrouptitle_text="Project Status",
                    showlegend=True,
                ))

    # ── Map Layout ────────────────────────────────────────────────────────────
    fig_map.update_layout(
        geo=dict(
            scope="usa",
            showland=True,
            landcolor="#1a1d27",
            showocean=True,
            oceancolor="#0f1117",
            showcountries=True,
            countrycolor="#333660",
            showsubunits=True,
            subunitcolor="#2a2f44",
            showcoastlines=True,
            coastlinecolor="#2a2f44",
            projection_type="albers usa",
            center=dict(lat=31.5, lon=-99.5),
            lataxis_range=[25.5, 37.0],
            lonaxis_range=[-107.0, -93.5],
            bgcolor="#0f1117",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        legend=dict(
            bgcolor="rgba(20,22,35,0.92)",
            bordercolor="#333660",
            borderwidth=1,
            font=dict(color="#d0d3e8", size=11),
            x=0.01, y=0.99,
            xanchor="left", yanchor="top",
            groupclick="toggleitem",
        ),
        font=dict(color="#d0d3e8"),
    )

    st.plotly_chart(fig_map, use_container_width=True)

    # ── Map legend note ───────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.77em; color:#6c7a89;'>"
        "Point size ∝ log(requested MW). 345-kV backbone is a conceptual schematic of major corridors (sources: ERCOT Dec 2024 Constraints Report). "
        "765-kV layer (if enabled) is <b>CONCEPTUAL</b> based on ERCOT Permian Basin Reliability Plan and Oncor Dec 2025 filing. "
        "Transmission geometry is simplified — not engineering-grade. * = tentative ownership."
        "</div>",
        unsafe_allow_html=True
    )

# ── Right Panel: Breakdowns ───────────────────────────────────────────────────
with right_col:
    st.markdown("<div class='section-header'>📊 Summary Panels</div>", unsafe_allow_html=True)

    # Top owners by MW
    if not filtered.empty:
        top_owners = (
            filtered.groupby("owner_display")["requested_mw"]
            .sum()
            .sort_values(ascending=False)
            .head(8)
            .reset_index()
        )
        fig_owners = px.bar(
            top_owners, x="requested_mw", y="owner_display",
            orientation="h",
            title="Top Owners (Visible MW)",
            labels={"requested_mw": "MW", "owner_display": ""},
            color_discrete_sequence=["#4fc3f7"],
        )
        fig_owners.update_layout(
            height=260, margin=dict(l=0, r=0, t=35, b=0),
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font=dict(color="#d0d3e8", size=10),
            title_font=dict(size=12),
            yaxis=dict(tickfont=dict(size=9)),
        )
        fig_owners.update_traces(texttemplate="%{x:,.0f}", textposition="outside", textfont_size=9)
        st.plotly_chart(fig_owners, use_container_width=True)

        # Sector breakdown donut
        sector_sum = filtered.groupby("sector")["requested_mw"].sum().reset_index()
        fig_sector = px.pie(
            sector_sum, values="requested_mw", names="sector",
            title="Sector Breakdown (Visible MW)",
            hole=0.55,
            color="sector",
            color_discrete_map=SECTOR_COLORS,
        )
        fig_sector.update_layout(
            height=240, margin=dict(l=0, r=0, t=35, b=0),
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font=dict(color="#d0d3e8", size=10),
            title_font=dict(size=12),
            legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
            showlegend=True,
        )
        st.plotly_chart(fig_sector, use_container_width=True)

        # Status breakdown bar (all projects, year-driven status split)
        status_breakdown_df = projects_df.copy()
        status_breakdown_df["status_display"] = np.where(
            status_breakdown_df["status_simple"] == "operational",
            "Operational",
            np.where(
                (status_breakdown_df["status_simple"] == "under review-advancing") &
                (status_breakdown_df["in_service_year"] <= year_val),
                "To Be Operational",
                np.where(
                    status_breakdown_df["status_simple"] == "under review-advancing",
                    "Under Review-Advancing",
                    "Unknown"
                )
            )
        )
        status_sum = status_breakdown_df.groupby("status_display")["requested_mw"].sum().reset_index()
        total_mw_all = projects_df["requested_mw"].sum()
        fig_status = px.bar(
            status_sum, x="status_display", y="requested_mw",
            title="Status Breakdown (Total Project MW)",
            labels={"requested_mw": "MW", "status_display": ""},
            color="status_display",
            color_discrete_map=STATUS_COLORS,
            category_orders={"status_display": ["Operational", "Under Review-Advancing", "To Be Operational", "Unknown"]},
        )
        fig_status.update_layout(
            height=220, margin=dict(l=0, r=0, t=35, b=0),
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font=dict(color="#d0d3e8", size=10),
            title_font=dict(size=12),
            showlegend=False,
            xaxis=dict(tickfont=dict(size=9)),
            yaxis=dict(range=[0, total_mw_all]),
        )
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("No projects match current filters.")

# ── ERCOT Queue Context Chart ─────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div class='section-header'>📈 ERCOT Aggregate Queue Categories (not one-dot-per-project)</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div class='disclaimer'>"
    "This chart uses <b>ERCOT's official queue category totals</b> from the March 2026 TAC Large Load Interconnection Status Update. "
    "These are aggregate MW counts across <i>all</i> ERCOT large load types — not filtered to data centers only. "
    "Projected years (2026–2030) are from ERCOT's own projected growth table. "
    "Source: ERCOT Large Load Integration Team, March 13, 2026."
    "</div>",
    unsafe_allow_html=True
)

queue_year_df = queue_df[queue_df["year"] == queue_chart_year].copy()

CAT_ORDER = [
    "No Studies Submitted",
    "Under ERCOT Review",
    "Planning Studies Approved",
    "Approved to Energize but Not Operational",
    "Observed Energized",
]
CAT_COLORS = {
    "No Studies Submitted":                  "#ff7675",
    "Under ERCOT Review":                    "#a29bfe",
    "Planning Studies Approved":             "#636e72",
    "Approved to Energize but Not Operational": "#00b894",
    "Observed Energized":                    "#00cec9",
}

# Full-timeline stacked bar
q_chart, q_table_col = st.columns([2, 1])

with q_chart:
    fig_queue = px.bar(
        queue_df[queue_df["mw"] > 0],
        x="year",
        y="mw",
        color="status_category",
        title=f"ERCOT Large Load Queue — All Categories by Year (2022–2030)",
        labels={"mw": "MW", "year": "Year", "status_category": "Queue Status"},
        color_discrete_map=CAT_COLORS,
        category_orders={"status_category": CAT_ORDER},
        barmode="stack",
    )
    fig_queue.update_layout(
        height=380, margin=dict(l=0, r=0, t=45, b=0),
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font=dict(color="#d0d3e8", size=11),
        legend=dict(
            bgcolor="rgba(20,22,35,0.85)",
            bordercolor="#333660",
            borderwidth=1,
            font=dict(size=10),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
        xaxis=dict(type="category", tickfont=dict(size=11)),
        yaxis_title="MW (all ERCOT large load types)",
    )
    # Highlight selected year
    yr_list = sorted(queue_df["year"].unique().tolist())
    yr_idx = yr_list.index(queue_chart_year)
    fig_queue.add_vrect(
        x0=yr_idx - 0.4, x1=yr_idx + 0.4,
        fillcolor="rgba(255,255,255,0.05)",
        line_color="rgba(255,255,255,0.4)",
        line_width=1.5,
        annotation_text=f"Selected: {queue_chart_year}",
        annotation_font_size=10,
        annotation_font_color="#fff",
    )
    st.plotly_chart(fig_queue, use_container_width=True)

with q_table_col:
    st.markdown(f"**{queue_chart_year} Queue Snapshot**")
    tbl = queue_year_df[queue_year_df["mw"] > 0][["status_category", "mw", "project_count"]].copy()
    tbl.columns = ["Status", "MW", "Projects"]
    tbl["MW"] = tbl["MW"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(tbl, hide_index=True, use_container_width=True)

    st.markdown(
        "<div style='font-size:0.76em; color:#6c7a89; margin-top:8px;'>"
        "Source: ERCOT Large Load Integration Team, March 2026 TAC Report. "
        "2026–2030 values are ERCOT projected growth from the Actual and Projected Large Load Growth table."
        "</div>",
        unsafe_allow_html=True
    )

# ── Project Table ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<div class='section-header'>📋 Project Table (filtered)</div>", unsafe_allow_html=True)

show_table = st.checkbox("Show/hide project table", value=True)
if show_table and not filtered.empty:
    display_cols = [
        "project_name", "sector", "owner_display", "requested_mw",
        "status_display", "in_service_year", "city", "county",
        "owner_tentative", "notes"
    ]
    tbl_df = filtered[display_cols].copy()
    tbl_df.columns = [
        "Project", "Sector", "Owner", "Requested MW",
        "Status", "ISD Year", "City", "County",
        "Owner Tentative?", "Notes"
    ]
    tbl_df["Requested MW"] = tbl_df["Requested MW"].apply(lambda x: f"{x:,.0f}")

    st.dataframe(
        tbl_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Owner Tentative?": st.column_config.CheckboxColumn("Tentative?"),
            "Notes": st.column_config.TextColumn("Notes", width="large"),
        }
    )
    st.caption(
        f"Showing {len(filtered)} of {len(projects_df)} projects | "
        "* = tentative/inferred ownership | ISD = expected in-service date | "
        "Default ISD = 2030 when no public date available"
    )
elif not show_table:
    pass
else:
    st.info("No projects match current filters.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='font-size:0.77em; color:#555e78; text-align:center;'>"
    "ERCOT Large Electronic Load Dashboard · UT Austin Energy Systems Course Project · April 2026 · "
    "Data sources: ERCOT March 2026 TAC Report, ERCOT Dec 2024 Constraints Report, EIA Oct 2024, "
    "Oracle/OpenAI Stargate Fact Sheet, Texas Observer, Pexapark, Fort Worth Pulse, "
    "The Real Deal, ENGIE Resources, Latitude Media, Utility Dive. "
    "This is a prototype research tool — not an operational or engineering-grade system."
    "</div>",
    unsafe_allow_html=True
)
