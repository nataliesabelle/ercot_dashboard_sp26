# ERCOT Dashboard Hub - Deployment & Developer Guide

## 📋 Table of Contents

1. [Local Development](#local-development)
2. [Configuration Management](#configuration-management)
3. [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
4. [Adding New Dashboards](#adding-new-dashboards)
5. [Troubleshooting](#troubleshooting)
6. [Architecture Details](#architecture-details)

---

## 🖥️ Local Development

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/nataliesabelle/ercot_dashboard_sp26.git
   cd ercot_dashboard_sp26
   ```

2. **Create a Python virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the hub locally:**
   ```bash
   streamlit run app.py
   ```
   
   The app will open at `http://localhost:8501`

### Testing Individual Dashboards

If you're developing a specific dashboard locally:

```bash
# For the generation & load dashboard
cd gen_dashboard
pip install -r requirements.txt
streamlit run "app (1).py"

# This runs on a different port (e.g., localhost:8502)
```

---

## ⚙️ Configuration Management

### Structure

The hub is configured primarily through two files:

```
ercot_dashboard_sp26/
├── dashboard_config.yaml          # Main configuration (dashboard URLs, metadata)
└── datacenter_dashboard/
    └── arcgisonlinehttps.txt      # ArcGIS Online URL (read at runtime)
```

### `dashboard_config.yaml` - Main Configuration File

This YAML file contains all dashboard definitions. **Example:**

```yaml
dashboards:
  generation_load:
    title: "Generation & New Load"
    description: "Rafael's Streamlit analysis..."
    url: "https://ercot-generation-load-dashboard.streamlit.app"
    owner: "Rafael"
    height: 900
    
  ercot_stats:
    title: "ERCOT Statistics & Analysis"
    description: "Abby's Streamlit dashboard..."
    url: "https://ercot-stats-dashboard.streamlit.app"
    owner: "Abby"
    height: 900
```

**Key Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Display name in the hub's tab bar |
| `description` | Yes | Brief description shown to users |
| `url` | Conditional* | Direct HTTPS URL to the dashboard |
| `url_config_file` | Conditional* | Path to a file containing the dashboard URL |
| `owner` | Yes | Team or person responsible for this dashboard |
| `height` | No | Iframe height in pixels (default: 900) |

\* Either `url` or `url_config_file` must be specified.

### `datacenter_dashboard/arcgisonlinehttps.txt` - ArcGIS Online Configuration

This file stores the ArcGIS Online dashboard URL separately to allow configuration without code changes.

**Example content:**
```
https://www.arcgisonline.com/apps/View/index.html?appid=a1b2c3d4e5f6g7h8
```

**Why separate?** The ArcGIS Online URL may be updated or rotated frequently, so storing it in a separate file allows the hub admin to update it without modifying code or YAML.

### Updating Dashboard URLs

**Scenario 1: Updating a Streamlit Dashboard URL**

1. Edit `dashboard_config.yaml`
2. Find the dashboard's configuration block
3. Update the `url` field
4. Commit and push to GitHub

**Example:**
```yaml
generation_load:
  url: "https://NEW-ercot-generation-load-dashboard.streamlit.app"  # Updated URL
```

**Scenario 2: Updating the ArcGIS Online URL**

1. Edit `datacenter_dashboard/arcgisonlinehttps.txt`
2. Replace the URL with the new one (first line only)
3. Commit and push (or you can update this file directly in the GitHub UI)

---

## 🚀 Deploying to Streamlit Community Cloud

### Step 1: Prepare Your GitHub Repository

Ensure your repository is public and contains:

- `app.py` (hub application)
- `dashboard_config.yaml` (configuration)
- `requirements.txt` (dependencies)
- `datacenter_dashboard/arcgisonlinehttps.txt` (ArcGIS URL)
- `README.md` (documentation)

### Step 2: Create a Streamlit Community Cloud Account

1. Go to https://streamlit.io/cloud
2. Sign up with your GitHub account
3. Authorize Streamlit to access your repositories

### Step 3: Deploy the Hub

1. In Streamlit Community Cloud, click **"Create app"**
2. Select your repository: `ercot_dashboard_sp26`
3. Set the main file: `app.py`
4. Leave the runtime options as default (unless you have special requirements)
5. Click **"Deploy"**

The hub will deploy and be accessible at a URL like:
```
https://ercot-dashboard-hub.streamlit.app
```

### Step 4: Monitor Deployed App

- View logs: Click the **"Manage app"** button on your deployment
- Redeploy: Any pushes to `main` will automatically redeploy the hub
- View health: Check the "Status" tab for deployment metrics

---

## 📊 Adding New Dashboards

### From a Developer's Perspective

If you've developed a new dashboard and want to add it to the hub:

1. **Deploy your dashboard** to a public, HTTPS URL
   - Streamlit: Use Streamlit Community Cloud
   - ArcGIS: Host on ArcGIS Online
   - Custom: Any public web server with HTTPS

2. **Add to `dashboard_config.yaml`:**
   ```yaml
   your_dashboard_key:
     title: "Your Dashboard Title"
     description: "A brief description of what this dashboard does"
     url: "https://your-dashboard-url.streamlit.app"
     owner: "Your Name or Team"
     height: 900  # Adjust if needed
   ```

3. **Commit and push:**
   ```bash
   git add dashboard_config.yaml
   git commit -m "Add new dashboard: Your Dashboard Title"
   git push origin main
   ```

4. **The hub will update automatically** within a few seconds

### From the Hub Administrator's Perspective

If you're maintaining the hub and someone submits a new dashboard:

1. **Verify** the dashboard URL is public and uses HTTPS
2. **Test** the dashboard in the hub locally:
   ```bash
   streamlit run app.py
   ```
3. **Add to `dashboard_config.yaml`** following the guidelines above
4. **Commit, push, and verify** the hub redeploys successfully

---

## 🔍 Troubleshooting

### Problem: "Dashboard not appearing in hub"

**Possible causes:**

1. **Configuration file error** → Check `dashboard_config.yaml` is valid YAML
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('dashboard_config.yaml'))"
   ```

2. **URL not HTTPS** → Dashboard URLs must start with `https://`

3. **URL is incorrect or unreachable** → Verify the URL works in your browser

4. **Dashboard key not in config** → Ensure the dashboard is listed under `dashboards:` in the YAML

### Problem: "ArcGIS Online dashboard not loading"

1. **Check file exists:**
   ```bash
   ls -la datacenter_dashboard/arcgisonlinehttps.txt
   ```

2. **Verify URL format:**
   ```bash
   cat datacenter_dashboard/arcgisonlinehttps.txt
   ```
   Should return a single URL starting with `https://`

3. **Check for whitespace:**
   - Remove any extra blank lines or trailing spaces
   - The first line should be the complete URL

### Problem: "Hub won't start locally"

1. **Check Python version:** `python3 --version` (should be 3.9+)

2. **Verify dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check YAML syntax:**
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('dashboard_config.yaml'))"
   ```

4. **Check file permissions:**
   ```bash
   chmod 644 dashboard_config.yaml
   chmod 644 datacenter_dashboard/arcgisonlinehttps.txt
   ```

### Problem: "Dashboard URL is correct but iframe shows blank page"

1. **Check CORS:** The dashboard may have CORS restrictions
   - Contact the dashboard owner
   - Consider hosting the dashboard differently

2. **Check iframe height:** Adjust the `height` parameter in `dashboard_config.yaml`

3. **Test in browser:** Try visiting the URL directly in your browser

---

## 🏗️ Architecture Details

### Hub-and-Spoke Design

```
        Hub (app.py)
        Navigation Layer
        Configuration Reader
              │
    ┌─────────┼─────────────────┐
    │         │                 │
Spoke 1    Spoke 2           Spoke 3
(Streamlit) (GIS)           (ArcGIS)
 Deployed   Deployed        Deployed
  @ URL A    @ URL B         @ URL C
```

### Why Not Just Clone Dashboards into Hub?

**Bad approach** (code duplication):
```
hub/
├── gen_dashboard_code/     # ❌ Duplicate code
├── stats_dashboard_code/   # ❌ Duplicate code
└── app.py
```

**Good approach** (hub-and-spoke):
```
hub/
├── app.py                   # ✅ Only orchestration
├── dashboard_config.yaml    # ✅ URLs to external dashboards
└── datacenter_dashboard/
    └── arcgisonlinehttps.txt
```

### Benefits

1. **Separation of Concerns:** Hub doesn't own or maintain dashboard code
2. **Independent Deployment:** Each dashboard deploys on its own schedule
3. **Scalability:** Adding dashboards doesn't increase hub complexity
4. **Failure Isolation:** If one dashboard goes down, others remain available
5. **Team Ownership:** Each team maintains their own dashboard

### URL Resolution Flow

```
Hub loads YAML config
        │
        ├─ For each dashboard:
        │  │
        │  ├─ Does it have a direct URL?
        │  │  ├─ Yes → Use it (validate HTTPS)
        │  │  └─ No → Check for url_config_file
        │  │
        │  └─ Does it have a url_config_file?
        │     ├─ Yes → Read first line from file
        │     └─ No → Show error message
        │
        └─ Render iframe with resolved URL
           (or show error)
```

---

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Community Cloud Docs](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [YAML Syntax Reference](https://yaml.org/)
- [HTTPS and Web Security](https://developer.mozilla.org/en-US/docs/Glossary/HTTPS)

---

## 📞 Questions or Issues?

- Check this guide first
- Review [`app.py`](../app.py) for code comments
- Check the main [README.md](../README.md)
- Open an issue on GitHub

---

**Last Updated:** April 2026 | Version 2.0
