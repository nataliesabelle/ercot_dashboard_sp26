# ERCOT Dashboard Hub - Quick Reference

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the hub locally
streamlit run app.py

# 3. Hub opens at http://localhost:8501
```

---

## 📁 File Map

| File | Purpose | Edit When? |
|------|---------|-----------|
| `app.py` | Main hub application | Rarely (only for features) |
| `dashboard_config.yaml` | Dashboard URLs & metadata | When adding/updating dashboards |
| `requirements.txt` | Hub dependencies | When adding Python packages |
| `datacenter_dashboard/arcgisonlinehttps.txt` | ArcGIS Online URL | When ArcGIS URL changes |
| `README.md` | Main documentation | When project scope changes |
| `DEPLOYMENT.md` | Deployment guide | When deployment process changes |

---

## 🏗️ Architecture at a Glance

```
┌─────────────────────────────────────────┐
│         Streamlit Hub (app.py)          │
│  • Reads configuration                  │
│  • Renders tabs                         │
│  • Embeds dashboards via iframes        │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────────────┐
    │          │                  │
┌───▼────┐ ┌──▼───┐ ┌────────┐ ┌─▼──────────┐
│Streamlit│ │GIS   │ │GitHub  │ │ArcGIS      │
│Dashboard│ │Map   │ │Pages   │ │Online      │
│ (Rafael)│ │      │ │        │ │            │
└────────┘ └──────┘ └────────┘ └────────────┘

HTTPS URLs loaded from:
• dashboard_config.yaml (direct URLs)
• External config files (ArcGIS URL)
```

---

## ✅ Configuration Checklist

**Before deploying the hub:**

- [ ] Update `dashboard_config.yaml` with actual dashboard URLs
- [ ] Update `datacenter_dashboard/arcgisonlinehttps.txt` with actual ArcGIS URL
- [ ] All URLs use HTTPS (not HTTP)
- [ ] All URLs are publicly accessible
- [ ] Test the hub locally: `streamlit run app.py`
- [ ] Verify all tabs load correctly

---

## 🔄 Adding a Dashboard Checklist

**When adding a new dashboard to the hub:**

1. **Deploy the dashboard** to a public HTTPS URL
2. **Add to `dashboard_config.yaml`:**
   ```yaml
   my_dashboard:
     title: "Dashboard Title"
     description: "What this dashboard shows"
     url: "https://your-dashboard.streamlit.app"
     owner: "Your Name"
     height: 900
   ```
3. **Commit and push**
4. **Test locally** before deploying
5. **Monitor deployment** in Streamlit Community Cloud

---

## 🐛 Troubleshooting Quick Links

### Dashboard not showing?
→ Check `dashboard_config.yaml` is valid YAML  
→ Verify URL uses HTTPS  
→ Verify URL is public and accessible  

### ArcGIS not loading?
→ Check `datacenter_dashboard/arcgisonlinehttps.txt` exists  
→ Verify URL starts with `https://`  
→ Remove extra whitespace or newlines  

### Hub won't start?
→ Ensure `requirements.txt` packages are installed  
→ Run: `python3 -m py_compile app.py`  
→ Check YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('dashboard_config.yaml'))"`  

---

## 📊 Current Dashboards

```
┌────────────────────────────────────────────────────┐
│ Tab 1: Generation & New Load (Rafael)              │
│ • Streamlit Community Cloud                        │
│ • Data center & AI load tracking                   │
├────────────────────────────────────────────────────┤
│ Tab 2: ERCOT Statistics & Analysis (Abby)          │
│ • Streamlit Community Cloud                        │
│ • Grid operations & market data                    │
├────────────────────────────────────────────────────┤
│ Tab 3: GIS Map (Interactive)                       │
│ • GitHub Pages (qgis2web)                          │
│ • Infrastructure & transmission visualization      │
├────────────────────────────────────────────────────┤
│ Tab 4: Data Centers & Infrastructure (ArcGIS)      │
│ • ArcGIS Online                                    │
│ • Data center locations & capacity                 │
└────────────────────────────────────────────────────┘
```

---

## 🚢 Deployment Process

### Option 1: Run Locally
```bash
streamlit run app.py
```

### Option 2: Deploy to Streamlit Community Cloud
1. Push to GitHub
2. Go to Streamlit Community Cloud
3. Create new app → Select repo → Set main file to `app.py`
4. Deploy

Automatic redeployment on every `main` branch push.

---

## 📞 Key Contacts

| Component | Owner |
|-----------|-------|
| Hub Architecture | Natalie Sabelle |
| Generation & Load Dashboard | Rafael |
| ERCOT Stats Dashboard | Abby |
| GIS Map | GIS Team |
| Data Centers (ArcGIS) | ERCOT Team |

---

## 📚 Documentation Structure

```
.
├── README.md              # Main overview & architecture
├── DEPLOYMENT.md          # How to deploy (detailed)
├── IMPLEMENTATION.md      # This implementation summary
├── QUICKREF.md           # This quick reference
├── app.py                # Main app (well-commented)
├── dashboard_config.yaml # Configuration (annotated)
└── gen_dashboard/README.md # Generation dashboard docs
```

---

## ⚡ One-Minute Hub Overview

**What is the hub?**  
A Streamlit app that displays multiple ERCOT dashboards as tabs without duplicating code.

**Why this design?**  
Each dashboard team can work independently and deploy whenever they want.

**How does it work?**  
Hub reads URLs from `dashboard_config.yaml` and displays each dashboard in an iframe.

**How to add dashboards?**  
Update `dashboard_config.yaml` with the new dashboard's URL and metadata.

**When should I edit code vs. config?**  
- Edit YAML: When adding dashboards or updating URLs
- Edit code: When adding new features to the hub itself

---

**Last Updated:** April 2026 | Version 1.0 | Production-Ready ✅
