"""
Population Dynamics Map — Texas County-Level Dashboard
-------------------------------------------------------
Interactive choropleth map + projection charts for:
  • Population growth (2020–2050)
  • Water demand growth (TWDB 2022 SWP)
  • Electricity demand growth (ERCOT 2024 LTDEF)
  • New large-load additions (MW by county)

Run:
    streamlit run app.py
"""

import json
import os
import warnings

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import FloatImage
from streamlit_folium import st_folium

warnings.filterwarnings("ignore")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Texas Population Dynamics Map",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GEOJSON_PATH = os.path.join(DATA_DIR, "texas_counties.geojson")
MERGED_PATH = os.path.join(DATA_DIR, "merged_county_data.csv")
POP_PATH = os.path.join(DATA_DIR, "population_projections.csv")
WATER_PATH = os.path.join(DATA_DIR, "water_demand.csv")
ELEC_PATH = os.path.join(DATA_DIR, "electricity_demand.csv")

# ── Load data (cached) ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(MERGED_PATH, dtype={"fips": str})
    df["fips"] = df["fips"].str.zfill(5)
    pop = pd.read_csv(POP_PATH, dtype={"fips": str})
    water = pd.read_csv(WATER_PATH, dtype={"fips": str})
    elec = pd.read_csv(ELEC_PATH, dtype={"fips": str})
    with open(GEOJSON_PATH) as f:
        geojson = json.load(f)
    return df, pop, water, elec, geojson


df, pop_df, water_df, elec_df, geojson = load_data()

# ── Layer configuration ────────────────────────────────────────────────────────
YEAR_OPTIONS = [2020, 2030, 2040, 2050]

