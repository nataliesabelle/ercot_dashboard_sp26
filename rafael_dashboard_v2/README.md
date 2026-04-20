# ERCOT Large Electronic Load Dashboard

**A policy/research decision-support prototype focused on data centers, AI, and crypto mining in ERCOT.**

UT Austin Energy Systems Course Project · April 2026

---

## How to Run

### Requirements
```
Python 3.9+
streamlit>=1.32
pandas>=2.0
plotly>=5.18
numpy>=1.24
```

### Install & Launch
```bash
# Clone or copy the project folder, then:
pip install -r requirements.txt
streamlit run app.py
```
The dashboard opens at `http://localhost:8501`.

---

## Project Scope Rules

- **Universe:** ERCOT Large Load Interconnection (LLI) process, projects tracked from 2024 onward.
- **Load type:** Data centers, AI computing, crypto mining, other large electronic loads (75 MW+ where at least half the power is computing). Projects clearly not in this profile are excluded.
- **Geography:** Inside the ERCOT footprint. (El Paso has a flag/note since it is on the ERCOT boundary and served by El Paso Electric, which has an interconnection agreement with ERCOT for some facilities.)
- **Defensibility:** Smaller, cleaner dataset preferred over a large messy one. When in doubt, a project is left out or fields are marked `unknown`.

---

## Status Logic (`status_simple`)

| `status_simple` | Mapping from ERCOT/Public Evidence |
|---|---|
| `operational` | Maps to ERCOT's **"Observed Energized"** category — projects that have received ERCOT Approval to Energize and are observed to be consuming power (non-simultaneous peak confirmed). Used when public news/ERCOT reporting confirms energization. |
| `approved-advancing` | Maps to ERCOT's **"Planning Studies Approved"** or **"Approved to Energize but Not Operational"** categories — projects that cleared ERCOT interconnection studies, or received Approval to Energize but are not yet drawing full observed power. Also used when strong public evidence (ERCOT filings, utility filings, TDLR construction permits) confirms planning approval. |
| `early-stage` | Maps to ERCOT's **"Under ERCOT Review"** or **"No Studies Submitted"** categories — projects publicly announced, in planning, or with interconnection requests submitted but not yet through ERCOT review. |
| `unknown` | Used when there is insufficient public evidence to assign any of the above categories with confidence. |

**Key rule:** Status is only assigned based on explicit public evidence (ERCOT TAC reports, PUCT filings, TDLR permits, press releases from ERCOT or developers). No status is inferred from speculation alone.

**Source for ERCOT category definitions:** ERCOT Large Load Integration Team, March 13, 2026 TAC Report (March-TAC-Report-6.pdf).

---

## In-Service Year Logic

- **Primary field:** Expected in-service date from public announcements, ERCOT LLI data, or TDLR construction permits.
- **Default = 2030:** If no public expected in-service date is available, `in_service_year = 2030` is assigned. This ensures the project only appears when the slider is at its maximum (2030), making the uncertainty visible to the user.
- **Year slider rule:** A project appears on the map when `in_service_year <= slider_year`.
- **Partial operational sites:** If Phase 1 of a multi-phase campus is operational, the in_service_year reflects the first publicly confirmed operational phase.

---

## Ownership Rules and Asterisk Convention

Ownership is inferred using a tiered approach:
1. **Directly confirmed** (press releases, SEC filings, ERCOT public data): `owner_tentative = false`, no asterisk.
2. **Strongly inferred** (multiple news sources, company announcements, utility filings pointing to the same owner): `owner_tentative = true`, displayed as `CompanyName*`.
3. **Unknown:** `owner_display = "Unknown Operator*"` with `owner_tentative = true`.

The asterisk (`*`) in `owner_display` is the UI signal that ownership is tentative. Users should treat these as working hypotheses, not confirmed facts.

---

## Transmission Backbone

### 345-kV Current Backbone
- **Source:** ERCOT 2024 Report on Existing and Potential Electric System Constraints and Needs (December 2024) — corridor identification from top-10 congestion constraint data, ERCOT load zone maps, and ERCOT system planning public documents.
- **Method:** Seven major high-voltage corridors were schematically approximated by connecting known geographic anchor points (Permian Basin, Panhandle, DFW, Austin, San Antonio, Houston, Gulf Coast). Exact tower locations are not reflected — this is a policy-visualization backbone, not engineering geometry.
- **Limitations:** 138-kV local lines are not shown. Rural radial lines are not shown. Corridor paths are straight-segment approximations between geographic anchors.

