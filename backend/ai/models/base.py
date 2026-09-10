from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseCentralAIModel(ABC):
    """
    Abstract Base Class for all Central AI/ML Engine Models in KrushiSetu.
    Enforces standardized interfaces, explainability, versioning,
    and metadata disclosure.
    """

    def __init__(self, model_name: str, model_version: str):
        self.model_name = model_name
        self.model_version = model_version

    @abstractmethod
    def predict(self, features: Any) -> Dict[str, Any]:
        """Runs inference on prepared features and returns structured prediction dictionary."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns model metadata, algorithm details, and data readiness flags."""
        pass