LAYERS = {
    "Population Growth (2020–2050)": {
        "col_pattern": "pop_{year}",
        "growth_col": "pop_growth_pct",
        "unit": "people",
        "colorscale": "YlOrRd",
        "legend_caption": "Population",
        "description": "Projected population by county (Texas Demographic Center 2022)",
    },
    "Water Demand Growth (2020–2050)": {
        "col_pattern": "water_{year}_kaf",
        "growth_col": "water_growth_pct",
        "unit": "thousand acre-feet",
        "colorscale": "YlGnBu",
        "legend_caption": "Water Demand (kAF)",
        "description": "Total water demand by county (TWDB 2022 State Water Plan)",
    },
    "Electricity Demand Growth (2020–2050)": {
        "col_pattern": "elec_peak_{year}_mw",
        "growth_col": "elec_growth_pct",
        "unit": "MW (peak)",
        "colorscale": "OrRd",
        "legend_caption": "Peak Demand (MW)",
        "description": "ERCOT peak electricity demand by county (ERCOT 2024 LTDEF)",
    },
    "New Large Load Added (MW)": {
        "col_pattern": None,  # static column
        "col_static": "new_load_mw",
        "growth_col": None,
        "unit": "MW",
        "colorscale": "RdPu",
        "legend_caption": "New Load (MW)",
        "description": "Proposed/approved new large load additions by county",
    },
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🗺️ Texas Population\nDynamics Map")
    st.markdown("---")

    layer_choice = st.selectbox(
        "📊 Map Layer",
        list(LAYERS.keys()),
        index=0,
    )

    year_choice = st.select_slider(
        "📅 Projection Year",
        options=YEAR_OPTIONS,
        value=2030,
        help="Move the slider to change the projection year shown on the map and charts.",
    )
    if layer_choice == "New Large Load Added (MW)":
        st.info("New load layer is static — not time-varying.")

    st.markdown("---")
    st.markdown("**Overlay Options**")
    show_datacenter_markers = st.checkbox("Show data center projects", value=True)

    st.markdown("---")
    st.caption(
        "**Sources:** Texas Demographic Center (2022), "
        "TWDB 2022 State Water Plan, ERCOT 2024 LTDEF, "
        "project queue data (gen_dashboard)"
    )

# ── Determine active column ────────────────────────────────────────────────────
layer_cfg = LAYERS[layer_choice]

if layer_cfg.get("col_pattern"):
    active_col = layer_cfg["col_pattern"].replace("{year}", str(year_choice))
else:
    active_col = layer_cfg["col_static"]

# ── State-level KPI metrics ────────────────────────────────────────────────────
st.title("🗺️ Texas Population Dynamics Dashboard")
st.caption(layer_cfg["description"])

total_2020_pop = df["pop_2020"].sum()
total_2050_pop = df["pop_2050"].sum()
total_water_2050 = df["water_2050_kaf"].sum()
total_elec_2050 = df["elec_peak_2050_mw"].sum()
total_new_load = df["new_load_mw"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("TX Population 2020", f"{total_2020_pop/1e6:.1f}M")
with k2:
    st.metric(
        "TX Population 2050",
        f"{total_2050_pop/1e6:.1f}M",
        delta=f"+{(total_2050_pop-total_2020_pop)/1e6:.1f}M",
    )
with k3:
    st.metric("Water Demand 2050", f"{total_water_2050/1000:.1f}M acre-ft")
with k4:
    st.metric("Peak Demand 2050", f"{total_elec_2050/1000:.0f} GW")
with k5:
    st.metric("Total New Load (MW)", f"{total_new_load:,.0f} MW")

st.markdown("---")

# ── Build Folium Map ────────────────────────────────────────────────────────────
COLOR_MAPS = {
    "YlOrRd": "YlOrRd",
    "YlGnBu": "YlGnBu",
    "OrRd": "OrRd",
    "RdPu": "RdPu",
}

m = folium.Map(
    location=[31.0, -99.5],
    zoom_start=6,
    tiles=None,
    prefer_canvas=True,
)

# Basemap: CartoDB Dark Matter
folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    name="Dark Matter",
    max_zoom=19,
    subdomains="abcd",
).add_to(m)

# Choropleth layer
choro = folium.Choropleth(
    geo_data=geojson,
    name=layer_choice,
    data=df[["fips", active_col]],
    columns=["fips", active_col],
    key_on="feature.id",
    fill_color=layer_cfg["colorscale"],
    fill_opacity=0.75,
    line_opacity=0.3,
    line_color="#ffffff",
    legend_name=f"{layer_cfg['legend_caption']} ({year_choice})",
    nan_fill_color="gray",
    nan_fill_opacity=0.2,
    highlight=True,
)
choro.add_to(m)

# Tooltip: show county name + active value on hover
# Build a lookup dict fips→value
val_lookup = dict(zip(df["fips"], df[active_col]))
name_lookup = dict(zip(df["fips"], df["county"]))

style_fn = lambda feat: {
    "fillOpacity": 0.0,
    "weight": 0,
    "color": "transparent",
}
highlight_fn = lambda feat: {
    "fillOpacity": 0.15,
    "weight": 2,
    "color": "#ffffff",
}

# Popup + tooltip via GeoJsonTooltip
tooltip_fields = []
tooltip_aliases = []

# Merge data back into geojson for tooltip
fips_to_row = df.set_index("fips").to_dict(orient="index")
for feat in geojson["features"]:
    fid = feat["id"].zfill(5)
    row = fips_to_row.get(fid, {})
    feat["properties"].update({
        "county": row.get("county", fid),
        "pop_2020": f'{row.get("pop_2020", 0):,}',
        "pop_2050": f'{row.get("pop_2050", 0):,}',
        "pop_growth": f'{row.get("pop_growth_pct", 0):.1f}%',
        "water_2050": f'{row.get("water_2050_kaf", 0):.1f} kAF',
        "water_growth": f'{row.get("water_growth_pct", 0):.1f}%',
        "elec_2050": f'{row.get("elec_peak_2050_mw", 0):.0f} MW',
        "elec_growth": f'{row.get("elec_growth_pct", 0):.1f}%',
        "new_load": f'{row.get("new_load_mw", 0):,.1f} MW',
        "ercot_zone": row.get("ercot_zone", ""),
    })

folium.GeoJson(
    geojson,
    style_function=style_fn,
    highlight_function=highlight_fn,
    tooltip=folium.GeoJsonTooltip(
        fields=["county", "pop_2020", "pop_2050", "pop_growth",
                "water_2050", "water_growth",
                "elec_2050", "elec_growth", "new_load", "ercot_zone"],
        aliases=["County:", "Population 2020:", "Population 2050:", "Pop Growth:",
                 "Water Demand 2050:", "Water Growth:",
                 "Peak Demand 2050:", "Elec Growth:", "New Load (MW):", "ERCOT Zone:"],
        sticky=True,
        style=(
            "background-color: #1a1a2e; color: white; "
            "font-family: monospace; font-size: 12px; "
            "border: 1px solid #444; border-radius: 4px; padding: 8px;"
        ),
    ),
    name="County Tooltips",
).add_to(m)

# Data center project markers
if show_datacenter_markers:
    projects_path = os.path.join(DATA_DIR, "..", "..", "gen_dashboard", "data", "projects.csv")
    projects_path = os.path.normpath(projects_path)
    if os.path.exists(projects_path):
        proj_df = pd.read_csv(projects_path)
        proj_df = proj_df.dropna(subset=["latitude", "longitude"])
        for _, row in proj_df.iterrows():
            mw = row.get("requested_mw", 0)
            status = row.get("status_simple", "Unknown")
            color = {
                "Operational": "green",
                "Under Construction": "orange",
                "Under Review": "blue",
                "Approved": "darkblue",
            }.get(status, "gray")
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=max(5, min(20, float(mw or 0) / 200)),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=folium.Popup(
                    f"<b>{row.get('project_name', '')}</b><br>"
                    f"Status: {status}<br>"
                    f"Capacity: {mw:,} MW<br>"
                    f"Owner: {row.get('owner_display', '')}",
                    max_width=220,
                ),
                tooltip=f"{row.get('project_name', '')} ({mw:,} MW)",
            ).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# ── Render map ─────────────────────────────────────────────────────────────────
