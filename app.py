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

import streamlit as st
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple


# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & UTILITIES
# ════════════════════════════════════════════════════════════════════════════════

def load_configuration() -> Optional[Dict]:
    """
    Load dashboard configuration from YAML file.
    
    Returns:
        Dictionary with dashboard configs, or None if file not found.
    """
    config_path = Path("dashboard_config.yaml")
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except yaml.YAMLError as e:
        st.error(f"❌ Error parsing dashboard_config.yaml: {e}")
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
    # Check for direct URL
    if "url" in dashboard_config:
        url = dashboard_config["url"].strip()
        if url and url.startswith("https://"):
            return url, None
        elif url:
            return None, "⚠️ URL must use HTTPS (not HTTP)"
        else:
            return None, "⚠️ Empty URL in configuration"
    
    # Check for external config file (e.g., ArcGIS Online URL)
    if "url_config_file" in dashboard_config:
        config_file_path = Path(dashboard_config["url_config_file"])
        if not config_file_path.exists():
            return None, f"⚠️ Configuration file not found: {dashboard_config['url_config_file']}"
        
        try:
            with open(config_file_path, "r") as f:
                url = f.read().strip().split("\n")[0]  # Read first non-empty line
            
            if not url:
                return None, "⚠️ Configuration file is empty"
            
            if not url.startswith("https://"):
                return None, "⚠️ URL in configuration file must use HTTPS"
            
            return url, None
        except Exception as e:
            return None, f"⚠️ Error reading configuration file: {e}"
    
    return None, "⚠️ No URL or URL config file specified"


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
    
    if error:
        st.warning(error)
        st.info("✏️ Please update the configuration and ensure the URL is accessible.")
    elif url:
        # Render iframe for the dashboard
        iframe_html = f"""
        <iframe 
            src="{url}" 
            width="100%" 
            height="{height}px" 
            frameborder="0" 
            allowfullscreen="true"
            style="border: 1px solid #e0e0e0; border-radius: 4px;">
        </iframe>
        """
        st.html(iframe_html)
    else:
        st.error("❌ Unable to load dashboard URL")


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
    - Focus: Grid operations, market data, system reliability metrics
    
    **3. GIS Map (Interactive)**
    - Focus: Geographic visualization of ERCOT infrastructure, transmission corridors, generation facilities
    - Hosted on: GitHub Pages (qgis2web)
    
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
    
    The `dashboard_config.yaml` file could not be found or loaded.
    Please ensure it exists in the repository root and is valid YAML.
    """)
else:
    dashboards = config.get("dashboards", {})
    
    if not dashboards:
        st.error("❌ No dashboards configured in dashboard_config.yaml")
    else:
        # Create tabs for each dashboard
        tab_labels = [db_config.get("title", key) for key, db_config in dashboards.items()]
        tabs = st.tabs(tab_labels)
        
        # Render each dashboard in its tab
        for tab, (dash_key, dash_config) in zip(tabs, dashboards.items()):
            with tab:
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
