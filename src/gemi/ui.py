from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

BANNER = r"""
   __ _ ___ _ __ ___ (_)
  / _` / _ \ '_ ` _ \| |
 | (_| \__/ | | | | | |
  \__, \___|_| |_| |_|_|
   __/ |
  |___/
"""


def print_banner():
    banner_text = Text(BANNER, style="bold cyan")
    version_line = Text("  v0.1.0", style="bold cyan")
    version_line.append(" — Free AI Coding Agent", style="dim")
    console.print(banner_text, end="")
    console.print(version_line)
    console.print()


def print_welcome(provider: str, model: str, cwd: str):
    panels = Columns([
        Panel(f"[bold green]{provider}[/bold green]", title="[dim]Provider[/dim]", border_style="cyan", padding=(0, 1), expand=True),
        Panel(f"[bold green]{model}[/bold green]", title="[dim]Model[/dim]", border_style="cyan", padding=(0, 1), expand=True),
    ], padding=(0, 1), expand=True)
    console.print(panels)
    console.print(Panel(f"[blue]{cwd}[/blue]", title="[dim]Directory[/dim]", border_style="cyan", padding=(0, 1)))
    console.print(
        "  [dim]Type[/dim] [bold]/help[/bold] [dim]for commands,[/dim] "
        "[bold]/quit[/bold] [dim]to exit[/dim]\n"
    )


