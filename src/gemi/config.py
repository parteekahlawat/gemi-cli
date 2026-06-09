from pathlib import Path

import yaml

GEMI_DIR = Path.home() / ".gemi"
CONFIG_PATH = GEMI_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "default_provider": "gemini",
    "default_model": "gemini-2.5-flash",
    "rotation": {
        "strategy": "failover",
        "auto_switch_provider": True,
        "provider_priority": [
            "gemini", "groq", "deepseek", "openrouter",
            "cerebras", "mistral", "together", "openai", "ollama",
        ],
    },
    "agent": {
        "max_iterations": 50,
        "auto_approve_reads": True,
        "auto_approve_writes": False,
    },
}


def ensure_gemi_dir():
    GEMI_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_gemi_dir()
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            user_config = yaml.safe_load(f) or {}
        return _deep_merge(DEFAULT_CONFIG, user_config)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    ensure_gemi_dir()
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
