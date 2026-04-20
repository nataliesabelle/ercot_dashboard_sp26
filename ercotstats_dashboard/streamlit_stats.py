from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    DATA_DIR / "clean_generation_data.parquet",
    DATA_DIR / "clean_generation_data.csv",
]
TIME_COL = "interval_start"
FUEL_COL = "fuel_type"
VALUE_COL = "generation_mw"

FUEL_ORDER = [
    "BIOMASS", "COAL", "GAS", "GAS-CC", "HYDRO",
    "NUCLEAR", "OTHER", "SOLAR", "WIND", "WSL",
]

FUEL_COLORS = {
    "BIOMASS": "#1f77b4",
    "COAL": "#ff7f0e",
    "GAS": "#2ca02c",
    "GAS-CC": "#d62728",
    "HYDRO": "#9467bd",
    "NUCLEAR": "#8c564b",
    "OTHER": "#e377c2",
    "SOLAR": "#fbbf24",
    "WIND": "#22c55e",
    "WSL": "#17becf",
}

FUEL_LABELS = {
    "BIOMASS": "Biomass",
    "COAL": "Coal",
    "GAS": "Natural Gas",
    "GAS-CC": "Gas Combined Cycle",
    "HYDRO": "Hydroelectric",
    "NUCLEAR": "Nuclear",
    "OTHER": "Other",
    "SOLAR": "Solar",
    "WIND": "Wind",
    "WSL": "WSL",
}


def _find_data_path() -> Path:
    for path in DATA_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find the ERCOT stats dataset in the ercotstats_dashboard folder."
    )


@st.cache_data(show_spinner=False)
def load_generation_data() -> pd.DataFrame:
    data_path = _find_data_path()

    if data_path.suffix.lower() == ".csv":
        df = pd.read_csv(data_path)
    else:
        df = pd.read_parquet(data_path)

    required = {TIME_COL, FUEL_COL, VALUE_COL}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.copy()
    df[TIME_COL] = pd.to_datetime(df[TIME_COL], errors="coerce")
    df[FUEL_COL] = df[FUEL_COL].astype(str).str.upper().str.strip()
    df[VALUE_COL] = pd.to_numeric(df[VALUE_COL], errors="coerce")
    df = df.dropna(subset=[TIME_COL, FUEL_COL, VALUE_COL]).sort_values(TIME_COL)
    return df.reset_index(drop=True)


def infer_interval_minutes(df: pd.DataFrame) -> int:
    timestamps = df[TIME_COL].drop_duplicates().sort_values()
    if len(timestamps) < 2:
        return 15

    diffs = timestamps.diff().dropna().dt.total_seconds() / 60
    if diffs.empty:
        return 15
    return int(round(float(diffs.median())))


def filter_complete_periods(df: pd.DataFrame, interval_minutes: int) -> pd.DataFrame:
    filtered = df.copy()
    expected_steps_per_day = int(round(24 * 60 / interval_minutes))

    daily_steps = (
        filtered[[TIME_COL]]
        .drop_duplicates()
        .assign(date=lambda frame: frame[TIME_COL].dt.floor("D"))
        .groupby("date")
        .size()
    )
    complete_days = daily_steps[daily_steps >= expected_steps_per_day * 0.95].index

    filtered["date"] = filtered[TIME_COL].dt.floor("D")
    filtered = filtered[filtered["date"].isin(complete_days)].copy()

    filtered["month"] = filtered[TIME_COL].dt.to_period("M")
    month_counts = filtered[["date", "month"]].drop_duplicates().groupby("month").size()
    month_expected = pd.Series(
        {month: month.days_in_month for month in month_counts.index}, dtype=float
    )
    complete_months = month_counts[month_counts >= month_expected * 0.95].index
    filtered = filtered[filtered["month"].isin(complete_months)].copy()

    filtered["year"] = filtered[TIME_COL].dt.year
    year_counts = filtered[["month", "year"]].drop_duplicates().groupby("year").size()
    complete_years = year_counts[year_counts >= 12].index
    filtered = filtered[filtered["year"].isin(complete_years)].copy()

    return filtered.reset_index(drop=True)


