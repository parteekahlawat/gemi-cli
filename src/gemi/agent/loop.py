import json
import os
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from gemi.agent.tools import TOOL_DEFINITIONS, execute_tool
from gemi.compaction import compact_messages, estimate_tokens, needs_compaction
from gemi.config import load_config
from gemi.keys.manager import KeyManager
from gemi.providers.base import Chunk, Message
from gemi.providers.gemini import GeminiProvider
from gemi.providers.ollama import OllamaProvider
from gemi.providers.openai_compat import OpenAICompatProvider
from gemi.registry import PROVIDERS, get_base_url, get_context_window, get_default_model, get_provider_info, get_provider_type
from gemi.sessions import save_session
from gemi.ui import print_plan, print_plan_approval, print_tool_call, print_tool_result

console = Console()

CHARS_PER_TOKEN = 4

SYSTEM_PROMPT = """You are gemi, an expert AI coding agent running in the user's terminal. You are a world-class software engineer. You can read, write, and edit files, run commands, search code, and manage git — all through your tools.

CRITICAL RULES — FOLLOW THESE EXACTLY:
1. NEVER ASK QUESTIONS. When the user asks you to do something, DO IT IMMEDIATELY. Do not ask "what command?", "what framework?", "which directory?", "what language?" — use your tools to find out. The ONLY exception: truly destructive operations (deleting production data, force pushing).
2. You have FULL ACCESS to the file system. NEVER say "I can't access files" or "please provide the path". You CAN read and write any file. All paths are relative to the current working directory.
3. ALWAYS use tools FIRST. When asked about code, files, or the project — read them with tools before responding. Never guess file contents.
4. When asked to "build", "complete", "fix", or "run" something — take action immediately. List directories, read package.json/Makefile/setup.py, figure out the right command, and run it. Show results.
5. When a project is in a subdirectory, run commands from that subdirectory. Use `cd subdirectory && command` or `--prefix subdirectory` for npm commands. NEVER run npm/pip/make in the wrong directory.
6. If a command fails, READ the error, understand it, and fix it yourself. Do not ask the user to fix it.

About gemi:
- gemi is a free open-source AI coding CLI with multi-provider support
- Providers: {providers_summary}
- Currently using: {current_provider}/{current_model}
- Features: multi-account key rotation, auto provider failover, encrypted key storage, session persistence
- Manage keys: `gemi key add <provider>` | View providers: `gemi providers` | Switch model: `/model <name>`
{active_keys_info}

Environment:
- Working directory: {cwd}
- Project structure:
{project_structure}
{project_context}

Tools available:
- list_directory(path) — list files. "." for current dir, "subfolder" for subfolder
- read_file(path) — read file contents with line numbers
- write_file(path, content) — create or overwrite a file
- edit_file(path, old_text, new_text) — find-and-replace in a file (exact match)
- run_command(command) — run shell command. Fast commands return immediately, long-running ones return after 30s with partial output while continuing in background
- search_files(pattern, path) — grep for text in files
- find_files(pattern) — find files by glob ("**/*.py", "*.json")
- git_status(), git_diff(), git_log(), git_commit(message, files), git_branch(action)
- create_plan(title, steps) — create a step-by-step plan for the user to review before execution

Planning vs Direct Execution:
- For COMPLEX tasks (building new features, creating projects, multi-file refactors, setting up infrastructure): FIRST call create_plan() with clear steps, then wait for user approval before executing.
- For SIMPLE tasks (fix a bug, read a file, run a command, small edits, answer a question): execute directly without a plan.
- A task is complex if it involves 3+ files or 3+ distinct actions.

Workflow:
1. User gives a task → read the codebase with tools to understand it
2. If complex → call create_plan() with steps, then execute each step after approval
3. If simple → execute directly
4. Verify: run tests, start dev server, check output
5. Report what you did in 1-2 sentences

Guidelines:
- Read files before editing them
- Make minimal, targeted changes
- Keep responses short — 1-2 sentences, not paragraphs
- When a project is in a subdirectory, always cd into it or use the right prefix
- When users ask about gemi itself (providers, features, keys), answer from your knowledge above
"""


