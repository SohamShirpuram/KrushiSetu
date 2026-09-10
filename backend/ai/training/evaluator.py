"""
MODEL EVALUATION PIPELINE
Computes regression and classification metrics on validation datasets.
"""

from typing import Dict, Any, List

class CropRequirementModelEvaluator:
    """
    Evaluates model candidate quality against holdout evaluation datasets.
    """

    @staticmethod
    def evaluate(predictions: List[float], actuals: List[float]) -> Dict[str, Any]:
        if not predictions or not actuals or len(predictions) != len(actuals):
            return {
                "status": "INSUFFICIENT_EVALUATION_DATA",
                "rmse": 0.0,
                "mae": 0.0,
                "r2_score": 0.0,
            }

        n = len(predictions)
        errors = [p - a for p, a in zip(predictions, actuals)]
        mae = sum(abs(e) for e in errors) / n
        mse = sum(e ** 2 for e in errors) / n
        rmse = mse ** 0.5

        mean_actual = sum(actuals) / n
        ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
        ss_res = sum(e ** 2 for e in errors)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return {
            "status": "EVALUATED",
            "eval_samples": n,
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
            "r2_score": round(max(0.0, r2), 3),
            "production_deployment_ready": r2 >= 0.85,
        }

