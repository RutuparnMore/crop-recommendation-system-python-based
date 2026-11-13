import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.soil_service import SoilService
from utils.weather_service import WeatherService
from utils.ml_engine import CropRecommendationEngine, AGRONOMIC_CROP_PROFILES
from utils.feasibility_engine import FeasibilityEngine
from utils.db_service import DatabaseService
from utils.fertilizer_history_engine import FertilizerHistoryEngine, AVAILABLE_FERTILIZERS

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="KrishiMitra AI - Precision Agritech Advisory",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Global Elegant CSS Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
        color: #14281d;
    }

    /* Background accent */
    .stApp {
        background-color: #f7faf7;
    }

    /* Elegant Top Navbar */
    .top-navbar {
        background: linear-gradient(135deg, #0f382c 0%, #1b4332 50%, #2d6a4f 100%);
        border-radius: 18px;
        padding: 20px 28px;
        margin-bottom: 24px;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(15, 56, 44, 0.2), 0 8px 10px -6px rgba(15, 56, 44, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    .top-navbar-title {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .top-navbar-subtitle {
        font-size: 0.95rem;
        color: #d8f3dc;
        margin-top: 4px;
        font-weight: 400;
    }

    /* Login Portal Styles */
    .login-container {
        max-width: 1100px;
        margin: 20px auto 40px auto;
    }
    .hero-card {
        background: linear-gradient(145deg, #0f382c 0%, #1b4332 60%, #2d6a4f 100%);
        border-radius: 24px;
        padding: 44px 38px;
        color: #ffffff;
        height: 100%;
        box-shadow: 0 20px 30px -10px rgba(15, 56, 44, 0.25);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        padding: 6px 14px;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: #b7e4c7;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -1px;
        margin-bottom: 16px;
        color: #ffffff;
    }
    .hero-description {
        font-size: 1.05rem;
        line-height: 1.6;
        color: #d8f3dc;
        margin-bottom: 28px;
    }
    .hero-feature-item {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
        font-size: 0.95rem;
        color: #eaf7ee;
        font-weight: 500;
    }
    .hero-feature-icon {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }
    
    .auth-portal-card {
        background: #ffffff;
        border: 1px solid #e1ebe3;
        border-radius: 24px;
        padding: 36px 32px;
        box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.05), 0 5px 15px rgba(0, 0, 0, 0.02);
    }

    /* Metric Capsules */
    .metric-capsule {
        background: #ffffff;
        border: 1px solid #e2ede5;
        border-radius: 16px;
        padding: 16px 14px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(15, 56, 44, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-capsule:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(15, 56, 44, 0.07);
        border-color: #b7e4c7;
    }
    .metric-capsule-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #52796f;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 4px;
    }
    .metric-capsule-val {
        font-size: 1.6rem;
        font-weight: 800;
        color: #1b4332;
        letter-spacing: -0.5px;
    }
    .metric-capsule-sub {
        font-size: 0.75rem;
        color: #718378;
        margin-top: 2px;
    }

    /* Crop Recommendation Cards */
    .crop-card-v2 {
        background: #ffffff;
        border: 1.5px solid #d8e6dc;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 20px rgba(15, 56, 44, 0.04);
        transition: all 0.25s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .crop-card-v2:hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 28px rgba(15, 56, 44, 0.09);
        border-color: #52b788;
    }
    .rank-pill {
        background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%);
        color: white;
        font-size: 0.75rem;
        font-weight: 800;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    .category-pill {
        background: #eaf5ee;
        color: #1b4332;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-left: 6px;
    }
    .rotation-pill-pro {
        background: #e0f2fe;
        color: #0369a1;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-top: 8px;
        border: 1px solid #bae6fd;
    }
    .rotation-pill-risk {
        background: #fee2e2;
        color: #b91c1c;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-top: 8px;
        border: 1px solid #fecaca;
    }
    .crop-title {
        font-size: 1.55rem;
        font-weight: 800;
        color: #0f382c;
        margin: 12px 0 2px 0;
        letter-spacing: -0.3px;
    }
    .crop-marathi {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d6a4f;
        margin-bottom: 14px;
    }

    /* Callout & Feedback Boxes */
    .pro-box {
        background-color: #f2f9f3;
        border-left: 4px solid #2d6a4f;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 0.92rem;
    }
    .con-box {
        background-color: #fef2f2;
        border-left: 4px solid #dc2626;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 0.92rem;
    }
    .infra-box {
        background-color: #f0fdf4;
        border-left: 4px solid #059669;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 0.92rem;
    }
    .tip-box {
        background-color: #fffbeb;
        border-left: 4px solid #d97706;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 0.92rem;
    }

    /* Sleek User Profile Badge */
    .user-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        padding: 6px 16px;
        font-size: 0.88rem;
        color: #ffffff;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }

    /* Section Cards */
    .content-section {
        background: #ffffff;
        border: 1px solid #e5ede7;
        border-radius: 20px;
        padding: 26px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
    }
</style>
""", unsafe_allow_html=True)

# --- Singleton Services Initialization ---
@st.cache_resource
def load_services():
    soil_svc = SoilService(csv_path="data/soil_database.csv")
    ml_svc = CropRecommendationEngine()
    feas_svc = FeasibilityEngine(ml_engine=ml_svc)
    db_svc = DatabaseService(db_path="data/farm_database.db")
    weather_svc = WeatherService()
    return soil_svc, ml_svc, feas_svc, db_svc, weather_svc

soil_service, ml_engine, feasibility_engine, db_service, weather_service = load_services()

def render_html(html_str: str):
    """
    Renders raw HTML safely in Streamlit without letting Markdown
    misinterpret indented lines or blank lines as code blocks.
    """
    clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown(" ".join(clean_lines), unsafe_allow_html=True)

# --- Initialize User Session State ---
if "user" not in st.session_state:
    st.session_state["user"] = None
if "guest_mode" not in st.session_state:
    st.session_state["guest_mode"] = False
if "active_location" not in st.session_state:
    st.session_state["active_location"] = "Baramati (Pune)"

# ==============================================================================
# VIEW 1: DEDICATED ELEGANT LOGIN & REGISTRATION PORTAL (PRE-AUTHENTICATION)
# ==============================================================================
def render_login_view():
    render_html("""
    <div class="login-container">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 2.8rem; margin-bottom: 4px;">🌾</div>
            <h1 style="font-size: 2.4rem; font-weight: 800; color: #0f382c; letter-spacing: -0.5px; margin: 0;">KrishiMitra AI</h1>
            <p style="font-size: 1.05rem; color: #52796f; margin-top: 6px;">Next-Generation Climate, Soil & Rotation Agricultural Advisory</p>
        </div>
    </div>
    """)

    col_hero, col_auth = st.columns([1.1, 1], gap="large")

    with col_hero:
        render_html("""
        <div class="hero-card">
            <div>
                <div class="hero-badge">🌿 AI FOR SUSTAINABLE AGRICULTURE</div>
                <div class="hero-title">Empowering Every Sowing Decision with Science.</div>
                <div class="hero-description">
                    KrishiMitra AI combines real-time satellite meteorology, ICAR soil classification, multi-season crop rotation intelligence, and machine learning to maximize farmer yield and break soil depletion cycles.
                </div>
                
                <div class="hero-feature-item">
                    <div class="hero-feature-icon">🌦️</div>
                    <div><b>Live Telemetry:</b> High-precision meteorological fetching for your exact taluka or village.</div>
                </div>
                <div class="hero-feature-item">
                    <div class="hero-feature-icon">🧪</div>
                    <div><b>Localized Soil Profiles:</b> Pre-mapped soil types, pH, and quantitative NPK across 330+ talukas.</div>
                </div>
                <div class="hero-feature-item">
                    <div class="hero-feature-icon">🔄</div>
                    <div><b>Crop Rotation Intelligence:</b> Rewards legume nitrogen carryover and safeguards against monoculture diseases.</div>
                </div>
                <div class="hero-feature-item">
                    <div class="hero-feature-icon">🌿</div>
                    <div><b>Fertilizer Memory:</b> Adjusts soil reserve based on your past 3 seasons of fertilizer applications.</div>
                </div>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255, 255, 255, 0.15); font-size: 0.85rem; color: #b7e4c7;">
                ✓ Calibrated with ICAR agronomic thresholds & Soil Health Card standards
            </div>
        </div>
        """)

    with col_auth:
        with st.container(border=True):
            auth_tab1, auth_tab2 = st.tabs(["🔐 Sign In", "📝 Create Farm Account"])

            with auth_tab1:
                st.markdown("#### Farmer Portal Login")
                st.caption("Access your registered farm history, saved seasons, and field data.")
                with st.form("form_signin"):
                    username = st.text_input("Username", placeholder="e.g. farmer_demo", key="in_user")
                    password = st.text_input("Password", type="password", placeholder="••••••••", key="in_pass")
                    btn_signin = st.form_submit_button("Sign In to Farm Dashboard", type="primary", use_container_width=True)

                    if btn_signin:
                        success, msg, user_data = db_service.authenticate_user(username, password)
                        if success:
                            st.session_state["user"] = user_data
                            st.session_state["guest_mode"] = False
                            st.session_state["active_location"] = user_data.get("default_location", "Baramati (Pune)")
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                st.divider()
                st.markdown("##### ⚡ Quick Access Options:")
                
                # One click demo button
                if st.button("🚀 One-Click Demo Login (Ramesh Patil - Baramati Farm)", use_container_width=True):
                    success, msg, user_data = db_service.authenticate_user("farmer_demo", "kisan123")
                    if success:
                        st.session_state["user"] = user_data
                        st.session_state["guest_mode"] = False
                        st.session_state["active_location"] = user_data.get("default_location", "Baramati (Pune)")
                        st.rerun()

                # Guest Explorer button
                if st.button("🌱 Continue as Guest Explorer", use_container_width=True):
                    st.session_state["guest_mode"] = True
                    st.session_state["user"] = None
                    st.rerun()

            with auth_tab2:
                st.markdown("#### Register New Farm Profile")
                st.caption("Set up your personalized farm database for multi-season tracking.")
                with st.form("form_signup"):
                    reg_name = st.text_input("Full Name", placeholder="e.g. Ramesh Patil")
                    reg_username = st.text_input("Choose Username", placeholder="e.g. ramesh_patil")
                    reg_password = st.text_input("Choose Password", type="password", placeholder="••••••••")
                    reg_location = st.text_input("Primary Farm Taluka / District", value="Baramati (Pune)")
                    reg_phone = st.text_input("Mobile Number (Optional)", placeholder="e.g. 9876543210")
                    btn_register = st.form_submit_button("Create My Account & Database", type="primary", use_container_width=True)

                    if btn_register:
                        success, msg, user_data = db_service.register_user(
                            username=reg_username, password=reg_password, full_name=reg_name,
                            default_location=reg_location, phone=reg_phone
                        )
                        if success:
                            st.session_state["user"] = user_data
                            st.session_state["guest_mode"] = False
                            st.session_state["active_location"] = reg_location
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)


# Check if user needs to be shown the Login Portal first
if st.session_state["user"] is None and not st.session_state.get("guest_mode", False):
    render_login_view()
    st.stop()


# ==============================================================================
# VIEW 2: ELEGANT AGRITECH MAIN DASHBOARD (AUTHENTICATED / GUEST)
# ==============================================================================

user = st.session_state["user"]
is_guest = st.session_state.get("guest_mode", False)
past_planting_records = db_service.get_user_planting_history(user["id"]) if user else []
past_planted_crops = [r["crop_name"] for r in past_planting_records if r.get("crop_name")]

# --- Top Navigation Bar ---
nav_col1, nav_col2 = st.columns([3, 2])

with nav_col1:
    render_html("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
        <span style="font-size: 2.2rem;">🌾</span>
        <div>
            <h1 style="font-size: 1.85rem; font-weight: 800; color: #0f382c; margin: 0; letter-spacing: -0.5px;">KrishiMitra AI</h1>
            <span style="font-size: 0.95rem; color: #52796f; font-weight: 500;">Precision Climate, Soil & Rotation Agronomic Advisory</span>
        </div>
    </div>
    """)

with nav_col2:
    st.write("")
    if user:
        p_col1, p_col2 = st.columns([3, 1])
        with p_col1:
            render_html(f"""
            <div style="background: #ffffff; border: 1px solid #d8e6dc; border-radius: 14px; padding: 10px 16px; text-align: right; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                <div style="font-weight: 700; color: #0f382c; font-size: 0.95rem;">👤 {user['full_name']}</div>
                <div style="font-size: 0.8rem; color: #52796f;">📍 {user.get('default_location', 'Maharashtra')} &nbsp;|&nbsp; 📜 {len(past_planting_records)} Seasons on Record</div>
            </div>
            """)
        with p_col2:
            if st.button("🚪 Log Out", use_container_width=True):
                st.session_state["user"] = None
                st.session_state["guest_mode"] = False
                st.rerun()
    else:
        g_col1, g_col2 = st.columns([3, 1])
        with g_col1:
            render_html("""
            <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 14px; padding: 10px 16px; text-align: right;">
                <div style="font-weight: 700; color: #92400e; font-size: 0.9rem;">🌱 Guest Explorer Mode</div>
                <div style="font-size: 0.78rem; color: #b45309;">Sign in to save seasonal decisions</div>
            </div>
            """)
        with g_col2:
            if st.button("🔐 Sign In", use_container_width=True, type="primary"):
                st.session_state["guest_mode"] = False
                st.rerun()

st.divider()

# --- SECTION 0: Field & Season History (When Logged In) ---
if user:
    with st.expander(f"📜 Field Planting History for {user['full_name']} ({len(past_planting_records)} Seasons on Record)", expanded=(len(past_planting_records) > 0)):
        if past_planting_records:
            st.markdown("Your previous crop decisions are automatically loaded to analyze **Crop Rotation Synergies** (e.g. legume nitrogen carryover) and avoid **Monoculture Diseases**.")
            
            history_cols = st.columns([2, 2, 2, 3, 2, 1])
            history_cols[0].markdown("**Season / Year**")
            history_cols[1].markdown("**Planted Crop**")
            history_cols[2].markdown("**Location & Soil**")
            history_cols[3].markdown("**Fertilizers Applied**")
            history_cols[4].markdown("**Notes**")
            history_cols[5].markdown("**Action**")

            for rec in past_planting_records:
                h_c = st.columns([2, 2, 2, 3, 2, 1])
                h_c[0].write(f"🗓️ {rec['season_name']} ({rec['year']})")
                h_c[1].write(f"🌱 **{rec['crop_name']}** ({rec['marathi_name']})")
                h_c[2].markdown(f"📍 {rec['location']}<br><span style='font-size:0.8rem; color:#666;'>{rec['soil_type']}</span>", unsafe_allow_html=True)
                h_c[3].write(rec['fertilizers_applied'] if rec['fertilizers_applied'] else "Standard basal dose")
                h_c[4].write(rec['notes'] if rec['notes'] else "-")
                if h_c[5].button("🗑️", key=f"del_{rec['id']}", help="Delete this planting record"):
                    db_service.delete_planting_record(rec["id"], user["id"])
                    st.success("Record removed.")
                    st.rerun()

            if past_planted_crops:
                st.info(f"🔄 **Crop Rotation Intelligence Active:** Last harvested crop on record is **{past_planted_crops[0]}**. Restorative rotation synergies are being applied to current recommendations!")
        else:
            st.info("No past planting records found yet. Once you confirm your final planting choice in Step 5 below, it will be permanently stored here!")
else:
    st.info("💡 **Farmer Tip:** You are exploring in Guest Mode. **Sign In or Register** using the button at the top-right to save your field decisions and unlock automatic multi-season crop rotation tracking!")


# --- SECTION 1: Location & Environmental Telemetry ---
st.markdown("### 📍 Step 1: Farm Location & Environmental Telemetry")

loc_col1, loc_col2 = st.columns([3, 1])

with loc_col1:
    location_mode = st.radio(
        "Location Input Mode:",
        ["Select from Maharashtra Database (330+ Talukas)", "Enter Any Custom Location (All India / Global)"],
        horizontal=True
    )

    all_db_locations = soil_service.get_all_locations()
    location_displays = [item["display"] for item in all_db_locations]

    if location_mode == "Select from Maharashtra Database (330+ Talukas)" and location_displays:
        pref_loc = st.session_state.get("active_location", "Baramati (Pune)")
        matched_idx = 43
        for i, disp in enumerate(location_displays):
            if pref_loc.lower() in disp.lower():
                matched_idx = i
                break

        selected_display = st.selectbox(
            "Select Taluka / District:",
            options=location_displays,
            index=matched_idx if matched_idx < len(location_displays) else 0,
            help="Select your taluka. Soil parameters will be automatically extracted from the local database."
        )
        selected_location_query = selected_display.split("(")[0].strip()
    else:
        selected_location_query = st.text_input(
            "Enter Location Name (Village, Taluka, District, or City):",
            value=st.session_state.get("active_location", "Nashik"),
            placeholder="e.g. Pune, Jalgaon, Ratnagiri, Satara, Solapur, Varanasi..."
        )

with loc_col2:
    st.write("")
    st.write("")
    fetch_btn = st.button("🚀 Fetch Telemetry & Analyze", type="primary", use_container_width=True)

with st.expander("⚙️ Meteorological API Settings (Optional OpenWeatherMap Key)"):
    custom_owm_key = st.text_input(
        "OpenWeatherMap API Key (Optional)",
        type="password",
        help="Leave blank to use free live Open-Meteo meteorological telemetry automatically with zero setup."
    )
    if custom_owm_key:
        weather_service.openweather_api_key = custom_owm_key.strip()

# Session state caching for current telemetry
if "telemetry_data" not in st.session_state or fetch_btn:
    with st.spinner("Fetching meteorological telemetry and localized soil profile..."):
        weather_info = weather_service.fetch_weather(selected_location_query)
        soil_info = soil_service.fetch_soil_profile(selected_location_query)
        st.session_state["telemetry_data"] = {
            "weather": weather_info,
            "soil": soil_info,
            "query": selected_location_query
        }

current_data = st.session_state["telemetry_data"]
weather = current_data["weather"]
soil = current_data["soil"]

# Telemetry Status Pills
status_c1, status_c2 = st.columns(2)
with status_c1:
    st.info(f"🌤️ **Weather Telemetry:** {weather['source']} | **Station:** {weather['location_name']}")
with status_c2:
    if soil.get("matched_in_database"):
        st.success(f"🌱 **Soil Database:** {soil['source']} | **Zone:** {soil['location_name']}")
    else:
        st.warning(f"🌱 **Soil Profile:** {soil['source']}")

# Telemetry Metrics Grid (Modern Capsules)
m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
with m1:
    render_html(f"""
    <div class="metric-capsule">
        <div class="metric-capsule-label">Temperature</div>
        <div class="metric-capsule-val">{weather['temperature']}°C</div>
        <div class="metric-capsule-sub">{weather['weather_description']}</div>
    </div>
    """)
with m2:
    render_html(f"""
    <div class="metric-capsule">
        <div class="metric-capsule-label">Rel. Humidity</div>
        <div class="metric-capsule-val">{weather['humidity']}%</div>
        <div class="metric-capsule-sub">Atmospheric</div>
    </div>
    """)
with m3:
    render_html(f"""
    <div class="metric-capsule">
        <div class="metric-capsule-label">Rainfall</div>
        <div class="metric-capsule-val">{weather['rainfall']} mm</div>
        <div class="metric-capsule-sub">Agro-Index</div>
    </div>
    """)
with m4:
    render_html(f"""
    <div class="metric-capsule">
        <div class="metric-capsule-label">Soil pH</div>
        <div class="metric-capsule-val">{soil['ph']}</div>
        <div class="metric-capsule-sub">Range: {soil.get('ph_range', '6.5-7.5')}</div>
    </div>
    """)
with m5:
    render_html(f"""
    <div class="metric-capsule">
        <div class="metric-capsule-label">Nitrogen (N)</div>
        <div class="metric-capsule-val">{soil['N']:.0f}</div>
        <div class="metric-capsule-sub">kg/ha</div>
    </div>
    """)
with m6:
    render_html(f"""
    <div class="metric-capsule">
        <div class="metric-capsule-label">Phosphorus (P)</div>
        <div class="metric-capsule-val">{soil['P']:.0f}</div>
        <div class="metric-capsule-sub">kg/ha</div>
    </div>
    """)
with m7:
    render_html(f"""
    <div class="metric-capsule">
        <div class="metric-capsule-label">Potassium (K)</div>
        <div class="metric-capsule-val">{soil['K']:.0f}</div>
        <div class="metric-capsule-sub">kg/ha</div>
    </div>
    """)

# Soil Details Summary Bar
render_html(f"""
<div style="background-color: #ffffff; border: 1px solid #d8e6dc; border-radius: 12px; padding: 12px 18px; margin: 16px 0; font-size: 0.92rem; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
    <b>🌍 Local Soil Type:</b> {soil['soil_type']} &nbsp;|&nbsp; 
    <b>🧪 Health Assessment:</b> {soil['overall_quality']} &nbsp;|&nbsp; 
    <b>⚠️ Nutrients / Contaminants:</b> {soil.get('nutrient_summary', 'Normal')}
</div>
""")

# Base soil values
active_n = float(soil['N'])
active_p = float(soil['P'])
active_k = float(soil['K'])
active_ph = float(soil['ph'])
active_temp = weather['temperature']
active_hum = weather['humidity']
active_rain = weather['rainfall']
active_soil_type = soil['soil_type']

# Option to fine-tune with farmer's actual Soil Health Card (SHC) report
with st.expander("⚙️ Optional: Fine-Tune Parameters (If you have a Soil Health Card report)"):
    st.caption("Adjust sliders below if your laboratory soil testing report shows specific values:")
    adj_col1, adj_col2, adj_col3, adj_col4 = st.columns(4)
    with adj_col1:
        custom_n = st.slider("Nitrogen (N kg/ha)", 10.0, 200.0, active_n, 5.0)
    with adj_col2:
        custom_p = st.slider("Phosphorus (P kg/ha)", 5.0, 150.0, active_p, 5.0)
    with adj_col3:
        custom_k = st.slider("Potassium (K kg/ha)", 10.0, 250.0, active_k, 5.0)
    with adj_col4:
        custom_ph = st.slider("Soil pH Level", 4.5, 9.5, active_ph, 0.1)

    active_n = custom_n
    active_p = custom_p
    active_k = custom_k
    active_ph = custom_ph

# --- SECTION 1.5: OPTIONAL FACTOR - Past 3 Seasons of Fertilizer Use ---
st.divider()
st.markdown("### 🧪 Optional Factor: Past 3 Seasons Fertilizer History")
st.caption("Fertilizers applied in previous seasons leave residual nitrogen, immobile phosphate pools, or potash buffers in the soil. Enabling this factor dynamically fine-tunes soil fertility.")

enable_fert_factor = st.checkbox("Include Past 3 Seasons Fertilizer History in Recommendation Engine", value=False)

fertilizer_insights = {"active": False}

if enable_fert_factor:
    saved_fert_records = db_service.get_user_fertilizer_history(user["id"]) if user else []
    saved_dict = {r["season_label"]: r for r in saved_fert_records}

    st.info("💡 **Agronomic Guidance:** Detail the fertilizers you applied across the last 3 crop seasons. This adjusts soil nitrogen accumulation, phosphorus fixation, and potassium reserve.")

    fert_tabs = st.tabs(["🌾 Season -1 (Previous Season)", "🌿 Season -2 (2 Seasons Ago)", "🌱 Season -3 (3 Seasons Ago)"])

    season_inputs = []

    season_labels = [
        "Season -1 (Previous Season: e.g. Last Rabi/Kharif)",
        "Season -2 (2 Seasons Ago: e.g. Last Kharif/Rabi)",
        "Season -3 (3 Seasons Ago: e.g. Year Ago)"
    ]

    for s_idx, (s_tab, s_label) in enumerate(zip(fert_tabs, season_labels)):
        with s_tab:
            default_saved = saved_dict.get(s_label, {})
            default_crop = ""
            if s_idx < len(past_planted_crops):
                default_crop = past_planted_crops[s_idx]
            elif default_saved:
                default_crop = default_saved.get("season_crop", "")

            c1, c2, c3 = st.columns([2, 3, 2])
            with c1:
                s_crop_val = st.text_input(f"Crop grown in {s_label.split('(')[0].strip()}", value=default_crop, key=f"scrop_{s_idx}")
            with c2:
                saved_ferts = default_saved.get("fertilizers_used", []) if default_saved else ["Urea (46% N)", "DAP (Di-Ammonium Phosphate 18:46:0)"]
                valid_defaults = [f for f in saved_ferts if f in AVAILABLE_FERTILIZERS]
                s_ferts = st.multiselect(
                    f"Fertilizers used in {s_label.split('(')[0].strip()}",
                    options=AVAILABLE_FERTILIZERS,
                    default=valid_defaults if valid_defaults else ["Urea (46% N)"],
                    key=f"sfert_{s_idx}"
                )
            with c3:
                s_intensity = st.selectbox(
                    "Application Dosage Intensity",
                    ["Standard / Balanced Recommended Dose", "Heavy / Intensive Repeated Application", "Low / Minimal Application"],
                    index=0 if not default_saved else (1 if "Heavy" in default_saved.get("intensity", "") else 0),
                    key=f"sint_{s_idx}"
                )

            season_inputs.append({
                "season_label": s_label,
                "season_crop": s_crop_val,
                "fertilizers_used": s_ferts,
                "intensity": s_intensity,
                "organic_manure_used": any("Compost" in f or "FYM" in f for f in s_ferts)
            })

    if user:
        if st.button("💾 Save Fertilizer Profile to Farm Account", type="secondary"):
            for s_in in season_inputs:
                db_service.save_fertilizer_season(
                    user_id=user["id"],
                    season_label=s_in["season_label"],
                    season_crop=s_in["season_crop"],
                    fertilizers_used=s_in["fertilizers_used"],
                    intensity=s_in["intensity"],
                    organic_manure_used=s_in["organic_manure_used"]
                )
            st.success("✓ Past 3 seasons fertilizer history saved to your farm database!")

    # Calculate Agronomic Adjustments
    fertilizer_insights = FertilizerHistoryEngine.analyze_fertilizer_history(
        season_records=season_inputs,
        base_n=active_n,
        base_p=active_p,
        base_k=active_k,
        base_ph=active_ph
    )

    st.markdown("##### 🔬 Soil Nutrient Adjustments Derived from Fertilizer History:")
    f_c1, f_c2, f_c3, f_c4 = st.columns(4)
    with f_c1:
        st.metric(
            "Effective Nitrogen (N)",
            f"{fertilizer_insights['adjusted_n']} kg/ha",
            delta=f"{fertilizer_insights['n_delta']:+0.1f} kg/ha (Residual)"
        )
    with f_c2:
        st.metric(
            "Effective Phosphorus (P)",
            f"{fertilizer_insights['adjusted_p']} kg/ha",
            delta=f"{fertilizer_insights['p_delta']:+0.1f} kg/ha (Reserve)"
        )
    with f_c3:
        st.metric(
            "Effective Potassium (K)",
            f"{fertilizer_insights['adjusted_k']} kg/ha",
            delta=f"{fertilizer_insights['k_delta']:+0.1f} kg/ha (Buffer)"
        )
    with f_c4:
        st.metric(
            "Adjusted pH Reaction",
            f"{fertilizer_insights['adjusted_ph']}",
            delta=f"{fertilizer_insights['ph_delta']:+0.2f}"
        )

    for ins in fertilizer_insights["soil_insights"]:
        render_html(f"""<div class="tip-box">ℹ️ {ins}</div>""")
    for warn in fertilizer_insights["warnings"]:
        render_html(f"""<div class="con-box">{warn}</div>""")

    active_n = fertilizer_insights["adjusted_n"]
    active_p = fertilizer_insights["adjusted_p"]
    active_k = fertilizer_insights["adjusted_k"]
    active_ph = fertilizer_insights["adjusted_ph"]

st.divider()

# --- SECTION 2: AI Crop Recommendation Engine ---
st.markdown("### 🤖 Step 2: AI Top 3 Recommended Crops")
st.markdown("Ranked using a **Machine Learning Classifier** combined with **Agronomic Multi-Factor Biological Matching** and **Crop Rotation Intelligence**.")

# Agronomic Class Filter Bar
filter_options = [
    "🌟 All Crops (Top Overall)",
    "🧅 Vegetables & Cash Crops",
    "🌾 Food Grains & Millets",
    "🌿 Pulses & Oilseeds",
    "🍎 Fruits & Orchards"
]
selected_category = st.radio(
    "**Filter Recommendations by Agronomic Crop Class:**",
    filter_options,
    horizontal=True,
    index=0
)

top_recommendations = ml_engine.recommend_top_crops(
    n=active_n,
    p=active_p,
    k=active_k,
    temp=active_temp,
    hum=active_hum,
    ph=active_ph,
    rain=active_rain,
    soil_type=active_soil_type,
    top_k=3,
    past_crops=past_planted_crops,
    fertilizer_insights=fertilizer_insights if enable_fert_factor else None,
    category_filter=selected_category
)

# Display Top 3 Cards
rec_cols = st.columns(3)

for idx, rec in enumerate(top_recommendations):
    with rec_cols[idx]:
        rotation_tag_html = ""
        if rec.get("rotation_bonus", 0) > 0:
            rotation_tag_html = f"<div class='rotation-pill-pro'>🔄 Rotation Bonus: +{rec['rotation_bonus']:.0f}%</div>"
        elif rec.get("rotation_bonus", 0) < 0:
            rotation_tag_html = f"<div class='rotation-pill-risk'>⚠️ Monoculture Risk: {rec['rotation_bonus']:.0f}%</div>"

        score_val = float(rec['score'])
        score_pct = min(100.0, max(0.0, score_val))

        card_html = f"""
        <div class="crop-card-v2">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
                    <span class="rank-pill">RANK #{idx + 1}</span>
                    <span class="category-pill">{rec['category']}</span>
                </div>
                {rotation_tag_html}
                <div class="crop-title">{rec['crop']}</div>
                <div class="crop-marathi">{rec['marathi_name']}</div>
                <div style="margin: 14px 0 16px 0;">
                    <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 0.9rem; margin-bottom: 6px;">
                        <span style="color: #2d6a4f;">Overall Suitability</span>
                        <span style="color: #1b4332; font-weight: 800;">{rec['score']}%</span>
                    </div>
                    <div style="background-color: #e5ece7; border-radius: 999px; height: 9px; width: 100%; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #1b4332, #52b788); height: 100%; width: {score_pct}%; border-radius: 999px;"></div>
                    </div>
                </div>
            </div>
            <div style="border-top: 1px dashed #d8e6dc; padding-top: 12px; margin-top: 8px;">
                <div style="font-size: 0.85rem; color: #4b6354; line-height: 1.6;">
                    <span>🗓️ <b>Season:</b> {rec['season']}</span><br>
                    <span>💧 <b>Water Need:</b> {rec['water_need']}</span>
                </div>
            </div>
        </div>
        """
        render_html(card_html)

        with st.expander(f"📖 Scientific Rationale for {rec['crop']}", expanded=True):
            st.markdown(f"> {rec['reasoning']}")

# Multi-Factor Agronomic Radar Comparison
st.markdown("#### 📊 Multi-Dimensional Suitability Comparison")
radar_col1, radar_col2 = st.columns([3, 2])

with radar_col1:
    categories = ['Temperature', 'Rainfall', 'Soil pH', 'Humidity', 'Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)']
    fig = go.Figure()

    colors = ['#1b4332', '#0284c7', '#d97706']
    for idx, rec in enumerate(top_recommendations):
        f_scores = [rec['feature_scores'].get(c, 70.0) for c in categories]
        f_scores.append(f_scores[0])
        fig.add_trace(go.Scatterpolar(
            r=f_scores,
            theta=categories + [categories[0]],
            fill='toself',
            name=f"{rec['crop']} ({rec['score']}%)",
            line=dict(color=colors[idx % len(colors)], width=2.5),
            opacity=0.55
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9)),
        ),
        showlegend=True,
        margin=dict(l=40, r=40, t=20, b=20),
        height=360
    )
    st.plotly_chart(fig, use_container_width=True)

