import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from backend.app.database.mongodb import db_manager

router = APIRouter(tags=["history"])


@router.get("/history/")
async def list_history():
    """Retrieve all conversations stored in MongoDB."""
    convs = db_manager.list_conversations()
    return {
        "status": "success",
        "count": len(convs),
        "conversations": convs
    }


@router.get("/history/{session_id}")
async def get_conversation(session_id: str):
    """Retrieve full conversation transcript and messages for session."""
    conv = db_manager.get_conversation(session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found.")
    return {
        "status": "success",
        "conversation": conv
    }


@router.post("/history/new")
async def create_new_session():
    """Initialize a brand new chat session."""
    session_id = str(uuid.uuid4())
    conv = db_manager.save_conversation(session_id, "New Satellite Analysis", [])
    return {
        "status": "success",
        "session_id": session_id,
        "conversation": conv
    }


@router.post("/history/save")
async def save_conversation_endpoint(data: Dict[str, Any]):
    """
    Explicitly save or update conversation session title, selected models,
    image references, or messages.
    """
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    title = data.get("title", "Satellite Analysis Session")
    messages = data.get("messages")
    selected_model = data.get("selected_model")
    image_references = data.get("image_references")

    conv = db_manager.save_conversation(
        session_id=session_id,
        title=title,
        messages=messages,
        selected_model=selected_model,
        image_references=image_references
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
