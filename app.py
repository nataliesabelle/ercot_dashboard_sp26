"""
ERCOT Dashboard Hub
═══════════════════════════════════════════════════════════════════════════════

A production-ready hub application that aggregates multiple ERCOT-related
dashboards via HTTPS iframes. This hub acts purely as a presentation and
orchestration layer—no data processing or analysis logic is duplicated.

Architecture: Hub-and-Spoke
───────────────────────────
• Hub (this app.py): Navigation, configuration, iframe orchestration
• Spokes (independent dashboards): Deployed separately, fully self-contained
  - Generation & Load Dashboard (Rafael, Streamlit)
  - ERCOT Statistics Dashboard (Abby, Streamlit)
  - GIS Map (qgis2web, GitHub Pages)
  - Data Center Infrastructure (ArcGIS Online)

Key Design Decisions:
───────────────────
1. YAML configuration: Easy to update URLs without code changes
2. Runtime URL resolution: Gracefully handles missing or misconfigured URLs
3. Iframe-only embedding: No code sharing, no state synchronization across dashboards
4. Clean separation of concerns: Hub only handles layout and navigation
5. HTTPS enforcement: All embedded content must use secure connections
"""

import ssl
import streamlit as st
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

try:
    from ercotstats_dashboard.streamlit_stats import render as render_ercot_stats_local
    ERCOT_STATS_IMPORT_ERROR = None
except Exception as import_error:
    render_ercot_stats_local = None
    ERCOT_STATS_IMPORT_ERROR = import_error

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "dashboard_config.yaml"


# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & UTILITIES
# ════════════════════════════════════════════════════════════════════════════════

def validate_url(url: str, source_label: str) -> Tuple[Optional[str], Optional[str]]:
    """Validate a dashboard URL and return a friendly error if needed."""
    clean_url = url.strip()

    if not clean_url:
        return None, f"⚠️ {source_label} is empty."

    if "YOUR_ARCGIS_APP_ID_HERE" in clean_url:
        return None, (
            "⚠️ The ArcGIS URL is still using the placeholder app ID. "
            "Update datacenter_dashboard/arcgisonlinehttps.txt with the final published ArcGIS link."
        )

    if not clean_url.startswith("https://"):
        return None, f"⚠️ {source_label} must use HTTPS."

    return clean_url, None


def read_first_nonempty_line(file_path: Path) -> str:
    """Return the first non-empty line from a text file."""
    with file_path.open("r", encoding="utf-8") as file_handle:
        for line in file_handle:
            stripped = line.strip()
            if stripped:
                return stripped
    return ""


def resolve_config_file_path(relative_config_path: Path) -> Optional[Path]:
    """Find a config file even if the uploaded filename changed slightly."""
    direct_path = APP_DIR / relative_config_path
    if direct_path.exists():
        return direct_path

    candidate_paths = [
        direct_path.with_suffix(""),
        direct_path.with_suffix(".text"),
    ]

    parent_dir = direct_path.parent
    normalized_target = relative_config_path.stem.lower().replace("_", "").replace("-", "")

    if parent_dir.exists():
        for child in parent_dir.iterdir():
            normalized_name = child.name.lower().replace("_", "").replace("-", "")
            if normalized_target in normalized_name or "rgisonlinehttps" in normalized_name:
                candidate_paths.append(child)

    for candidate in candidate_paths:
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def build_embed_url(url: str) -> str:
    """Add the recommended query parameter for Streamlit-hosted embeds."""
    parsed = urlparse(url)
    if parsed.netloc.lower().endswith("streamlit.app"):
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.setdefault("embed", "true")
        return urlunparse(parsed._replace(query=urlencode(query)))
    return url