### 765-kV Conceptual Layer
- **Source:** ERCOT Permian Basin Reliability Plan (filed July 2024, PUCT approved October 2024); Oncor's December 2025 filing for the Longshore Switch–Drill Hole Switch ~180-mile 765-kV line; ERCOT 2024 RTP 765-kV plan documents; Utility Dive January 2026.
- **Method:** Two conceptual corridors (main Permian→Central Texas path, and a northern branch toward DFW) were drawn as schematic approximations based on ERCOT's public filing descriptions of the Permian Basin export path.
- **Labeled CONCEPTUAL in the dashboard.** Exact alignment is subject to PUCT and ERCOT approval processes. The PUCT was expected to make a statewide 765-kV voltage decision by May 2025 (extended). Do not treat this geometry as an engineering-grade route.

---

## ERCOT Queue Context Chart

The "ERCOT Aggregate Queue Categories" chart uses **ERCOT's own official categories and MW totals** from:
- **Historical / current / projected queue status MW:** ERCOT Update, House Committee on State Affairs, April 9, 2026, slide 3, "Large Load Interconnection Requests (as of March 26, 2026)." The same slide appears in the April 1, 2026 Senate Business & Commerce deck.
- **This chart reflects ALL ERCOT large load types** (data centers, crypto, industrial, hydrogen, etc.) — not filtered to data centers only. This is by design: the chart is aggregate ERCOT context, separate from the project-level filtered map.
- **Chronology:** The chart renders years as ordered categories from 2022 through 2030, preserving discrete year labels while preventing categorical sorting issues.
- **Selected year:** The sidebar's queue-chart year selector still controls the adjacent snapshot table and is shown on the chart with a subtle outline.
- **2030 vs. 2029 audit:** ERCOT's April 2026 slide shows total large-load queue MW rising from **328,213 MW in 2029** to **410,618 MW in 2030**. If the chart ever shows a lower 2030 value than 2029, that should be treated as a data/transcription issue, not ERCOT's source trend.

Category definitions per ERCOT (March 2026):
- **No Studies Submitted:** Tracked by ERCOT but insufficient info to begin review.
- **Under ERCOT Review:** Studies under active ERCOT review.
- **Planning Studies Approved:** ERCOT approved required interconnection studies.
- **Approved to Energize but Not Operational:** Received energization approval but not yet drawing observed power.
- **Observed Energized:** Receiving approval AND observed consuming power (peak consumption tracked monthly).

---

## Changelog

### April 2026 moderate queue/interconnection polish pass
- Corrected the queue status MW table against ERCOT's April 2026 large-load hearing slide.
- Populated the queue snapshot `Projects` column using ERCOT-backed counts where printed and bounded estimates where ERCOT did not publish a status-by-year project-count table.
- Added exactly three ERCOT large-load queue/interconnection panels:
  - **Large Loads by Project Type** to show the data-center skew and estimated average MW/request.
  - **Large Load Requests by Submitted Quarter** to show the 2025/2026 request wave associated with AI/data-center demand.
  - **Large Load Requests by TSP** to show concentration by transmission service provider.
- Preserved the existing dark theme, presentation style, map, sidebar filters, project table, and protected project/transmission files.

### Earlier April 2026 polish pass
- Fixed the ERCOT aggregate queue chart to display years in deterministic chronological order from 2022 through 2030 while keeping the x-axis categorical.
- Moved the queue chart title out of the Plotly figure and into the Streamlit section header; the explanatory disclaimer remains above the chart.
- Kept the queue legend horizontal and adjusted chart margins to reduce crowding between the header, disclaimer, chart area, and legend.
- Replaced the selected-year filled highlight with a subtler outline.
- Removed the top metric cards labeled "Operational" and "Under Review-Advancing" and reflowed the remaining cards into a balanced four-card row.

---

## Queue Data Audit

### Direct ERCOT values

The following queue MW values are treated as **direct ERCOT values** because they are printed in the slide 3 table of ERCOT's April 2026 House/Senate large-load update:

| Year | Observed Energized | A2E but Not Operational | Planning Studies Approved | Under ERCOT Review | No Studies Submitted | Total MW |
|---:|---:|---:|---:|---:|---:|---:|
| 2025 | 5,778 | 935 | 30 | 0 | 0 | 6,743 |
| 2026 | 5,778 | 2,748 | 3,181 | 6,478 | 25,253 | 43,438 |
| 2027 | 5,778 | 2,941 | 10,739 | 30,539 | 101,702 | 151,699 |
| 2028 | 5,778 | 2,941 | 15,923 | 51,315 | 177,879 | 253,836 |
| 2029 | 5,778 | 3,241 | 19,040 | 61,966 | 238,188 | 328,213 |
| 2030 | 5,778 | 3,241 | 21,343 | 86,605 | 293,651 | 410,618 |

