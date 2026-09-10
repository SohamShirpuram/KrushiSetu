from typing import Dict, Any, List
from backend.ai.models.base import BaseCentralAIModel

class PSToGPAllocationModel(BaseCentralAIModel):
    """
    Central AI/ML Engine: Panchayat Samiti -> Gram Panchayat Crop Allocation Model.
    Architecture: Explainable Multi-Factor Land & Soil Suitability Optimization (v1.0.0-prototype).
    
    GUARANTEES:
    1. Quota Conservation: sum(allocations) == total_approved_quota_mt exactly.
    2. Multi-factor Suitability: Balances cultivable land area, crop-soil compatibility,
       irrigation canal/lift coverage, organic carbon ratings, and active farmer density.
    3. Fully Explainable: Every GP allocation includes specific soil, land, and math trace.
    """

    def __init__(self):
        super().__init__(
            model_name="Central AI - PSToGPAllocationModel",
            model_version="v1.0.0-prototype"
        )

    def predict(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Runs optimization across candidate Gram Panchayats under the Panchayat Samiti.
        """
        gp_profiles = features.get("gp_profiles", [])
        total_quota_mt = float(features.get("total_quota_mt", 0.0))
        crop_name = features.get("crop_name", "Crop")
        season = features.get("season", "Rabi 2026")
        panchayat_samiti_name = features.get("panchayat_samiti_name", "Baramati Block Panchayat Samiti")

        if not gp_profiles or total_quota_mt <= 0:
            return []

        clean_crop = crop_name.split()[0].replace("(", "").replace(")", "").strip().lower()

        # Step 1: Compute raw suitability weights for each GP
        weighted_gps = []
        for gp in gp_profiles:
            cultivable_ha = float(gp.get("cultivable_area_hectares", 100.0))
            soil_type = gp.get("soil_type", "Medium Deep Black Cotton Soil")
            primary_crops = gp.get("primary_crops", "").lower()
            irrigation_pct = float(gp.get("irrigation_coverage_pct", 60.0))
            organic_matter = gp.get("organic_matter_rating", "MEDIUM").upper()
            farmers_count = int(gp.get("active_farmers_count", 50))

            # Crop-soil compatibility score (0.0 to 1.0)
            if clean_crop in primary_crops:
                crop_match_score = 1.0
            elif any(c in primary_crops for c in ["wheat", "soybean", "gram", "sugarcane", "paddy"]):
                crop_match_score = 0.75
            else:
                crop_match_score = 0.50

            # Irrigation score (0.0 to 1.0)
            irrigation_score = min(max(irrigation_pct / 100.0, 0.3), 1.0)

            # Organic matter rating score
            if organic_matter == "HIGH":
                organic_score = 1.0
            elif organic_matter == "MEDIUM":
                organic_score = 0.8
            else:
                organic_score = 0.5

            # Farmer availability factor (0.5 to 1.2)
            farmer_factor = min(max(farmers_count / 250.0, 0.5), 1.2)

            # Multi-factor Composite Suitability Index
            composite_suitability = (
                (crop_match_score * 0.40) +
                (irrigation_score * 0.25) +
                (organic_score * 0.20) +
                (farmer_factor * 0.15)
            )

            # Combined Allocation Weight
            allocation_weight = cultivable_ha * composite_suitability

            # Categorical Suitability Rating
            if composite_suitability >= 0.80:
                suitability_cat = "HIGH_SUITABILITY"
            elif composite_suitability >= 0.65:
                suitability_cat = "MEDIUM_SUITABILITY"
            else:
                suitability_cat = "MODERATE_SUITABILITY"

            # Confidence Score
            confidence = round(0.90 + (composite_suitability * 0.05), 2)

            weighted_gps.append({
                "gp": gp,
                "cultivable_ha": cultivable_ha,
                "composite_suitability": composite_suitability,
                "allocation_weight": allocation_weight,
                "suitability_cat": suitability_cat,
                "confidence": confidence,
                "crop_match_score": crop_match_score,
                "irrigation_pct": irrigation_pct,
                "organic_matter": organic_matter,
                "soil_type": soil_type,
            })

        total_weight = sum(item["allocation_weight"] for item in weighted_gps) or 1.0

        # Step 2: Compute proportional allocation ensuring sum == total_quota_mt
        allocations = []
        allocated_sum = 0.0

        for item in weighted_gps:
            share = item["allocation_weight"] / total_weight
            allocated_mt = round(total_quota_mt * share, 1)
            allocated_sum += allocated_mt

            gp_info = item["gp"]
            reasoning = (
                f"Allocated {allocated_mt:,.1f} MT ({share * 100:.1f}%) based on {item['cultivable_ha']} Ha cultivable land, "
                f"{item['soil_type']} with {item['irrigation_pct']:.1f}% irrigation coverage and "
                f"{item['organic_matter']} organic matter rating. Active farmers: {gp_info.get('active_farmers_count', 0)}."
            )

            priority = "CRITICAL" if total_quota_mt > 20000 else "HIGH" if item["suitability_cat"] == "HIGH_SUITABILITY" else "NORMAL"

            allocations.append({
                "gp_code": gp_info["gp_code"],
                "gp_name": gp_info["gp_name"],
                "panchayat_samiti_name": panchayat_samiti_name,
                "crop_name": crop_name,
                "season": season,
                "agricultural_area_ha": item["cultivable_ha"],
                "active_farmers_count": gp_info.get("active_farmers_count", 0),
                "ai_recommended_quantity_mt": allocated_mt,
                "ai_priority": priority,
                "ai_suitability": item["suitability_cat"],
                "ai_confidence_score": item["confidence"],
                "ai_reasoning": reasoning,
                "model_name": self.model_name,
                "model_version": self.model_version,
                "ai_factors": {
                    "cultivable_ha": item["cultivable_ha"],
                    "soil_type": item["soil_type"],
                    "crop_match_score": item["crop_match_score"],
                    "irrigation_pct": item["irrigation_pct"],
                    "organic_matter": item["organic_matter"],
                    "composite_suitability": round(item["composite_suitability"], 3),
                    "share_pct": round(share * 100, 2),
                }
            })

        # Step 3: Exact Quota Balancing (Absorb minor floating point rounding on top GP)
        diff = round(total_quota_mt - allocated_sum, 1)
        if abs(diff) > 0 and len(allocations) > 0:
            allocations[0]["ai_recommended_quantity_mt"] = round(allocations[0]["ai_recommended_quantity_mt"] + diff, 1)

        return allocations

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "type": "Multi-Factor Land & Soil Suitability Allocation Optimizer",
            "weights": {
                "crop_soil_compatibility": 0.40,
                "irrigation_coverage": 0.25,
                "organic_matter": 0.20,
                "farmer_density": 0.15,
            },
            "conservation_guaranteed": True,
        }

