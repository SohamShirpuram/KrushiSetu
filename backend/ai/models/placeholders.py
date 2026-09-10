"""
FUTURE AI MODULE PLACEHOLDERS & INTERFACES:
Defines clean structural interfaces for upcoming KrushiSetu AI modules.
These modules will branch from the One Central AI Engine in future stages.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseFutureModule(ABC):
    """Base interface for upcoming KrushiSetu Central AI modules."""
    
    @abstractmethod
    def predict(self, *args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("This AI module is scheduled for future implementation stages.")

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        return {"status": "SCHEDULED", "module": self.__class__.__name__}

# Note: PSToGPAllocationModel is concretely implemented in ps_gp_allocation_model.py (Task 3)
# Note: GPToFarmerRecommendationModel is concretely implemented in farmer_recommendation_model.py (Task 4)


class FarmerCropRecommendationModel(BaseFutureModule):
    """Farmer Individual Crop & Advisory Recommendation Module (Future)"""
    def predict(self, farmer_id: str, land_details: dict, soil_card: dict) -> Dict[str, Any]:
        raise NotImplementedError("Farmer Crop Recommendation AI model scheduled for future stage.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "SCHEDULED_STAGE_2", "module": "FarmerCropRecommendationModel"}


class MajorWarehouseCVGradingModel(BaseFutureModule):
    """Major Warehouse Computer Vision Automated Grading Model (Future)"""
    def predict(self, grain_image_bytes: bytes, physical_metrics: dict) -> Dict[str, Any]:
        raise NotImplementedError("Production Computer Vision Grading model scheduled for future stage.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "SCHEDULED_STAGE_3", "module": "MajorWarehouseCVGradingModel"}


class MinorWarehouseDemandStockModel(BaseFutureModule):
    """Minor Warehouse Transit Godown Demand & Stock Prediction Model (Future)"""
    def predict(self, warehouse_id: str, historical_sales: list) -> Dict[str, Any]:
        raise NotImplementedError("Minor Warehouse Demand/Stock AI model scheduled for future stage.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "SCHEDULED_STAGE_3", "module": "MinorWarehouseDemandStockModel"}


class CropSpoilagePredictionModel(BaseFutureModule):
    """Grain Silo Spoilage Risk & Aeration Prediction Model (Future)"""
    def predict(self, temp_series: list, humidity_series: list, days_stored: int) -> Dict[str, Any]:
        raise NotImplementedError("Spoilage Prediction AI model scheduled for future stage.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "SCHEDULED_STAGE_4", "module": "CropSpoilagePredictionModel"}


class SupplyChainAnomalyDetectionModel(BaseFutureModule):
    """End-to-End Supply Chain Anomaly & Discrepancy Detection Model (Future)"""
    def predict(self, transit_events: list, weighbridge_logs: list) -> Dict[str, Any]:
        raise NotImplementedError("Supply Chain Anomaly Detection AI model scheduled for future stage.")

    def get_status(self) -> Dict[str, Any]:
        return {"status": "SCHEDULED_STAGE_4", "module": "SupplyChainAnomalyDetectionModel"}