with radar_col2:
    st.markdown("##### 🔍 Why This Multi-Season Model Excels")
    st.markdown(f"""
    - **Dual Validation:** Pairs statistical machine learning with ICAR/FAO biological limits.
    - **Crop Rotation Safeguards:** {'Active! Factoring your previously logged crops to prevent soil-borne pests.' if past_planted_crops else 'Log in to auto-enable past season rotation bonuses and monoculture warnings.'}
    - **Fertilizer Memory:** {'Active! Accounting for past fertilizer residual nutrients.' if enable_fert_factor else 'Optional factor disabled. Uses current soil testing baseline.'}
    - **Soil-Climate Coupling:** Considers both rhizosphere chemistry (pH, N, P, K) and ambient meteorological stress.
    """)

# Full 20-Crop Agronomic Leaderboard
with st.expander("📋 View Complete 20-Crop Feasibility Leaderboard & Scientific Rankings", expanded=False):
    st.caption("Comprehensive comparative ranking of all catalogued crops for your exact soil parameters and meteorological conditions:")
    if hasattr(ml_engine, "last_evaluated_candidates") and ml_engine.last_evaluated_candidates:
        leaderboard_data = []
        for rank_idx, c_item in enumerate(ml_engine.last_evaluated_candidates):
            rot_tag = f"+{c_item['rotation_bonus']:.0f}%" if c_item['rotation_bonus'] > 0 else (f"{c_item['rotation_bonus']:.0f}%" if c_item['rotation_bonus'] < 0 else "-")
            leaderboard_data.append({
                "Rank": f"#{rank_idx + 1}",
                "Crop": f"{c_item['crop']} ({c_item['marathi_name']})",
                "Category": c_item['category'],
                "Overall Suitability": f"{c_item['score']}%",
                "Biological Match": f"{c_item['agri_score']}%",
                "ML Density Fit": f"{c_item['ml_density']}%",
                "Rotation Bonus": rot_tag,
                "Season": c_item['season'],
                "Water Demand": c_item['water_need']
            })
        st.dataframe(pd.DataFrame(leaderboard_data), use_container_width=True, hide_index=True)

