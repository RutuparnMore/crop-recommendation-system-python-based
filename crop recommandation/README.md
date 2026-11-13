# 🌾 KrishiMitra AI: Climate, Soil & Rotation-Driven Crop Advisory System

**KrishiMitra AI** is a state-of-the-art Agritech decision support platform built using **Python, Streamlit, Pandas, Scikit-learn, and SQLite**. It empowers farmers, agronomists, and agricultural extension workers to make scientifically backed crop selection choices by bridging live meteorological telemetry, localized soil health mapping, multi-season crop rotation intelligence, past fertilizer memory, and explainable Machine Learning.

---

## 🏗️ Architecture & Component Overview

```
d:/crop recommandation/
├── app.py                         # Streamlit frontend & interactive dashboard
├── requirements.txt               # Python dependency specifications
├── test_suite.py                  # Automated validation test suite (7 testing phases)
├── README.md                      # Comprehensive technical documentation
├── data/
│   ├── farm_database.db           # SQLite database (Users, Planting Decisions, Fertilizer History)
│   ├── soil_database.csv          # Localized soil database (330+ Maharashtra talukas)
│   └── crop_rf_model.joblib       # Trained Scikit-Learn Random Forest model
├── utils/
│   ├── __init__.py
│   ├── db_service.py              # SQLite user auth, planting records & fertilizer history CRUD
│   ├── fertilizer_history_engine.py # Multi-season fertilizer impact & crop rotation synergy engine
│   ├── soil_service.py            # Soil profile parser, nutrient derivation & heuristics
│   ├── weather_service.py         # Multi-engine meteorological service (OpenWeatherMap + Open-Meteo)
│   ├── ml_engine.py               # ML classifier with rotation intelligence & explainability logic
│   └── feasibility_engine.py      # Custom crop stress test (Pros, Cons, Infrastructure, Yield Tips)
└── .streamlit/
    └── config.toml                # Agritech green UI theme configuration
```

---

## 🌟 Core Features & Enhancements

### 1. Farmer Authentication & Persistent Database (`farm_database.db`)
- **Full Login & Registration System:**
  - Secure password hashing using `PBKDF2-HMAC-SHA256` with unique cryptographic salts.
  - Profiles store farmer name, contact, primary farm location, and historical seasonal records.
  - **1-Click Demo Login:** Included for testing with pre-seeded multi-season farm data (`farmer_demo`).
- **Database Schema:**
  - `users`: Farmer credentials and primary farm zone.
  - `crop_planting_history`: Multi-season log of crops planted, soil conditions, fertilizers, and field notes.
  - `fertilizer_history`: Structured record of fertilizers applied across the past 3 seasons.

### 2. Final Planting Decision & Season Logging (Next-Season Memory)
- **Step 5: Final Decision Recording:**
  - Farmers choose the crop they have finally decided to sow for the current season (e.g., *Kharif 2026*, *Rabi 2026-27*).
  - Can select from the AI Top 3 Recommended Crops, the custom analyzed crop, or any crop in the catalog.
  - Input planned fertilizers (e.g. *DAP 50 kg + 3 tons FYM*) and plot notes.
  - **Stored permanently in SQLite:** When the farmer logs in next season, the platform automatically retrieves this historical data to:
    - Reward **Crop Rotation Synergies** (e.g., following a nitrogen-fixing legume with high-demand cereals).
    - Warn against **Monoculture Hazards** (e.g., consecutive cotton sowing attracting Pink Bollworm pupae carryover).

### 3. Optional Factor: Past 3 Seasons Fertilizer History
- A dedicated, optional agronomic factor:
  - Toggle: `[x] Include Past 3 Seasons Fertilizer History in Recommendation Engine`
  - Captures usage across **Season -1 (Previous Season)**, **Season -2**, and **Season -3**:
    - Nitrogenous: *Urea (46% N)*
    - Phosphatic: *DAP (18:46:0)*, *Single Super Phosphate (SSP)*
    - Potassic: *Muriate of Potash (MOP 0:0:60)*
    - Complex: *NPK 10:26:26*, *12:32:16*, *19:19:19*
    - Organic: *Compost / Farmyard Manure (FYM) / Vermicompost*
    - Micronutrients: *Zinc Sulfate ($ZnSO_4$)*
  - Application Dosage Intensity: *Low*, *Standard/Balanced*, *Heavy/Intensive*.
- **Agronomic Impact Engine:**
  - Dynamically calculates **Residual Nitrogen ($N_{\Delta}$)**, **Phosphorus Accumulation ($P_{\Delta}$)**, **Potash Buffer ($K_{\Delta}$)**, and soil pH shifts.
  - Warns against high phosphorus fixation and nitrate leaching.
  - Directly feeds adjusted nutrient values into the Machine Learning recommendation engine!

### 4. Location-Based Telemetry & Soil Mapping
- **Dual Location Input Modes:**
  - **Database Mode:** Autocomplete selector across **330+ talukas in Maharashtra**.
  - **Free-Text Search:** Enter any village, taluka, district, or city globally.
- **Meteorological Telemetry:** Live temperature (°C), relative humidity (%), and agro-rainfall index (mm).
- **Localized Soil Parameters:** Soil Type, pH range, and derived quantitative Nitrogen (N), Phosphorus (P), and Potassium (K) in kg/ha.

### 5. AI Crop Recommendation Engine (Scikit-learn + Rotation Intelligence)
- Hybrid recommendation system:
  1. **Scikit-learn Random Forest Classifier** (or pure-NumPy policy-safe fallback).
  2. **Biological Envelope Compatibility** based on ICAR & FAO agronomic standards.
  3. **Crop Rotation Synergy Scoring:** Rewards restorative rotation (+10%) and penalizes monoculture (-12%).
- Outputs the **Top 3 Recommended Crops** with suitability scores, Marathi vernacular names, water requirements, and explainable rationale.
- Interactive multi-dimensional radar comparison chart.

### 6. Custom Crop Feasibility Analyzer (Pros & Cons)
- Stress-tests custom crop entries against local soil, weather, previous crops, and fertilizer memory.
- Outputs **Positives (Pros)**, **Negatives (Cons / Risks)**, and **Required Irrigation / Soil Infrastructure**.

### 7. Yield Optimization & Actionable Tips
- Specific micronutrient protocols (Zinc Sulfate, Agricultural Gypsum, Liming, Elemental Sulfur).
- Precision NPK basal and split scheduling.
- **Printable Advisory Report:** One-click download of the complete advisory as a formatted `.txt` report.

---

## 🚀 Installation & Running the Application

### 1. Install Dependencies
```bash
cd "d:/crop recommandation"
pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```bash
python test_suite.py
```

### 3. Launch the Streamlit Web Application
```bash
python -m streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.
