import time
from dataclasses import dataclass, field

from rich.console import Console

from gemi.config import load_config
from gemi.keys.store import get_decrypted_keys
from gemi.registry import ALL_PROVIDER_NAMES, PROVIDERS, get_provider_info

console = Console()


@dataclass
class KeyState:
    provider: str
    name: str
    api_key: str
    requests_used: int = 0
    tokens_used: int = 0
    last_used: float = 0
    cooldown_until: float = 0
    is_exhausted: bool = False


@dataclass
class KeyManager:
    config: dict = field(default_factory=dict)
    _keys: dict[str, list[KeyState]] = field(default_factory=dict)
    _current_index: dict[str, int] = field(default_factory=dict)
    _current_provider: str = ""
    _model_index: dict[str, int] = field(default_factory=dict)
    _failed_models: dict[str, set] = field(default_factory=dict)

    def __post_init__(self):
        if not self.config:
            self.config = load_config()
        self._current_provider = self.config.get("default_provider", "gemini")
        self._load_all_keys()

    def _load_all_keys(self):
        priority = self.config.get("rotation", {}).get(
            "provider_priority", ALL_PROVIDER_NAMES
        )
        all_providers = set(priority) | set(ALL_PROVIDER_NAMES)

        for provider in priority:
            self._load_provider_keys(provider)

        for provider in all_providers - set(priority):
            self._load_provider_keys(provider)

    def _load_provider_keys(self, provider: str):
        info = get_provider_info(provider)

        if provider == "ollama":
            self._keys[provider] = [
                KeyState(provider="ollama", name="local", api_key="")
            ]
            self._current_index[provider] = 0
            return

        keys = get_decrypted_keys(provider)
        if keys:
            self._keys[provider] = [
                KeyState(
                    provider=k["provider"],
                    name=k["name"],
                    api_key=k["api_key"],
                )
                for k in keys
            ]
            self._current_index[provider] = 0

    def get_current_key(self) -> KeyState | None:
        keys = self._keys.get(self._current_provider, [])
        if not keys:
            return self._try_failover()
        idx = self._current_index.get(self._current_provider, 0)
        key = keys[idx]
        if key.cooldown_until > time.time():
            return self._rotate_key()
        return key

    def get_current_provider(self) -> str:
        return self._current_provider

    def get_current_model(self) -> str | None:
        info = PROVIDERS.get(self._current_provider)
        if not info or not info["models"]:
            return None
        idx = self._model_index.get(self._current_provider, 0)
        return info["models"][idx]

    def get_models_for_provider(self, provider: str) -> list[str]:
        info = PROVIDERS.get(provider)
        if not info:
            return []
        return info["models"]

    def try_next_model(self) -> str | None:
        provider = self._current_provider
        info = PROVIDERS.get(provider)
        if not info or not info["models"]:
            return None

        models = info["models"]
        current_idx = self._model_index.get(provider, 0)
        failed = self._failed_models.get(provider, set())
        failed.add(models[current_idx])
        self._failed_models[provider] = failed

        for i in range(1, len(models)):
            next_idx = (current_idx + i) % len(models)
            candidate = models[next_idx]
            if candidate not in failed:
                self._model_index[provider] = next_idx
                console.print(f"  [cyan]Trying model {candidate} on {provider}...[/cyan]")
                return candidate

        return None

    def reset_failed_models(self):
        self._failed_models.clear()
        self._model_index.clear()

    def record_usage(self, tokens: int = 0):
        key = self._get_current_key_state()
        if key:
            key.requests_used += 1
            key.tokens_used += tokens
            key.last_used = time.time()

    def report_rate_limit(self, retry_after: float | None = None) -> KeyState | None:
        key = self._get_current_key_state()
        if key:
            cooldown = retry_after or 60
            key.cooldown_until = time.time() + cooldown
            mins, secs = divmod(int(cooldown), 60)
            if mins > 0:
                wait_str = f"{mins}m {secs}s"
            else:
                wait_str = f"{secs}s"
            console.print(
                f"  [yellow]Rate limited on {key.provider}/{key.name} — retry in {wait_str}, rotating...[/yellow]"
            )
        return self._rotate_key()

    def report_exhausted(self) -> KeyState | None:
        key = self._get_current_key_state()
        if key:
            key.is_exhausted = True
            console.print(
                f"  [yellow]{key.provider}/{key.name} exhausted[/yellow]"
            )
        return self._rotate_key()

    def _rotate_key(self) -> KeyState | None:
        keys = self._keys.get(self._current_provider, [])
        if not keys:
            return self._try_failover()

        start_idx = self._current_index.get(self._current_provider, 0)
        now = time.time()

        for i in range(1, len(keys) + 1):
            idx = (start_idx + i) % len(keys)
            candidate = keys[idx]
            if not candidate.is_exhausted and candidate.cooldown_until <= now:
                self._current_index[self._current_provider] = idx
                console.print(
                    f"  [green]Switched to {candidate.provider}/{candidate.name}[/green]"
                )
                return candidate

        return self._try_failover()

    def _try_failover(self) -> KeyState | None:
        if not self.config.get("rotation", {}).get("auto_switch_provider", True):
            return None

        priority = self.config.get("rotation", {}).get(
            "provider_priority", ALL_PROVIDER_NAMES
        )
        now = time.time()

        for provider in priority:
            if provider == self._current_provider:
                continue
            keys = self._keys.get(provider, [])
            for i, key in enumerate(keys):
                if not key.is_exhausted and key.cooldown_until <= now:
                    self._current_provider = provider
                    self._current_index[provider] = i
                    info = get_provider_info(provider)
                    display = info["name"] if info else provider
                    console.print(
                        f"  [bold green]Failover → {display} ({key.name})[/bold green]"
                    )
                    return key

        return None

    def get_nearest_cooldown(self) -> float | None:
        now = time.time()
        nearest = None
        for keys in self._keys.values():
            for key in keys:
                if key.is_exhausted:
                    continue
                if key.cooldown_until > now:
                    wait = key.cooldown_until - now
                    if nearest is None or wait < nearest:
                        nearest = wait
        return nearest

    def get_any_available_key(self) -> KeyState | None:
        now = time.time()
        priority = self.config.get("rotation", {}).get(
            "provider_priority", ALL_PROVIDER_NAMES
        )
        for provider in priority:
            keys = self._keys.get(provider, [])
            for i, key in enumerate(keys):
                if not key.is_exhausted and key.cooldown_until <= now:
                    self._current_provider = provider
                    self._current_index[provider] = i
                    return key
        return None

    def _get_current_key_state(self) -> KeyState | None:
        keys = self._keys.get(self._current_provider, [])
        if not keys:
            return None
        idx = self._current_index.get(self._current_provider, 0)
        return keys[idx]

    def get_status(self) -> list[dict]:
        status = []
        now = time.time()
        for provider, keys in self._keys.items():
            for i, key in enumerate(keys):
                is_current = (
                    provider == self._current_provider
                    and i == self._current_index.get(provider, 0)
                )
                state = "active" if is_current else "standby"
                cooldown_remaining = 0
                if key.is_exhausted:
                    state = "exhausted"
                elif key.cooldown_until > now:
                    cooldown_remaining = int(key.cooldown_until - now)
                    mins, secs = divmod(cooldown_remaining, 60)
                    if mins > 0:
                        state = f"cooldown ({mins}m {secs}s)"
                    else:
                        state = f"cooldown ({secs}s)"
                status.append({
                    "provider": provider,
                    "name": key.name,
                    "state": state,
                    "requests": key.requests_used,
                    "tokens": key.tokens_used,
                    "cooldown_remaining": cooldown_remaining,
                })
        return status
