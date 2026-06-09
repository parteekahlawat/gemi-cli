import asyncio
import os
import sys

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.table import Table

from gemi.config import GEMI_DIR, load_config, save_config
from gemi.keys.store import add_key, list_keys, remove_key
from gemi.registry import ALL_PROVIDER_NAMES, PROVIDERS, get_base_url, get_provider_info, get_provider_type
from gemi.sessions import (
    generate_session_id,
    list_sessions,
    load_session,
)
from gemi.ui import print_banner, print_help, print_key_status, print_welcome

app = typer.Typer(
    name="gemi",
    help="Free AI coding agent — multi-account key rotation with provider failover",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    resume: str = typer.Option(None, "--resume", "-r", help="Resume a previous session by ID"),
):
    if ctx.invoked_subcommand is not None:
        return
    asyncio.run(_interactive_loop(resume_id=resume))


async def _interactive_loop(resume_id: str | None = None):
    from gemi.agent.loop import AgentLoop
    from gemi.agent.tools import cleanup_background_processes, get_last_edit

    print_banner()

    session_id = resume_id or generate_session_id()
    agent = AgentLoop(session_id=session_id)

    if not agent.provider:
        console.print("[bold yellow]No API keys found.[/bold yellow]")
        console.print("Add a Gemini API key to get started:\n")
        console.print("  [bold]gemi key add gemini[/bold]\n")
        console.print("Get a free key at: [link]https://aistudio.google.com/apikey[/link]\n")
        return

    if resume_id:
        old_messages = load_session(resume_id)
        if old_messages:
            agent.load_session(old_messages)
            console.print(f"  [green]Resumed session {resume_id} ({len(old_messages)} messages)[/green]")
        else:
            console.print(f"  [yellow]Session {resume_id} not found, starting fresh[/yellow]")

    provider_name = agent.key_manager.get_current_provider()
    print_welcome(provider_name, agent.model, os.getcwd())
    console.print(f"  Session: [dim]{session_id}[/dim]")

    GEMI_DIR.mkdir(parents=True, exist_ok=True)
    history_file = str(GEMI_DIR / "history.txt")
    session = PromptSession(history=FileHistory(history_file))

    def _get_border():
        try:
            w = os.get_terminal_size().columns
        except OSError:
            w = 80
        return "─" * (w - 2)

    def _prompt():
        try:
            return session.prompt("│ ❯ ")
        except (EOFError, KeyboardInterrupt):
            return None

    console.print(f"\n[dim]╭{_get_border()}╮[/dim]")

    while True:
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, _prompt
            )
        except (EOFError, KeyboardInterrupt, asyncio.CancelledError):
            user_input = None

        if user_input is None:
            console.print(f"[dim]╰{_get_border()}╯[/dim]")
            cleanup_background_processes()
            console.print("[dim]Goodbye![/dim]")
            break

        user_input = user_input.strip()
        if not user_input:
            sys.stdout.write("\033[A\033[2K")
            sys.stdout.flush()
            continue

        console.print(f"[dim]╰{_get_border()}╯[/dim]")

        if user_input.startswith("/"):
            cmd = user_input.lower().split()[0]
            if cmd in ("/quit", "/exit", "/q"):
                cleanup_background_processes()
                console.print("[dim]Goodbye![/dim]")
                break
            elif cmd == "/help":
                print_help()
            elif cmd == "/status":
                print_key_status(agent.key_manager.get_status())
                console.print(f"\n  {agent.get_status_line()}")
            elif cmd == "/clear":
                agent.messages = agent.messages[:1]
                agent.total_tokens_used = 0
                agent.total_requests = 0
                console.print("[dim]Conversation cleared.[/dim]")
            elif cmd == "/model":
                parts = user_input.split()
                if len(parts) < 2:
                    console.print(f"  Current model: [green]{agent.model}[/green]")
                    console.print("  Usage: /model <model-name>")
                else:
                    agent.model = parts[1]
                    console.print(f"  Switched to: [green]{agent.model}[/green]")
            elif cmd == "/undo":
                last_edit = get_last_edit()
                if last_edit:
                    from pathlib import Path
                    p = Path(last_edit["path"])
                    p.write_text(last_edit["old_content"])
                    console.print(f"  [green]Undone last edit to {last_edit['path']}[/green]")
                else:
                    console.print("  [yellow]Nothing to undo[/yellow]")
            elif cmd == "/plan":
                plan = agent.get_plan()
                if plan:
                    from gemi.ui import print_plan
                    print_plan(plan["title"], plan["steps"])
                else:
                    console.print("  [dim]No active plan. Start a complex task and gemi will create one automatically.[/dim]")
            elif cmd == "/sessions":
                _show_sessions()
            elif cmd == "/tokens":
                console.print(agent.get_detailed_status())
            else:
                console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            console.print(f"\n[dim]╭{_get_border()}╮[/dim]")
            continue

        await agent.chat(user_input)
        console.print(f"\n[dim]╭{_get_border()}╮[/dim]")


