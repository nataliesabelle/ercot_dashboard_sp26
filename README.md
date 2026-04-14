# ERCOT Dashboard Hub v2

**A scalable, production-ready hub application that aggregates multiple ERCOT-related analysis dashboards via HTTPS iframes.**

## 🏗️ Architecture: Hub-and-Spoke

This repository implements a **hub-and-spoke architecture** for dashboard aggregation:

```
                        ┌─────────────────────┐
                        │  Hub App (app.py)   │
                        │  Navigation Layer   │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
            ┌───────▼────────┐  ┌──▼──────────┐  ┌─▼────────────────┐
            │ Gen Dashboard  │  │ Stats       │  │ GIS Map          │
            │ (Rafael)       │  │ Dashboard   │  │ (Junco)   │
            │ Streamlit      │  │ (Abby)      │  │ qgis2web         │
            │ Community Cloud│  │ Streamlit   │  │                  │
            └────────────────┘  │ Community   │  └──────────────────┘
                                │ Cloud       │
                                └─────────────┘
                                
              ┌──────────────────────────────────┐
              │  Data Centers Dashboard          │
              │  (ArcGIS Online)                 │
              └──────────────────────────────────┘
```

### Why This Architecture?

- **Separation of Concerns:** Each dashboard maintains its own codebase, data pipeline, and deployment
- **Scalability:** Add new dashboards without modifying the hub
- **Resilience:** Dashboard failures don't affect the hub or other dashboards
- **Ownership:** Each team member owns and maintains their dashboard independently
- **Technology Flexibility:** Dashboards can use different technologies (Streamlit, ArcGIS, static HTML, etc.)

## 🚀 Quick Start

### Option 1: Run the Hub Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the hub app
streamlit run app.py
```

The hub will open at `http://localhost:8501` and display all configured dashboards as tabs.

### Option 2: Individual Dashboard Development

Each dashboard can be developed and tested independently:

```bash
# For the generation & load dashboard
cd gen_dashboard
pip install -r requirements.txt
streamlit run "app (1).py"
```

## 📊 Included Dashboards

| Dashboard | Owner | Technology | Hosted On |
|-----------|-------|-----------|-----------|
| **Generation & New Load** | Rafael | Streamlit | Streamlit Community Cloud |
| **ERCOT Statistics & Analysis** | Abby | Streamlit | Streamlit Community Cloud |
| **GIS Map** | Junco | qgis2web / GitHub Pages | GitHub Pages |
| **Data Centers & Infrastructure** | Natalie R. | ArcGIS Online | ArcGIS Online |

## ⚙️ Configuration

### Hub Configuration: `dashboard_config.yaml`

All dashboard URLs and metadata are centralized in [`dashboard_config.yaml`](dashboard_config.yaml):

```yaml
dashboards:
  generation_load:
    title: "Generation & New Load"
    url: "https://ercot-generation-load-dashboard.streamlit.app"
    owner: "Rafael"
    height: 900
```

**To update a dashboard URL:** Simply edit `dashboard_config.yaml` and redeploy the hub.

### ArcGIS Online Configuration: `datacenter_dashboard/arcgisonlinehttps.txt`

The Data Centers dashboard URL is stored separately in [`datacenter_dashboard/arcgisonlinehttps.txt`](datacenter_dashboard/arcgisonlinehttps.txt) for flexibility:

```
https://www.arcgisonline.com/apps/View/index.html?appid=...
```

The hub reads this file at runtime, so you can update the ArcGIS URL without code changes.

## 🔧 Adding a New Dashboard

1. **Deploy your dashboard** to a publicly accessible URL (must use HTTPS)
2. **Add to `dashboard_config.yaml`:**
   ```yaml
   your_dashboard:
     title: "Your Dashboard Title"
     description: "Brief description"
     url: "https://your-dashboard.streamlit.app"
     owner: "Your Name"
     height: 900
   ```
3. **Redeploy the hub** (the hub will pick up the new dashboard automatically)

## 📁 Repository Structure

