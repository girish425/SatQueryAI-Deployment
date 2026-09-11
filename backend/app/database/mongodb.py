import os
import re
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load backend/.env
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent.parent
_env_path = _backend_dir / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=True)
else:
    load_dotenv(override=True)

logger = logging.getLogger("satquery.database")

# Read MONGODB_URI and DATABASE_NAME from backend/.env
RAW_MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MONGODB_DB_NAME", "satquery_ai")


def sanitize_mongodb_uri(uri: str) -> str:
    """
    Handle connection string quirks such as placeholder angle brackets <password>
    accidentally left by users when pasting from MongoDB Atlas.
    """
    if not uri:
        return ""
    # Strip < > around password if present: :<secret>@ -> :secret@
    return re.sub(r':<([^>]+)>@', r':\1@', uri)


def mask_mongodb_uri(uri: str) -> str:
    """
    Safely mask the database password in connection URIs to avoid exposing credentials.
    Never hardcode or expose the MongoDB password in logs, API responses, or error traces.
    Turns: mongodb+srv://username:password@host -> mongodb+srv://username:****@host
    """
    if not uri:
        return "Not Configured"
    return re.sub(r'(://[^:]+:)([^@]+)(@)', r'\1****\3', uri)


MONGODB_URI = sanitize_mongodb_uri(RAW_MONGODB_URI)


