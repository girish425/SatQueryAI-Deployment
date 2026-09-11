import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from backend.app.database.schemas import ChatRequest, ChatResponse
from backend.app.agent.controller import agent_controller
from backend.app.api.auth import get_current_user

router = APIRouter(tags=["chat"])
UPLOAD_DIR = Path("./uploads")


@router.post("/chat/", response_model=ChatResponse)
async def chat_query(request: ChatRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """
    Primary chat endpoint. Passes user question and attached images to the Agent Controller,
    which determines intent, selects ONE model workflow, executes it, and records conversation.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Resolve image paths
    resolved_paths: List[str] = []
    for img_id in request.image_ids:
        # Check if full path or filename in upload directory
        candidate = UPLOAD_DIR / img_id
        if candidate.exists():
            resolved_paths.append(str(candidate))
        elif Path(img_id).exists():
            resolved_paths.append(img_id)
        else:
            # Search in sample_data
            sample_candidate = Path("./sample_data") / img_id
            if sample_candidate.exists():
                resolved_paths.append(str(sample_candidate))
            else:
                # Search partial match in uploads
                matches = list(UPLOAD_DIR.glob(f"*{img_id}*"))
                if matches:
                    resolved_paths.append(str(matches[0]))

    if not resolved_paths:
        raise HTTPException(
            status_code=400,
            detail="No valid satellite image found. Please upload or retrieve a .tif / .tiff satellite image first."
        )

    try:
        user_id = current_user.get("user_id") if current_user else None
        response_data = agent_controller.process_query(
            query=request.query,
            image_paths=resolved_paths,
            session_id=request.session_id,
            user_id=user_id
        )
        return response_data
    except ValueError as ve:
        # User-friendly domain exceptions (e.g. missing second image, bad format)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Prevent leaking raw python traces while providing descriptive feedback
        raise HTTPException(
            status_code=500,
            detail=f"The selected analysis model could not process this image: {str(e)}"
        )
