"""
CONTROLLED OFFLINE TRAINING DATASET BUILDER
Prepares structured multi-factor feature matrices from historical operational tables.
Designed for controlled offline training pipelines.
Does NOT run automatically on database mutations.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import (
    FDCropRequirement,
    FDCrisisRecord,
    FDDemandProjection,
    FDWeatherData,
    FarmerHarvestRecord,
)

class CropRequirementDatasetBuilder:
    """
    Constructs feature matrices (X) and label targets (y) from accumulated
    operational records for offline model training.
    """

    @staticmethod
    def build_training_dataset(db: Session) -> Dict[str, Any]:
        """
        Gathers historical requirements and actual harvests to form training rows.
        """
        requirements = db.query(FDCropRequirement).all()
        harvests = db.query(FarmerHarvestRecord).all()
        crises = db.query(FDCrisisRecord).all()
        demands = db.query(FDDemandProjection).all()
        weathers = db.query(FDWeatherData).all()

        rows = []
        for req in requirements:
            # Match approximate demand and crisis for this crop
            demand_match = next((d for d in demands if req.crop_name and d.crop_name and req.crop_name[:4] in d.crop_name), None)
            crisis_match = next((c for c in crises if req.crop_name and c.crop_name and req.crop_name[:4] in c.crop_name), None)
            
            curr_demand = demand_match.current_demand_mt if demand_match else 15000.0
            deficit = crisis_match.deficit_amount_mt if crisis_match else 0.0
            rain = weathers[0].rainfall_mm if weathers else 640.0

            target_qty = req.human_final_quantity_mt or req.target_quantity_mt

            rows.append({
                "crop_name": req.crop_name,
                "season": req.season,
                "current_demand_mt": curr_demand,
                "deficit_mt": deficit,
                "rainfall_mm": rain,
                "target_quantity_mt": target_qty,
            })

        sample_count = len(rows)
        # Check statistical sufficiency for training production weights
        is_sufficient = sample_count >= 50
        status_note = (
            f"Dataset assembled with {sample_count} historical rows. "
            f"{'Sufficient for initial regression fitting.' if is_sufficient else 'Dataset size is insufficient for deep model training (recommended minimum N >= 50). Using explainable heuristic prototype.'}"
        )

        return {
            "dataset_name": "krushisetu_crop_requirements_v1",
            "feature_columns": ["current_demand_mt", "deficit_mt", "rainfall_mm"],
            "target_column": "target_quantity_mt",
            "samples_count": sample_count,
            "is_sufficient_for_training": is_sufficient,
            "status_note": status_note,
            "data": rows,
        }

