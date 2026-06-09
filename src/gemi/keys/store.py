import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet

from gemi.config import GEMI_DIR, ensure_gemi_dir

KEYS_PATH = GEMI_DIR / "keys.json"
SECRET_PATH = GEMI_DIR / ".secret"


def _get_or_create_secret() -> bytes:
    ensure_gemi_dir()
    if SECRET_PATH.exists():
        return SECRET_PATH.read_bytes()
    key = Fernet.generate_key()
    SECRET_PATH.write_bytes(key)
    SECRET_PATH.chmod(0o600)
    return key


def _cipher() -> Fernet:
    return Fernet(_get_or_create_secret())


def _load_raw() -> list[dict]:
    if not KEYS_PATH.exists():
        return []
    data = json.loads(KEYS_PATH.read_text())
    return data if isinstance(data, list) else []


def _save_raw(keys: list[dict]):
    ensure_gemi_dir()
    KEYS_PATH.write_text(json.dumps(keys, indent=2))
    KEYS_PATH.chmod(0o600)


def add_key(provider: str, name: str, api_key: str):
    keys = _load_raw()
    for k in keys:
        if k["provider"] == provider and k["name"] == name:
            k["api_key"] = _cipher().encrypt(api_key.encode()).decode()
            _save_raw(keys)
            return
    keys.append({
        "provider": provider,
        "name": name,
        "api_key": _cipher().encrypt(api_key.encode()).decode(),
        "added_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_raw(keys)


def remove_key(provider: str, name: str) -> bool:
    keys = _load_raw()
    filtered = [k for k in keys if not (k["provider"] == provider and k["name"] == name)]
    if len(filtered) == len(keys):
        return False
    _save_raw(filtered)
    return True


def list_keys(provider: str | None = None) -> list[dict]:
    keys = _load_raw()
    if provider:
        keys = [k for k in keys if k["provider"] == provider]
    result = []
    for k in keys:
        result.append({
            "provider": k["provider"],
            "name": k["name"],
            "added_at": k["added_at"],
        })
    return result


def get_decrypted_keys(provider: str) -> list[dict]:
    keys = _load_raw()
    result = []
    f = _cipher()
    for k in keys:
        if k["provider"] == provider:
            result.append({
                "provider": k["provider"],
                "name": k["name"],
                "api_key": f.decrypt(k["api_key"].encode()).decode(),
            })
    return result