### Queue MW values changed

| Year | Status category | Old value | New value | Source | Method |
|---:|---|---:|---:|---|---|
| 2025 | Observed Energized | 6,743 | 5,778 | ERCOT April 2026 House/Senate large-load update, slide 3 | Direct from printed table |
| 2025 | Approved to Energize but Not Operational | 0 | 935 | ERCOT April 2026 House/Senate large-load update, slide 3 | Direct from printed table |
| 2025 | Planning Studies Approved | 0 | 30 | ERCOT April 2026 House/Senate large-load update, slide 3 | Direct from printed table |
| 2029 | Under ERCOT Review | 238,188 | 61,966 | ERCOT April 2026 House/Senate large-load update, slide 3 | Direct from printed table; corrected transcription error |
| 2029 | No Studies Submitted | 236,188 | 238,188 | ERCOT April 2026 House/Senate large-load update, slide 3 | Direct from printed table; corrected transcription error |

The corrected 2029 values make the year total **328,213 MW**, matching ERCOT's printed total. The prior CSV totaled **502,435 MW** for 2029 because one status row was transcribed incorrectly.

### Project-count values

ERCOT's April 2026 submitted-quarter and TSP charts print request-count labels that sum to **562 large-load requests** as of March 26, 2026. ERCOT does not provide a machine-readable status-by-year project-count table in the attached materials, so the dashboard uses a bounded estimate for `project_count` in `queue_categories.csv`:

- Historical observed counts from the existing CSV were retained where already populated for 2022-2024.
- 2025-2030 totals were bounded by the 562 total request labels visible in the ERCOT submitted-quarter and TSP charts.
- The 2030 total is set to 562 requests.
- Intermediate year totals are scaled from ERCOT's printed queue MW totals using the 2030 average of about 731 MW/request, then allocated across status categories in proportion to each year's printed MW by status.
- Observed Energized is held at 10 projects from 2025 onward as a simple continuity assumption from the existing observed-count history.

| Year | Project-count total now shown | Status-level method |
|---:|---:|---|
| 2022 | 4 | Existing historical value retained |
| 2023 | 10 | Existing historical value retained |
| 2024 | 10 | Existing historical value retained |
| 2025 | 12 | Existing observed history plus small estimates for A2E/planning rows |
| 2026 | 59 | Reconstructed from ERCOT total request labels and MW/status proportions |
| 2027 | 208 | Reconstructed from ERCOT total request labels and MW/status proportions |
| 2028 | 347 | Reconstructed from ERCOT total request labels and MW/status proportions |
| 2029 | 449 | Reconstructed from ERCOT total request labels and MW/status proportions |
| 2030 | 562 | Anchored to ERCOT visible request-count labels from submitted-quarter/TSP charts |

These counts are meant for class/demo interpretation, not regulatory reporting. They keep the snapshot table meaningful without implying ERCOT published exact status-by-year project counts.

### Project-count values added or revised