def _get_project_structure() -> str:
    cwd = Path.cwd()
    lines = []
    for entry in sorted(cwd.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if entry.name.startswith(".") and entry.name not in (".env", ".gitignore"):
            continue
        prefix = "📁" if entry.is_dir() else "  "
        lines.append(f"{prefix} {entry.name}")
    return "\n".join(lines[:30]) or "(empty directory)"


def _get_project_context() -> str:
    gemi_md = Path.cwd() / ".gemi.md"
    if gemi_md.exists():
        content = gemi_md.read_text(errors="replace")
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"
        return f"\nProject context (.gemi.md):\n{content}\n"
    return ""


def _create_provider(provider_name: str, api_key: str, config: dict):
    provider_type = get_provider_type(provider_name)

    if provider_type == "gemini":
        return GeminiProvider(api_key=api_key)
    elif provider_type == "ollama":
        base_url = get_base_url(provider_name) or "http://localhost:11434"
        return OllamaProvider(base_url=base_url)
    elif provider_type == "openai_compat":
        base_url = get_base_url(provider_name) or "https://api.openai.com/v1"
        return OpenAICompatProvider(api_key=api_key, base_url=base_url)
    else:
        base_url = get_base_url(provider_name) or "https://api.openai.com/v1"
        return OpenAICompatProvider(api_key=api_key, base_url=base_url)


def _get_model(provider_name: str, config: dict) -> str:
    if provider_name == config.get("default_provider", "gemini"):
        return config.get("default_model", get_default_model(provider_name))
    return get_default_model(provider_name)


def _parse_retry_after(error: Exception) -> float | None:
    retry_after = None

    if hasattr(error, "response") and error.response is not None:
        headers = getattr(error.response, "headers", {})
        if "retry-after" in headers:
            try:
                retry_after = float(headers["retry-after"])
            except (ValueError, TypeError):
                pass
        if not retry_after and "x-ratelimit-reset" in headers:
            try:
                import time
                reset_ts = float(headers["x-ratelimit-reset"])
                retry_after = max(1, reset_ts - time.time())
            except (ValueError, TypeError):
                pass

    if not retry_after:
        import re
        match = re.search(r"retry.{0,5}?(\d+)\s*s", str(error).lower())
        if match:
            retry_after = float(match.group(1))
        else:
            match = re.search(r"try again in (\d+)", str(error).lower())
            if match:
                retry_after = float(match.group(1))

    return retry_after


class AgentLoop:
    def __init__(self, session_id: str | None = None):
        self.config = load_config()
        self.key_manager = KeyManager(config=self.config)
        self.messages: list[Message] = []
        self.provider = None
        self.model = None
        self.session_id = session_id or ""
        self.total_tokens_used = 0
        self.total_requests = 0
        self.provider_usage: dict[str, dict] = {}
        self.current_plan: dict | None = None
        self._init_provider()

    def _init_provider(self):
        key_state = self.key_manager.get_current_key()
        if not key_state:
            console.print("[bold red]No API keys configured. Run: gemi key add gemini[/bold red]")
            return
        provider_name = self.key_manager.get_current_provider()
        self.provider = _create_provider(provider_name, key_state.api_key, self.config)
        self.model = _get_model(provider_name, self.config)

        providers_summary = ", ".join(
            f"{name} ({info['name']})" for name, info in PROVIDERS.items()
        )

        key_status = self.key_manager.get_status()
        configured = [s for s in key_status if s["state"] != "no key"]
        if configured:
            lines = [f"- Configured providers with keys: {', '.join(dict.fromkeys(s['provider'] for s in configured))}"]
            active = [s for s in configured if s["state"] == "active"]
            if active:
                lines.append(f"- Active key: {active[0]['provider']}/{active[0]['name']}")
            active_keys_info = "\n".join(lines)
        else:
            active_keys_info = "- No API keys configured yet"

        system_prompt = SYSTEM_PROMPT.format(
            cwd=os.getcwd(),
            project_structure=_get_project_structure(),
            project_context=_get_project_context(),
            providers_summary=providers_summary,
            current_provider=provider_name,
            current_model=self.model,
            active_keys_info=active_keys_info,
        )
        self.messages = [Message(role="system", content=system_prompt)]

    def load_session(self, messages: list[Message]):
        self.messages = messages

    def _switch_provider(self):
        key_state = self.key_manager.get_current_key()
        if not key_state:
            return False
        provider_name = self.key_manager.get_current_provider()
        self.provider = _create_provider(provider_name, key_state.api_key, self.config)
        model_from_manager = self.key_manager.get_current_model()
        self.model = model_from_manager or _get_model(provider_name, self.config)
        self._fit_context_to_model()
        return True

    def _fit_context_to_model(self):
        provider_name = self.key_manager.get_current_provider()
        max_tokens = get_context_window(provider_name, self.model)
        max_chars = int(max_tokens * CHARS_PER_TOKEN * 0.8)

        total_chars = sum(len(m.content or "") for m in self.messages)
        if total_chars <= max_chars:
            return

        system_msg = self.messages[0] if self.messages and self.messages[0].role == "system" else None
        recent = self.messages[1:] if system_msg else self.messages[:]

        kept = []
        used_chars = len(system_msg.content) if system_msg else 0

        for msg in reversed(recent):
            msg_chars = len(msg.content or "")
            if used_chars + msg_chars > max_chars:
                break
            kept.insert(0, msg)
            used_chars += msg_chars

        dropped = len(recent) - len(kept)
        if dropped > 0:
            summary = Message(
                role="user",
                content=f"[{dropped} earlier messages were trimmed to fit the current model's context window. The conversation continues below.]",
            )
            self.messages = ([system_msg] if system_msg else []) + [summary] + kept
            console.print(
                f"  [dim]Trimmed {dropped} old messages to fit {self.model} context window[/dim]"
            )

    def _maybe_compact(self):
        provider_name = self.key_manager.get_current_provider()
        max_tokens = get_context_window(provider_name, self.model)
        if needs_compaction(self.messages, max_tokens):
            old_count = len(self.messages)
            self.messages = compact_messages(self.messages, max_tokens)
            new_count = len(self.messages)
            if new_count < old_count:
                console.print(
                    f"  [dim]Compacted context: {old_count} → {new_count} messages[/dim]"
                )

    def _auto_save(self):
        if self.session_id:
            save_session(
                self.session_id,
                self.messages,
                metadata={
                    "cwd": os.getcwd(),
                    "provider": self.key_manager.get_current_provider(),
                    "model": self.model,
                    "tokens_used": self.total_tokens_used,
                },
            )

    def get_status_line(self) -> str:
        provider = self.key_manager.get_current_provider()
        tokens = self.total_tokens_used
        reqs = self.total_requests
        ctx = estimate_tokens(self.messages)
        max_ctx = get_context_window(provider, self.model)
        ctx_pct = min(100, int(ctx / max_ctx * 100))
        return f"{provider}/{self.model} | tokens: ~{tokens:,} / {max_ctx:,} | reqs: {reqs} | context: {ctx_pct}%"

    def get_detailed_status(self) -> str:
        provider = self.key_manager.get_current_provider()
        max_ctx = get_context_window(provider, self.model)
        ctx = estimate_tokens(self.messages)
        ctx_pct = min(100, int(ctx / max_ctx * 100))
        keys = self.key_manager.get_status()
        provider_keys = [k for k in keys if k["provider"] == provider]
        total_keys = len(provider_keys)
        active_keys = len([k for k in provider_keys if k["state"] not in ("exhausted",)])

        lines = [
            f"  [bold]Current[/bold]",
            f"  Provider:  [green]{provider}[/green]",
            f"  Model:     [green]{self.model}[/green]",
            f"  Context:   [cyan]{ctx:,}[/cyan] / {max_ctx:,} ({ctx_pct}%)",
            f"  Keys:      [cyan]{active_keys}[/cyan] active / {total_keys} total",
            f"  Session:   [dim]{self.session_id}[/dim]",
            "",
            f"  [bold]Usage This Session[/bold]",
        ]

        if self.provider_usage:
            for prov, usage in self.provider_usage.items():
                prov_max = get_context_window(prov, usage["model"])
                marker = " [green]◀ active[/green]" if prov == provider else ""
                lines.append(f"  [cyan]{prov}[/cyan] ({usage['model']}){marker}")
                lines.append(f"    Tokens: ~{usage['tokens']:,} / {prov_max:,}  |  Requests: {usage['requests']}")
        else:
            lines.append(f"  [dim]No requests made yet[/dim]")

        lines.append("")
        lines.append(f"  [bold]Total:[/bold] ~{self.total_tokens_used:,} tokens | {self.total_requests} requests")

        return "\n".join(lines)

    def _update_plan_progress(self, tool_name: str):
        if not self.current_plan:
            return
        steps = self.current_plan["steps"]
        for step in steps:
            if step["status"] == "pending":
                step["status"] = "in_progress"
                break
        for i, step in enumerate(steps):
            if step["status"] == "in_progress" and i > 0:
                prev = steps[i - 1]
                if prev["status"] == "in_progress":
                    prev["status"] = "done"
        in_progress = [s for s in steps if s["status"] == "in_progress"]
        if not in_progress:
            pending = [s for s in steps if s["status"] == "pending"]
            if not pending:
                for s in steps:
                    if s["status"] != "done":
                        s["status"] = "done"
                self.current_plan = None
                return
        print_plan(self.current_plan["title"], steps)

    def get_plan(self) -> dict | None:
        return self.current_plan

    async def chat(self, user_input: str):
        if not self.provider:
            console.print("[bold red]No provider available. Add API keys first.[/bold red]")
            return

        self.messages.append(Message(role="user", content=user_input))
        self._maybe_compact()

        max_iterations = self.config.get("agent", {}).get("max_iterations", 50)
        auto_approve_reads = self.config.get("agent", {}).get("auto_approve_reads", True)
        auto_approve_writes = self.config.get("agent", {}).get("auto_approve_writes", False)

        for iteration in range(max_iterations):
            text_response, tool_calls, tokens_used = await self._call_provider()

            self.total_tokens_used += tokens_used
            self.total_requests += 1

            current = self.key_manager.get_current_provider()
            if current not in self.provider_usage:
                self.provider_usage[current] = {"tokens": 0, "requests": 0, "model": self.model}
            self.provider_usage[current]["tokens"] += tokens_used
            self.provider_usage[current]["requests"] += 1
            self.provider_usage[current]["model"] = self.model
            self.key_manager.record_usage(tokens_used)

            if not tool_calls:
                if not text_response.strip() and tokens_used == 0:
                    console.print("\n  [bold red]Could not get a response. All providers failed or returned empty.[/bold red]")
                    console.print("  [yellow]Try again, or check provider status with /status[/yellow]")
                    return
                self.messages.append(Message(role="assistant", content=text_response))
                break

            self.messages.append(Message(
                role="assistant",
                content=text_response,
                tool_calls=tool_calls,
            ))

            plan_created = False
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                func_args = tc["function"]["arguments"]
                if isinstance(func_args, str):
                    try:
                        func_args = json.loads(func_args)
                    except json.JSONDecodeError:
                        func_args = {}

                if func_name == "create_plan":
                    plan_title = func_args.get("title", "Plan")
                    plan_steps = func_args.get("steps", [])
                    for step in plan_steps:
                        step["status"] = "pending"
                    self.current_plan = {"title": plan_title, "steps": plan_steps}
                    print_plan(plan_title, plan_steps)
                    approved = print_plan_approval()
                    if approved:
                        result = "Plan approved by user. Execute each step now. After completing each step, briefly state what you did."
                    else:
                        result = "Plan rejected by user. Ask what they'd like to change."
                        self.current_plan = None
                    self.messages.append(Message(
                        role="tool",
                        content=result,
                        tool_call_id=tc["id"],
                        name=func_name,
                    ))
                    plan_created = True
                    continue

                WRITE_TOOLS = {"write_file", "edit_file", "run_command", "git_commit"}

                print_tool_call(func_name, func_args)

                result = execute_tool(
                    func_name,
                    func_args,
                    auto_approve_reads=auto_approve_reads,
                    auto_approve_writes=auto_approve_writes,
                )

                if func_name in WRITE_TOOLS:
                    print_tool_result(func_name, result)

                if self.current_plan:
                    self._update_plan_progress(func_name)

                self.messages.append(Message(
                    role="tool",
                    content=result,
                    tool_call_id=tc["id"],
                    name=func_name,
                ))


        self._auto_save()
        provider = self.key_manager.get_current_provider()
        max_ctx = get_context_window(provider, self.model)
        ctx = estimate_tokens(self.messages)
        ctx_pct = min(100, int(ctx / max_ctx * 100))
        bar_width = 20
        filled = int(bar_width * ctx_pct / 100)
        bar = "[green]" + "━" * filled + "[/green][dim]" + "━" * (bar_width - filled) + "[/dim]"
        console.print(f"\n  [dim]{provider}/{self.model}[/dim]  ~{self.total_tokens_used:,} tokens  {bar} {ctx_pct}%")

    async def _call_provider(self, max_cycles: int = 5) -> tuple[str, list[dict] | None, int]:
        import asyncio

        max_attempts = 50
        attempt = 0

        for cycle in range(max_cycles):
            while attempt < max_attempts:
                attempt += 1
                live = None
                try:
                    text_parts = []
                    all_tool_calls = []

                    provider_label = f"[dim]{self.key_manager.get_current_provider()}/{self.model}[/dim]"

                    def _render(content_text):
                        md = Markdown(content_text) if content_text else Markdown("")
                        return Panel(md, border_style="blue", padding=(0, 1), subtitle=provider_label, subtitle_align="right")

                    async for chunk in self.provider.chat(
                        messages=self.messages,
                        tools=TOOL_DEFINITIONS,
                        model=self.model,
                        stream=True,
                    ):
                        if chunk.text:
                            text_parts.append(chunk.text)
                            if not live:
                                live = Live(_render("".join(text_parts)), console=console, refresh_per_second=12, vertical_overflow="visible")
                                live.start()
                            else:
                                live.update(_render("".join(text_parts)))
                        if chunk.tool_calls:
                            all_tool_calls.extend(chunk.tool_calls)

                    if live:
                        live.stop()
                    text = "".join(text_parts)

                    error_phrases = ["provider returned error", "model is overloaded", "no endpoints found", "service unavailable"]
                    text_lower = text.strip().lower()
                    is_error_response = any(phrase in text_lower for phrase in error_phrases)

                    if is_error_response or (not text.strip() and not all_tool_calls):
                        provider = self.key_manager.get_current_provider()
                        reason = f"error response: {text.strip()[:80]}" if is_error_response else "empty response"
                        console.print(f"\n  [red]Error on {provider}/{self.model}: {reason}[/red]")
                        next_model = self.key_manager.try_next_model()
                        if next_model:
                            self.model = next_model
                            continue
                        self.key_manager.report_rate_limit(retry_after=30)
                        if self._switch_provider():
                            continue
                        break

                    tokens = len(text) // CHARS_PER_TOKEN
                    return text, all_tool_calls if all_tool_calls else None, tokens

                except Exception as e:
                    if live and live.is_started:
                        live.stop()
                    error_str = str(e).lower()
                    provider = self.key_manager.get_current_provider()
                    retry_after = _parse_retry_after(e)

                    if "401" in error_str or "403" in error_str or "unauthorized" in error_str or "user not found" in error_str or ("invalid" in error_str and "key" in error_str):
                        console.print(f"\n  [red]Auth error on {provider}: invalid API key[/red]")
                        console.print(f"  [yellow]Check with: gemi key list {provider}[/yellow]")
                        self.key_manager.report_exhausted()
                        if self._switch_provider():
                            continue
                        break

                    elif "429" in error_str or "rate" in error_str or "quota" in error_str or "resource" in error_str:
                        next_model = self.key_manager.try_next_model()
                        if next_model:
                            self.model = next_model
                            continue
                        self.key_manager.report_rate_limit(retry_after=retry_after)
                        if self._switch_provider():
                            continue
                        break

                    elif "connect" in error_str or "connection" in error_str or "timeout" in error_str or "unreachable" in error_str:
                        console.print(f"\n  [red]Can't reach {provider}[/red]")
                        self.key_manager.report_exhausted()
                        if self._switch_provider():
                            continue
                        break

                    elif "provider returned error" in error_str or "no endpoints" in error_str or "overloaded" in error_str or "service unavailable" in error_str:
                        console.print(f"\n  [red]Error on {provider}/{self.model}:[/red] [dim]{str(e)[:100]}[/dim]")
                        next_model = self.key_manager.try_next_model()
                        if next_model:
                            self.model = next_model
                            continue
                        self.key_manager.report_rate_limit(retry_after=retry_after)
                        if self._switch_provider():
                            continue
                        break

                    else:
                        console.print(f"\n  [red]Error on {provider}/{self.model}: {e}[/red]")
                        next_model = self.key_manager.try_next_model()
                        if next_model:
                            self.model = next_model
                            continue
                        self.key_manager.report_rate_limit(retry_after=retry_after)
                        if self._switch_provider():
                            continue
                        break

            # Inner loop exhausted all models/providers — wait for cooldown before next cycle
            available = self.key_manager.get_any_available_key()
            if available:
                self._switch_provider()
                continue

            wait_time = self.key_manager.get_nearest_cooldown()
            if wait_time and cycle < max_cycles - 1:
                wait_secs = min(wait_time + 2, 120)
                mins, secs = divmod(int(wait_secs), 60)
                wait_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                console.print(f"\n  [yellow]All providers on cooldown. Waiting {wait_str} before retry (cycle {cycle + 1}/{max_cycles})...[/yellow]")
                await asyncio.sleep(wait_secs)
                self.key_manager.reset_failed_models()
                available = self.key_manager.get_any_available_key()
                if available:
                    info = get_provider_info(available.provider)
                    display = info["name"] if info else available.provider
                    console.print(f"  [green]Retrying with {display} ({available.name})...[/green]")
                    self._switch_provider()
                    continue

            console.print(f"\n  [bold red]All providers and models exhausted after {cycle + 1} cycles. Add more keys or wait.[/bold red]")
            return "", None, 0

        return "", None, 0
