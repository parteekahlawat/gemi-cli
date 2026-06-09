import json
import time
from pathlib import Path

from gemi.config import GEMI_DIR
from gemi.providers.base import Message

SESSIONS_DIR = GEMI_DIR / "sessions"


def _ensure_dir():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def save_session(session_id: str, messages: list[Message], metadata: dict | None = None):
    _ensure_dir()
    data = {
        "session_id": session_id,
        "saved_at": time.time(),
        "metadata": metadata or {},
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "tool_call_id": m.tool_call_id,
                "name": m.name,
            }
            for m in messages
        ],
    }
    path = SESSIONS_DIR / f"{session_id}.json"
    path.write_text(json.dumps(data, indent=2))


def load_session(session_id: str) -> list[Message] | None:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [
        Message(
            role=m["role"],
            content=m.get("content", ""),
            tool_calls=m.get("tool_calls"),
            tool_call_id=m.get("tool_call_id"),
            name=m.get("name"),
        )
        for m in data["messages"]
    ]


def list_sessions() -> list[dict]:
    _ensure_dir()
    sessions = []
    for path in sorted(SESSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text())
            msg_count = len(data.get("messages", []))
            user_msgs = [m for m in data.get("messages", []) if m["role"] == "user"]
            preview = user_msgs[0]["content"][:80] if user_msgs else "(empty)"
            sessions.append({
                "id": data["session_id"],
                "saved_at": data.get("saved_at", 0),
                "messages": msg_count,
                "preview": preview,
                "cwd": data.get("metadata", {}).get("cwd", ""),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return sessions


def delete_session(session_id: str) -> bool:
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def generate_session_id() -> str:
    import hashlib
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