st.divider()

# --- SECTION 3: Custom Crop Feasibility Analyzer ---
st.markdown("### 🎯 Step 3: Custom Crop Feasibility Analyzer (Pros & Cons)")
st.caption("Have a specific crop in mind? Test whether your climate, soil, and field history can support it before investing capital.")

custom_col1, custom_col2 = st.columns([3, 1])

with custom_col1:
    preset_crops = ["Sugarcane", "Cotton", "Soybean", "Onion", "Grapes", "Pomegranate", "Banana", "Rice (Paddy)", "Wheat", "Tomato"]
    user_crop_input = st.selectbox(
        "Do you have a specific crop in mind?",
        options=preset_crops + ["Other (Type custom crop name)"],
        index=0
    )

    if user_crop_input == "Other (Type custom crop name)":
        user_crop_input = st.text_input("Enter the crop name you wish to evaluate:", placeholder="e.g. Turmeric, Ginger, Papaya, Coffee, Watermelon...")

with custom_col2:
    st.write("")
    st.write("")
    analyze_crop_btn = st.button("🔬 Stress-Test This Crop", type="primary", use_container_width=True)

# Perform Feasibility Analysis with rotation and fertilizer insights
feasibility_result = feasibility_engine.analyze_feasibility(
    crop_input=user_crop_input,
    weather={
        "temperature": active_temp,
        "humidity": active_hum,
        "rainfall": active_rain
    },
    soil={
        "soil_type": active_soil_type,
        "ph": active_ph,
        "N": active_n,
        "P": active_p,
        "K": active_k,
        "deficiencies": soil.get("deficiencies", []),
        "risks": soil.get("risks", []),
        "overall_quality": soil.get("overall_quality", "")
    },
    past_crops=past_planted_crops,
    fertilizer_insights=fertilizer_insights if enable_fert_factor else None
)

