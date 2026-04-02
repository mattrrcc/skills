---
name: ollama
description: "Launch and configure Ollama to run local LLMs (default: qwen3.5) and integrate them with Claude Code or other tools. TRIGGER when: user wants to run models locally with Ollama, asks about qwen3.5, or wants to use an Ollama-served model as a Claude Code backend."
license: Complete terms in LICENSE.txt
---

# Ollama Local Model Launcher

This skill helps you install Ollama, pull models (default: `qwen3.5`), start the server, and wire it into Claude Code or any OpenAI-compatible client.

---

## Quick Start

### 1. Install Ollama

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS (Homebrew):**
```bash
brew install ollama
```

**Windows:** Download the installer from https://ollama.com/download

---

### 2. Start the Ollama server

```bash
ollama serve
```

This starts the server at `http://localhost:11434`. Keep this terminal open, or run it as a background service.

**macOS background service:**
```bash
brew services start ollama
```

**Linux systemd service:**
```bash
sudo systemctl enable --now ollama
```

---

### 3. Pull and run qwen3.5

```bash
# Pull the model (downloads once, ~2–5 GB depending on variant)
ollama pull qwen3.5

# Run interactively in the terminal
ollama run qwen3.5
```

**Available qwen3.5 variants** (specify with the tag):

| Tag | Size | Use case |
|-----|------|----------|
| `qwen3.5` | Default (1.7B) | Fast, low-resource |
| `qwen3.5:7b` | 7B | Balanced quality/speed |
| `qwen3.5:14b` | 14B | Higher quality |
| `qwen3.5:32b` | 32B | Best quality, needs ~20 GB RAM |

Example with a specific variant:
```bash
ollama pull qwen3.5:7b
ollama run qwen3.5:7b
```

---

### 4. Verify the server is running

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON list of installed models including `qwen3.5`.

---

## Using Ollama with Claude Code

Claude Code supports custom OpenAI-compatible API endpoints. Point it at your local Ollama server:

```bash
ANTHROPIC_BASE_URL=http://localhost:11434/v1 \
ANTHROPIC_API_KEY=ollama \
claude --model qwen3.5
```

Or set these permanently in your shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
export ANTHROPIC_BASE_URL=http://localhost:11434/v1
export ANTHROPIC_API_KEY=ollama
```

Then launch Claude Code normally:
```bash
claude --model qwen3.5
```

> **Note:** Ollama's OpenAI-compatible endpoint is at `/v1`. The `ANTHROPIC_API_KEY` value can be any non-empty string when using Ollama locally — Ollama does not validate it.

---

## Using Ollama via OpenAI-Compatible API

Ollama exposes an OpenAI-compatible REST API. Use it from any tool or language:

### cURL

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Python (openai SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required by SDK, not validated by Ollama
)

response = client.chat.completions.create(
    model="qwen3.5",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### TypeScript (openai SDK)

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:11434/v1",
  apiKey: "ollama",
});

const response = await client.chat.completions.create({
  model: "qwen3.5",
  messages: [{ role: "user", content: "Hello!" }],
});
console.log(response.choices[0].message.content);
```

### Python (native Ollama SDK)

```python
import ollama

response = ollama.chat(
    model="qwen3.5",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response["message"]["content"])
```

Install the Ollama Python SDK:
```bash
pip install ollama
```

---

## Ollama CLI Reference

```bash
# List installed models
ollama list

# Pull a model
ollama pull qwen3.5

# Remove a model
ollama rm qwen3.5

# Show model info
ollama show qwen3.5

# Run interactively
ollama run qwen3.5

# Run with a single prompt (non-interactive)
ollama run qwen3.5 "Explain recursion in one sentence"

# Copy a model under a new name
ollama cp qwen3.5 my-qwen

# Push to Ollama registry (requires account)
ollama push <your-namespace>/qwen3.5
```

---

## Modelfile Customization

Create a custom variant of qwen3.5 with a system prompt and tuned parameters:

```dockerfile
# Modelfile
FROM qwen3.5

SYSTEM """
You are a concise coding assistant. Answer in plain text without markdown unless the user asks for code.
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
```

Build and run it:
```bash
ollama create my-coder -f Modelfile
ollama run my-coder
```

---

## Troubleshooting

**`ollama: command not found`**
The install script may not have updated your PATH. Try:
```bash
export PATH=$PATH:/usr/local/bin
```
Or restart your terminal.

**Port 11434 already in use**
Another process is using the port. Find and stop it:
```bash
lsof -i :11434
kill <PID>
```
Or run Ollama on a different port:
```bash
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

**Model pull is slow / stalls**
Ollama resumes interrupted downloads. If a pull stalls, press Ctrl+C and re-run `ollama pull qwen3.5`.

**Out of memory**
Try a smaller variant:
```bash
ollama pull qwen3.5        # 1.7B default — smallest
ollama pull qwen3.5:7b-q4  # 7B quantized — good balance
```

**Claude Code returns errors about the model**
Ensure the model name passed to `--model` exactly matches an installed model shown by `ollama list`. Model names are case-sensitive.

---

## Hardware Requirements

| Variant | Min RAM | Recommended |
|---------|---------|-------------|
| qwen3.5 (1.7B) | 4 GB | 8 GB |
| qwen3.5:7b | 8 GB | 16 GB |
| qwen3.5:14b | 16 GB | 32 GB |
| qwen3.5:32b | 32 GB | 64 GB |

GPU acceleration is used automatically when available (NVIDIA CUDA, Apple Metal, AMD ROCm).
