import logging
from typing import Dict, Any, List

logger = logging.getLogger("satquery.model_selector")


class ModelSelector:
    """Registry and lazy loader for specialized remote sensing analysis models."""

    def __init__(self):
        # Lazy cache: models instantiated only when invoked
        self._loaded_models: Dict[str, Any] = {}

        # Model metadata registry
        self.MODEL_REGISTRY = {
            "image_understanding": {
                "id": "image_understanding",
                "name": "RS-Image-Understanding-Baseline",
                "module": "backend.app.models.image_understanding",
                "class_name": "ImageUnderstandingModel",
                "description": "Calculates pixel-derived land-cover statistics, vegetative/water indices, and scene summary.",
                "min_images": 1
            },
            "vqa": {
                "id": "vqa",
                "name": "RS-VQA-Spectral-Baseline",
                "module": "backend.app.models.vqa",
                "class_name": "VQAModel",
                "description": "Question-aware feature detection and presence reasoning across spectral bands.",
                "min_images": 1
            },
            "grounding": {
                "id": "grounding",
                "name": "RS-Grounding-Baseline",
                "module": "backend.app.models.grounding",
                "class_name": "ImageGroundingModel",
                "description": "Spatial localization, boundary detection, and bounding box overlay.",
                "min_images": 1
            },
            "change_detection": {
                "id": "change_detection",
                "name": "RS-BiTemporal-Change-Baseline",
                "module": "backend.app.models.change_detection",
                "class_name": "ChangeDetectionModel",
                "description": "Bi-temporal difference mapping, thresholded change mask, and area calculation.",
                "min_images": 2
            },
            "optical_sar": {
                "id": "optical_sar",
                "name": "RS-Optical-SAR-Fusion-Baseline",
                "module": "backend.app.models.optical_sar",
                "class_name": "OpticalSARModel",
                "description": "Multimodal fusion comparing optical surface reflectance with microwave SAR radar backscatter.",
                "min_images": 1
            }
        }

    def select_model(self, intent: str, num_images: int) -> Dict[str, Any]:
        """Select exactly one model workflow for the detected intent and validate prerequisites."""
        if intent not in self.MODEL_REGISTRY:
            intent = "image_understanding"

        model_info = self.MODEL_REGISTRY[intent]

        # Validate input constraints
        if intent == "change_detection" and num_images < 2:
            raise ValueError("Change detection requires two images. Please upload a before and after image.")

        if num_images == 0:
            raise ValueError("No satellite image uploaded. Please upload a .tif or .tiff satellite image.")

        return model_info

    def get_or_load_model(self, model_id: str):
        """Lazy loader: loads model on demand and caches it."""
        if model_id in self._loaded_models:
            return self._loaded_models[model_id]

        model_info = self.MODEL_REGISTRY.get(model_id)
        if not model_info:
            raise ValueError(f"Unknown model identifier: {model_id}")

        logger.info(f"Lazily loading model: {model_info['name']}...")
        import importlib
        module = importlib.import_module(model_info["module"])
        cls = getattr(module, model_info["class_name"])
        instance = cls()
        self._loaded_models[model_id] = instance
        return instance


model_selector = ModelSelector()