def _show_sessions():
    sessions = list_sessions()
    if not sessions:
        console.print("  [yellow]No saved sessions[/yellow]")
        return
    table = Table(title="Saved Sessions", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Messages", justify="right")
    table.add_column("Directory", style="dim")
    table.add_column("Preview")
    for s in sessions[:10]:
        table.add_row(s["id"], str(s["messages"]), s.get("cwd", ""), s["preview"][:60])
    console.print(table)
    console.print("\n  Resume with: [bold]gemi --resume <id>[/bold]")


key_app = typer.Typer(help="Manage API keys")
app.add_typer(key_app, name="key")


def _validate_api_key(provider: str, api_key: str) -> tuple[bool, str]:
    provider_type = get_provider_type(provider)
    info = get_provider_info(provider)
    model = info["default_model"] if info else "gpt-4o-mini"

    try:
        if provider_type == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents="Say hi in one word.",
                config={"max_output_tokens": 5},
            )
            return True, ""

        elif provider_type == "openai_compat":
            from openai import OpenAI
            base_url = get_base_url(provider) or "https://api.openai.com/v1"
            extra_headers = {}
            if "openrouter" in base_url:
                extra_headers["HTTP-Referer"] = "https://github.com/gemi-cli/gemi"
                extra_headers["X-Title"] = "gemi"
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers=extra_headers or None,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say hi in one word."}],
                max_tokens=5,
            )
            return True, ""

    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str or "user not found" in error_str or "invalid" in error_str:
            return False, "Authentication failed — key is invalid or expired"
        elif "404" in error_str or "not found" in error_str and "model" in error_str:
            return True, ""
        elif "429" in error_str or "rate" in error_str or "quota" in error_str:
            return True, ""
        else:
            return False, str(e)

    return True, ""


@key_app.command("add")
def key_add(
    provider: str = typer.Argument(help="Provider: " + ", ".join(ALL_PROVIDER_NAMES)),
    name: str = typer.Option("default", "--name", "-n", help="Label for this key"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or omit to enter interactively)"),
):
    info = get_provider_info(provider)
    if not info:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        console.print(f"Available: {', '.join(ALL_PROVIDER_NAMES)}")
        return

    if not info["needs_key"]:
        console.print(f"[green]{info['name']} doesn't need an API key — it runs locally![/green]")
        console.print(f"  Default model: {info['default_model']}")
        console.print(f"  Make sure it's running: ollama serve")
        return

    existing = list_keys(provider)
    existing_names = {k["name"] for k in existing}

    if name == "default" and "default" in existing_names:
        console.print(f"\n  [yellow]You already have a '{name}' key for {provider}.[/yellow]")
        console.print(f"  Existing keys: {', '.join(existing_names)}")
        choice = typer.prompt(
            "  Enter a new name for this key, or 'replace' to overwrite",
            default=f"acc{len(existing) + 1}",
        )
        if choice.lower() == "replace":
            pass
        else:
            name = choice.strip()

    if key:
        api_key = key.strip()
    else:
        console.print(f"\n  [bold]{info['name']}[/bold]")
        if info["key_url"]:
            console.print(f"  Get your key at: [link]{info['key_url']}[/link]")
        if info["free_tier"]:
            console.print(f"  [green]Free tier available[/green]")
        console.print(f"  Default model: {info['default_model']}")
        console.print()
        api_key = typer.prompt("Paste your API key", hide_input=True)

    if not api_key.strip():
        console.print("[red]Empty key, aborting.[/red]")
        return

    api_key = api_key.strip()

    console.print(f"\n  [dim]Validating key with {info['name']}...[/dim]")
    valid, error_msg = _validate_api_key(provider, api_key)

    if not valid:
        console.print(f"  [bold red]Invalid API key:[/bold red] {error_msg}")
        console.print(f"  Key was NOT saved. Please check your key and try again.")
        if info["key_url"]:
            console.print(f"  Get a valid key at: [link]{info['key_url']}[/link]")
        return

    console.print(f"  [green]Key verified![/green]")

    add_key(provider, name, api_key)
    console.print(f"\n[green]Key '{name}' added for {info['name']}[/green]")
    console.print(f"  Base URL: [dim]{info['base_url'] or 'native SDK'}[/dim]")
    console.print(f"  Model: [dim]{info['default_model']}[/dim]")

    existing = list_keys(provider)
    if len(existing) > 1:
        console.print(f"  [dim]You now have {len(existing)} keys for {provider} — rotation enabled![/dim]")