map_col, legend_col = st.columns([4, 1])
with map_col:
    st_folium(m, width=None, height=580, returned_objects=[], use_container_width=True)
with legend_col:
    st.markdown("#### 🔵 Data Centers")
    st.markdown("""
<div style='font-size:13px; line-height:2'>
🟢 Operational<br>
🟠 Under Construction<br>
🔵 Under Review / Approved<br>
⚪ Unknown
</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### 📌 How to use")
    st.markdown("""
<div style='font-size:12px; color:#aaa;'>
• Change the <b>Map Layer</b> and <b>Projection Year</b> in the sidebar<br>
• Hover over a county for stats<br>
• Click data center circles for project details<br>
• Use the layer control on the map to toggle overlays
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS SECTION
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📈 Texas Projection Charts (2020–2050)")

CHART_THEME = {
    "template": "plotly_dark",
    "paper_bgcolor": "#0e1117",
    "plot_bgcolor": "#0e1117",
    "font_color": "#e0e0e0",
}

# ── Chart 1: Population — top 15 counties ─────────────────────────────────────
top_pop = pop_df.nlargest(15, "pop_2050")[
    ["county", "pop_2020", "pop_2030", "pop_2040", "pop_2050"]
].copy()
top_pop_melt = top_pop.melt(id_vars="county", var_name="year", value_name="population")
top_pop_melt["year"] = top_pop_melt["year"].str.extract(r"(\d{4})").astype(int)
top_pop_melt["population_M"] = top_pop_melt["population"] / 1e6

# ── Chart 2: Water demand — stacked by TWDB region ────────────────────────────
water_region = (
    water_df.groupby("twdb_region")[
        ["demand_2020_kaf", "demand_2030_kaf", "demand_2040_kaf", "demand_2050_kaf"]
    ]
    .sum()
    .reset_index()
)
water_region_melt = water_region.melt(
    id_vars="twdb_region", var_name="year", value_name="demand_kaf"
)
water_region_melt["year"] = water_region_melt["year"].str.extract(r"(\d{4})").astype(int)
water_region_melt["demand_MAF"] = water_region_melt["demand_kaf"] / 1000

REGION_NAMES = {
    "A": "A — Panhandle", "B": "B — Red River", "C": "C — Brazos-DFW",
    "D": "D — East Texas", "E": "E — El Paso", "F": "F — Permian Basin",
    "G": "G — Brazos-Central", "H": "H — Houston-Gulf", "I": "I — SE Texas",
    "J": "J — Hill Country", "K": "K — Central Corridor", "L": "L — San Antonio",
    "M": "M — Lower Rio Grande", "N": "N — Coastal Bend", "O": "O — South Plains",
    "P": "P — South Texas",
}
water_region_melt["region_name"] = water_region_melt["twdb_region"].map(REGION_NAMES)

# ── Chart 3: Electricity demand — by ERCOT zone ───────────────────────────────
elec_zone = (
    elec_df.groupby("ercot_zone")[
        ["peak_mw_2020", "peak_mw_2030", "peak_mw_2040", "peak_mw_2050"]
    ]
    .sum()
    .reset_index()
)
elec_zone_melt = elec_zone.melt(
    id_vars="ercot_zone", var_name="year", value_name="peak_mw"
)
elec_zone_melt["year"] = elec_zone_melt["year"].str.extract(r"(\d{4})").astype(int)
elec_zone_melt["peak_gw"] = elec_zone_melt["peak_mw"] / 1000

ZONE_NAMES = {
    "NCENT": "North Central (DFW)",
    "SCENT": "South Central (Austin-SA)",
    "COAST": "Coast (Houston)",
    "SOUTH": "South (RGV-SA)",
    "NORTH": "North",
    "EAST": "East",
    "WEST": "West (Permian)",
    "FWEST": "Far West",
}
elec_zone_melt["zone_name"] = elec_zone_melt["ercot_zone"].map(ZONE_NAMES)

# ── Chart 4: Comparative growth index by major metro region ───────────────────
METRO_REGIONS = {
    "DFW Metro": ["48113", "48439", "48085", "48121", "48257", "48139", "48367", "48397"],
    "Houston Metro": ["48201", "48157", "48339", "48039", "48167", "48473"],
    "Austin-SA Corridor": ["48453", "48491", "48209", "48029", "48187", "48091"],
    "Rio Grande Valley": ["48215", "48061", "48427", "48489"],
    "West Texas": ["48329", "48135", "48303", "48451", "48141"],
    "Rest of Texas": None,  # everything else
}

metro_rows = []
major_fips = {f for fips_list in METRO_REGIONS.values() if fips_list for f in fips_list}

for region_name, fips_list in METRO_REGIONS.items():
    if fips_list:
        sub = df[df["fips"].isin(fips_list)]
    else:
        sub = df[~df["fips"].isin(major_fips)]
    pop_growth = (sub["pop_2050"].sum() - sub["pop_2020"].sum()) / sub["pop_2020"].sum() * 100
    water_growth = (
        (sub["water_2050_kaf"].sum() - sub["water_2020_kaf"].sum())
        / sub["water_2020_kaf"].sum() * 100
    )
    elec_growth = (
        (sub["elec_peak_2050_mw"].sum() - sub["elec_peak_2020_mw"].sum())
        / sub["elec_peak_2020_mw"].sum() * 100
    )
    metro_rows.append({
        "region": region_name,
        "Population": round(pop_growth, 1),
        "Water Demand": round(water_growth, 1),
        "Electricity Demand": round(elec_growth, 1),
    })

metro_df = pd.DataFrame(metro_rows)
metro_melt = metro_df.melt(id_vars="region", var_name="variable", value_name="growth_pct")

# ── Layout: 2×2 chart grid ────────────────────────────────────────────────────
chart_row1_left, chart_row1_right = st.columns(2)

# Chart 1 — Population projections
with chart_row1_left:
    st.markdown("##### 👥 Population Projections — Top 15 Counties")
    fig1 = px.line(
        top_pop_melt,
        x="year",
        y="population_M",
        color="county",
        markers=True,
        labels={"population_M": "Population (millions)", "year": "Year", "county": "County"},
        template="plotly_dark",
    )
    fig1.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(font=dict(size=10), x=0, y=1),
        margin=dict(l=40, r=20, t=20, b=40),
        height=380,
        xaxis=dict(tickvals=YEAR_OPTIONS),
    )
    fig1.update_traces(line=dict(width=2))
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2 — Water demand by TWDB region (stacked bar)
with chart_row1_right:
    st.markdown("##### 💧 Water Demand by TWDB Region (Million Acre-Feet)")
    fig2 = px.bar(
        water_region_melt,
        x="year",
        y="demand_MAF",
        color="region_name",
        barmode="stack",
        labels={"demand_MAF": "Demand (million acre-ft)", "year": "Year", "region_name": "TWDB Region"},
        template="plotly_dark",
    )
    fig2.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(font=dict(size=9), x=1.01, y=1),
        margin=dict(l=40, r=20, t=20, b=40),
        height=380,
        xaxis=dict(tickvals=YEAR_OPTIONS),
    )
    st.plotly_chart(fig2, use_container_width=True)