v_score = feasibility_result["feasibility_score"]
v_badge = feasibility_result["verdict_badge"]

if v_badge == "success":
    st.success(f"### ✅ Viability Verdict: {feasibility_result['verdict']} (Score: {v_score}%)")
elif v_badge == "warning":
    st.warning(f"### ⚠️ Viability Verdict: {feasibility_result['verdict']} (Score: {v_score}%)")
else:
    st.error(f"### ❌ Viability Verdict: {feasibility_result['verdict']} (Score: {v_score}%)")

st.markdown(f"**Crop Selected:** `{feasibility_result['crop_name']}` ({feasibility_result['marathi_name']}) &nbsp;|&nbsp; **Category:** `{feasibility_result['category']}` &nbsp;|&nbsp; **Water Need:** `{feasibility_result['water_need']}`")

pro_col, con_col = st.columns(2)

with pro_col:
    st.markdown("#### 🟢 Positives (Pros)")
    if feasibility_result["positives"]:
        for pro in feasibility_result["positives"]:
            render_html(f"""<div class="pro-box">✅ {pro}</div>""")
    else:
        st.info("No significant natural advantages found for this crop in current conditions.")

with con_col:
    st.markdown("#### 🔴 Negatives (Cons & Risks)")
    if feasibility_result["negatives"]:
        for con in feasibility_result["negatives"]:
            render_html(f"""<div class="con-box">⚠️ {con}</div>""")
    else:
        st.success("No critical environmental bottlenecks detected!")

