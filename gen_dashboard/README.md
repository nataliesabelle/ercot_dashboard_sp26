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
- **Historical (2022–2025):** ERCOT Large Load Integration Team March 2026 TAC Report (Actual and Projected Large Load Growth 2022–2030 table).
- **Projected (2026–2030):** Same ERCOT source table (projected growth by status category).
- **This chart reflects ALL ERCOT large load types** (data centers, crypto, industrial, hydrogen, etc.) — not filtered to data centers only. This is by design: the chart is aggregate ERCOT context, separate from the project-level filtered map.

Category definitions per ERCOT (March 2026):
- **No Studies Submitted:** Tracked by ERCOT but insufficient info to begin review.
- **Under ERCOT Review:** Studies under active ERCOT review.
- **Planning Studies Approved:** ERCOT approved required interconnection studies.
- **Approved to Energize but Not Operational:** Received energization approval but not yet drawing observed power.
- **Observed Energized:** Receiving approval AND observed consuming power (peak consumption tracked monthly).

---

## Data Sources

| Source | Used For |
|---|---|
| ERCOT Large Load Integration Team, March 2026 TAC Report | Queue category MW/counts, aggregate statistics, ERCOT category definitions |
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
ercot_dashboard/
├── app.py                          # Main Streamlit dashboard
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