chart_row2_left, chart_row2_right = st.columns(2)

# Chart 3 — Electricity demand by ERCOT zone
with chart_row2_left:
    st.markdown("##### ⚡ Peak Electricity Demand by ERCOT Zone (GW)")
    fig3 = px.area(
        elec_zone_melt.sort_values(["zone_name", "year"]),
        x="year",
        y="peak_gw",
        color="zone_name",
        labels={"peak_gw": "Peak Demand (GW)", "year": "Year", "zone_name": "ERCOT Zone"},
        template="plotly_dark",
    )
    fig3.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(font=dict(size=10), x=0, y=1),
        margin=dict(l=40, r=20, t=20, b=40),
        height=380,
        xaxis=dict(tickvals=YEAR_OPTIONS),
    )
    st.plotly_chart(fig3, use_container_width=True)

# Chart 4 — Comparative growth index
with chart_row2_right:
    st.markdown("##### 📊 % Growth 2020→2050 by Major Region")
    fig4 = px.bar(
        metro_melt,
        x="region",
        y="growth_pct",
        color="variable",
        barmode="group",
        labels={"growth_pct": "% Growth (2020→2050)", "region": "Region", "variable": "Metric"},
        template="plotly_dark",
        color_discrete_map={
            "Population": "#f97316",
            "Water Demand": "#3b82f6",
            "Electricity Demand": "#a855f7",
        },
    )
    fig4.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(font=dict(size=10), x=0, y=1),
        margin=dict(l=40, r=20, t=20, b=60),
        height=380,
        xaxis=dict(tickangle=-20, tickfont=dict(size=10)),
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── Data table (expandable) ────────────────────────────────────────────────────
with st.expander("📋 View County Data Table"):
    display_cols = [
        "county", "ercot_zone", "twdb_region",
        "pop_2020", "pop_2050", "pop_growth_pct",
        "water_2020_kaf", "water_2050_kaf", "water_growth_pct",
        "elec_peak_2020_mw", "elec_peak_2050_mw", "elec_growth_pct",
        "new_load_mw",
    ]
    st.dataframe(
        df[display_cols].sort_values("pop_2050", ascending=False),
        use_container_width=True,
        height=400,
        column_config={
            "county": "County",
            "ercot_zone": "ERCOT Zone",
            "twdb_region": "TWDB Region",
            "pop_2020": st.column_config.NumberColumn("Pop 2020", format="%,d"),
            "pop_2050": st.column_config.NumberColumn("Pop 2050", format="%,d"),
            "pop_growth_pct": st.column_config.NumberColumn("Pop Growth %", format="%.1f%%"),
            "water_2020_kaf": st.column_config.NumberColumn("Water 2020 (kAF)", format="%.1f"),
            "water_2050_kaf": st.column_config.NumberColumn("Water 2050 (kAF)", format="%.1f"),
            "water_growth_pct": st.column_config.NumberColumn("Water Growth %", format="%.1f%%"),
            "elec_peak_2020_mw": st.column_config.NumberColumn("Elec 2020 (MW)", format="%.0f"),
            "elec_peak_2050_mw": st.column_config.NumberColumn("Elec 2050 (MW)", format="%.0f"),
            "elec_growth_pct": st.column_config.NumberColumn("Elec Growth %", format="%.1f%%"),
            "new_load_mw": st.column_config.NumberColumn("New Load (MW)", format="%.1f"),
        },
    )

st.caption(
    "Data sources: Texas Demographic Center 2022 Projections | "
    "TWDB 2022 State Water Plan | ERCOT 2024 Long-Term Demand & Energy Forecast | "
    "ERCOT Interconnection Queue (processed)"
)
