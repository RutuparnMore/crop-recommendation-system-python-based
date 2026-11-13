"""Test suite for KrishiMitra Agritech System with Database & Multi-Season Factors."""
import sys
import os
import json
from utils.soil_service import SoilService
from utils.weather_service import WeatherService
from utils.ml_engine import CropRecommendationEngine
from utils.feasibility_engine import FeasibilityEngine
from utils.db_service import DatabaseService
from utils.fertilizer_history_engine import FertilizerHistoryEngine

def run_tests():
    print("==================================================")
    print("1. Testing SoilService...")
    soil_svc = SoilService("data/soil_database.csv")
    print(f"Total locations loaded: {len(soil_svc.get_all_locations())}")
    
    soil_pune = soil_svc.fetch_soil_profile("Baramati")
    print(f"Baramati Soil: {soil_pune['soil_type']}, pH={soil_pune['ph']}, N={soil_pune['N']}, P={soil_pune['P']}, K={soil_pune['K']}")
    assert soil_pune["matched_in_database"] is True, "Failed to match Baramati in DB"

    soil_unknown = soil_svc.fetch_soil_profile("Patna")
    print(f"Patna Soil: {soil_unknown['soil_type']}, pH={soil_unknown['ph']}")
    assert soil_unknown["matched_in_database"] is False, "Patna should not match DB"

    print("\n==================================================")
    print("2. Testing WeatherService...")
    weather_svc = WeatherService()
    w_pune = weather_svc.fetch_weather("Pune")
    print(f"Pune Weather: Temp={w_pune['temperature']}°C, Humidity={w_pune['humidity']}%, Rain={w_pune['rainfall']}mm, Source={w_pune['source']}")
    assert "temperature" in w_pune and w_pune["temperature"] > -50, "Invalid weather"

    print("\n==================================================")
    print("3. Testing DatabaseService (Auth, Plantings, Fertilizers)...")
    test_db_path = "data/test_farm.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    db = DatabaseService(db_path=test_db_path)

    # Test registration
    ok, msg, user = db.register_user("vikram_kisan", "pass1234", "Vikram Shinde", "Jalgaon")
    assert ok is True, f"Registration failed: {msg}"
    print(f"User registered successfully: {user['full_name']} (@{user['username']})")

    # Test login
    ok_log, msg_log, auth_user = db.authenticate_user("vikram_kisan", "pass1234")
    assert ok_log is True, f"Login failed: {msg_log}"
    print(f"Authentication verified for user ID: {auth_user['id']}")

    # Test bad login
    bad_log, _, _ = db.authenticate_user("vikram_kisan", "wrongpass")
    assert bad_log is False, "Bad password should fail authentication"

    # Test saving planting decision (Current / Previous season)
    rec1_id = db.save_planting_decision(
        user_id=auth_user["id"],
        season_name="Kharif 2025",
        year=2025,
        crop_name="Soybean",
        marathi_name="सोयाबीन",
        category="Oilseed / Legume",
        location="Jalgaon",
        soil_type="Deep Black Cotton Soil",
        ph=7.6,
        n=45.0,
        p=38.0,
        k=65.0,
        temperature=28.0,
        rainfall=110.0,
        fertilizers_applied="DAP (50 kg) + Rhizobium bio-fertilizer",
        notes="Planted in East field; good nodulation."
    )
    print(f"Saved Season 1 planting decision: Record #{rec1_id}")

    # Save second season (e.g. Rabi 2025-26)
    rec2_id = db.save_planting_decision(
        user_id=auth_user["id"],
        season_name="Rabi 2025-26",
        year=2025,
        crop_name="Wheat",
        marathi_name="गहू",
        category="Cereal Food Grain",
        location="Jalgaon",
        soil_type="Deep Black Cotton Soil",
        ph=7.6,
        n=52.0,
        p=35.0,
        k=60.0,
        temperature=22.0,
        rainfall=40.0,
        fertilizers_applied="Urea split doses (2 bags) + SSP",
        notes="Wheat followed soybean."
    )
    print(f"Saved Season 2 planting decision: Record #{rec2_id}")

    # Test retrieving planting history
    history = db.get_user_planting_history(auth_user["id"])
    print(f"Total retrieved planting records for user: {len(history)}")
    assert len(history) == 2, "Expected 2 saved planting seasons"
    assert history[0]["crop_name"] == "Wheat", "Newest crop should be Wheat"
    assert history[1]["crop_name"] == "Soybean", "Previous crop should be Soybean"

    print("\n==================================================")
    print("4. Testing FertilizerHistoryEngine (Past 3 Seasons Factor)...")
    past_seasons_fert = [
        {
            "season_label": "Season -1",
            "season_crop": "Wheat",
            "fertilizers_used": ["Urea (46% N)", "Single Super Phosphate (SSP 16% P, 11% S, 19% Ca)"],
            "intensity": "Standard / Balanced Recommended Dose"
        },
        {
            "season_label": "Season -2",
            "season_crop": "Soybean",
            "fertilizers_used": ["DAP (Di-Ammonium Phosphate 18:46:0)", "Compost / Farmyard Manure (FYM) / Vermicompost"],
            "intensity": "Standard / Balanced Recommended Dose",
            "organic_manure_used": True
        },
        {
            "season_label": "Season -3",
            "season_crop": "Chickpea",
            "fertilizers_used": ["Zinc Sulfate (ZnSO4, 21% / 33%)"],
            "intensity": "Low / Minimal Application"
        }
    ]

    fert_eval = FertilizerHistoryEngine.analyze_fertilizer_history(
        season_records=past_seasons_fert,
        base_n=soil_pune["N"],
        base_p=soil_pune["P"],
        base_k=soil_pune["K"],
        base_ph=soil_pune["ph"]
    )
    print(f"Fertilizer Adjustments: N_delta={fert_eval['n_delta']} kg/ha, P_delta={fert_eval['p_delta']} kg/ha, K_delta={fert_eval['k_delta']} kg/ha")
    print(f"Adjusted Soil NPK: N={fert_eval['adjusted_n']}, P={fert_eval['adjusted_p']}, K={fert_eval['adjusted_k']}")
    assert fert_eval["adjusted_n"] >= soil_pune["N"], "Nitrogen should be increased by past urea"
    assert fert_eval["adjusted_p"] >= soil_pune["P"], "Phosphorus should be increased by past DAP/SSP"

    print("\n==================================================")
    print("5. Testing Crop Rotation Synergy & Monoculture Penalization...")
    # Legume -> Cereal synergy
    bonus_rot, syn_rot, _ = FertilizerHistoryEngine.evaluate_crop_rotation_synergy("Wheat", ["Soybean"])
    print(f"Rotation Bonus (Wheat after Soybean): +{bonus_rot}% | Synergy: {syn_rot[0] if syn_rot else ''}")
    assert bonus_rot > 0, "Wheat after Soybean should receive positive rotation bonus"

    # Cotton after Cotton monoculture penalty
    penalty_rot, _, risks_rot = FertilizerHistoryEngine.evaluate_crop_rotation_synergy("Cotton", ["Cotton"])
    print(f"Monoculture Penalty (Cotton after Cotton): {penalty_rot}% | Risk: {risks_rot[0] if risks_rot else ''}")
    assert penalty_rot < 0, "Cotton after Cotton must receive negative monoculture penalty"

    print("\n==================================================")
    print("6. Testing ML Recommendation Engine with Rotation & Fertilizer Inputs...")
    ml_engine = CropRecommendationEngine()
    recs_with_history = ml_engine.recommend_top_crops(
        n=fert_eval["adjusted_n"],
        p=fert_eval["adjusted_p"],
        k=fert_eval["adjusted_k"],
        temp=w_pune["temperature"],
        hum=w_pune["humidity"],
        ph=fert_eval["adjusted_ph"],
        rain=w_pune["rainfall"],
        soil_type=soil_pune["soil_type"],
        top_k=3,
        past_crops=["Soybean"],
        fertilizer_insights=fert_eval
    )
    print("Top 3 Recommendations incorporating past Soybean rotation and fertilizer history:")
    for idx, r in enumerate(recs_with_history):
        print(f"  #{idx+1}: {r['crop']} ({r['score']}%) [Rotation Bonus: {r.get('rotation_bonus', 0)}%]")
        print(f"       Reasoning: {r['reasoning'][:120]}...")
    assert len(recs_with_history) == 3, "Expected 3 crop recommendations"

    print("\n==================================================")
    print("7. Testing FeasibilityEngine with Monoculture Detection...")
    feas_engine = FeasibilityEngine(ml_engine)
    feas_mono = feas_engine.analyze_feasibility(
        crop_input="Cotton",
        weather={"temperature": 30.0, "humidity": 60.0, "rainfall": 80.0},
        soil=soil_pune,
        past_crops=["Cotton"]
    )
    print(f"Cotton after Cotton Viability Score: {feas_mono['feasibility_score']}%")
    has_mono_warning = any("Monoculture" in neg for neg in feas_mono["negatives"])
    print(f"Monoculture warning triggered in negatives: {has_mono_warning}")
    assert has_mono_warning, "Expected monoculture hazard in negatives for Cotton after Cotton"

    # Clean up test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\n==================================================")
    print("ALL AGRONOMIC, DATABASE, AND MULTI-SEASON TEST SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
