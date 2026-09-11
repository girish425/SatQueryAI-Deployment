import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

from backend.app.agent.intent_classifier import intent_classifier
from backend.app.agent.model_selector import model_selector
from backend.app.database.mongodb import db_manager

logger = logging.getLogger("satquery.agent_controller")


class AgentController:
    """
    Central Agent Controller / Decision-Making Layer.
    Orchestrates Intent Analysis -> Model Selection -> Single Model Execution -> Result Formatting.
    """

    def process_query(
        self,
        query: str,
        image_paths: List[str],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())

        if not image_paths or len(image_paths) == 0:
            raise ValueError("No satellite image uploaded. Please upload a .tif or .tiff satellite image.")

        # Step 1: Analyze user query and classify intent
        num_images = len(image_paths)
        classification = intent_classifier.classify(query, num_images=num_images)
        intent = classification["intent"]
        intent_conf = classification["confidence"]
        reason = classification["reason"]

        logger.info(f"Agent classified query: '{query}' -> Intent: {intent} (conf: {intent_conf})")

        # Step 2: Select ONE appropriate workflow
        model_info = model_selector.select_model(intent, num_images)
        model_id = model_info["id"]

        # Step 3: Lazy load and execute ONLY the selected model
        logger.info(f"Executing ONLY model workflow: {model_info['name']}")
        model_instance = model_selector.get_or_load_model(model_id)

        if intent in ["change_detection", "optical_sar"]:
            result = model_instance.analyze(image_paths=image_paths, query=query)
        else:
            result = model_instance.analyze(image_path=image_paths[0], query=query)

        total_proc_time = round(time.time() - start_time, 2)

        # Merge processing times into technical details
        tech_details = result.get("technical_details", {})
        tech_details["processing_time_sec"] = total_proc_time
        tech_details["selected_intent"] = intent
        tech_details["intent_confidence"] = intent_conf
        tech_details["model_selected"] = model_info["name"]

        response_payload = {
            "session_id": session_id,
            "query": query,
            "image_ids": [Path(p).name for p in image_paths],
            "intent": intent,
            "intent_confidence": intent_conf,
            "model_used": model_info["name"],
            "reason": reason,
            "answer": result["answer"],
            "evidence": result["evidence"],
            "technical_details": tech_details,
            "confidence": result.get("confidence", 0.85),
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Step 4: Persist in Conversation History (MongoDB Atlas / Fallback)
        img_refs = [Path(p).name for p in image_paths]
        user_msg = {
            "session_id": session_id,
            "role": "user",
            "message": query,
            "query": query,
            "image_ids": img_refs,
            "image_references": img_refs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        asst_msg = {
            "session_id": session_id,
            "role": "assistant",
            "message": result["answer"]["summary"],
            "query": query,
            "ai_response": result["answer"],
            "selected_model": model_info["name"],
            "model_used": model_info["name"],
            "image_ids": img_refs,
            "image_references": img_refs,
            "timestamp": response_payload["timestamp"],
            "intent": intent,
            "intent_confidence": intent_conf,
            "answer": result["answer"],
            "evidence": result["evidence"],
            "technical_details": tech_details,
            "confidence": result.get("confidence", 0.85),
            "processing_time": total_proc_time
        }

        # Auto title from first query if new conversation
        existing = db_manager.get_conversation(session_id)
        if not existing:
            title = query[:40] + ("..." if len(query) > 40 else "")
            db_manager.save_conversation(
                session_id=session_id,
                title=title,
                messages=[user_msg, asst_msg],
                selected_model=model_info["name"],
                image_references=img_refs,
                user_id=user_id
            )
        else:
            db_manager.add_message(session_id, user_msg, user_id=user_id)
            db_manager.add_message(session_id, asst_msg, user_id=user_id)

        return response_payload


agent_controller = AgentController()