def compute_kpis_for_year(df_year: pd.DataFrame) -> Dict[str, float | str | None]:
    total_ts_year = df_year.groupby(TIME_COL, as_index=False)[VALUE_COL].sum()
    daily_year = (
        df_year.assign(date=df_year[TIME_COL].dt.floor("D"))
        .groupby("date", as_index=False)[VALUE_COL]
        .sum()
    )
    total_by_fuel_year = (
        df_year.groupby(FUEL_COL, as_index=False)[VALUE_COL]
        .sum()
        .sort_values(VALUE_COL, ascending=False)
    )

    peak_mw = total_ts_year[VALUE_COL].max() if not total_ts_year.empty else np.nan
    avg_mw = total_ts_year[VALUE_COL].mean() if not total_ts_year.empty else np.nan
    total_mwh = daily_year[VALUE_COL].sum() if not daily_year.empty else np.nan
    top_fuel = total_by_fuel_year.iloc[0][FUEL_COL] if not total_by_fuel_year.empty else None

    return {
        "peak_mw": peak_mw,
        "avg_mw": avg_mw,
        "total_mwh": total_mwh,
        "top_fuel": top_fuel,
    }


@st.cache_data(show_spinner=False)
def prepare_aggregates() -> Dict[str, object]:
    df = load_generation_data()
    interval_minutes = infer_interval_minutes(df)
    clean = filter_complete_periods(df, interval_minutes)

    total_ts = (
        clean.groupby(TIME_COL, as_index=False)[VALUE_COL]
        .sum()
        .rename(columns={VALUE_COL: "total_mw"})
    )
    daily = (
        clean.assign(date=clean[TIME_COL].dt.floor("D"))
        .groupby("date", as_index=False)[VALUE_COL]
        .sum()
        .rename(columns={VALUE_COL: "generation_mwh"})
    )
    monthly_fuel = (
        clean.assign(month=clean[TIME_COL].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", FUEL_COL], as_index=False)[VALUE_COL]
        .sum()
        .rename(columns={VALUE_COL: "generation_mwh"})
    )
    yearly_fuel = (
        clean.assign(year=clean[TIME_COL].dt.year)
        .groupby(["year", FUEL_COL], as_index=False)[VALUE_COL]
        .sum()
        .rename(columns={VALUE_COL: "generation_mwh"})
    )
    yearly_total = yearly_fuel.groupby("year", as_index=False)["generation_mwh"].sum()
    yearly_share = yearly_fuel.merge(yearly_total, on="year", suffixes=("", "_total"))
    yearly_share["share_pct"] = 100 * yearly_share["generation_mwh"] / yearly_share["generation_mwh_total"]
    hourly_profile = (
        clean.assign(hour=clean[TIME_COL].dt.hour)
        .groupby(["hour", FUEL_COL], as_index=False)[VALUE_COL]
        .mean()
        .rename(columns={VALUE_COL: "avg_mw"})
    )
    fuel_time = (
        clean.groupby([TIME_COL, FUEL_COL], as_index=False)[VALUE_COL]
        .sum()
        .rename(columns={VALUE_COL: "mw"})
    )
    total_by_fuel = (
        clean.groupby(FUEL_COL, as_index=False)[VALUE_COL]
        .sum()
        .rename(columns={VALUE_COL: "generation_mwh"})
        .sort_values("generation_mwh", ascending=False)
    )

    years = sorted(clean["year"].dropna().unique().tolist())
    kpis_by_year = {int(year): compute_kpis_for_year(clean[clean["year"] == year]) for year in years}

    return {
        "clean": clean,
        "total_ts": total_ts,
        "daily": daily,
        "monthly_fuel": monthly_fuel,
        "yearly_share": yearly_share,
        "hourly_profile": hourly_profile,
        "fuel_time": fuel_time,
        "total_by_fuel": total_by_fuel,
        "years": years,
        "default_year": max(years) if years else None,
        "kpis_by_year": kpis_by_year,
        "latest_timestamp": total_ts[TIME_COL].max() if not total_ts.empty else None,
    }


def _style_figure(fig: go.Figure, title: str, show_legend: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0.5, xanchor="center"),
        margin=dict(l=30, r=20, t=60, b=30),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title=None),
    )
    return fig


def _fmt_number(value: float, suffix: str = "") -> str:
    if pd.isna(value):
        return "N/A"
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B{suffix}"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M{suffix}"
    if abs_value >= 1_000:
        return f"{value / 1_000:.1f}K{suffix}"
    return f"{value:.0f}{suffix}"


