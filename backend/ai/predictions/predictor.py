from datetime import datetime
import time
import json
from typing import Dict, Any
from backend.ai.data_preparation import PreparedCropFeatures
from backend.ai.models.crop_requirement_model import CropRequirementRecommendationModel

class CropRequirementPredictor:
    """
    PREDICTION RUNNER:
    Coordinates feature feeding into the model, generates official
    prediction tracking IDs, and serializes input references for permanent audit storage.
    """

    def __init__(self, model: CropRequirementRecommendationModel = None):
        self.model = model or CropRequirementRecommendationModel()

    def generate_prediction(self, features: PreparedCropFeatures, db_prediction_count: int = 0) -> Dict[str, Any]:
        """
        Executes inference, attaches official prediction ID, and structures storage payload.
        """
        raw_prediction = self.model.predict(features)
        
        # Format official prediction tracking ID: PRED-CR-2026-XXXX
        seq = db_prediction_count + 1
        prediction_id = f"PRED-CR-2026-{seq:04d}"

        # JSON serialized snapshot of inputs
        input_ref_dict = features.to_summary_dict()
        input_ref_json = json.dumps(input_ref_dict)

        # JSON serialized factors
        factors_json = json.dumps(raw_prediction["factors"])

        return {
            "prediction_id": prediction_id,
            "module_name": "crop_requirement_recommendation",
            "model_name": self.model.model_name,
            "model_version": self.model.model_version,
            "input_data_reference": input_ref_json,
            "input_data_summary": input_ref_dict,
            "ai_recommended_crop": raw_prediction["recommended_crop"],
            "ai_recommended_quantity": raw_prediction["recommended_quantity_mt"],
            "ai_priority": raw_prediction["priority"],
            "ai_reasoning": raw_prediction["reasoning"],
            "ai_factors": factors_json,
            "ai_factors_dict": raw_prediction["factors"],
            "ai_confidence": raw_prediction["confidence"],
            "suitable_region": raw_prediction["suitable_region"],
            "generated_at": datetime.utcnow(),
            "review_status": "PENDING_REVIEW",
            "metadata": raw_prediction["metadata"],
        }