```
ercot_dashboard_sp26/
├── app.py                          # Hub application (MAIN ENTRY POINT)
├── dashboard_config.yaml           # Dashboard URLs and metadata
├── requirements.txt                # Hub dependencies (streamlit, pyyaml)
│
├── gen_dashboard/                  # Generation & Load Dashboard (Rafael)
│   ├── app (1).py
│   ├── requirements.txt
│   └── data/
│
├── ercotstats_dashboard/           # ERCOT Statistics Dashboard (Abby)
│   ├── another try (1).ipynb
│   └── ...
│
├── map_dashboard/                  # GIS Map (qgis2web, GitHub Pages)
│   ├── index (1).html
│   └── [assets]
│
└── datacenter_dashboard/           # Data Centers (ArcGIS Online)
    └── arcgisonlinehttps.txt       # ArcGIS Online URL
```

## 🔐 Security & Best Practices

- ✅ **HTTPS Only:** All embedded dashboards must use HTTPS
- ✅ **No Code Sharing:** Dashboards are embedded via iframes (no shared code or state)
- ✅ **Graceful Degradation:** If a dashboard URL is invalid or unreachable, the hub shows a clear error message
- ✅ **Version Control:** Dashboard URLs are in YAML config (easy to track in git)
- ✅ **Separation of Secrets:** Each dashboard manages its own credentials and environment variables

## 📝 Design Principles

1. **Hub is Stateless:** The hub orchestrates only—no data processing
2. **Configuration-Driven:** URLs and metadata in YAML, not hardcoded
3. **Iframe-Only Embedding:** No JavaScript injection, no HTML inlining from dashboards
4. **Graceful Error Handling:** Clear messages if URLs are missing or invalid
5. **Easy to Extend:** Adding dashboards requires only YAML updates

## 🚢 Deployment

### Deploy the Hub to Streamlit Community Cloud

```bash
# Commit and push to GitHub
git add app.py dashboard_config.yaml requirements.txt
git commit -m "Add ERCOT Dashboard Hub"
git push origin main

# In Streamlit Community Cloud:
# 1. Create new app
# 2. Select this repository
# 3. Set main file: app.py
# 4. Deploy
```

### Deploy Individual Dashboards

Each spoke dashboard is deployed independently using its own deployment mechanism:

- **Streamlit dashboards:** Streamlit Community Cloud, Hugging Face Spaces, or cloud platforms
- **GIS map:** GitHub Pages (static files)
- **ArcGIS:** ArcGIS Online (embedded in hub)

## 📚 Documentation

- **Hub Design:** See [`app.py`](app.py) for detailed inline documentation
- **Gen Dashboard:** See [`gen_dashboard/README.md`](gen_dashboard/README.md)
- **Configuration:** See [`dashboard_config.yaml`](dashboard_config.yaml) for all configuration options

## 🛠️ Troubleshooting

**Dashboard not appearing?**
- Check that the URL in `dashboard_config.yaml` is correct and uses HTTPS
- Verify the URL is publicly accessible
- Check the hub's sidebar for error messages

**Hub won't start?**
- Ensure `dashboard_config.yaml` exists and is valid YAML
- Ensure `pyyaml` is installed: `pip install pyyaml`

**Custom ArcGIS URL not loading?**
- Verify `datacenter_dashboard/arcgisonlinehttps.txt` exists
- Verify the URL starts with `https://`
- Check for extra whitespace or newlines in the file

## 📞 Support & Attribution

- **Hub Architecture & Implementation:** Natalie Sherman
- **Generation & Load Dashboard:** Rafael
- **ERCOT Statistics Dashboard:** Abby
- **GIS Map:** Junco
- **Data Centers (ArcGIS):** Natalie R.

## 📄 License

This project is for academic and policy research purposes. See individual dashboard repositories for licensing details. Team Texas in the Spring 2026 CE377K Introduction to Energy Systems course at The University of Texas at Austin created this dashboard as their final project. 

---

**Last Updated:** April 13 2026 | **Version:** 2.0
