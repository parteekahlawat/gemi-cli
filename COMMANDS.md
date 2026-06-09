# gemi — Command Reference

Complete reference for every command available in gemi.

---

## Quick Reference

### CLI Commands

| Command | Description |
|---------|-------------|
| [`gemi`](#gemi) | Start an interactive coding session |
| [`gemi key add`](#gemi-key-add) | Add an API key for a provider |
| [`gemi key list`](#gemi-key-list) | List all stored API keys |
| [`gemi key remove`](#gemi-key-remove) | Remove a stored API key |
| [`gemi key status`](#gemi-key-status) | Show key health and usage stats |
| [`gemi model`](#gemi-model) | Show or change the default model |
| [`gemi providers`](#gemi-providers) | List all supported providers |
| [`gemi sessions`](#gemi-sessions) | List saved sessions |
| [`gemi config`](#gemi-config) | Show current configuration |
| [`gemi config set`](#gemi-config-set) | Update a config value |

### In-Session Commands

| Command | Description |
|---------|-------------|
| [`/help`](#help) | Show command help panel |
| [`/status`](#status) | Show key rotation status and usage |
| [`/tokens`](#tokens) | Show detailed token and session stats |
| [`/model`](#model) | Switch model mid-session |
| [`/undo`](#undo) | Undo the last file edit |
| [`/sessions`](#sessions) | List saved sessions |
| [`/clear`](#clear) | Clear conversation and reset counters |
| [`/quit`](#quit) | Exit gemi |

### Agent Tools

| Tool | Type | Description |
|------|------|-------------|
| [`read_file`](#read_file) | Read | Read file contents with line numbers |
| [`list_directory`](#list_directory) | Read | List files and folders |
| [`search_files`](#search_files) | Read | Search for text across files |
| [`find_files`](#find_files) | Read | Find files by glob pattern |
| [`git_status`](#git_status) | Read | Show modified and untracked files |
| [`git_diff`](#git_diff) | Read | Show diff of changes |
| [`git_log`](#git_log) | Read | Show recent commits |
| [`git_branch`](#git_branch) | Read | List, create, or switch branches |
| [`write_file`](#write_file) | Write | Create or overwrite a file |
| [`edit_file`](#edit_file) | Write | Find-and-replace text in a file |
| [`run_command`](#run_command) | Write | Execute a shell command |
| [`git_commit`](#git_commit) | Write | Stage files and commit |

---

## CLI Commands

### `gemi`

Start an interactive coding agent session in the current directory.

```bash
gemi [--resume <session-id>]
```

**Flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--resume <id>` | `-r <id>` | Resume a previously saved session |

**Examples:**

```bash
gemi                          # New session in current directory
gemi --resume c99f3b33        # Resume a saved session
gemi -r c99f3b33              # Short form
cd ~/projects/myapp && gemi   # Start in a specific project
```

**What happens on startup:**
1. Loads config from `~/.gemi/config.yaml`
2. Loads all API keys and initializes key rotation
3. Connects to the first available provider
4. Reads `.gemi.md` if present in the current directory
5. Opens the interactive REPL

---

### `gemi key add`

Add an API key for a provider. Prompts interactively if `--key` is not provided (input is hidden).

```bash
gemi key add <provider> [--name <label>] [--key <api_key>]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `provider` | Yes | Provider name: `gemini`, `groq`, `deepseek`, `openrouter`, `mistral`, `openai`, `together`, `cerebras`, `ollama` |

**Flags:**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--name` | `-n` | `default` | Label for this key (use for multi-account) |
| `--key` | `-k` | *(interactive)* | Pass API key inline |

**Examples:**

```bash
# Interactive (recommended — hides input)
gemi key add gemini
gemi key add gemini --name acc1
gemi key add gemini --name acc2
gemi key add groq --name personal

# Inline
gemi key add gemini --name acc1 --key AIzaSy...
gemi key add groq -n work -k gsk_...
```

**Notes:**
- Keys are encrypted and stored at `~/.gemi/keys.json`
- Adding 2+ keys for the same provider enables automatic rotation
- Running `gemi key add ollama` will tell you no key is needed

---

### `gemi key list`

List all stored API keys. Optionally filter by provider.

```bash
gemi key list [provider]
```

**Examples:**

```bash
gemi key list            # All keys
gemi key list gemini     # Only Gemini keys
```

**Sample output:**

```
┌──────────┬─────────┬────────────┐
│ Provider │ Name    │ Added      │
├──────────┼─────────┼────────────┤
│ gemini   │ acc1    │ 2026-06-06 │
│ gemini   │ acc2    │ 2026-06-06 │
│ groq     │ default │ 2026-06-07 │
└──────────┴─────────┴────────────┘
```

---

### `gemi key remove`

Remove a stored API key by provider and label.

```bash
gemi key remove <provider> <name>
```

**Examples:**

```bash
gemi key remove gemini acc2
gemi key remove groq default
```

---

### `gemi key status`

Show health and usage of all loaded keys — which is active, on cooldown, or exhausted.

```bash
gemi key status
```

**Sample output:**

```
┌──────────┬─────────┬──────────────┬──────────┬────────┐
│ Provider │ Name    │ State        │ Requests │ Tokens │
├──────────┼─────────┼──────────────┼──────────┼────────┤
│ gemini   │ acc1    │ active       │ 12       │ 4500   │
│ gemini   │ acc2    │ standby      │ 0        │ 0      │
│ groq     │ default │ cooldown(45s)│ 8        │ 2100   │
│ ollama   │ local   │ standby      │ 0        │ 0      │
└──────────┴─────────┴──────────────┴──────────┴────────┘
```

**Key states:**

| State | Meaning |
|-------|---------|
| `active` | Currently being used for requests |
| `standby` | Ready as a backup, not in use |
| `cooldown (Xs)` | Rate limited, waiting X seconds |
| `exhausted` | All retries spent, won't be used again this session |

---

### `gemi model`

Show the current model and all available models per configured provider, or set a new default.

```bash
gemi model [name]
```

**Examples:**

```bash
gemi model                     # Show current model + available models
gemi model gemini-2.5-pro      # Set default to gemini-2.5-pro
gemi model llama-3.3-70b-versatile
```

---

### `gemi providers`

Show a table of all 9 supported providers with status, default model, free tier info, and key URL.

```bash
gemi providers
```

**Sample output:**

```
┌────────────┬───────────────┬──────┬────────────────────────┬──────────────────────┬────────────────┐
│ Provider   │ Name          │ Free │ Default Model          │ Key URL              │ Status         │
├────────────┼───────────────┼──────┼────────────────────────┼──────────────────────┼────────────────┤
│ gemini     │ Google Gemini │ Yes  │ gemini-2.5-flash       │ aistudio.google.com  │ Ready          │
│ groq       │ Groq          │ Yes  │ llama-3.3-70b-versatile│ console.groq.com     │ Ready          │
│ deepseek   │ DeepSeek      │ No   │ deepseek-chat          │ platform.deepseek.com│ Not configured │
│ ...        │               │      │                        │                      │                │
└────────────┴───────────────┴──────┴────────────────────────┴──────────────────────┴────────────────┘
```

---

### `gemi sessions`

List saved sessions (up to 10 most recent). Shows session ID, message count, working directory, and a preview of the first message.

```bash
gemi sessions
```

Resume any session with `gemi --resume <id>`.

---

### `gemi config`

Show the current configuration in YAML format.

```bash
gemi config
```

Config file location: `~/.gemi/config.yaml`

---

### `gemi config set`

Update a config value. Supports dot notation for nested keys.

```bash
gemi config set <key> <value>
```

**Examples:**

```bash
gemi config set default_model gemini-2.5-pro
gemi config set default_provider groq
gemi config set agent.auto_approve_writes true
gemi config set agent.max_iterations 30
gemi config set rotation.auto_switch_provider false
```

**All config keys:**

| Key | Default | Description |
|-----|---------|-------------|
| `default_provider` | `gemini` | Provider used on startup |
| `default_model` | `gemini-2.5-flash` | Model used on startup |
| `rotation.strategy` | `failover` | Rotation strategy: `failover`, `round-robin`, `least-used` |
| `rotation.auto_switch_provider` | `true` | Auto-failover to next provider when keys exhausted |
| `rotation.provider_priority` | `gemini, groq, ...` | Failover order |
| `agent.max_iterations` | `50` | Max tool-call loops per message |
| `agent.auto_approve_reads` | `true` | Auto-approve read tools without asking |
| `agent.auto_approve_writes` | `false` | Auto-approve write tools without asking |

**Default provider priority:**

`gemini` > `groq` > `deepseek` > `openrouter` > `cerebras` > `mistral` > `together` > `openai` > `ollama`

---

## In-Session Commands

These are typed inside the gemi REPL (after running `gemi`). All start with `/`.

### `/help`

Show a quick reference panel of all in-session commands.

```
❯ /help
```

---

### `/status`

Show the key rotation table (all keys with state, requests, tokens) plus a summary line with provider, model, token usage, and context percentage.

```
❯ /status
```

Shows both the key table (same as `gemi key status`) and a one-line summary:

```
gemini/gemini-2.5-flash | tokens: ~500 / 1,000,000 | reqs: 3 | context: 1%
```

---

### `/tokens`

Show detailed token and session statistics.

```
❯ /tokens
  Provider:  gemini
  Model:     gemini-2.5-flash
  Tokens:    ~500 / 1,000,000
  Context:   1,200 / 1,000,000 (0%)
  Requests:  3
  Keys:      2 active / 3 total
  Session:   c99f3b33
```

| Field | Description |
|-------|-------------|
| Tokens | Estimated output tokens used / provider's context window |
| Context | Current conversation size / max context window |
| Requests | Number of API calls made this session |
| Keys | Active (usable) keys / total keys for current provider |

---

### `/model`

Show the current model or switch to a different one mid-session.

```
❯ /model                        # Show current model
  Current model: gemini-2.5-flash

❯ /model gemini-2.5-pro         # Switch model
  Switched to: gemini-2.5-pro
```

The model stays changed for the rest of the session. To change permanently, use `gemi config set default_model <name>` from terminal.

---

### `/undo`

Undo the last file edit made by the agent. Restores the file to its exact state before the most recent `edit_file` or `write_file` call.

```
❯ /undo
  Undone last edit to src/app.py
```

Only the most recent edit can be undone. If no edits have been made, shows "Nothing to undo".

---

### `/sessions`

List saved sessions. Same output as `gemi sessions` from terminal.

```
❯ /sessions
```

---

### `/clear`

Clear the entire conversation history and reset token/request counters. The system prompt is preserved. Useful when context is getting large or you want a fresh start without exiting.

```
❯ /clear
  Conversation cleared.
```

---

### `/quit`

Exit gemi. Session is auto-saved before exit. Also works with `/exit` and `/q`.

```
❯ /quit
  Goodbye!
```

You can also press `Ctrl+C` or `Ctrl+D` to exit.

---

## Agent Tools

These tools are used by the AI agent internally to interact with your codebase. You never call them directly — the agent decides when to use them based on your request.

**Read tools** run silently (no output shown to you). **Write tools** show what they're about to do and ask for confirmation before executing (unless `auto_approve_writes` is `true`).

---

### `read_file`

**Type:** Read (silent, auto-approved)

Read the contents of a file with line numbers.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `path` | Yes | Path to file (relative to current directory) |

Returns file content with numbered lines. Rejects files larger than 1MB.

---

### `list_directory`

**Type:** Read (silent, auto-approved)

List files and directories in a path. Shows folders with a folder icon, files without. Limited to 100 entries.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `path` | No | `.` | Directory to list |

---

### `search_files`

**Type:** Read (silent, auto-approved)

Search for a text pattern across files. Works like `grep -rn` — returns matching files with line numbers and context.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `pattern` | Yes | — | Text pattern to search for |
| `path` | No | `.` | Directory to search in |

Limited to 20 matching files, 5 matches per file. Times out after 15 seconds.

---

### `find_files`

**Type:** Read (silent, auto-approved)

Find files matching a glob pattern.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `pattern` | Yes | Glob pattern (e.g., `**/*.py`, `src/**/*.tsx`) |

Returns up to 50 matching file paths.

---

### `git_status`

**Type:** Read (silent, auto-approved)

Show the current branch and working tree status (modified, staged, untracked files).

No parameters.

---

### `git_diff`

**Type:** Read (silent, auto-approved)

Show git diff output. Defaults to unstaged changes.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `ref` | No | — | Ref to diff against (`HEAD`, `main`, `HEAD~3`) |
| `staged` | No | — | Set to `"true"` to show staged changes |

Diff output is truncated at 5000 characters.

---

### `git_log`

**Type:** Read (silent, auto-approved)

Show recent git commit history in one-line format.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `count` | No | `10` | Number of commits to show (max 50) |

---

### `git_branch`

**Type:** Read (auto-approved for `list`, requires approval for `create`/`switch`)

List branches, create a new branch, or switch branches.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `action` | Yes | `list`, `create <name>`, or `switch <name>` |

---

### `write_file`

**Type:** Write (requires approval)

Create a new file or overwrite an existing file. Creates parent directories if needed.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `path` | Yes | Path to write to |
| `content` | Yes | Full file content |

---

### `edit_file`

**Type:** Write (requires approval)

Edit a file by finding exact text and replacing it. The `old_text` must match exactly once in the file.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `path` | Yes | Path to the file |
| `old_text` | Yes | Exact text to find |
| `new_text` | Yes | Replacement text |

Fails if `old_text` is not found or matches more than once. Edits are tracked and can be undone with `/undo`.

---

### `run_command`

**Type:** Write (requires approval)

Execute a shell command in the current working directory. Returns stdout, stderr, and exit code.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `command` | Yes | Shell command to run |

Times out after 60 seconds.

---

### `git_commit`

**Type:** Write (requires approval)

Stage files and create a git commit.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `message` | Yes | — | Commit message |
| `files` | No | all changes | Space-separated paths to stage, or `.` for everything |