@st.cache_data(ttl=300, show_spinner=False)
def probe_dashboard_url(url: str) -> Tuple[bool, Optional[str]]:
    """Check whether the external dashboard URL is reachable and public."""
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )

    try:
        ssl_context = ssl._create_unverified_context()
        with urlopen(request, timeout=12, context=ssl_context) as response:
            final_url = response.geturl()
            status_code = getattr(response, "status", 200)

        if "share.streamlit.io/errors/not_found" in final_url:
            return False, "⚠️ This Streamlit dashboard is missing or not publicly accessible at the configured URL."

        if status_code >= 400:
            return False, f"⚠️ This dashboard returned HTTP {status_code}."

        return True, None
    except HTTPError as error:
        if error.code == 404:
            return False, "⚠️ This external dashboard URL returns 404 Not Found."
        if error.code in (401, 403):
            return False, "⚠️ This dashboard is not public yet or requires sign-in."
        return False, f"⚠️ This dashboard returned HTTP {error.code}."
    except URLError as error:
        if "CERTIFICATE_VERIFY_FAILED" in str(error.reason):
            return True, None
        return False, f"⚠️ The dashboard could not be reached: {error.reason}"
    except Exception:
        return True, None


def load_configuration() -> Optional[Dict]:
    """
    Load dashboard configuration from the repository root next to this file.

    Returns:
        Dictionary with dashboard configs, or None if the file is missing.
    """
    if not CONFIG_PATH.exists():
        return None

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as file_handle:
            config = yaml.safe_load(file_handle)
        return config
    except yaml.YAMLError as e:
        st.error(f"❌ Error parsing {CONFIG_PATH.name}: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error reading configuration: {e}")
        return None