class LocalFallbackStore:
    """
    Resilient file-backed fallback store. Ensures SatQuery AI remains fully functional
    even when MongoDB Atlas is unreachable, network is offline, or Atlas IP access is pending.
    """

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_dir / "conversations_store.json"
        self.users_path = self.data_dir / "users_store.json"
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._users: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load fallback store: {e}")
                self._cache = {}
        if self.users_path.exists():
            try:
                with open(self.users_path, "r", encoding="utf-8") as f:
                    self._users = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load users store: {e}")
                self._users = {}

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save fallback store: {e}")

    def _save_users(self):
        try:
            with open(self.users_path, "w", encoding="utf-8") as f:
                json.dump(self._users, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save users store: {e}")

    def create_user(self, email: str, password_hash: str, full_name: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        user_doc = {
            "user_id": user_id,
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "full_name": full_name.strip(),
            "created_at": now
        }
        self._users[user_id] = user_doc
        self._save_users()
        return user_doc

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        norm = email.lower().strip()
        for u in self._users.values():
            if u.get("email", "").lower().strip() == norm:
                return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def get_conversation(self, session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conv = self._cache.get(session_id)
        if not conv:
            return None
        if user_id and conv.get("user_id") and conv.get("user_id") != user_id:
            return None
        return conv

    def list_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        convs = list(self._cache.values())
        if user_id:
            convs = [c for c in convs if c.get("user_id") == user_id]
        convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return convs

    def save_conversation(
        self,
        session_id: str,
        title: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        selected_model: Optional[str] = None,
        image_references: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        if session_id not in self._cache:
            self._cache[session_id] = {
                "session_id": session_id,
                "title": title,
                "user_id": user_id,
                "created_at": now,
                "updated_at": now,
                "selected_model": selected_model or "RS-MultiModal-Pipeline",
                "image_references": image_references or [],
                "messages": messages or []
            }
        else:
            conv = self._cache[session_id]
            conv["title"] = title or conv.get("title", "New Satellite Analysis")
            conv["updated_at"] = now
            if user_id and not conv.get("user_id"):
                conv["user_id"] = user_id
            if selected_model:
                conv["selected_model"] = selected_model
            if image_references:
                conv["image_references"] = list(set(conv.get("image_references", []) + image_references))
            if messages is not None:
                conv["messages"] = messages
        self._save()
        return self._cache[session_id]

    def add_message(self, session_id: str, message: Dict[str, Any], user_id: Optional[str] = None) -> None:
        if session_id not in self._cache:
            self.save_conversation(session_id, "New Satellite Analysis", [], user_id=user_id)
        msg_clean = message.copy()
        if user_id and "user_id" not in msg_clean:
            msg_clean["user_id"] = user_id
        self._cache[session_id]["messages"].append(msg_clean)
        self._cache[session_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def delete_conversation(self, session_id: str) -> bool:
        if session_id in self._cache:
            del self._cache[session_id]
            self._save()
            return True
        return False


class MongoDBConnectionManager:
    """
    Reusable MongoDB connection manager with Atlas support, SSL certificate validation,
    connection health-checking, diagnostic reporting, and graceful local fallback.
    """

    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self.last_error = None
        self.diagnostic_message = None
        self.fallback = LocalFallbackStore()
        self._init_connection()

    def _init_connection(self):
        """Establish reusable connection to MongoDB Atlas or local MongoDB."""
        if not MONGODB_URI:
            self.is_connected = False
            self.last_error = "MONGODB_URI not defined in backend/.env"
            self.diagnostic_message = "MongoDB URI is missing in backend/.env. Please configure MONGODB_URI."
            logger.warning(self.diagnostic_message)
            return

        try:
            from pymongo import MongoClient
            import certifi

            # Pass certifi CA bundle for secure TLS with MongoDB Atlas
            connect_kwargs = {
                "serverSelectionTimeoutMS": 2500,
                "connectTimeoutMS": 2500,
            }
            try:
                connect_kwargs["tlsCAFile"] = certifi.where()
            except Exception:
                pass

            client = MongoClient(MONGODB_URI, **connect_kwargs)
            # Test ping to confirm active connection
            client.admin.command('ping')

            self.client = client
            self.db = client[DATABASE_NAME]
            self.is_connected = True
            self.last_error = None
            self.diagnostic_message = f"Connected to MongoDB Atlas successfully (Database: {DATABASE_NAME})."
            logger.info(f"Connected to MongoDB successfully: {mask_mongodb_uri(MONGODB_URI)} [DB: {DATABASE_NAME}]")

            # Create helpful collection indexes
            try:
                self.db.conversations.create_index("session_id", unique=True)
                self.db.conversations.create_index("updated_at")
                self.db.conversations.create_index("user_id")
                self.db.messages.create_index([("session_id", 1), ("timestamp", 1)])
                self.db.messages.create_index("user_id")
                self.db.users.create_index("email", unique=True)
            except Exception as ie:
                logger.debug(f"Index creation note: {ie}")

        except Exception as e:
            self.is_connected = False
            err_str = str(e)
            self.last_error = err_str

            # Construct clear, user-friendly diagnostic guidance
            if "TLSV1_ALERT_INTERNAL_ERROR" in err_str or "SSL handshake failed" in err_str:
                self.diagnostic_message = (
                    "MongoDB Atlas connection rejected (SSL TLS Alert). "
                    "Action Required: Your current IP address is not whitelisted in MongoDB Atlas. "
                    "In MongoDB Atlas, go to 'Network Access' -> 'Add IP Address' -> add '0.0.0.0/0' (allow from anywhere) or your current IP."
                )
            elif "Authentication failed" in err_str or "auth failed" in err_str:
                self.diagnostic_message = (
                    "MongoDB Atlas authentication failed. "
                    "Action Required: Verify the database username and password in backend/.env."
                )
            elif "timed out" in err_str.lower() or "timeout" in err_str.lower():
                self.diagnostic_message = (
                    "MongoDB Atlas connection timed out. "
                    "Action Required: Ensure network connectivity and check that the cluster is running and your IP is whitelisted in Atlas Network Access."
                )
            else:
                self.diagnostic_message = f"MongoDB connection error: {err_str[:160]}"

            masked = mask_mongodb_uri(MONGODB_URI)
            logger.warning(f"MongoDB Atlas connection unavailable for {masked}: {self.diagnostic_message}. Using resilient fallback store.")

    def get_database(self):
        """Return active MongoDB database instance if connected, else None."""
        if self.is_connected:
            return self.db
        return None

    def check_health(self) -> Dict[str, Any]:
        """
        Database health check endpoint logic.
        Never exposes the real password; returns connection state, masked URI, and clear guidance.
        """
        # Attempt reconnection if previously disconnected
        if not self.is_connected and MONGODB_URI:
            self._init_connection()

        health_data = {
            "status": "connected" if self.is_connected else "disconnected",
            "database": DATABASE_NAME,
            "uri": mask_mongodb_uri(MONGODB_URI),
            "fallback_active": not self.is_connected,
        }

        if self.is_connected and self.db is not None:
            try:
                # Active ping verification
                self.client.admin.command('ping')
                conv_count = self.db.conversations.count_documents({})
                msg_count = self.db.messages.count_documents({})
                health_data["message"] = f"Connected to MongoDB Atlas database '{DATABASE_NAME}'"
                health_data["collections"] = {
                    "conversations": conv_count,
                    "messages": msg_count
                }
            except Exception as e:
                self.is_connected = False
                health_data["status"] = "disconnected"
                health_data["error"] = str(e)[:160]
                health_data["message"] = "Connection lost during ping."
        else:
            health_data["error"] = self.diagnostic_message or "MongoDB is not connected."
            health_data["message"] = (
                self.diagnostic_message
                or "Using resilient local JSON store. No data is lost."
            )

        return health_data

    # -------------------------------------------------------------
    # User Authentication & Management Methods
    # -------------------------------------------------------------

    def create_user(self, email: str, password_hash: str, full_name: str) -> Dict[str, Any]:
        """Create a new user in MongoDB Atlas (with fallback)."""
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        user_doc = {
            "user_id": user_id,
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "full_name": full_name.strip(),
            "created_at": now
        }
        if self.is_connected and self.db is not None:
            try:
                self.db.users.insert_one(user_doc.copy())
            except Exception as e:
                logger.error(f"Error inserting user to MongoDB: {e}")
        return self.fallback.create_user(email, password_hash, full_name)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email address."""
        norm = email.lower().strip()
        if self.is_connected and self.db is not None:
            try:
                u = self.db.users.find_one({"email": norm}, {"_id": 0})
                if u:
                    return u
            except Exception as e:
                logger.error(f"Error finding user by email: {e}")
        return self.fallback.get_user_by_email(email)

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a user by unique user_id."""
        if self.is_connected and self.db is not None:
            try:
                u = self.db.users.find_one({"user_id": user_id}, {"_id": 0})
                if u:
                    return u
            except Exception as e:
                logger.error(f"Error finding user by id: {e}")
        return self.fallback.get_user_by_id(user_id)

    # -------------------------------------------------------------
    # Session & Message Persistence Methods (with User Privacy)
    # -------------------------------------------------------------

    def get_conversation(self, session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve full conversation transcript and messages for session, strictly verifying user ownership."""
        if self.is_connected and self.db is not None:
            try:
                query = {"session_id": session_id}
                if user_id:
                    query["user_id"] = user_id
                conv = self.db.conversations.find_one(query, {"_id": 0})
                if conv:
                    messages = list(self.db.messages.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1))
                    conv["messages"] = messages
                    return conv
            except Exception as e:
                logger.error(f"Error fetching conversation from MongoDB: {e}")
        return self.fallback.get_conversation(session_id, user_id=user_id)

    def list_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List conversation sessions filtered by user_id for strict privacy."""
        if self.is_connected and self.db is not None:
            try:
                query = {"user_id": user_id} if user_id else {}
                convs = list(self.db.conversations.find(query, {"_id": 0}).sort("updated_at", -1))
                return convs
            except Exception as e:
                logger.error(f"Error listing conversations from MongoDB: {e}")
        return self.fallback.list_conversations(user_id=user_id)

    def save_conversation(
        self,
        session_id: str,
        title: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        selected_model: Optional[str] = None,
        image_references: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store chat session, user queries, AI responses, selected models,
        timestamps, uploaded image references, and owner user_id.
        """
        now = datetime.now(timezone.utc).isoformat()
        conv_doc = {
            "session_id": session_id,
            "title": title or "New Satellite Analysis",
            "updated_at": now,
            "selected_model": selected_model or "RS-MultiModal-Pipeline",
            "image_references": image_references or []
        }
        if user_id:
            conv_doc["user_id"] = user_id

        if self.is_connected and self.db is not None:
            try:
                self.db.conversations.update_one(
                    {"session_id": session_id},
                    {
                        "$set": conv_doc,
                        "$setOnInsert": {"created_at": now}
                    },
                    upsert=True
                )
                if messages is not None and len(messages) > 0:
                    for msg in messages:
                        msg_clean = msg.copy()
                        msg_clean["session_id"] = session_id
                        if user_id and "user_id" not in msg_clean:
                            msg_clean["user_id"] = user_id
                        self.db.messages.update_one(
                            {
                                "session_id": session_id,
                                "role": msg_clean.get("role", "user"),
                                "timestamp": msg_clean.get("timestamp")
                            },
                            {"$set": msg_clean},
                            upsert=True
                        )
            except Exception as e:
                logger.error(f"Error saving session to MongoDB: {e}")

        return self.fallback.save_conversation(
            session_id=session_id,
            title=title,
            messages=messages,
            selected_model=selected_model,
            image_references=image_references,
            user_id=user_id
        )

    def add_message(self, session_id: str, message: Dict[str, Any], user_id: Optional[str] = None) -> None:
        """Append an individual user or assistant message to session with user privacy."""
        msg_clean = message.copy()
        msg_clean["session_id"] = session_id
        if user_id and "user_id" not in msg_clean:
            msg_clean["user_id"] = user_id
        if "timestamp" not in msg_clean:
            msg_clean["timestamp"] = datetime.now(timezone.utc).isoformat()

        if self.is_connected and self.db is not None:
            try:
                self.db.messages.insert_one(msg_clean)
                update_set = {
                    "updated_at": msg_clean["timestamp"],
                    "selected_model": msg_clean.get("selected_model") or msg_clean.get("model_used", "RS-MultiModal-Pipeline")
                }
                if user_id:
                    update_set["user_id"] = user_id
                self.db.conversations.update_one(
                    {"session_id": session_id},
                    {
                        "$set": update_set,
                        "$addToSet": {
                            "image_references": {"$each": msg_clean.get("image_references", [])}
                        }
                    },
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error saving message to MongoDB: {e}")

        self.fallback.add_message(session_id, message, user_id=user_id)

    def delete_conversation(self, session_id: str) -> bool:
        """Remove conversation and all associated messages."""
        if self.is_connected and self.db is not None:
            try:
                self.db.conversations.delete_one({"session_id": session_id})
                self.db.messages.delete_many({"session_id": session_id})
            except Exception as e:
                logger.error(f"Error deleting conversation from MongoDB: {e}")
        return self.fallback.delete_conversation(session_id)


# Global reusable MongoDB connection manager
db_manager = MongoDBConnectionManager()