if feasibility_result["infrastructure"]:
    st.markdown("#### 🏗️ Recommended Irrigation & Protective Infrastructure")
    for infra in feasibility_result["infrastructure"]:
        render_html(f"""<div class="infra-box">🛠️ {infra}</div>""")

st.divider()

# --- SECTION 4: Yield Optimization & Actionable Tips ---
st.markdown("### 💡 Step 4: Yield Optimization & Actionable Agronomic Tips")
st.caption("Targeted, science-backed field recommendations tailored to your soil chemistry and selected crop.")

tip_col1, tip_col2 = st.columns([1, 1])

with tip_col1:
    st.markdown(f"#### 🌾 Tailored Advice for `{feasibility_result['crop_name']}`")
    if feasibility_result["yield_tips"]:
        for tip in feasibility_result["yield_tips"]:
            render_html(f"""<div class="tip-box">🌱 {tip}</div>""")
    else:
        st.info("Standard package of practices applies.")

with tip_col2:
    st.markdown("#### 🧪 Soil Health & Correction Protocols")
    st_lower = active_soil_type.lower()
    st_def = [d.lower() for d in soil.get("deficiencies", [])]
    st_risk = [r.lower() for r in soil.get("risks", [])]

    soil_protocols = []

    if any("zinc" in d for d in st_def) or "calcareous" in st_lower or "black" in st_lower:
        soil_protocols.append(
            "**Zinc Deficiency Correction:** Apply 25 kg/ha of Zinc Sulfate ($ZnSO_4$, 21%) into the soil during seedbed preparation. Avoid mixing directly with Phosphatic fertilizers (DAP/SSP) to prevent chemical precipitation."
        )

    if any("salin" in r for r in st_risk) or "saline" in st_lower:
        soil_protocols.append(
            "**Salinity & Electrical Conductivity (EC) Management:** Apply 500–800 kg/acre Agricultural Gypsum ($CaSO_4$) to displace exchangeable sodium. Follow with furrow leaching and incorporate green manure (Dhaincha or Sunnhemp)."
        )

    if "lime" in st_lower or active_ph > 8.0:
        soil_protocols.append(
            "**Lime Chlorosis & Iron Deficiency:** High calcium carbonate fixes iron and phosphorus. Apply elemental sulfur (25 kg/acre) or spray Chelated Iron (Fe-EDTA 12%) @ 1.5 g/liter water to prevent leaf yellowing."
        )

    if "laterite" in st_lower or active_ph < 6.2:
        soil_protocols.append(
            "**Soil Acidity Amelioration:** Apply Agricultural Lime or Dolomite (300 kg/acre) 3 weeks prior to sowing. Apply Single Super Phosphate (SSP) instead of DAP to supply both phosphorus and calcium."
        )

    soil_protocols.append(
        f"**Precision NPK Scheduling:** Current effective soil state is N:{active_n:.0f}, P:{active_p:.0f}, K:{active_k:.0f} kg/ha. Apply 50% Nitrogen as basal and remaining 50% split at 30 & 60 days after sowing. Apply full Phosphorus and Potash at sowing."
    )

    for proto in soil_protocols:
        render_html(f"""<div class="tip-box">📋 {proto}</div>""")

