"""
Agronomic engine for assessing:
1. Past 3 seasons fertilizer history (Optional Factor).
2. Previous seasons crop rotation synergies and monoculture risks.
"""

from typing import Dict, Any, List, Tuple, Optional

# Fertilizer agronomic nutrient profiles and characteristics
FERTILIZER_DATABASE = {
    "Urea (46% N)": {
        "primary_nutrient": "N",
        "n_contrib": 46.0, "p_contrib": 0.0, "k_contrib": 0.0,
        "ph_impact": -0.15,  # slight acidifying effect with repeated heavy use
        "residual_effect": "Elevated soil nitrates, rapid vegetative boost, risks lodging if excessive",
        "description": "High-analysis nitrogen fertilizer. Fast acting, prone to leaching or volatilization."
    },
    "DAP (Di-Ammonium Phosphate 18:46:0)": {
        "primary_nutrient": "P",
        "n_contrib": 18.0, "p_contrib": 46.0, "k_contrib": 0.0,
        "ph_impact": 0.05,
        "residual_effect": "High phosphorus buildup. Immobile in soil; can induce Zinc deficiency in calcareous soils.",
        "description": "Widely used basal phosphatic fertilizer with starter nitrogen."
    },
    "MOP (Muriate of Potash 0:0:60)": {
        "primary_nutrient": "K",
        "n_contrib": 0.0, "p_contrib": 0.0, "k_contrib": 60.0,
        "ph_impact": 0.0,
        "residual_effect": "Supplies chloride and potassium; enhances drought tolerance and fruit skin strength.",
        "description": "Standard potassium source for boll/fruit enlargement and water regulation."
    },
    "Single Super Phosphate (SSP 16% P, 11% S, 19% Ca)": {
        "primary_nutrient": "P",
        "n_contrib": 0.0, "p_contrib": 16.0, "k_contrib": 0.0,
        "ph_impact": -0.05,
        "residual_effect": "Provides essential Sulfur and Calcium along with Phosphorus. Ideal for oilseeds and pulses.",
        "description": "Multi-nutrient phosphatic fertilizer with active sulfur and calcium."
    },
    "NPK Complex (10:26:26 / 12:32:16)": {
        "primary_nutrient": "NPK",
        "n_contrib": 12.0, "p_contrib": 30.0, "k_contrib": 20.0,
        "ph_impact": 0.0,
        "residual_effect": "Balanced balanced basal nutrient reserve across all three macronutrients.",
        "description": "Granular complex fertilizer offering sustained release of N, P, and K."
    },
    "Compost / Farmyard Manure (FYM) / Vermicompost": {
        "primary_nutrient": "Organic Carbon",
        "n_contrib": 10.0, "p_contrib": 8.0, "k_contrib": 10.0,
        "ph_impact": 0.0,
        "residual_effect": "High Soil Organic Carbon (SOC), buffers soil pH, enhances microbial biomass and water holding capacity.",
        "description": "Decomposed biological matter vital for soil physical health and micronutrient availability."
    },
    "Zinc Sulfate (ZnSO4, 21% / 33%)": {
        "primary_nutrient": "Micronutrient",
        "n_contrib": 0.0, "p_contrib": 0.0, "k_contrib": 0.0,
        "ph_impact": 0.0,
        "residual_effect": "Eliminates zinc chlorosis, supports auxin synthesis and enzyme activation.",
        "description": "Essential micronutrient for black calcareous and high-pH soils."
    },
    "19:19:19 (Water Soluble Foliar/Drip)": {
        "primary_nutrient": "NPK",
        "n_contrib": 19.0, "p_contrib": 19.0, "k_contrib": 19.0,
        "ph_impact": 0.0,
        "residual_effect": "Completely soluble, readily assimilated, minimal soil residual accumulation.",
        "description": "High-purity fertigation / foliar grade balanced fertilizer."
    }
}

AVAILABLE_FERTILIZERS = list(FERTILIZER_DATABASE.keys())