@key_app.command("list")
def key_list(
    provider: str = typer.Argument(None, help="Filter by provider"),
):
    keys = list_keys(provider)
    if not keys:
        console.print("[yellow]No keys found.[/yellow]")
        console.print("Add one with: [bold]gemi key add gemini[/bold]")
        return

    table = Table(title="API Keys", show_header=True)
    table.add_column("Provider", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Added", style="dim")

    for k in keys:
        table.add_row(k["provider"], k["name"], k["added_at"][:10])

    console.print(table)


@key_app.command("remove")
def key_remove(
    provider: str = typer.Argument(help="Provider name"),
    name: str = typer.Argument("default", help="Key label"),
):
    if remove_key(provider, name):
        console.print(f"[green]Removed key '{name}' for {provider}[/green]")
    else:
        console.print(f"[red]Key '{name}' for {provider} not found[/red]")


@key_app.command("status")
def key_status():
    from gemi.agent.loop import AgentLoop
    agent = AgentLoop()
    print_key_status(agent.key_manager.get_status())


@app.command("sessions")
def sessions_cmd():
    _show_sessions()


config_app = typer.Typer(help="View and edit configuration")
app.add_typer(config_app, name="config")


@config_app.callback(invoke_without_command=True)
def config_show(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return
    import yaml
    config = load_config()
    console.print("[bold]Current configuration:[/bold]\n")
    console.print(yaml.dump(config, default_flow_style=False))


@config_app.command("set")
def config_set(
    key: str = typer.Argument(help="Config key (dot notation, e.g. 'default_model')"),
    value: str = typer.Argument(help="Value to set"),
):
    config = load_config()
    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        if part not in target or not isinstance(target[part], dict):
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value
    save_config(config)
    console.print(f"[green]Set {key} = {value}[/green]")


@app.command("model")
def model_cmd(name: str = typer.Argument(None, help="Model to switch to")):
    config = load_config()
    if name:
        config["default_model"] = name
        save_config(config)
        console.print(f"[green]Default model set to: {name}[/green]")
    else:
        console.print(f"Current model: [green]{config.get('default_model', 'gemini-2.5-flash')}[/green]")
        console.print(f"Current provider: [green]{config.get('default_provider', 'gemini')}[/green]")
        console.print()
        stored = {k["provider"] for k in list_keys()}
        stored.add("ollama")
        for pname in ALL_PROVIDER_NAMES:
            info = PROVIDERS[pname]
            has_key = pname in stored
            status = "[green]configured[/green]" if has_key else "[dim]no key[/dim]"
            console.print(f"  [bold]{pname}[/bold] ({info['name']}) — {status}")
            if has_key:
                for m in info["models"][:4]:
                    console.print(f"    - {m}")


@app.command("providers")
def providers_cmd():
    table = Table(title="Available Providers", show_header=True)
    table.add_column("Provider", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Free", style="green")
    table.add_column("Default Model", style="dim")
    table.add_column("Key URL")
    table.add_column("Status")

    stored = {k["provider"] for k in list_keys()}
    stored.add("ollama")

    for pname, info in PROVIDERS.items():
        has_key = pname in stored
        free = "Yes" if info["free_tier"] else "No"
        url = info["key_url"] or "—"
        status = "[green]Ready[/green]" if has_key else "[dim]Not configured[/dim]"
        table.add_row(pname, info["name"], free, info["default_model"], url, status)

    console.print(table)
    console.print("\nAdd a provider: [bold]gemi key add <provider>[/bold]")


if __name__ == "__main__":
    app()