def print_key_status(status: list[dict]):
    table = Table(
        show_header=True,
        header_style="bold",
        border_style="dim",
        title="Key Status",
        title_style="bold",
        padding=(0, 1),
    )
    table.add_column("Provider", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("State")
    table.add_column("Requests", justify="right", style="dim")
    table.add_column("Tokens", justify="right", style="dim")

    for entry in status:
        state_style = "green"
        if entry["state"] == "exhausted":
            state_style = "red"
        elif "cooldown" in entry["state"]:
            state_style = "yellow"
        elif entry["state"] == "standby":
            state_style = "dim"

        table.add_row(
            entry["provider"],
            entry["name"],
            Text(entry["state"], style=state_style),
            str(entry["requests"]),
            str(entry["tokens"]),
        )

    console.print(table)


def print_help():
    help_text = (
        "[bold cyan]Session Commands[/bold cyan]\n"
        "  [bold]/help[/bold]          Show this help\n"
        "  [bold]/status[/bold]        Key rotation status & usage\n"
        "  [bold]/tokens[/bold]        Detailed token stats\n"
        "  [bold]/model[/bold] [dim]<m>[/dim]     Switch model mid-session\n"
        "  [bold]/plan[/bold]          View current plan progress\n"
        "  [bold]/undo[/bold]          Undo the last file edit\n"
        "  [bold]/sessions[/bold]      List saved sessions\n"
        "  [bold]/clear[/bold]         Clear conversation history\n"
        "  [bold]/quit[/bold]          Exit gemi\n"
        "\n"
        "[bold cyan]Tips[/bold cyan]\n"
        "  Resume a session:  [bold]gemi --resume <id>[/bold]\n"
        "  Project context:   Create a [bold].gemi.md[/bold] in your project root"
    )
    console.print(Panel(help_text, title="[bold]gemi help[/bold]", border_style="cyan", padding=(1, 2)))


def print_tool_call(name: str, args: dict):
    TOOL_ICONS = {
        "read_file": "📄",
        "write_file": "📝",
        "edit_file": "✏️ ",
        "run_command": "⚙️ ",
        "list_directory": "📁",
        "search_files": "🔍",
        "find_files": "🔍",
        "git_status": "📊",
        "git_diff": "📊",
        "git_log": "📊",
        "git_commit": "💾",
        "git_branch": "🌿",
        "create_plan": "📋",
    }
    icon = TOOL_ICONS.get(name, "⚡")

    if name == "create_plan":
        return

    if name == "read_file":
        label = f"Read {args.get('path', '')}"
    elif name == "write_file":
        label = f"Write {args.get('path', '')}"
    elif name == "edit_file":
        label = f"Edit {args.get('path', '')}"
    elif name == "run_command":
        cmd = args.get("command", "")
        label = f"`{cmd[:60]}{'...' if len(cmd) > 60 else ''}`"
    elif name == "list_directory":
        label = f"List {args.get('path', '.')}"
    elif name == "search_files":
        label = f"Search '{args.get('pattern', '')}'"
    elif name == "find_files":
        label = f"Find '{args.get('pattern', '')}'"
    elif name == "git_commit":
        label = f"Commit: {args.get('message', '')[:50]}"
    else:
        label = name.replace("_", " ").title()

    console.print(f"\n  {icon} [bold dim]{label}[/bold dim]")


def print_tool_result(name: str, result: str):
    if not result.strip():
        return

    if name == "edit_file" and "Diff:" in result:
        parts = result.split("Diff:\n", 1)
        if len(parts) == 2:
            console.print(f"  [green]{parts[0].strip()}[/green]")
            print_diff(parts[1])
            return

    if name == "write_file":
        console.print(f"  [green]{result.strip()}[/green]")
        return

    if name == "run_command":
        lines = result.strip().splitlines()
        preview = lines[:5]
        text = "\n".join(preview)
        if len(lines) > 5:
            text += f"\n... ({len(lines)} lines total)"
        console.print(Panel(text, border_style="dim", padding=(0, 1), expand=False))
        return

    lines = result.strip().splitlines()
    if len(lines) > 3:
        preview = "\n".join(lines[:3]) + f"\n[dim]... ({len(lines)} lines)[/dim]"
    else:
        preview = result.strip()
    console.print(f"  [dim]{preview[:300]}[/dim]")


def print_diff(diff_text: str):
    lines = diff_text.strip().splitlines()
    output = Text()
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            output.append(f"  {line}\n", style="dim")
        elif " + " in line and (stripped[0].isdigit() or stripped.startswith("+")):
            output.append(f"  {line}\n", style="white on green")
        elif " - " in line and (stripped[0].isdigit() or stripped.startswith("-")):
            output.append(f"  {line}\n", style="white on red")
        elif stripped.startswith("+ "):
            output.append(f"  {line}\n", style="white on green")
        elif stripped.startswith("- "):
            output.append(f"  {line}\n", style="white on red")
        else:
            output.append(f"  {line}\n", style="dim")
    console.print(Panel(output, border_style="dim", title="[dim]diff[/dim]", padding=(0, 1), expand=False))


def print_approval_prompt(name: str, args: dict) -> bool:
    console.print()

    if name == "edit_file":
        console.print(f"  [bold yellow]Edit file:[/bold yellow] [blue]{args.get('path', '')}[/blue]")
        old = args.get("old_text", "")
        new = args.get("new_text", "")

        start_line = 1
        try:
            from pathlib import Path
            file_content = Path(args.get("path", "")).read_text()
            pos = file_content.find(old)
            if pos >= 0:
                start_line = file_content[:pos].count("\n") + 1
        except Exception:
            pass

        diff = Text()
        ln = start_line
        for line in old.splitlines():
            diff.append(f"  {ln:4d} - {line}\n", style="white on red")
            ln += 1
        ln = start_line
        for line in new.splitlines():
            diff.append(f"  {ln:4d} + {line}\n", style="white on green")
            ln += 1
        console.print(Panel(diff, border_style="dim", title="[dim]proposed change[/dim]", padding=(0, 1), expand=False))
    elif name == "write_file":
        path = args.get("path", "")
        content = args.get("content", "")
        lines = content.splitlines()
        console.print(f"  [bold yellow]Write file:[/bold yellow] [blue]{path}[/blue] ({len(lines)} lines)")
        diff = Text()
        for ln, line in enumerate(lines, 1):
            diff.append(f"  {ln:4d} + {line}\n", style="white on green")
        if len(lines) > 50:
            shown = Text()
            for ln, line in enumerate(lines[:40], 1):
                shown.append(f"  {ln:4d} + {line}\n", style="white on green")
            shown.append(f"\n  ... {len(lines) - 40} more lines ...\n", style="dim")
            console.print(Panel(shown, border_style="dim", title="[dim]new file[/dim]", padding=(0, 1), expand=False))
        else:
            console.print(Panel(diff, border_style="dim", title="[dim]new file[/dim]", padding=(0, 1), expand=False))
    elif name == "run_command":
        cmd = args.get("command", "")
        console.print(f"  [bold yellow]Run command:[/bold yellow]")
        console.print(Panel(cmd, border_style="yellow", padding=(0, 1), expand=False))
    elif name == "git_commit":
        msg = args.get("message", "")
        files = args.get("files", "all changes")
        console.print(f"  [bold yellow]Git commit:[/bold yellow] {msg}")
        console.print(f"  [dim]Files: {files}[/dim]")
    else:
        console.print(f"  [bold yellow]{name}[/bold yellow]")
        for k, v in args.items():
            display = str(v)[:200]
            console.print(f"    {k}: {display}")

    return _interactive_select(
        options=["a) Yes, allow", "b) No, deny"],
        default=0,
    ) == 0


def _read_key() -> str:
    import sys
    import tty
    import termios

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A":
                    return "up"
                elif ch3 == "B":
                    return "down"
            return "esc"
        elif ch in ("\r", "\n"):
            return "enter"
        elif ch == "\x03":
            return "ctrl-c"
        elif ch in ("j",):
            return "down"
        elif ch in ("k",):
            return "up"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _interactive_select(options: list[str], default: int = 0) -> int:
    import sys

    selected = default

    def _render():
        lines = []
        for i, opt in enumerate(options):
            if i == selected:
                if i == 0:
                    lines.append(f"  [bold white on green]  {opt}  [/bold white on green]")
                else:
                    lines.append(f"  [bold white on red]  {opt}  [/bold white on red]")
            else:
                lines.append(f"  [dim]  {opt}  [/dim]")
        return "\n".join(lines)

    console.print()
    console.print(_render())
    console.print(f"\n  [dim]↑↓ to select, Enter to confirm[/dim]")

    num_lines = len(options) + 2

    while True:
        try:
            key = _read_key()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write(f"\033[{num_lines}A\033[J")
            sys.stdout.flush()
            console.print(f"  [red]Denied[/red]")
            return 1

        if key == "up":
            selected = (selected - 1) % len(options)
        elif key == "down":
            selected = (selected + 1) % len(options)
        elif key == "enter":
            sys.stdout.write(f"\033[{num_lines}A\033[J")
            sys.stdout.flush()
            chosen = options[selected]
            if selected == 0:
                console.print(f"  [green]{chosen}[/green]")
            else:
                console.print(f"  [red]{chosen}[/red]")
            return selected
        elif key == "ctrl-c" or key == "esc":
            sys.stdout.write(f"\033[{num_lines}A\033[J")
            sys.stdout.flush()
            console.print(f"  [red]Denied[/red]")
            return 1

        sys.stdout.write(f"\033[{num_lines}A\033[J")
        sys.stdout.flush()
        console.print()
        console.print(_render())
        console.print(f"\n  [dim]↑↓ to select, Enter to confirm[/dim]")


def print_status_bar(status_line: str):
    console.print(f"\n  [dim]{status_line}[/dim]")


def print_plan(title: str, steps: list[dict], show_status: bool = True):
    lines = []
    for i, step in enumerate(steps, 1):
        status = step.get("status", "pending")
        if status == "done":
            icon = "[green]✓[/green]"
        elif status == "in_progress":
            icon = "[yellow]▶[/yellow]"
        elif status == "failed":
            icon = "[red]✗[/red]"
        else:
            icon = "[dim]○[/dim]"

        step_title = step.get("title", f"Step {i}")
        desc = step.get("description", "")

        if status == "in_progress":
            lines.append(f"  {icon} [bold]{i}. {step_title}[/bold]")
        elif status == "done":
            lines.append(f"  {icon} [green]{i}. {step_title}[/green]")
        elif status == "failed":
            lines.append(f"  {icon} [red]{i}. {step_title}[/red]")
        else:
            lines.append(f"  {icon} [dim]{i}. {step_title}[/dim]")

        if desc and status != "done":
            lines.append(f"      [dim]{desc}[/dim]")

    content = "\n".join(lines)
    console.print(Panel(content, title=f"[bold cyan]{title}[/bold cyan]", border_style="cyan", padding=(1, 1)))


def print_plan_approval() -> bool:
    return _interactive_select(
        options=["a) Yes, execute this plan", "b) No, let me modify it"],
        default=0,
    ) == 0