def resolve_dashboard_url(dashboard_config: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve dashboard URL from config, checking both direct URL and external config files.

    Args:
        dashboard_config: Configuration dict for a single dashboard

    Returns:
        Tuple of (url, error_message). If successful, url is returned and error is None.
        If unsuccessful, url is None and error is a user-friendly message.
    """
    if "url" in dashboard_config:
        return validate_url(dashboard_config["url"], "Dashboard URL")

    if "url_config_file" in dashboard_config:
        relative_config_path = Path(str(dashboard_config["url_config_file"]))
        config_file_path = resolve_config_file_path(relative_config_path)

        if config_file_path is None:
            return None, f"⚠️ Configuration file not found: {relative_config_path}"

        try:
            url = read_first_nonempty_line(config_file_path)
            return validate_url(url, f"URL in {config_file_path.relative_to(APP_DIR)}")
        except Exception as e:
            return None, f"⚠️ Error reading configuration file {config_file_path.relative_to(APP_DIR)}: {e}"

    return None, "⚠️ No URL or URL config file specified."


def render_dashboard_tab(title: str, description: str, url: Optional[str],
                         error: Optional[str], height: int, owner: str):
    """
    Render a single dashboard tab with iframe or error message.

    Args:
        title: Dashboard name
        description: Dashboard description
        url: Dashboard URL (if available)
        error: Error message (if URL resolution failed)
        height: Iframe height in pixels
        owner: Dashboard owner/team
    """
    st.markdown(f"### {title}")
    st.markdown(description)
    st.markdown(f"*Maintained by: {owner}*")
    st.divider()

    try:
        safe_height = max(int(height), 400)
    except (TypeError, ValueError):
        safe_height = 900

    if error:
        st.warning(error)
        st.info(
            "✏️ Update the dashboard source in dashboard_config.yaml or the linked text file, then refresh this page."
        )
    elif url:
        embed_url = build_embed_url(url)
        is_reachable, access_message = probe_dashboard_url(embed_url)

        if access_message:
            st.warning(access_message)

        if is_reachable:
            st.iframe(embed_url, height=safe_height)
            st.caption("If the embedded view is blocked by the host site, open the dashboard directly below.")
        else:
            st.info("The dashboard can still be opened directly while the hosting issue is fixed.")

        st.link_button("Open dashboard in a new tab", url)
    else:
        st.error("❌ Unable to load dashboard URL.")


def render_local_stats_tab(title: str, description: str, owner: str, fallback_url: Optional[str] = None):
    """Render Abby's ERCOT statistics tab from the local notebook-derived assets."""
    st.markdown(f"### {title}")
    st.markdown(description)
    st.markdown(f"*Maintained by: {owner}*")
    st.divider()

    if render_ercot_stats_local is None:
        st.error(f"❌ Unable to import the local ERCOT stats dashboard: {ERCOT_STATS_IMPORT_ERROR}")
    else:
        render_ercot_stats_local()

    if fallback_url:
        st.caption("Optional external deployment link")
        st.link_button("Open external stats app", fallback_url)


# ════════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION & SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ERCOT Dashboard Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar Content ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📊 ERCOT Dashboard Hub")
    st.divider()
    
    st.markdown("""
    ### 🎯 About This Hub
    
    This hub aggregates multiple ERCOT-related analysis dashboards into a single,
    unified interface. Each dashboard is **independently deployed** and updated by
    its respective team, ensuring scalability and maintainability.
    
    **Hub-and-Spoke Architecture:**
    - **Hub** (this application): Navigation and presentation layer
    - **Spokes** (individual dashboards): Fully self-contained deployments
    """)
    
    st.divider()
    
    st.markdown("""
    ### 📈 Dashboards Included
    
    **1. Generation & New Load Analysis**
    - Hosted by: Rafael
    - Focus: ERCOT generation capacity, new data center loads, AI computing facilities
    
    **2. ERCOT Statistics & Market Analysis**
    - Hosted by: Abby
    - Focus: Local generation trends, fuel mix, and system operations visuals
    
    **3. Population Dynamics Map**
    - Focus: Population and infrastructure dynamics visualized in an embedded external app
    - Hosted as: External web app / Streamlit deployment
    
    **4. Data Centers & Infrastructure**
    - Focus: Data center locations, capacity, ArcGIS-powered mapping
    - Hosted on: ArcGIS Online
    """)
    
    st.divider()
    
    st.markdown("""
    ### ℹ️ Data & Attribution
    
    - **Data Sources:** ERCOT, PUCT filings, public announcements, news sources
    - **Update Frequency:** Varies by dashboard (see respective dashboards for details)
    - **Liability:** Each dashboard team maintains data accuracy for their domain
    - **Policy Research:** For academic/policy use only
    """)
    
    st.divider()
    
    st.markdown("""
    ### 🔧 For Developers
    
    **Adding a New Dashboard:**
    1. Push your Streamlit app to Streamlit Community Cloud or host elsewhere (HTTPS)
    2. Update `dashboard_config.yaml` with the new dashboard's URL and metadata
    3. Redeploy this hub app
    
    **Updating URLs:**
    - Edit `dashboard_config.yaml` (direct URLs)
    - Edit `datacenter_dashboard/arcgisonlinehttps.txt` (ArcGIS Online URL)
    
    **Repository:** https://github.com/nataliesabelle/ercot_dashboard_sp26
    """)


# ════════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT: DASHBOARD TABS
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("# ⚡ ERCOT Dashboard Hub")
st.markdown("*Aggregating ERCOT energy, generation, and infrastructure analysis*")
st.divider()

# Load configuration
config = load_configuration()

if config is None:
    st.error("""
    ❌ **Configuration Error**

    The dashboard configuration could not be found or loaded.
    Please ensure dashboard_config.yaml exists next to app.py and is valid YAML.
    """)
else:
    dashboards = config.get("dashboards", {})

    if not isinstance(dashboards, dict) or not dashboards:
        st.error("❌ No valid dashboards are configured in dashboard_config.yaml")
    else:
        # Create tabs for each dashboard
        tab_labels = [db_config.get("title", key) for key, db_config in dashboards.items()]
        tabs = st.tabs(tab_labels)
        
        # Render each dashboard in its tab
        for tab, (dash_key, dash_config) in zip(tabs, dashboards.items()):
            with tab:
                if dash_key == "ercot_stats":
                    fallback_url = dash_config.get("url") if isinstance(dash_config, dict) else None
                    render_local_stats_tab(
                        title=dash_config.get("title", dash_key),
                        description=dash_config.get("description", ""),
                        owner=dash_config.get("owner", "Unknown"),
                        fallback_url=fallback_url,
                    )
                else:
                    # Resolve URL (with graceful error handling)
                    url, error = resolve_dashboard_url(dash_config)

                    # Render the dashboard or error message
                    render_dashboard_tab(
                        title=dash_config.get("title", dash_key),
                        description=dash_config.get("description", ""),
                        url=url,
                        error=error,
                        height=dash_config.get("height", 900),
                        owner=dash_config.get("owner", "Unknown"),
                    )


# ════════════════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
---
**ERCOT Dashboard Hub v1.0** • Built with Streamlit • [Repository](https://github.com/nataliesabelle/ercot_dashboard_sp26)
""")
