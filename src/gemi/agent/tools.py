import os
import signal
import subprocess
import threading
from pathlib import Path

from rich.console import Console

from gemi.ui import print_approval_prompt

console = Console()

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file. Returns the file content with line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read (relative to current directory)",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Edit a file by replacing old_text with new_text. The old_text must match exactly.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "old_text": {
                    "type": "string",
                    "description": "The exact text to find and replace",
                },
                "new_text": {
                    "type": "string",
                    "description": "The text to replace it with",
                },
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "run_command",
        "description": "Execute a shell command and return its output. Commands run non-blocking — fast commands return immediately, long-running ones return after 30s with partial output while continuing in background.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and directories in the given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list (defaults to current directory)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "search_files",
        "description": "Search for a text pattern in files. Like grep -rn.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (defaults to current directory)",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "find_files",
        "description": "Find files matching a glob pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '**/*.py', '*.json')",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "git_status",
        "description": "Show the current git status — modified, staged, and untracked files.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "git_diff",
        "description": "Show git diff of unstaged changes, or diff between two refs.",
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {
                    "type": "string",
                    "description": "Optional ref to diff against (e.g., 'HEAD', 'main', 'HEAD~3'). Defaults to unstaged changes.",
                },
                "staged": {
                    "type": "string",
                    "description": "Set to 'true' to show staged changes instead.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "git_log",
        "description": "Show recent git commit history.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "string",
                    "description": "Number of commits to show (default: 10)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "git_commit",
        "description": "Stage files and create a git commit.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Commit message",
                },
                "files": {
                    "type": "string",
                    "description": "Space-separated file paths to stage, or '.' for all changes",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "git_branch",
        "description": "List branches, create a new branch, or switch branches.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "'list', 'create <name>', or 'switch <name>'",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "create_plan",
        "description": "Create a step-by-step plan for complex tasks. Use this BEFORE executing when the task involves multiple files, multiple steps, or building something new. Each step should be a concrete action you will take.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title for the plan",
                },
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Short title for this step",
                            },
                            "description": {
                                "type": "string",
                                "description": "What you will do in this step",
                            },
                        },
                        "required": ["title", "description"],
                    },
                    "description": "List of steps to execute",
                },
            },
            "required": ["title", "steps"],
        },
    },
]

_edit_history: list[dict] = []
_background_processes: list[subprocess.Popen] = []


def execute_tool(name: str, args: dict, auto_approve_reads: bool = True, auto_approve_writes: bool = False) -> str:
    read_tools = {"read_file", "list_directory", "search_files", "find_files", "git_status", "git_diff", "git_log"}
    write_tools = {"write_file", "edit_file", "run_command", "git_commit", "git_branch"}

    if name in write_tools and not auto_approve_writes:
        if not print_approval_prompt(name, args):
            return "User denied this action."

    try:
        if name == "read_file":
            return _read_file(args["path"])
        elif name == "write_file":
            return _write_file(args["path"], args["content"])
        elif name == "edit_file":
            return _edit_file(args["path"], args["old_text"], args["new_text"])
        elif name == "run_command":
            return _run_command(args["command"])
        elif name == "list_directory":
            return _list_directory(args.get("path", "."))
        elif name == "search_files":
            return _search_files(args["pattern"], args.get("path", "."))
        elif name == "find_files":
            return _find_files(args["pattern"])
        elif name == "git_status":
            return _git_status()
        elif name == "git_diff":
            return _git_diff(args.get("ref"), args.get("staged"))
        elif name == "git_log":
            return _git_log(args.get("count", "10"))
        elif name == "git_commit":
            return _git_commit(args["message"], args.get("files"))
        elif name == "git_branch":
            return _git_branch(args["action"])
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"