def render() -> None:
    st.caption("Local analysis rendered from Abby’s notebook assets in the ercotstats_dashboard folder.")

    try:
        data = prepare_aggregates()
    except Exception as error:
        st.error(f"Unable to render the ERCOT statistics visuals: {error}")
        return

    years = data["years"]
    if not years:
        st.warning("No complete years were found in the generation dataset.")
        return

    selected_year = st.selectbox(
        "Select reporting year",
        options=years,
        index=len(years) - 1,
        key="ercot_stats_year",
    )

    kpi = data["kpis_by_year"].get(int(selected_year), {})
    latest_timestamp = data["latest_timestamp"]
    latest_text = pd.to_datetime(latest_timestamp).strftime("%Y-%m-%d %H:%M") if latest_timestamp is not None else "N/A"

    st.markdown(f"**Latest timestamp in dataset:** {latest_text}")

    metric_cols = st.columns(4)
    metric_cols[0].metric(f"Peak generation ({selected_year})", _fmt_number(kpi.get("peak_mw", np.nan), " MW"))
    metric_cols[1].metric(f"Average generation ({selected_year})", _fmt_number(kpi.get("avg_mw", np.nan), " MW"))
    metric_cols[2].metric(f"Total energy ({selected_year})", _fmt_number(kpi.get("total_mwh", np.nan), " MWh"))
    top_fuel = kpi.get("top_fuel")
    metric_cols[3].metric(
        f"Top fuel ({selected_year})",
        FUEL_LABELS.get(str(top_fuel), str(top_fuel)) if top_fuel else "N/A",
    )

    total_generation_fig = px.line(
        data["total_ts"],
        x=TIME_COL,
        y="total_mw",
        labels={TIME_COL: "Time", "total_mw": "Generation (MW)"},
    )
    total_generation_fig.update_traces(line=dict(width=1.4, color="#2563eb"))

    total_by_fuel_fig = px.bar(
        data["total_by_fuel"],
        x=FUEL_COL,
        y="generation_mwh",
        color=FUEL_COL,
        category_orders={FUEL_COL: FUEL_ORDER},
        color_discrete_map=FUEL_COLORS,
        labels={FUEL_COL: "Fuel", "generation_mwh": "Generation (MWh)"},
    )

    monthly_fuel_fig = px.bar(
        data["monthly_fuel"],
        x="month",
        y="generation_mwh",
        color=FUEL_COL,
        category_orders={FUEL_COL: FUEL_ORDER},
        color_discrete_map=FUEL_COLORS,
        labels={"month": "Month", "generation_mwh": "Generation (MWh)", FUEL_COL: "Fuel"},
    )
    monthly_fuel_fig.update_layout(barmode="stack")

    yearly_share_fig = px.bar(
        data["yearly_share"],
        x="year",
        y="share_pct",
        color=FUEL_COL,
        category_orders={FUEL_COL: FUEL_ORDER},
        color_discrete_map=FUEL_COLORS,
        labels={"year": "Year", "share_pct": "Share (%)", FUEL_COL: "Fuel"},
    )
    yearly_share_fig.update_layout(barmode="stack")

    hourly_profile_fig = px.line(
        data["hourly_profile"],
        x="hour",
        y="avg_mw",
        color=FUEL_COL,
        category_orders={FUEL_COL: FUEL_ORDER},
        color_discrete_map=FUEL_COLORS,
        labels={"hour": "Hour of Day", "avg_mw": "Average Generation (MW)", FUEL_COL: "Fuel"},
    )

    fuel_time_fig = px.area(
        data["fuel_time"],
        x=TIME_COL,
        y="mw",
        color=FUEL_COL,
        category_orders={FUEL_COL: FUEL_ORDER},
        color_discrete_map=FUEL_COLORS,
        labels={TIME_COL: "Time", "mw": "Generation (MW)", FUEL_COL: "Fuel"},
    )

    left_col, right_col = st.columns(2)
    left_col.plotly_chart(_style_figure(total_generation_fig, "Total Generation Over Time", show_legend=False), use_container_width=True)
    right_col.plotly_chart(_style_figure(total_by_fuel_fig, "Total Generation by Fuel Type", show_legend=False), use_container_width=True)

    left_col, right_col = st.columns(2)
    left_col.plotly_chart(_style_figure(monthly_fuel_fig, "Monthly Generation by Fuel Type"), use_container_width=True)
    right_col.plotly_chart(_style_figure(yearly_share_fig, "Fuel Mix Share by Year"), use_container_width=True)

    st.plotly_chart(_style_figure(hourly_profile_fig, "Average Hourly Generation Profile by Fuel Type"), use_container_width=True)
    st.plotly_chart(_style_figure(fuel_time_fig, "Generation by Fuel Type Over Time"), use_container_width=True)

    with st.expander("Show cleaned source data preview"):
        preview = data["clean"][[TIME_COL, FUEL_COL, VALUE_COL]].head(100)
        st.dataframe(preview, use_container_width=True, hide_index=True)
