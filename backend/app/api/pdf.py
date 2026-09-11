from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from backend.app.database.mongodb import db_manager
from backend.app.pdf.conversation_pdf import generate_conversation_pdf

router = APIRouter(tags=["pdf"])


@router.get("/conversation/{session_id}/pdf")
async def download_conversation_pdf(session_id: str):
    """
    Generate and download a comprehensive, beautifully styled PDF report of the conversation session.
    """
    conv = db_manager.get_conversation(session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found for PDF export.")

    try:
        pdf_buffer = generate_conversation_pdf(conv, static_evidence_dir="./evidence")
        filename = f"SatQuery_Analysis_{session_id[:8]}.pdf"

        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate conversation PDF: {str(e)}")
