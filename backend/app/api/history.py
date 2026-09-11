import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from backend.app.database.mongodb import db_manager
from backend.app.api.auth import get_current_user

router = APIRouter(tags=["history"])


@router.get("/history/")
async def list_history(current_user: Optional[dict] = Depends(get_current_user)):
    """Retrieve conversations strictly filtered by the authenticated user for privacy."""
    user_id = current_user.get("user_id") if current_user else None
    convs = db_manager.list_conversations(user_id=user_id)
    return {
        "status": "success",
        "count": len(convs),
        "conversations": convs
    }


@router.get("/history/{session_id}")
async def get_conversation(session_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Retrieve full conversation transcript and messages, enforcing user privacy."""
    user_id = current_user.get("user_id") if current_user else None
    conv = db_manager.get_conversation(session_id, user_id=user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found or unauthorized.")
    return {
        "status": "success",
        "conversation": conv
    }


@router.post("/history/new")
async def create_new_session(current_user: Optional[dict] = Depends(get_current_user)):
    """Initialize a brand new chat session tied to current user."""
    session_id = str(uuid.uuid4())
    user_id = current_user.get("user_id") if current_user else None
    conv = db_manager.save_conversation(session_id, "New Satellite Analysis", [], user_id=user_id)
    return {
        "status": "success",
        "session_id": session_id,
        "conversation": conv
    }


@router.post("/history/save")
async def save_conversation_endpoint(data: Dict[str, Any], current_user: Optional[dict] = Depends(get_current_user)):
    """
    Explicitly save or update conversation session title, selected models,
    image references, or messages tied to the authenticated user.
    """
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    title = data.get("title", "Satellite Analysis Session")
    messages = data.get("messages")
    selected_model = data.get("selected_model")
    image_references = data.get("image_references")
    user_id = current_user.get("user_id") if current_user else data.get("user_id")

    conv = db_manager.save_conversation(
        session_id=session_id,
        title=title,
        messages=messages,
        selected_model=selected_model,
        image_references=image_references,
        user_id=user_id
    )
    return {
        "status": "success",
        "session_id": session_id,
        "conversation": conv
    }


@router.get("/history/db/status")
async def get_history_db_status():
    """Retrieve database health and connection status for history management."""
    return db_manager.check_health()


@router.delete("/history/{session_id}")
async def delete_conversation(session_id: str):
    """Delete a conversation by session ID."""
    success = db_manager.delete_conversation(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found to delete.")
    return {
        "status": "success",
        "message": f"Session {session_id} deleted."
    }