| Year | Status category | Old count | New count | Method |
|---:|---|---:|---:|---|
| 2025 | Approved to Energize but Not Operational | 0 | 1 | Estimated from ERCOT chart labels and average MW/request |
| 2025 | Planning Studies Approved | 0 | 1 | Estimated from ERCOT chart labels and average MW/request |
| 2026 | Observed Energized | 0 | 10 | Continuity assumption from existing observed-count history |
| 2026 | Approved to Energize but Not Operational | 0 | 4 | Estimated from ERCOT chart labels and average MW/request |
| 2026 | Planning Studies Approved | 0 | 4 | Estimated from ERCOT chart labels and average MW/request |
| 2026 | Under ERCOT Review | 0 | 8 | Estimated from ERCOT chart labels and average MW/request |
| 2026 | No Studies Submitted | 0 | 33 | Estimated from ERCOT chart labels and average MW/request |
| 2027 | Observed Energized | 0 | 10 | Continuity assumption from existing observed-count history |
| 2027 | Approved to Energize but Not Operational | 0 | 4 | Estimated from ERCOT chart labels and average MW/request |
| 2027 | Planning Studies Approved | 0 | 15 | Estimated from ERCOT chart labels and average MW/request |
| 2027 | Under ERCOT Review | 0 | 41 | Estimated from ERCOT chart labels and average MW/request |
| 2027 | No Studies Submitted | 0 | 138 | Estimated from ERCOT chart labels and average MW/request |
| 2028 | Observed Energized | 0 | 10 | Continuity assumption from existing observed-count history |
| 2028 | Approved to Energize but Not Operational | 0 | 4 | Estimated from ERCOT chart labels and average MW/request |
| 2028 | Planning Studies Approved | 0 | 21 | Estimated from ERCOT chart labels and average MW/request |
| 2028 | Under ERCOT Review | 0 | 70 | Estimated from ERCOT chart labels and average MW/request |
| 2028 | No Studies Submitted | 0 | 242 | Estimated from ERCOT chart labels and average MW/request |
| 2029 | Observed Energized | 0 | 10 | Continuity assumption from existing observed-count history |
| 2029 | Approved to Energize but Not Operational | 0 | 5 | Estimated from ERCOT chart labels and average MW/request |
| 2029 | Planning Studies Approved | 0 | 26 | Estimated from ERCOT chart labels and average MW/request |
| 2029 | Under ERCOT Review | 0 | 84 | Estimated from ERCOT chart labels and average MW/request |
| 2029 | No Studies Submitted | 0 | 324 | Estimated from ERCOT chart labels and average MW/request |
| 2030 | Observed Energized | 0 | 10 | Continuity assumption from existing observed-count history |
| 2030 | Approved to Energize but Not Operational | 0 | 5 | Estimated from ERCOT chart labels and average MW/request |
| 2030 | Planning Studies Approved | 0 | 29 | Estimated from ERCOT chart labels and average MW/request |
| 2030 | Under ERCOT Review | 0 | 118 | Estimated from ERCOT chart labels and average MW/request |
| 2030 | No Studies Submitted | 0 | 400 | Estimated from ERCOT chart labels and average MW/request |

### New visual panels

1. **Large Loads by Project Type**
   - Uses ERCOT April 2026 slide 3 for the direct data-center MW value: **355,830 MW**, or **87.6%** of the 410,618 MW queue.
   - Uses the printed non-data-center percentage labels on slide 3 for the remaining project-type MW estimates.
   - Uses presentation-friendly estimated counts allocated from the 562 total request labels so the viewer can compare MW versus number of requests.
   - Key assumption: the count split by project type is approximate because the slide prints percentages/MW much more clearly than category-by-category counts.

2. **Large Load Requests by Submitted Quarter**
   - Uses the printed ERCOT request-count labels from slide 4. These labels sum to 562 requests.
   - Uses best-effort MW reconstruction from the slide's stacked bars, scaled to the 410,618 MW queue total.
   - Key assumption: the quarter-level MW bars are reconstructed from the published figure because ERCOT did not provide a machine-readable table in the attached material.

3. **Large Load Requests by TSP**
   - Uses the printed ERCOT request-count labels from slide 5. These labels also sum to 562 requests.
   - Uses best-effort GW reconstruction from the slide's horizontal bars.
   - Key assumption: TSP-level GW values are approximate; the count labels and the strong concentration pattern, especially Oncor's leading position, are the more reliable takeaway.

### ERCOT sources used

| Source | Used for | Direct or reconstructed |
|---|---|---|
| ERCOT Update, House Committee on State Affairs, April 9, 2026 | Queue status MW table, project-type chart, submitted-quarter chart, TSP chart, batch-process context | Direct where values are printed; reconstructed where chart bars lack machine-readable tables |
| ERCOT Update, Senate Committee on Business & Commerce, April 1, 2026 | Cross-check of same large-load slide deck content | Direct cross-check |
| ERCOT Large Load Interconnection Status Update / March TAC materials, March 2026 | Category definitions and process context | Direct for definitions/context |
| ERCOT filing in PUCT Project No. 58777, Item 38, April 15, 2026 | Long-term load forecast and TSP RFI context | Direct context; not used to overwrite the queue chart |

### Remaining uncertainties

- ERCOT did not publish the underlying spreadsheet for the April 2026 project-type, submitted-quarter, or TSP charts in the attached files.
- Some MW values in the new panels are reconstructed visually and should be treated as approximate.
- `project_count` by queue status/year is estimated, not a direct ERCOT-published table.
- The aggregate queue includes all large-load types and should not be interpreted as a data-center-only queue, even though ERCOT reports that data centers dominate the MW total.

---

## Data Sources