st.divider()

# --- SECTION 5: FINAL PLANTING DECISION & CROP LOGGING ---
st.markdown("### 🎯 Step 5: Final Planting Decision & Season Logging")
st.caption("Commit your final planting decision to your personal farm database. When you log in next season, the system will use this record to suggest the best rotational crops and alert you against monoculture risks!")

decision_crop_options = [r["crop"] for r in top_recommendations]
if feasibility_result["crop_name"] not in decision_crop_options:
    decision_crop_options.append(feasibility_result["crop_name"])
for c in list(AGRONOMIC_CROP_PROFILES.keys()):
    if c not in decision_crop_options:
        decision_crop_options.append(c)

current_year = datetime.now().year
default_season_names = [
    f"Kharif {current_year}",
    f"Rabi {current_year}-{str(current_year+1)[-2:]}",
    f"Summer / Zaid {current_year}",
    f"Annual {current_year}"
]

dec_col1, dec_col2 = st.columns([1, 1])

with dec_col1:
    final_chosen_crop = st.selectbox(
        "🌱 Which crop have you finally decided to plant?",
        options=decision_crop_options,
        index=0,
        help="Select the crop you have decided to plant this season based on the AI recommendations."
    )
    final_season_name = st.selectbox(
        "🗓️ Sowing Season & Year:",
        options=default_season_names + ["Custom Season Entry"],
        index=0
    )
    if final_season_name == "Custom Season Entry":
        final_season_name = st.text_input("Enter Custom Season Name:", placeholder=f"e.g. Late Kharif {current_year}")

