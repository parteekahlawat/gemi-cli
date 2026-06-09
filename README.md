<p align="center">
  <pre align="center">
   __ _ ___ _ __ ___ (_)
  / _` / _ \ '_ ` _ \| |
 | (_| \__/ | | | | | |
  \__, \___|_| |_| |_|_|
   __/ |
  |___/
  </pre>
  <strong>Free AI coding agent for your terminal.</strong><br>
  Multi-account key rotation. 9 providers. Auto-failover. Never pay for AI coding.
</p>

<p align="center">
  <a href="#installation">Install</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#supported-providers">Providers</a> •
  <a href="#the-never-pay-setup">Never Pay Setup</a> •
  <a href="#features">Features</a>
</p>

---

## What is gemi?

gemi is a free, open-source AI coding agent that runs in your terminal — like Claude Code or Cursor, but **free forever**.

It uses Google Gemini's free API tier as the primary provider, rotates across multiple API keys when you hit rate limits, and automatically fails over to 8 other providers (Groq, OpenRouter, Mistral, Cerebras, DeepSeek, Together AI, OpenAI, Ollama).

**The key insight:** A single free Gemini account gives you ~250-1,500 requests/day. With 3 accounts + fallback providers, you can code all day without paying a cent.

---

## Installation

```bash
# Install from PyPI
pipx install gemi-cli
# or
pip install gemi-cli

# From source
git clone https://github.com/AyeAI-Dev/gemi.git
cd gemi
pip install -e .

# Verify
gemi --help
```

> **Requires Python 3.10+**

---

## Quick Start

```bash
# 1. Add a free Gemini API key (https://aistudio.google.com/apikey)
gemi key add gemini

# 2. Navigate to your project
cd ~/your-project

# 3. Start coding
gemi
```

That's it. gemi reads your project, understands the codebase, and can read/write files, run commands, manage git, and build features for you.

---

## Demo

```
❯ build a REST API for a todo app with FastAPI

📋 Plan: Build Todo REST API
╭──────────────────────────────────────────────╮
│  ○ 1. Set up project structure               │
│  ○ 2. Create database models                 │
│  ○ 3. Build CRUD endpoints                   │
│  ○ 4. Add input validation                   │
│  ○ 5. Run and verify                         │
╰──────────────────────────────────────────────╯
  a) Yes, execute this plan

  📝 Write app/main.py
  📝 Write app/models.py
  📝 Write app/routes.py
  ⚙️  `pip install fastapi uvicorn sqlalchemy`
  ⚙️  `uvicorn app.main:app --reload`
  ✓ Process running in background (PID 12345)

  Done! API running at http://localhost:8000
```

---

## Supported Providers

9 providers pre-configured. Zero URL config — just add your key.

| Provider | Free Tier | Default Model | Get Key |
|---|---|---|---|
| **Gemini** | Yes — 250+ RPD | `gemini-2.5-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| **Groq** | Yes — 1,000 RPD | `llama-3.3-70b-versatile` | [console.groq.com/keys](https://console.groq.com/keys) |
| **OpenRouter** | Yes — 27+ free models | `deepseek/deepseek-r1:free` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Mistral** | Yes — 1B tokens/month | `codestral-latest` | [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys) |
| **Cerebras** | Yes — fast inference | `llama-3.3-70b` | [cloud.cerebras.ai](https://cloud.cerebras.ai/) |
| **DeepSeek** | No (cheap) | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| **Together AI** | Signup credits | `Llama-3.3-70B-Instruct-Turbo` | [api.together.ai](https://api.together.ai/settings/api-keys) |
| **OpenAI** | No | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com/api-keys) |
| **Ollama** | Unlimited (local) | `qwen3` | No key needed |

```bash
# Add any provider
gemi key add gemini
gemi key add groq --key gsk_...
gemi key add openrouter

# See all providers
gemi providers
```

---

## The "Never Pay" Setup

```bash
# Gemini — 3 Google accounts for rotation
gemi key add gemini --name acc1 --key AIzaSy...
gemi key add gemini --name acc2 --key AIzaSy...
gemi key add gemini --name acc3 --key AIzaSy...

# Groq — fast fallback
gemi key add groq --key gsk_...

# Cerebras — another free option
gemi key add cerebras --key csk-...

# OpenRouter — 27+ free models
gemi key add openrouter --key sk-or-...

# Ollama — unlimited local (optional)
ollama pull qwen3
```

**Automatic failover chain:**

```
gemini/acc1 → gemini/acc2 → gemini/acc3 → groq → cerebras → openrouter → mistral → ollama
```

All automatic. You never have to think about it. Context is preserved across switches.

| Gemini Accounts | Requests/Day | Coding Time |
|---|---|---|
| 1 | ~500-1,500 | 2-4 hours |
| 3 | ~1,500-4,500 | 6-12 hours |
| 5 | ~2,500-7,500 | Full day |

---

## Features

### AI Coding Agent
- Full ReAct agent loop — reads code, makes plans, writes files, runs commands
- **Plan mode** — automatically creates step-by-step plans for complex tasks, asks for approval before executing
- Streaming markdown responses with syntax highlighting
- 13 built-in tools (file ops, git, shell, search)

### Multi-Provider Key Rotation
- 9 pre-configured providers (zero URL/format config)
- Unlimited API keys per provider
- Auto-rotation on rate limit (429)
- Auto-failover across providers when all keys exhausted
- Encrypted key storage (`~/.gemi/keys.json`)
- Per-key usage tracking
- 3 rotation strategies: `failover`, `round-robin`, `least-used`

### Smart Command Execution
- All commands run non-blocking — fast commands return instantly, long-running ones (dev servers, builds) return after 30s with partial output and continue in background
- Background processes auto-cleaned on exit

### Session Management
- Auto-save after every message
- Resume any session: `gemi --resume <id>`
- Context auto-compaction at 75% usage
- Auto-trim on provider switch to fit smaller context windows

### Safety
- Diff preview on every file edit (green/red with line numbers)
- User approval required for writes and commands
- `/undo` to revert the last edit
- Configurable auto-approve settings

### Project Context
- Drop a `.gemi.md` in your project root with stack info, conventions, and instructions
- gemi reads it on startup and follows your project's rules

---

## Commands

### CLI (Terminal)

| Command | Description |
|---------|-------------|
| `gemi` | Start interactive coding session |
| `gemi --resume <id>` | Resume a saved session |
| `gemi key add <provider>` | Add an API key |
| `gemi key list [provider]` | List stored keys |
| `gemi key remove <provider> <name>` | Remove a key |
| `gemi key status` | Show key health & usage |
| `gemi model [name]` | Show or change default model |
| `gemi providers` | List all supported providers |
| `gemi sessions` | List saved sessions |
| `gemi config` | Show current config |
| `gemi config set <key> <value>` | Update a config value |

### In-Session (Inside gemi)

| Command | Description |
|---------|-------------|
| `/help` | Show help panel |
| `/status` | Key rotation status & usage summary |
| `/tokens` | Detailed token and session stats |
| `/model <name>` | Switch model mid-session |
| `/plan` | View current plan progress |
| `/undo` | Undo last file edit |
| `/sessions` | List saved sessions |
| `/clear` | Clear conversation & reset counters |
| `/quit` | Exit gemi (also `/exit`, `/q`, Ctrl+C) |

### Agent Tools

The AI uses these automatically — you don't call them directly.

**Read tools** (auto-approved, run silently):

| Tool | Description |
|------|-------------|
| `read_file` | Read file with line numbers |
| `list_directory` | List files and folders |
| `search_files` | Grep for text across files |
| `find_files` | Find files by glob pattern |
| `git_status` | Show modified/staged/untracked |
| `git_diff` | Show diffs |
| `git_log` | Commit history |
| `git_branch` | List/create/switch branches |

**Write tools** (require approval):

| Tool | Description |
|------|-------------|
| `write_file` | Create or overwrite a file |
| `edit_file` | Find-and-replace with diff view |
| `run_command` | Execute shell command (non-blocking) |
| `git_commit` | Stage and commit |
| `create_plan` | Create a step-by-step plan for complex tasks |

---

## Configuration

Config file: `~/.gemi/config.yaml`

```yaml
default_provider: gemini
default_model: gemini-2.5-flash

rotation:
  strategy: failover          # failover | round-robin | least-used
  auto_switch_provider: true
  provider_priority:
    - gemini
    - groq
    - deepseek
    - openrouter
    - cerebras
    - mistral
    - together
    - openai
    - ollama

agent:
  max_iterations: 50
  auto_approve_reads: true
  auto_approve_writes: false  # set true to skip approval prompts
```

```bash
gemi config set default_model gemini-2.5-pro
gemi config set rotation.strategy round-robin
gemi config set agent.auto_approve_writes true
```

---

## Free Tier Rate Limits

### Google Gemini

| Model | RPM | RPD | TPM | Context |
|---|---|---|---|---|
| `gemini-2.5-flash` | 10 | 250 | 250,000 | 1M |
| `gemini-2.5-flash-lite` | 15 | 1,000 | 250,000 | 1M |
| `gemini-2.5-pro` | 5 | 100 | 250,000 | 1M |

### Groq

| Model | RPM | RPD | TPM | Context |
|---|---|---|---|---|
| `llama-3.3-70b-versatile` | 30 | 1,000 | 12,000 | 128K |
| `llama-3.1-8b-instant` | 30 | 14,400 | 6,000 | 128K |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 30 | 1,000 | 30,000 | 128K |

### OpenRouter (Free Models)

27+ free models. IDs end with `:free`. Key highlights:

| Model | Context |
|---|---|
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1M |
| `qwen/qwen3-coder:free` | 1M |
| `google/gemma-4-31b-it:free` | 262K |
| `meta-llama/llama-3.3-70b-instruct:free` | 128K |

### Others

| Provider | Key Limits | Notes |
|---|---|---|
| **Mistral** | 2 RPM, 1B tokens/month | Slow RPM, huge monthly budget |
| **Cerebras** | 5-30 RPM, 1M tokens/day | Fastest inference (~2,600 tok/s) |
| **Ollama** | Unlimited | Local, no internet needed |

### Best Free Models for Coding

| Use Case | Best Option | Why |
|---|---|---|
| Daily driver | Gemini 2.5 Flash | 1M context, strong tool calling |
| Fast responses | Groq Llama 3.3 70B | ~300 tokens/sec |
| Largest model | OpenRouter Nemotron Ultra 550B | 550B params, free |
| Most requests | Groq Llama 3.1 8B | 14,400 RPD |
| Most tokens/month | Mistral Codestral | 1B tokens/month, code-focused |
| Unlimited local | Ollama Qwen 3 | No limits, best tool calling |

---

## Context & Switching

**Context is 100% preserved when switching keys or providers.** Conversation history lives in gemi's memory, not on any server. When a key or provider switches mid-task, the full context is sent to the new endpoint.

When switching to a smaller model, gemi auto-trims old messages to fit. Recent messages are always kept.

---

## Project Context File

Create `.gemi.md` in your project root:

```markdown
# My Project

FastAPI backend with PostgreSQL.

## Stack
- Python 3.12, FastAPI, SQLAlchemy
- pytest for testing

## Conventions
- snake_case everywhere
- Routes in app/routes/
- Models in app/models/
- Run tests: pytest -v
```

gemi reads this on startup and follows your project's rules.

---

## Sessions

```bash
gemi                       # auto-generates session ID
gemi sessions              # list saved sessions
gemi --resume a3f8b2c1     # resume a session
```

Sessions are stored at `~/.gemi/sessions/` as JSON.

---

## vs Other Tools

| Feature | gemi | Claude Code | Gemini CLI | Cursor |
|---|---|---|---|---|
| Free | Yes | No ($20/mo) | Yes | No ($20/mo) |
| Multi-account rotation | Yes | No | No | No |
| Multi-provider failover | Yes (9) | No | No | No |
| Local model fallback | Yes (Ollama) | No | No | No |
| Key usage tracking | Yes | No | No | No |
| Plan mode | Yes | Yes | No | Yes |
| Open source | Yes | Yes | Yes | No |
| Install | `pip` / `pipx` | `npm` | `npx` | App |

---

## Roadmap

### Built (v0.1.0)

- [x] 13 agent tools (files, git, shell, search, planning)
- [x] 9 pre-configured providers
- [x] Multi-account key rotation & failover
- [x] Plan mode (auto-detect complex tasks)
- [x] Non-blocking command execution
- [x] Session persistence & resume
- [x] Context compaction & auto-trim
- [x] Diff view + undo
- [x] `.gemi.md` project context
- [x] Encrypted key storage

### Planned

- [ ] Tab completion (commands, paths, models)
- [ ] Multi-line input (paste code blocks)
- [ ] Image/screenshot reading (Gemini vision)
- [ ] Web search tool
- [ ] Memory system (cross-session preferences)
- [ ] MCP server support
- [ ] VS Code extension

---

## License

MIT

---

<p align="center">
  <strong>Built by <a href="https://a79.ai">a79.ai</a></strong><br>
  <a href="https://github.com/AyeAI-Dev/gemi">GitHub</a> •
  <a href="https://github.com/AyeAI-Dev/gemi/issues">Issues</a>
</p>