| Source | Used For |
|---|---|
| ERCOT Large Load Integration Team, March 2026 TAC Report | Queue context, aggregate statistics, ERCOT category definitions |
| ERCOT April 2026 House/Senate large-load update decks | Queue category MW, project type, submitted quarter, TSP concentration, batch-process context |
| ERCOT PUCT Project No. 58777 Item 38 filing (Apr. 15, 2026) | Long-term load forecast and TSP RFI context |
| ERCOT Dec 2024 Report on Constraints and Needs | Transmission backbone, 765-kV plan, top-10 congestion constraints |
| ERCOT Strategic Plan 2024-2028 | ERCOT background, grid facts |
| Oracle/OpenAI Stargate Fact Sheet (Sep 2025) | Stargate Abilene, Shackelford details |
| Pexapark (Nov 2025) | Google Haskell/Armstrong County projects |
| The Real Deal (Dec 2025) | Google Midlothian Building 5 |
| Fort Worth Pulse (Oct 2025) | MSB Global Sulphur Springs campus |
| Texas Observer (Nov 2025) | Riot Rockdale, Milam County crypto, Far West Texas crypto |
| Substack/Dave Friedman (Jan 2026) | Stargate Milam County, queue context |
| EIA Today in Energy (Oct 2024) | LFL statistics, capacity context |
| ServerCountry.org | CyrusOne/ECP/KKR Whitney, Vantage, Amazon DeSoto |
| Blueprint Data Centers LinkedIn (Apr 2026) | CoreWeave Taylor, Blueprint Georgetown |
| ENGIE Resources (Mar 2026) | DFW market overview, DataBank |
| YouTube video (Mar 2026) | Hood County, Fannin County, DFW hyperscale campus context |
| Instagram/GW Ranch (Feb 2026) | GW Ranch West Texas; Meta El Paso |
| Utility Dive (Jan 2026) | 765-kV Oncor filing context |

---

## Major Data Gaps and Future Improvements

### Current Gaps
1. **ERCOT does not publish project-level LLI data with owner names.** Individual project identities are inferred from public news, TDLR filings, and press releases. Many projects in the actual queue have no public information.
2. **MW estimates for some projects are approximate** (e.g., the Far West Texas crypto cluster aggregate, some planned campuses).
3. **Exact coordinates** for several projects are city/county centroids, not parcel-level.
4. **Meta El Paso** is flagged as a boundary case — El Paso Electric territory intersects ERCOT interconnection, but El Paso is generally considered outside the ERCOT footprint. Retained with a caveat.
5. **Vantage Data Centers Frontier Campus** has no confirmed location; coordinates are an approximate Texas centroid.
6. **Submission dates** are not publicly available for most projects at the project level.

### Where Data is Strong vs. Weak
- **Strong:** Stargate Abilene, Google Midlothian, Riot Rockdale, Google Haskell/Armstrong (confirmed via company press releases and TDLR filings).
- **Moderate:** CyrusOne/Calpine Whitney, ECP/KKR Bosque, Blueprint Taylor/Georgetown (industry databases, LinkedIn posts).
- **Weak:** Hood County campus, Fannin County campus, DFW 768-acre campus, Data City Texas — developer identity unconfirmed; MW estimates derived from media reports.

### Recommended Future Improvements
1. Integrate PUCT and ERCOT public docket search for LLI filings by transmission provider territory.
2. Add TDLR (Texas Dept. of Licensing and Regulation) construction permit data as a systematic source for project discovery.
3. Add ERCOT LFL Task Force periodic status updates as machine-readable input.
4. Implement a quarterly refresh cycle aligned with ERCOT's monthly TAC reports.
5. Add county-level transmission constraint overlay from ERCOT congestion rent data.
6. Disaggregate aggregate clusters (e.g., Far West Texas crypto) as individual projects become publicly identifiable.
7. Add water consumption data (HARC 2026 estimates: ~9,567 MW → 25B gallons water) as a co-visualization layer.

---

## Files

```
rafael_dashboard_v2/
├── app_v2.py                       # Main Streamlit dashboard
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── data/
    ├── projects.csv                # Master project table (30 projects)
    ├── queue_categories.csv        # ERCOT aggregate queue categories by year
    └── transmission_backbone.json  # Transmission layer geometry (conceptual)
```

---

## Important Disclaimers

- This is a **prototype policy/research dashboard**, not an engineering-grade contingency simulator.
- **Do not use for operational grid planning.**
- Transmission backbone geometry is **conceptual** — not exact. The 765-kV layer is labeled CONCEPTUAL in the UI.
- All `owner_tentative = true` entries (marked `*`) represent working hypotheses based on public signals, not confirmed ownership.
- MW figures for projects with `status_simple = "early-stage"` or `unknown` represent **requested capacity**, not approved or guaranteed capacity. ERCOT's own data shows only ~1.8% of the total queue was operational as of late 2025.