with dec_col2:
    final_fertilizers = st.text_input(
        "🧪 Fertilizers Planned / Applied for this Crop:",
        placeholder="e.g. DAP 50 kg/acre + FYM 3 tons + Zinc Sulfate 10 kg"
    )
    final_notes = st.text_area(
        "📝 Farm Plot Notes / Targets:",
        placeholder="e.g. North plot with drip irrigation; aiming for early market harvest."
    )

if user is None:
    st.warning("⚠️ **You are currently in Guest Mode.** Please **Sign In or Register** at the top right to permanently save this planting decision into the database.")
    c_demo, _ = st.columns([1, 2])
    with c_demo:
        if st.button("⚡ Quick Login as Demo Farmer to Save", use_container_width=True):
            success, msg, user_data = db_service.authenticate_user("farmer_demo", "kisan123")
            if success:
                st.session_state["user"] = user_data
                st.session_state["guest_mode"] = False
                st.session_state["active_location"] = user_data.get("default_location", "Baramati (Pune)")
                st.rerun()
else:
    if st.button("💾 Confirm & Save Planting Decision to Farm History", type="primary", use_container_width=True):
        crop_prof = AGRONOMIC_CROP_PROFILES.get(final_chosen_crop, {})
        m_name = crop_prof.get("marathi_name", "")
        cat_name = crop_prof.get("category", "Agricultural Crop")

        rec_id = db_service.save_planting_decision(
            user_id=user["id"],
            season_name=final_season_name,
            year=current_year,
            crop_name=final_chosen_crop,
            marathi_name=m_name,
            category=cat_name,
            location=current_data['query'],
            soil_type=active_soil_type,
            ph=active_ph,
            n=active_n,
            p=active_p,
            k=active_k,
            temperature=active_temp,
            rainfall=active_rain,
            fertilizers_applied=final_fertilizers,
            notes=final_notes
        )

        st.success(f"""
        ### 🎉 Planting Decision Recorded Successfully!
        - **Farmer:** `{user['full_name']}`
        - **Season:** `{final_season_name}`
        - **Crop Decided:** `{final_chosen_crop}` ({m_name})
        - **Location:** `{current_data['query']}`
        
        *This decision is now securely saved in your SQLite farm database (Record #{rec_id}). Next season, the AI will use this record to recommend optimal rotational crops!*
        """)
        st.balloons()

