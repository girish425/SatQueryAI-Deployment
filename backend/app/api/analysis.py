from fastapi import APIRouter
from backend.app.agent.model_selector import model_selector

router = APIRouter(tags=["analysis"])


@router.get("/analysis/models")
async def list_registered_models():
    """List all registered modular remote-sensing analysis engines."""
    return {
        "status": "success",
        "models": model_selector.MODEL_REGISTRY
    }
