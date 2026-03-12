# 🎓 Kochi Education Survey Dashboard

An interactive web dashboard for exploring education infrastructure across Kochi Corporation wards, built with **Streamlit + Plotly + Folium**.

---

## 📁 Project Structure

```
kochi_edu_dashboard/
├── app.py                        # Main Streamlit app
├── Education-Ward_Level.xlsx     # Ward-level survey data (22 wards)
├── Education_Schools.xlsx        # School-level survey data (48 schools)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🚀 Local Setup

```bash
# 1. Clone or copy the project folder
cd kochi_edu_dashboard

# 2. Create virtual environment (optional)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the dashboard
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## ☁️ Deploy to Streamlit Cloud (One-Click)

1. Push this folder to a **public GitHub repository** (include both `.xlsx` files)
2. Go to [https://share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"**
4. Select your repo, branch (`main`), and set **Main file path** → `app.py`
5. Click **Deploy** — your dashboard is live in ~2 minutes!

> ⚠️ Make sure both Excel files are committed to the repo root alongside `app.py`.

---

## 📊 Dashboard Features

| Tab | Content |
|-----|---------|
| **Ward Comparison** | Enrollment by ward, gender distribution, tuition centres, VHS & special school presence |
| **School Map** | Interactive Folium map with GPS pins; click popups show full school profile |
| **Facility Analyzer** | Smart classroom heatmap, facility scores, scatter plots, playground availability |
| **Transport & Equity** | Student/teacher transport modes, gender equity histogram, distance distribution, radar chart |
| **Correlations & Clusters** | KMeans ward clustering, correlation matrix, regression scatter plots |
| **Insight Generator** | 10 live auto-computed insights + 10 "What-If" expandable panels |

---

## 🔍 Sidebar Filters

- **Ward(s)** — Multi-select any of the 22 surveyed wards
- **School Board** — State / CBSE / ICSE / Others
- **School Type** — Government / Aided / Private
- **School Level** — Primary / Upper Primary / High School / Higher Secondary / VHS / KG
- **Playground** — All / Yes / No
- **Smart Classrooms Range** — Slider 0–60
- **Max Distance to Public Transport** — Slider 0–10 km

All charts, KPIs, and insights update dynamically.

---

## ⚠️ Data Limitations

- Wards 37 & 41: Anganwadis were closed at time of survey
- Ward 63: Data unavailable
- Survey conducted pre-2025 delimitation
- 22 wards surveyed (not all 74 Kochi Corporation wards)
- Some GPS coordinates corrected for obvious outliers
- Distance outliers (>50 km) set to null

---

## 🛠️ Tech Stack

- **Streamlit** — Web app framework
- **Plotly** — Interactive charts (bar, scatter, heatmap, radar, pie)
- **Folium + streamlit-folium** — Leaflet-based interactive map
- **scikit-learn** — KMeans clustering for ward classification
- **pandas / numpy** — Data processing

---

*Kochi Education Survey 2025 | Dashboard by Anthropic Claude*