st.divider()

# --- SECTION 6: Export / Download Farm Advisory Summary ---
st.markdown("### 📑 Farm Advisory Summary Report")
st.caption("Download a formatted agricultural advisory report for documentation or sharing with field agronomists.")

user_display_name = user['full_name'] if user else "Guest Farmer"

report_md = f"""# KRISHIMITRA AI - CROP & SOIL ADVISORY REPORT
Farmer Name: {user_display_name}
Farm Location: {current_data['query'].title()}
Soil Source: {soil['source']}
Weather Telemetry Source: {weather['source']}
Report Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

==================================================
1. ENVIRONMENTAL & SOIL TELEMETRY
- Ambient Temperature: {weather['temperature']} °C ({weather['weather_description']})
- Atmospheric Relative Humidity: {weather['humidity']} %
- Agro-Rainfall Index: {weather['rainfall']} mm
- Soil Classification: {active_soil_type}
- Effective Soil pH: {active_ph:.1f}
- Effective Soil Nitrogen (N): {active_n:.1f} kg/ha
- Effective Soil Phosphorus (P): {active_p:.1f} kg/ha
- Effective Soil Potassium (K): {active_k:.1f} kg/ha
- Soil Quality Assessment: {soil.get('overall_quality', 'Normal')}
- Past 3 Seasons Fertilizer History Active: {"YES" if enable_fert_factor else "NO"}
- Past Crops Rotation Active: {"YES (" + ', '.join(past_planted_crops[:3]) + ")" if past_planted_crops else "NO"}

==================================================
2. TOP 3 SCIENTIFIC CROP RECOMMENDATIONS
Rank 1: {top_recommendations[0]['crop']} ({top_recommendations[0]['marathi_name']}) - Suitability: {top_recommendations[0]['score']}%
Reasoning: {top_recommendations[0]['reasoning']}

Rank 2: {top_recommendations[1]['crop']} ({top_recommendations[1]['marathi_name']}) - Suitability: {top_recommendations[1]['score']}%
Reasoning: {top_recommendations[1]['reasoning']}

Rank 3: {top_recommendations[2]['crop']} ({top_recommendations[2]['marathi_name']}) - Suitability: {top_recommendations[2]['score']}%
Reasoning: {top_recommendations[2]['reasoning']}

==================================================
3. CUSTOM CROP FEASIBILITY EVALUATION
Target Crop: {feasibility_result['crop_name']} ({feasibility_result['marathi_name']})
Viability Score: {feasibility_result['feasibility_score']}%
Verdict: {feasibility_result['verdict']}

Positives (Pros):
{chr(10).join(['- ' + p for p in feasibility_result['positives']])}

Negatives (Cons / Risks):
{chr(10).join(['- ' + c for c in feasibility_result['negatives']])}

Recommended Infrastructure:
{chr(10).join(['- ' + i for i in feasibility_result['infrastructure']])}

==================================================
4. ACTIONABLE YIELD OPTIMIZATION TIPS
{chr(10).join(['- ' + t for t in feasibility_result['yield_tips']])}

Soil Health Protocols:
{chr(10).join(['- ' + p for p in soil_protocols])}

==================================================
5. FINAL PLANTING DECISION LOG
Decided Crop: {final_chosen_crop}
Season: {final_season_name}
Planned Fertilizers: {final_fertilizers if final_fertilizers else "Standard basal dose"}
Notes: {final_notes if final_notes else "None"}

Report generated by KrishiMitra AI - Precision Agritech Platform.
"""

st.download_button(
    label="📥 Download Printable Farm Advisory Report (.txt)",
    data=report_md,
    file_name=f"krishimitra_advisory_{current_data['query'].lower().replace(' ', '_')}.txt",
    mime="text/plain",
    use_container_width=True
)

render_html("""
<div style="text-align: center; color: #718378; font-size: 0.85rem; margin-top: 40px; padding: 20px 0; border-top: 1px solid #e2ede5;">
    KrishiMitra AI Precision Agriculture Platform • Built with Streamlit, Scikit-Learn & SQLite • Designed for Indian Farming Communities
</div>
""")