class FertilizerHistoryEngine:
    """Evaluates multi-season fertilizer application patterns and previous crop rotation impacts."""

    @staticmethod
    def analyze_fertilizer_history(
        season_records: List[Dict[str, Any]],
        base_n: float,
        base_p: float,
        base_k: float,
        base_ph: float
    ) -> Dict[str, Any]:
        """
        Calculates adjusted residual soil NPK and pH based on the past 3 seasons of fertilizer usage.
        season_records: list of dicts with keys:
           'season_label', 'season_crop', 'fertilizers_used' (list of str), 'intensity' (Low, Standard/Balanced, Heavy/Excessive)
        """
        if not season_records:
            return {
                "active": False,
                "adjusted_n": base_n,
                "adjusted_p": base_p,
                "adjusted_k": base_k,
                "adjusted_ph": base_ph,
                "n_delta": 0.0,
                "p_delta": 0.0,
                "k_delta": 0.0,
                "ph_delta": 0.0,
                "nitrogen_status": "Baseline",
                "phosphorus_status": "Baseline",
                "potassium_status": "Baseline",
                "organic_carbon_status": "Standard",
                "soil_insights": ["No past fertilizer records provided; using standard soil baseline."],
                "warnings": []
            }

        intensity_multipliers = {
            "Low": 0.5,
            "Low / Minimal Application": 0.5,
            "Standard/Balanced": 1.0,
            "Standard / Balanced Recommended Dose": 1.0,
            "Heavy/Excessive": 1.7,
            "Heavy / Intensive Repeated Application": 1.7
        }

        # Weight recent seasons higher: Season -1 (50%), Season -2 (30%), Season -3 (20%)
        recency_weights = [0.50, 0.30, 0.20]

        total_n_delta = 0.0
        total_p_delta = 0.0
        total_k_delta = 0.0
        total_ph_delta = 0.0
        organic_seasons_count = 0
        zinc_applied_count = 0
        heavy_urea_count = 0
        heavy_dap_count = 0

        insights = []
        warnings = []

        for idx, rec in enumerate(season_records[:3]):
            weight = recency_weights[idx] if idx < len(recency_weights) else 0.15
            intensity = rec.get("intensity", "Standard/Balanced")
            mult = intensity_multipliers.get(intensity, 1.0)
            ferts = rec.get("fertilizers_used", [])
            if isinstance(ferts, str):
                ferts = [ferts]

            # Check individual fertilizers
            for f in ferts:
                f_data = FERTILIZER_DATABASE.get(f)
                if not f_data:
                    # Partial match
                    for k, v in FERTILIZER_DATABASE.items():
                        if f.lower() in k.lower():
                            f_data = v
                            break

                if f_data:
                    # Scale based on nutrient residual fractions (N is mobile ~20% residual, P is immobile ~45% residual, K ~30%)
                    n_gain = (f_data["n_contrib"] * 0.20) * mult * weight
                    p_gain = (f_data["p_contrib"] * 0.40) * mult * weight
                    k_gain = (f_data["k_contrib"] * 0.30) * mult * weight
                    ph_shift = f_data["ph_impact"] * mult * weight

                    total_n_delta += n_gain
                    total_p_delta += p_gain
                    total_k_delta += k_gain
                    total_ph_delta += ph_shift

                    if "Urea" in f and mult >= 1.5:
                        heavy_urea_count += 1
                    if "DAP" in f and mult >= 1.5:
                        heavy_dap_count += 1
                    if "Compost" in f or "FYM" in f or rec.get("organic_manure_used"):
                        organic_seasons_count += 1
                    if "Zinc" in f:
                        zinc_applied_count += 1

        # Calculate adjusted parameters
        adj_n = round(max(10.0, min(180.0, base_n + total_n_delta)), 1)
        adj_p = round(max(5.0, min(140.0, base_p + total_p_delta)), 1)
        adj_k = round(max(10.0, min(220.0, base_k + total_k_delta)), 1)
        adj_ph = round(max(4.5, min(9.0, base_ph + total_ph_delta)), 2)

        # Generate scientific interpretations
        if heavy_urea_count >= 2:
            warnings.append(
                "⚠️ **High Residual Nitrogen:** Intensive Urea use detected across multiple seasons. Avoid excess nitrogenous basal doses to prevent crop lodging and vegetative overrun."
            )
            insights.append("Soil has high residual nitrate. Excellent for heavy foliage consumers like Sugarcane and Maize, but reduces nodulation efficacy for pulses.")

        if heavy_dap_count >= 2:
            warnings.append(
                "⚠️ **Phosphorus Fixation Alert:** Frequent heavy DAP applications lead to insoluble calcium-phosphate fixation in black/calcareous soils, which suppresses micronutrient Zinc intake."
            )
            insights.append("High residual Phosphate detected. Recommend using Phosphorus Solubilizing Bacteria (PSB) to mobilize fixed phosphates without buying more DAP.")

        if organic_seasons_count >= 2:
            insights.append("🌱 **Superior Soil Health:** Regular Farmyard Manure / Compost application has enriched Soil Organic Carbon (SOC), stabilizing moisture retention and cation exchange.")

        if zinc_applied_count > 0:
            insights.append("✓ **Zinc Enrichment:** Soil has received active zinc supplementation in recent seasons, minimizing micro-nutrient chlorosis risk.")

        # Determine status tiers
        n_status = "High Reserve" if total_n_delta > 12 else ("Moderate Boost" if total_n_delta > 4 else "Baseline")
        p_status = "High Accumulation" if total_p_delta > 15 else ("Adequate" if total_p_delta > 5 else "Baseline")
        k_status = "Rich Potash Buffer" if total_k_delta > 15 else ("Adequate" if total_k_delta > 5 else "Baseline")
        org_status = "Rich (Organic Matter Added)" if organic_seasons_count >= 2 else ("Moderate" if organic_seasons_count == 1 else "Needs Organic Addition")

        return {
            "active": True,
            "adjusted_n": adj_n,
            "adjusted_p": adj_p,
            "adjusted_k": adj_k,
            "adjusted_ph": adj_ph,
            "n_delta": round(total_n_delta, 1),
            "p_delta": round(total_p_delta, 1),
            "k_delta": round(total_k_delta, 1),
            "ph_delta": round(total_ph_delta, 2),
            "nitrogen_status": n_status,
            "phosphorus_status": p_status,
            "potassium_status": k_status,
            "organic_carbon_status": org_status,
            "soil_insights": insights,
            "warnings": warnings
        }

    @staticmethod
    def evaluate_crop_rotation_synergy(
        candidate_crop: str,
        past_crops: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Evaluates crop rotation principles against previously planted crops.
        Returns:
            rotation_bonus (can be positive for good rotation, or negative for monoculture risk),
            synergy_reasons (list of pros),
            risk_reasons (list of cons/warnings).
        """
        if not past_crops:
            return 0.0, [], []

        last_crop = past_crops[0].lower()
        cand_lower = candidate_crop.lower()

        legumes = ["soybean", "chickpea", "harbara", "chana", "pigeonpea", "tur", "arhar", "groundnut", "green gram", "black gram"]
        heavy_feeders = ["sugarcane", "cotton", "maize", "corn", "banana"]
        solanaceous = ["tomato", "potato", "chilli", "brinjal", "eggplant"]
        cereals = ["wheat", "rice", "paddy", "sorghum", "jowar", "pearl millet", "bajra"]

        bonus = 0.0
        synergies = []
        risks = []

        # 1. Monoculture Penalty (Exact same crop consecutively)
        if cand_lower in last_crop or last_crop in cand_lower:
            bonus = -12.0
            risks.append(
                f"**Monoculture Hazard:** Consecutive planting of **{candidate_crop}** after **{past_crops[0]}** elevates soil-borne pathogen carryover, pest pupae infestation, and specific root-zone nutrient exhaustion."
            )
            if "cotton" in cand_lower:
                risks.append("Continuous cotton promotes Pink Bollworm (*Pectinophora gossypiella*) survival in subterranean cocoons.")
            elif "sugarcane" in cand_lower:
                risks.append("Continuous ratoon / adsali sugarcane causes subsoil compaction and increases Red Rot (*Colletotrichum falcatum*) disease pressure.")
            return bonus, synergies, risks

        # 2. Solanaceous family monoculture
        if any(s in last_crop for s in solanaceous) and any(s in cand_lower for s in solanaceous):
            bonus = -10.0
            risks.append(f"**Family Monoculture:** Both **{past_crops[0]}** and **{candidate_crop}** belong to the Solanaceae family; sharing susceptibility to Bacterial Wilt (*Ralstonia*) and root-knot nematodes.")
            return bonus, synergies, risks

        # 3. Legume -> Cereal / Cotton / Heavy Feeder Synergy (EXCELLENT)
        if any(leg in last_crop for leg in legumes):
            if any(c in cand_lower for c in cereals) or any(hf in cand_lower for hf in heavy_feeders):
                bonus = 10.0
                synergies.append(
                    f"**Outstanding Crop Rotation:** Planting **{candidate_crop}** following **{past_crops[0]}** (a nitrogen-fixing legume) takes direct advantage of biologically fixed residual soil nitrogen (~25–40 kg N/ha) and enhanced soil aeration."
                )

        # 4. Heavy Feeder -> Legume Synergy (RESTORATIVE)
        if any(hf in last_crop for hf in heavy_feeders) or any(c in last_crop for c in cereals):
            if any(leg in cand_lower for leg in legumes):
                bonus = 9.0
                synergies.append(
                    f"**Soil Restorative Rotation:** Following heavy feeder **{past_crops[0]}** with legume **{candidate_crop}** restores depleted organic nitrogen, interrupts the pest cycle, and rejuvenates root-zone microbial ecology."
                )

        # 5. Deep root vs Shallow root rotation
        if any(dr in last_crop for dr in ["pigeonpea", "cotton"]):
            if any(sr in cand_lower for sr in ["onion", "wheat"]):
                bonus += 4.0
                synergies.append(f"**Root-Zone Stratification:** Alternating between deep-taproot ({past_crops[0]}) and shallow fibrous-root ({candidate_crop}) prevents continuous exhaustion of a single subsoil depth.")

        return bonus, synergies, risks