def get_last_edit() -> dict | None:
    return _edit_history[-1] if _edit_history else None


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"File not found: {path}"
    if p.stat().st_size > 1_000_000:
        return f"File too large: {p.stat().st_size} bytes. Read a specific section instead."
    content = p.read_text(errors="replace")
    lines = content.split("\n")
    numbered = [f"{i + 1:4d} | {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered)


def _write_file(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written {len(content)} bytes to {path}"


def _edit_file(path: str, old_text: str, new_text: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"File not found: {path}"
    content = p.read_text()
    count = content.count(old_text)
    if count == 0:
        return "old_text not found in file. Make sure it matches exactly."
    if count > 1:
        return f"old_text found {count} times. Provide a more specific match."

    start_pos = content.index(old_text)
    start_line = content[:start_pos].count("\n") + 1

    _edit_history.append({"path": path, "old_content": content})
    new_content = content.replace(old_text, new_text, 1)
    p.write_text(new_content)
    diff_lines = _make_diff(old_text, new_text, path, start_line)
    return f"Edited {path} successfully.\n\nDiff:\n{diff_lines}"


def _make_diff(old_text: str, new_text: str, path: str, start_line: int = 1) -> str:
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    lines = []
    ln = start_line
    for line in old_lines:
        lines.append(f"{ln:4d} - {line.rstrip()}")
        ln += 1
    ln = start_line
    for line in new_lines:
        lines.append(f"{ln:4d} + {line.rstrip()}")
        ln += 1
    return "\n".join(lines)


def _run_command(command: str) -> str:
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd(),
            start_new_session=True,
        )

        captured_stdout = []
        captured_stderr = []

        def _read_stream(stream, buf):
            try:
                for line in stream:
                    buf.append(line)
            except Exception:
                pass

        t_out = threading.Thread(target=_read_stream, args=(proc.stdout, captured_stdout), daemon=True)
        t_err = threading.Thread(target=_read_stream, args=(proc.stderr, captured_stderr), daemon=True)
        t_out.start()
        t_err.start()

        t_out.join(timeout=30)
        t_err.join(timeout=0.5)

        poll = proc.poll()
        if poll is not None:
            t_out.join(timeout=2)
            t_err.join(timeout=1)
            output = ""
            if captured_stdout:
                output += "".join(captured_stdout)
            if captured_stderr:
                output += f"\nSTDERR:\n{''.join(captured_stderr)}"
            if poll != 0:
                output += f"\nExit code: {poll}"
            return output.strip() or "(no output)"

        _background_processes.append(proc)
        output = f"Process still running after 30s — continuing in background (PID {proc.pid}).\n"
        initial_out = "".join(captured_stdout).strip()
        initial_err = "".join(captured_stderr).strip()
        if initial_out:
            lines = initial_out.splitlines()
            preview = "\n".join(lines[:15])
            if len(lines) > 15:
                preview += f"\n... ({len(lines)} lines total)"
            output += f"\nOutput so far:\n{preview}"
        if initial_err:
            lines = initial_err.splitlines()
            preview = "\n".join(lines[:10])
            output += f"\nStderr so far:\n{preview}"

        try:
            proc.stdout.close()
        except Exception:
            pass
        try:
            proc.stderr.close()
        except Exception:
            pass

        return output

    except Exception as e:
        return f"Error running command: {e}"


def cleanup_background_processes():
    for proc in _background_processes:
        try:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass
    _background_processes.clear()


def _list_directory(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"Directory not found: {path}"
    if not p.is_dir():
        return f"Not a directory: {path}"
    entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    lines = []
    for entry in entries[:100]:
        prefix = "📁 " if entry.is_dir() else "   "
        lines.append(f"{prefix}{entry.name}")
    if len(list(p.iterdir())) > 100:
        lines.append(f"  ... and {len(list(p.iterdir())) - 100} more")
    return "\n".join(lines) or "(empty directory)"


def _search_files(pattern: str, path: str) -> str:
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*", "-l", pattern, path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if not result.stdout.strip():
            return f"No matches found for '{pattern}'"

        files = result.stdout.strip().split("\n")[:20]
        output_parts = []
        for f in files:
            grep_result = subprocess.run(
                ["grep", "-n", pattern, f],
                capture_output=True,
                text=True,
                timeout=5,
            )
            matches = grep_result.stdout.strip().split("\n")[:5]
            output_parts.append(f"\n{f}:")
            output_parts.extend(f"  {m}" for m in matches)

        return "\n".join(output_parts)
    except subprocess.TimeoutExpired:
        return "Search timed out."


def _find_files(pattern: str) -> str:
    matches = sorted(Path(".").glob(pattern))[:50]
    if not matches:
        return f"No files matching '{pattern}'"
    return "\n".join(str(m) for m in matches)


def _git_status() -> str:
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True, timeout=10, cwd=os.getcwd(),
    )
    if result.returncode != 0:
        return f"Not a git repository or git error: {result.stderr.strip()}"
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, timeout=5, cwd=os.getcwd(),
    )
    output = f"Branch: {branch.stdout.strip()}\n\n"
    output += result.stdout.strip() or "(working tree clean)"
    return output


def _git_diff(ref: str | None = None, staged: str | None = None) -> str:
    cmd = ["git", "diff"]
    if staged == "true":
        cmd.append("--staged")
    elif ref:
        cmd.append(ref)
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=15, cwd=os.getcwd(),
    )
    output = result.stdout.strip()
    if not output:
        return "No changes to show."
    if len(output) > 5000:
        output = output[:5000] + "\n\n... (diff truncated, too large)"
    return output


def _git_log(count: str = "10") -> str:
    try:
        n = min(int(count), 50)
    except ValueError:
        n = 10
    result = subprocess.run(
        ["git", "log", f"-{n}", "--oneline", "--decorate"],
        capture_output=True, text=True, timeout=10, cwd=os.getcwd(),
    )
    return result.stdout.strip() or "No commits yet."


def _git_commit(message: str, files: str | None = None) -> str:
    if files:
        file_list = files.split()
        add_result = subprocess.run(
            ["git", "add"] + file_list,
            capture_output=True, text=True, timeout=10, cwd=os.getcwd(),
        )
        if add_result.returncode != 0:
            return f"Failed to stage files: {add_result.stderr.strip()}"
    else:
        add_result = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, text=True, timeout=10, cwd=os.getcwd(),
        )

    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True, timeout=15, cwd=os.getcwd(),
    )
    if result.returncode != 0:
        return f"Commit failed: {result.stderr.strip()}"
    return result.stdout.strip()


def _git_branch(action: str) -> str:
    parts = action.strip().split(maxsplit=1)
    cmd = parts[0].lower()

    if cmd == "list":
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True, text=True, timeout=10, cwd=os.getcwd(),
        )
        return result.stdout.strip() or "No branches."

    if len(parts) < 2:
        return "Usage: 'list', 'create <name>', or 'switch <name>'"

    branch_name = parts[1]
    if cmd == "create":
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True, text=True, timeout=10, cwd=os.getcwd(),
        )
    elif cmd == "switch":
        result = subprocess.run(
            ["git", "checkout", branch_name],
            capture_output=True, text=True, timeout=10, cwd=os.getcwd(),
        )
    else:
        return f"Unknown git branch action: {cmd}. Use 'list', 'create', or 'switch'."

    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip() or result.stderr.strip()
