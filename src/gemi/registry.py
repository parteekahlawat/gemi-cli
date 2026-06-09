PROVIDERS = {
    "gemini": {
        "name": "Google Gemini",
        "type": "gemini",
        "base_url": None,
        "default_model": "gemini-2.5-flash",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
        ],
        "free_tier": True,
        "key_url": "https://aistudio.google.com/apikey",
        "key_prefix": "AIza",
        "needs_key": True,
        "context_window": 1_000_000,
    },
    "groq": {
        "name": "Groq",
        "type": "openai_compat",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3-32b",
            "allam-2-7b",
        ],
        "free_tier": True,
        "key_url": "https://console.groq.com/keys",
        "key_prefix": "gsk_",
        "needs_key": True,
        "context_window": 128_000,
    },
    "deepseek": {
        "name": "DeepSeek",
        "type": "openai_compat",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "free_tier": False,
        "key_url": "https://platform.deepseek.com/api_keys",
        "key_prefix": "sk-",
        "needs_key": True,
        "context_window": 128_000,
    },
    "openrouter": {
        "name": "OpenRouter",
        "type": "openai_compat",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "qwen/qwen3-coder:free",
        "models": [
            "qwen/qwen3-coder:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "openai/gpt-oss-120b:free",
            "google/gemma-4-31b-it:free",
            "qwen/qwen3-next-80b-a3b-instruct:free",
            "moonshotai/kimi-k2.6:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "poolside/laguna-m.1:free",
            "z-ai/glm-4.5-air:free",
        ],
        "free_tier": True,
        "key_url": "https://openrouter.ai/keys",
        "key_prefix": "sk-or-",
        "needs_key": True,
        "context_window": 1_000_000,
    },
    "mistral": {
        "name": "Mistral AI",
        "type": "openai_compat",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "codestral-latest",
        "models": [
            "codestral-latest",
            "mistral-large-latest",
            "mistral-small-latest",
            "pixtral-large-latest",
        ],
        "free_tier": True,
        "key_url": "https://console.mistral.ai/api-keys",
        "key_prefix": "",
        "needs_key": True,
        "context_window": 128_000,
    },
    "openai": {
        "name": "OpenAI",
        "type": "openai_compat",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
        ],
        "free_tier": False,
        "key_url": "https://platform.openai.com/api-keys",
        "key_prefix": "sk-",
        "needs_key": True,
        "context_window": 128_000,
    },
    "together": {
        "name": "Together AI",
        "type": "openai_compat",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
        ],
        "free_tier": False,
        "key_url": "https://api.together.ai/settings/api-keys",
        "key_prefix": "",
        "needs_key": True,
        "context_window": 128_000,
    },
    "cerebras": {
        "name": "Cerebras",
        "type": "openai_compat",
        "base_url": "https://api.cerebras.ai/v1",
        "default_model": "llama-3.3-70b",
        "models": [
            "llama-3.3-70b",
            "llama-4-scout-17b-16e-instruct",
        ],
        "free_tier": True,
        "key_url": "https://cloud.cerebras.ai/",
        "key_prefix": "csk-",
        "needs_key": True,
        "context_window": 128_000,
    },
    "ollama": {
        "name": "Ollama (Local)",
        "type": "ollama",
        "base_url": "http://localhost:11434",
        "default_model": "qwen3",
        "models": [
            "qwen3",
            "gemma4",
            "mistral-small",
            "llama3.3",
            "deepseek-v3.2",
            "llama4-scout",
        ],
        "free_tier": True,
        "key_url": None,
        "key_prefix": "",
        "needs_key": False,
        "context_window": 32_768,
    },
}

ALL_PROVIDER_NAMES = list(PROVIDERS.keys())


def get_provider_info(name: str) -> dict | None:
    return PROVIDERS.get(name)


def get_provider_type(name: str) -> str:
    info = PROVIDERS.get(name)
    if not info:
        return "openai_compat"
    return info["type"]


def get_base_url(name: str) -> str | None:
    info = PROVIDERS.get(name)
    if not info:
        return None
    return info["base_url"]


def get_default_model(name: str) -> str:
    info = PROVIDERS.get(name)
    if not info:
        return "gpt-4o-mini"
    return info["default_model"]


def get_context_window(name: str, model: str | None = None) -> int:
    if name == "gemini":
        return 1_000_000
    info = PROVIDERS.get(name)
    if info:
        return info["context_window"]
    return 128_000


def list_free_providers() -> list[str]:
    return [name for name, info in PROVIDERS.items() if info["free_tier"]]
