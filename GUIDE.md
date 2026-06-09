# gemi — Documentation

Free AI coding agent for your terminal. Multi-account key rotation, multi-provider failover, never pay for AI coding assistance.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Supported Providers](#supported-providers)
- [Setting Up Each Provider](#setting-up-each-provider)
- [Free Tier Rate Limits](#free-tier-rate-limits)
- [Key Management](#key-management)
- [Multi-Account Rotation](#multi-account-rotation)
- [Context & Account Switching](#context--account-switching)
- [Commands Reference](#commands-reference)
  - [CLI Commands](#cli-commands-terminal)
  - [In-Session Commands](#in-session-commands-inside-gemi)
  - [Agent Tools](#agent-tools)
- [Features](#features)
- [Configuration](#configuration)
- [Project Context File](#project-context-file)
- [Sessions](#sessions)
- [Roadmap](#roadmap)

---

## Installation

```bash
git clone https://github.com/your-username/gemi.git
cd gemi
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Verify
gemi --help
```

---

## Quick Start

```bash
# 1. Add a free Gemini API key
gemi key add gemini

# 2. Navigate to your project
cd ~/your-project

# 3. Start coding
gemi
```

---

## Supported Providers

gemi has **9 providers** pre-configured. You don't need to set base URLs or configure API formats — just add your key and go.

```bash
# See all providers and their status
gemi providers
```

| Provider | Name | Free Tier | Default Model | Needs Key |
|---|---|---|---|---|
| `gemini` | Google Gemini | Yes | gemini-2.5-flash | Yes |
| `groq` | Groq | Yes | llama-3.3-70b-versatile | Yes |
| `deepseek` | DeepSeek | No (cheap) | deepseek-chat | Yes |
| `openrouter` | OpenRouter | Yes (27+ models) | deepseek/deepseek-r1:free | Yes |
| `mistral` | Mistral AI | Yes | codestral-latest | Yes |
| `openai` | OpenAI | No | gpt-4o-mini | Yes |
| `together` | Together AI | No (signup credits) | Llama-3.3-70B-Instruct-Turbo | Yes |
| `cerebras` | Cerebras | Yes | llama-3.3-70b | Yes |
| `ollama` | Ollama (Local) | Yes (unlimited) | qwen3 | No |

**Every provider is zero-config.** Base URLs, API formats, and default models are all built in. Just:

```bash
gemi key add <provider>
```

---

## Setting Up Each Provider

### 1. Google Gemini (Recommended)

Best free tier. 1M token context window, strong tool calling.

**Get your key:**
1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with Google
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)

**Add to gemi:**
```bash
# Interactive
gemi key add gemini

# Inline
gemi key add gemini --key AIzaSy...your_key

# Multiple accounts for rotation
gemi key add gemini --name personal --key AIzaSy...key1
gemi key add gemini --name work     --key AIzaSy...key2
gemi key add gemini --name alt      --key AIzaSy...key3
```

**Available models:**
- `gemini-2.5-flash` (default, fast)
- `gemini-2.5-flash-lite` (fastest, lighter)
- `gemini-2.5-pro` (most capable, lower limits)

---

### 2. Groq (Fast Inference)

Extremely fast responses. Good for quick tasks.

**Get your key:**
1. Go to [https://console.groq.com/keys](https://console.groq.com/keys)
2. Sign up (free, no credit card)
3. Click **"Create API Key"**
4. Copy the key (starts with `gsk_...`)

**Add to gemi:**
```bash
gemi key add groq
# or
gemi key add groq --key gsk_...your_key
```

**Available models:**
- `llama-3.3-70b-versatile` (default)
- `llama-3.1-8b-instant`
- `deepseek-r1-distill-llama-70b`
- `gemma2-9b-it`
- `meta-llama/llama-4-scout-17b-16e-instruct`

---

### 3. DeepSeek

High quality coding model. Very cheap (not free).

**Get your key:**
1. Go to [https://platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
2. Sign up and add credits
3. Create an API key (starts with `sk-...`)

**Add to gemi:**
```bash
gemi key add deepseek --key sk-...your_key
```

**Available models:**
- `deepseek-chat` (default)
- `deepseek-reasoner`

---

### 4. OpenRouter (27+ Free Models)

One key, access to dozens of free models from different providers.

**Get your key:**
1. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Sign up (free)
3. Click **"Create Key"**
4. Copy the key (starts with `sk-or-...`)

**Add to gemi:**
```bash
gemi key add openrouter --key sk-or-...your_key
```

**Switch between free models:**
```bash
gemi model deepseek/deepseek-r1:free
gemi model meta-llama/llama-3.3-70b-instruct:free
gemi model qwen/qwen3-coder:free
gemi model google/gemma-3-27b-it:free
gemi model microsoft/phi-4:free
gemi model mistralai/mistral-small-3.2-24b-instruct:free
gemi model nousresearch/hermes-3-llama-3.1-405b:free
```

> All free model IDs end with `:free`

---

### 5. Mistral AI

All models accessible for free. 1 billion tokens/month but only 2 RPM.

**Get your key:**
1. Go to [https://console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)
2. Sign up (phone verification, no credit card)
3. Create a key

**Add to gemi:**
```bash
gemi key add mistral --key ...your_key
```

**Available models:**
- `codestral-latest` (default, best for code)
- `mistral-large-latest`
- `mistral-small-latest`
- `pixtral-large-latest`

---

### 6. OpenAI

Not free. Requires paid account.

**Get your key:**
1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in (credit card required)
3. Create a key (starts with `sk-...`)

**Add to gemi:**
```bash
gemi key add openai --key sk-...your_key
```

**Available models:**
- `gpt-4o-mini` (default, cheapest)
- `gpt-4o`
- `gpt-4.1-mini`
- `gpt-4.1-nano`

---

### 7. Together AI

Signup credits ($25-$100). Not permanently free.

**Get your key:**
1. Go to [https://api.together.ai/settings/api-keys](https://api.together.ai/settings/api-keys)
2. Sign up (get free credits)
3. Create a key

**Add to gemi:**
```bash
gemi key add together --key ...your_key
```

**Available models:**
- `meta-llama/Llama-3.3-70B-Instruct-Turbo` (default)
- `deepseek-ai/DeepSeek-R1`
- `Qwen/Qwen2.5-Coder-32B-Instruct`

---

### 8. Cerebras (Fast & Free)

Fast inference with free tier.

**Get your key:**
1. Go to [https://cloud.cerebras.ai/](https://cloud.cerebras.ai/)
2. Sign up (free)
3. Create a key (starts with `csk-...`)

**Add to gemi:**
```bash
gemi key add cerebras --key csk-...your_key
```

**Available models:**
- `llama-3.3-70b` (default)
- `llama-4-scout-17b-16e-instruct`

---

### 9. Ollama (Local / Unlimited)

Runs on your machine. No key, no limits, no internet needed.

**Install:**
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull qwen3
ollama serve
```

**No key needed — gemi auto-detects Ollama.**

**Best models for coding agents (tool calling support):**

| Model | Size | Tool Calling | Notes |
|---|---|---|---|
| qwen3 | 8B-72B | Excellent | Most reliable |
| gemma4 | 9B-27B | Good | Also supports vision |
| mistral-small | 24B | Strong | Native function calling |
| llama3.3 | 70B | Decent | General purpose |
| deepseek-v3.2 | 236B | Good | Needs 64GB+ RAM |

---

## Free Tier Rate Limits (Per Model)

Every free model available through gemi, with exact limits.

### Google Gemini

No credit card required. Limits are per-project. Resets at midnight PT.

| Model ID | RPM | RPD | TPM | Context | Max Output |
|---|---|---|---|---|---|
| `gemini-2.5-flash` | 10 | 250 | 250,000 | 1,048,576 | 65,536 |
| `gemini-2.5-flash-lite` | 15 | 1,000 | 250,000 | 1,048,576 | 65,536 |
| `gemini-2.5-pro` | 5 | 100 | 250,000 | 1,048,576 | 65,536 |

### Groq

No credit card required. Limits are per-org, per-model.

| Model ID | RPM | RPD | TPM | Context | Max Output |
|---|---|---|---|---|---|
| `llama-3.3-70b-versatile` | 30 | 1,000 | 12,000 | 131,072 | 32,768 |
| `llama-3.1-8b-instant` | 30 | 14,400 | 6,000 | 131,072 | 131,072 |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 30 | 1,000 | 30,000 | 131,072 | 32,768 |
| `openai/gpt-oss-120b` | 30 | 1,000 | 8,000 | 131,072 | 65,536 |
| `openai/gpt-oss-20b` | 30 | 1,000 | 8,000 | 131,072 | 65,536 |
| `qwen/qwen3-32b` | 60 | 1,000 | 6,000 | 131,072 | 32,768 |
| `allam-2-7b` | 30 | 7,000 | 6,000 | 131,072 | 8,192 |

### OpenRouter (Free Models)

One API key works with all models. Free model IDs end with `:free`. No credit card required.

**Global limits:** 20 RPM. 50 RPD without credits, 1,000 RPD with $10+ credits purchased.

| Model ID | Context |
|---|---|
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1,000,000 |
| `nvidia/nemotron-3-super-120b-a12b:free` | 1,000,000 |
| `qwen/qwen3-coder:free` | 1,000,000 |
| `openai/gpt-oss-120b:free` | 131,072 |
| `openai/gpt-oss-20b:free` | 131,072 |
| `google/gemma-4-31b-it:free` | 262,144 |
| `google/gemma-4-26b-a4b-it:free` | 262,144 |
| `qwen/qwen3-next-80b-a3b-instruct:free` | 262,144 |
| `moonshotai/kimi-k2.6:free` | 262,144 |
| `meta-llama/llama-3.3-70b-instruct:free` | 131,072 |
| `nousresearch/hermes-3-llama-3.1-405b:free` | 131,072 |
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256,000 |
| `poolside/laguna-m.1:free` | 262,144 |
| `z-ai/glm-4.5-air:free` | 131,072 |
| `liquid/lfm-2.5-1.2b-thinking:free` | 33,000 |

> 27+ free models available. Use `gemi model <model-id>` to switch. TPM and max output depend on upstream provider.

### Mistral AI

Phone verification required. No credit card. All models accessible.

| Metric | Limit |
|---|---|
| RPM | 2 |
| TPM | 500,000 |
| Tokens/Month | 1,000,000,000 (1 billion) |

| Model ID | Context |
|---|---|
| `codestral-2508` | 256,000 |
| `mistral-large-2512` | 256,000 |
| `mistral-small-2603` | 262,000 |
| `devstral-2-2512` | 256,000 |
| `pixtral-large-latest` | 128,000 |
| `ministral-3-8b-2512` | 128,000 |

> 2 RPM is very slow for interactive coding. Best as a high-capacity fallback — 1B tokens/month is the largest free budget.

### Cerebras

No credit card required. Extremely fast inference (~2,600 tokens/sec).

| Metric | Limit |
|---|---|
| RPM | 5-30 (varies by model) |
| TPM | 30,000-60,000 |
| Tokens/Day | 1,000,000 |
| Context (free tier) | 8,192 (128K on request) |

| Model ID | Notes |
|---|---|
| `llama-4-scout` | Best on Cerebras |
| `qwen3-32b` | Good for code |
| `deepseek-r1` | Reasoning model |
| `gpt-oss-120b` | Large general model |

> 8K default context on free tier is the main limitation. Request higher limits via their dashboard.

### Ollama (Local — No Limits)

Runs on your hardware. No API. No quotas. No internet.

| Model | Sizes | Tool Calling | Min RAM | Notes |
|---|---|---|---|---|
| `qwen3` / `qwen3.5` | 0.8B-122B | Excellent | 4GB-64GB | Most reliable for agents |
| `gemma4` | 12B, 26B, 31B | Good | 8GB-20GB | Multimodal + tools |
| `llama3.3` / `llama4-scout` | 8B-70B / 17B MoE | Decent | 8GB-40GB | Solid general purpose |
| `deepseek-v3.2` | 685B MoE | Good | 64GB+ | Best reasoning, heavy |
| `mistral-small` | 24B | Strong | 16GB | Native function calling |
| `nemotron-3-super` | 120B MoE | Excellent | 32GB+ | Agent-grade tool use |
| `glm-5` / `glm-4.7` | 40B / 30B | Good | 20GB | Optimized for agentic use |
| `minimax-m3` | 45B | Good | 24GB | Multimodal + tools |

> Start with `qwen3` 14B+ or `gemma4` 31B for reliable tool calling. Models under 8B tend to produce unreliable JSON.

### Summary: Best Free Models for Coding

| Use Case | Best Free Option | Why |
|---|---|---|
| Daily driver | Gemini 2.5 Flash | 1M context, 250 RPD, best quality/limit ratio |
| Fast responses | Groq Llama 3.3 70B | ~300 tokens/sec, 1,000 RPD |
| Largest free model | OpenRouter Nemotron Ultra 550B | 550B params, 1M context, free |
| Most requests/day | Groq Llama 3.1 8B | 14,400 RPD |
| Most tokens/month | Mistral (any model) | 1 billion tokens/month |
| Best code model | Mistral Codestral | Purpose-built for code, 256K context |
| Unlimited local | Ollama Qwen 3.5 | No limits, best tool calling |
| Fastest inference | Cerebras Llama 4 Scout | ~2,600 tokens/sec |

---

## Key Management

```bash
# Add keys (interactive or inline)
gemi key add gemini
gemi key add groq --key gsk_...
gemi key add deepseek --name main --key sk-...

# List all keys
gemi key list

# List keys for one provider
gemi key list gemini

# Check key health and usage
gemi key status

# Remove a key
gemi key remove gemini default

# See all available providers
gemi providers
```

Keys are encrypted and stored at `~/.gemi/keys.json`.

---

## Multi-Account Rotation

### Why

A single Gemini account gives ~500-1,500 requests/day. Each user message with tool calls burns ~4 API requests. You hit the limit in a few hours.

### How many accounts = how much coding

| Gemini Accounts | Requests/Day | Coding Time |
|---|---|---|
| 1 | ~500-1,500 | 2-4 hours |
| 3 | ~1,500-4,500 | 6-12 hours |
| 5 | ~2,500-7,500 | Full day |

**No limit on the number of keys per provider.**

### The "Never Pay" Setup

```bash
# Gemini (3 Google accounts)
gemi key add gemini --name acc1 --key AIzaSy...
gemi key add gemini --name acc2 --key AIzaSy...
gemi key add gemini --name acc3 --key AIzaSy...

# Groq (fast fallback)
gemi key add groq --key gsk_...

# Cerebras (another free option)
gemi key add cerebras --key csk-...

# OpenRouter (27+ free models)
gemi key add openrouter --key sk-or-...

# Ollama (unlimited local)
ollama pull qwen3
```

**Failover chain:**
```
gemini/acc1 → gemini/acc2 → gemini/acc3 → groq → cerebras → openrouter → mistral → ollama
```

All automatic. You never have to think about it.

### Rotation Strategies

```yaml
# ~/.gemi/config.yaml
rotation:
  strategy: failover       # Use key until rate-limited, then next
  # strategy: round-robin  # Alternate evenly across keys
  # strategy: least-used   # Pick freshest key each time
```

---

## Context & Account Switching

### Does context survive when switching?

**Yes. 100% preserved.**

Conversation history lives in gemi's RAM, not on any server. When a key or provider switches, the same full conversation is sent to the new endpoint.

```
You: "Fix the bug in auth.py"
  ├─ gemini/acc1 → reads auth.py        OK
  ├─ gemini/acc1 → edits auth.py        OK
  ├─ gemini/acc1 → 429 RATE LIMITED
  │
  │   Rate limited on gemini/acc1, rotating...
  │   Switched to gemini/acc2
  │
  ├─ gemini/acc2 → runs tests           OK (full context preserved)
  └─ Done!
```

### Context window differences

When switching to a smaller model, gemi auto-trims old messages to fit. Recent messages are always kept.

| Provider | Context Window |
|---|---|
| Gemini 2.5 Flash/Pro | 1,000,000 tokens |
| Groq / DeepSeek / Mistral / OpenAI | 128,000 tokens |
| Ollama (qwen3) | 32,768 tokens |

---

## Commands Reference

### CLI Commands (Terminal)

These commands are run directly in your terminal (outside of a gemi session).

---

#### `gemi`

Start an interactive coding agent session in the current directory.

```bash
gemi
```

**Flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--resume <id>` | `-r <id>` | Resume a previously saved session by its ID |

**Examples:**

```bash
gemi                        # Start a new session in current directory
gemi --resume c99f3b33      # Resume session c99f3b33
gemi -r c99f3b33            # Same thing, short form
cd ~/projects/myapp && gemi # Start gemi inside a specific project
```

---

#### `gemi key add <provider>`

Add an API key for a provider. If no `--key` flag is given, prompts interactively (input is hidden).

```bash
gemi key add <provider> [--name <label>] [--key <api_key>]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `provider` | Yes | One of: `gemini`, `groq`, `deepseek`, `openrouter`, `mistral`, `openai`, `together`, `cerebras`, `ollama` |

**Flags:**

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--name <label>` | `-n <label>` | `default` | Label for this key (use for multi-account: `acc1`, `acc2`, etc.) |
| `--key <api_key>` | `-k <api_key>` | *(interactive)* | Pass API key inline (skips interactive prompt) |

**Examples:**

```bash
# Interactive — prompts for key securely
gemi key add gemini
gemi key add gemini --name acc1
gemi key add gemini --name acc2
gemi key add groq --name personal

# Inline — useful for scripts
gemi key add gemini --name acc1 --key AIzaSy...
gemi key add groq -n work -k gsk_...
```

---

#### `gemi key list [provider]`

List all stored API keys (shows provider, label, and date added).

```bash
gemi key list             # List all keys
gemi key list gemini      # List only Gemini keys
```

**Output:**

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

#### `gemi key remove <provider> <name>`

Remove a stored API key by provider and label.

```bash
gemi key remove gemini acc2
gemi key remove groq default
```

---

#### `gemi key status`

Show the health and usage of all keys — which is active, which is on cooldown, and request/token counts.

```bash
gemi key status
```

**Output:**

```
┌──────────┬─────────┬──────────┬──────────┬────────┐
│ Provider │ Name    │ State    │ Requests │ Tokens │
├──────────┼─────────┼──────────┼──────────┼────────┤
│ gemini   │ acc1    │ active   │ 12       │ 4500   │
│ gemini   │ acc2    │ standby  │ 0        │ 0      │
│ groq     │ default │ standby  │ 0        │ 0      │
│ ollama   │ local   │ standby  │ 0        │ 0      │
└──────────┴─────────┴──────────┴──────────┴────────┘
```

**States:** `active` (currently in use), `standby` (ready as backup), `cooldown (Xs)` (rate limited, waiting), `exhausted` (all retries spent)

---

#### `gemi model [name]`

Show or change the default model.

```bash
gemi model                  # Show current model + all available models per provider
gemi model gemini-2.5-pro   # Set default model to gemini-2.5-pro
```

---

#### `gemi providers`

Show a table of all 9 supported providers with their status, default model, free tier, and key URL.

```bash
gemi providers
```

---

#### `gemi sessions`

List all saved sessions (up to 10 most recent).

```bash
gemi sessions
```

**Output:**

```
┌──────────┬──────────┬──────────────────────────────┬──────────────────────────────────┐
│ ID       │ Messages │ Directory                    │ Preview                          │
├──────────┼──────────┼──────────────────────────────┼──────────────────────────────────┤
│ c99f3b33 │ 8        │ /Users/you/projects/myapp    │ help me fix the login bug...     │
│ 74b1076c │ 3        │ /Users/you/projects/blog     │ hey                              │
└──────────┴──────────┴──────────────────────────────┴──────────────────────────────────┘
```

Resume with: `gemi --resume c99f3b33`

---

#### `gemi config`

Show the current configuration (YAML format).

```bash
gemi config
```

---

#### `gemi config set <key> <value>`

Update a config value. Supports dot notation for nested keys.

```bash
gemi config set default_model gemini-2.5-pro
gemi config set default_provider groq
gemi config set agent.auto_approve_writes true
gemi config set agent.max_iterations 30
gemi config set rotation.strategy round-robin
```

**All config keys:**

| Key | Default | Description |
|-----|---------|-------------|
| `default_provider` | `gemini` | Provider used on startup |
| `default_model` | `gemini-2.5-flash` | Model used on startup |
| `rotation.strategy` | `failover` | Key rotation strategy (`failover`, `round-robin`, `least-used`) |
| `rotation.auto_switch_provider` | `true` | Auto-failover to next provider when all keys exhausted |
| `rotation.provider_priority` | *(see below)* | Order of provider failover |
| `agent.max_iterations` | `50` | Max tool-call loops per message |
| `agent.auto_approve_reads` | `true` | Auto-approve read-only tools (read_file, list_directory, etc.) |
| `agent.auto_approve_writes` | `false` | Auto-approve write tools (write_file, edit_file, run_command, etc.) |

**Default provider priority:**
`gemini` > `groq` > `deepseek` > `openrouter` > `cerebras` > `mistral` > `together` > `openai` > `ollama`

Config file location: `~/.gemi/config.yaml`

---

### In-Session Commands (Inside gemi)

These commands are used during an active gemi session (after running `gemi`). All start with `/`.

---

#### `/help`

Show a quick reference panel of all in-session commands.

---

#### `/status`

Show the key rotation table (all keys with their state) plus a summary line with current provider, model, tokens, and context usage.

---

#### `/tokens`

Show detailed token and session stats:

```
  Provider:  gemini
  Model:     gemini-2.5-flash
  Tokens:    ~500 / 1,000,000
  Context:   1,200 / 1,000,000 (0%)
  Requests:  3
  Keys:      2 active / 3 total
  Session:   c99f3b33
```

---

#### `/model <name>`

Switch the model mid-session without restarting.

```
/model gemini-2.5-pro
/model llama-3.3-70b-versatile
```

If run without a name, shows the current model.

---

#### `/undo`

Undo the last file edit made by the agent. Restores the file to its state before the edit.

---

#### `/sessions`

List saved sessions (same as `gemi sessions` from terminal).

---

#### `/clear`

Clear the conversation history and reset token/request counters. Keeps the system prompt.

---

#### `/quit` `/exit` `/q`

Exit the gemi session. Session is auto-saved before exit.

---

### Agent Tools

These are the tools the AI agent uses internally to interact with your codebase. You don't call these directly — the agent decides when to use them based on your request.

#### Read-Only Tools (auto-approved)

| Tool | Description | Example Use |
|------|-------------|-------------|
| `read_file(path)` | Read file contents with line numbers | "Read my package.json" |
| `list_directory(path)` | List files and folders in a directory | "What files are in src/" |
| `search_files(pattern, path)` | Grep for text across files (like `grep -rn`) | "Find where login() is used" |
| `find_files(pattern)` | Find files matching a glob pattern | "Find all .tsx files" |
| `git_status()` | Show modified, staged, and untracked files | "What's changed?" |
| `git_diff(ref, staged)` | Show diff of changes | "Show me the diff" |
| `git_log(count)` | Show recent commit history | "Show last 5 commits" |
| `git_branch(action)` | List, create, or switch branches | "What branch am I on?" |

#### Write Tools (require approval unless `auto_approve_writes` is `true`)

| Tool | Description | Example Use |
|------|-------------|-------------|
| `write_file(path, content)` | Create or overwrite a file | "Create a new utils.py" |
| `edit_file(path, old_text, new_text)` | Find-and-replace in a file (exact match) | "Change the function name" |
| `run_command(command)` | Execute a shell command (60s timeout) | "Run the tests" |
| `git_commit(message, files)` | Stage files and create a commit | "Commit these changes" |

Write tools show you what they're about to do and ask for confirmation before executing. Read-only tools run silently in the background.

---

## Features

### Core Agent
- Interactive terminal with streaming responses
- Markdown rendering with syntax highlighting
- ReAct agent loop (think, act, observe)
- Up to 50 tool-call iterations per message

### Tools (12 total)

| Tool | Description |
|---|---|
| `read_file` | Read file with line numbers |
| `write_file` | Create or overwrite file |
| `edit_file` | Find-and-replace with diff view |
| `run_command` | Execute shell commands |
| `list_directory` | List files and folders |
| `search_files` | Grep for patterns |
| `find_files` | Glob pattern matching |
| `git_status` | Modified/staged/untracked files |
| `git_diff` | View diffs |
| `git_log` | Commit history |
| `git_commit` | Stage and commit |
| `git_branch` | List/create/switch branches |

### Key Rotation & Failover
- 9 pre-configured providers (zero URL config)
- Unlimited keys per provider
- Auto-rotation on rate limit (429)
- Auto-failover across providers
- Encrypted key storage
- Per-key usage tracking
- 3 rotation strategies (failover, round-robin, least-used)

### Session Management
- Auto-save after every message
- Resume with `gemi --resume <id>`
- Full message history, metadata, token count

### Context Management
- Auto-compaction at 75% context usage
- Auto-trim on provider switch
- Summary of trimmed messages preserved

### Token Tracking
- Per-session token and request count
- Context usage percentage
- Status line: `gemini/gemini-2.5-flash | tokens: ~1,234 | reqs: 5 | context: 12%`

### Safety
- Diff view on every edit
- `/undo` to revert last edit
- User confirmation for writes and commands
- Configurable auto-approve settings

### Project Context
- `.gemi.md` file — project-specific instructions loaded on startup

---

## Configuration

Config file: `~/.gemi/config.yaml`

```yaml
default_provider: gemini
default_model: gemini-2.5-flash

rotation:
  strategy: failover
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
  auto_approve_writes: false
```

```bash
gemi config set default_model gemini-2.5-pro
gemi config set default_provider groq
gemi config set agent.auto_approve_writes true
gemi config set rotation.strategy round-robin
```

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

gemi reads this on startup and understands your project immediately.

---

## Sessions

```bash
gemi                       # auto-generates session ID
gemi sessions              # list saved sessions
gemi --resume a3f8b2c1     # resume a session
```

Stored at `~/.gemi/sessions/` as JSON.

---

## Roadmap

### Built (v0.1.0)

- [x] 12 agent tools (files, git, shell, search)
- [x] 9 pre-configured providers (zero-config)
- [x] Multi-account key rotation
- [x] Multi-provider failover
- [x] Session persistence and resume
- [x] Context compaction
- [x] Token tracking
- [x] Diff view + undo
- [x] `.gemi.md` project context
- [x] Encrypted key storage

### Planned — Tier 2

- [ ] Permission system (granular allow/deny per tool)
- [ ] Tab completion (commands, file paths, models)
- [ ] Live status bar (provider, model, tokens, key health)
- [ ] Multi-line input (paste code blocks)
- [ ] Auto-retry on malformed responses
- [ ] Image/screenshot reading (Gemini vision)

### Planned — Tier 3

- [ ] Web search
- [ ] Memory system (cross-session preferences)
- [ ] Plan mode (explore before coding)
- [ ] Subagents (parallel file reading)
- [ ] MCP server support
- [ ] Code review mode
- [ ] VS Code extension
