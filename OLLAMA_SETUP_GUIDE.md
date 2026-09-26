# Ollama Integration Guide for Inquilab

This guide will help you get Ollama connected and working with your Inquilab agent.

## What is Ollama?

Ollama is a tool for running large language models (LLMs) locally on your machine. It's completely private, fast, and doesn't require internet connectivity for inference.

**Key Features:**
- 🚀 Run LLMs locally without API calls
- 🔒 100% private - no data sent to cloud services
- ⚡ Fast inference on your hardware
- 📦 Easy model management
- 🛠️ Simple HTTP API

## Quick Start

### Step 1: Install Ollama

#### Windows
1. Download: https://ollama.ai/download/windows
2. Run the installer (Ollama-windows-amd64.exe)
3. Follow installation prompts
4. Restart your terminal/IDE
5. Ollama will automatically start as a background service

#### macOS
```bash
# Using direct download
https://ollama.ai/download/mac

# Or with Homebrew
brew install ollama
```

#### Linux
```bash
curl https://ollama.ai/install.sh | sh
```

### Step 2: Verify Installation

```bash
# Check Ollama version
ollama --version

# Start Ollama (if not auto-started)
ollama serve
```

You should see:
```
connecting to the ollama app...
```

Ollama will now be available at: **http://localhost:11434**

### Step 3: Pull a Model

Choose a model based on your hardware:

```bash
# Fast & lightweight (7B models - good starting point)
ollama pull mistral:7b
ollama pull llama2:7b
ollama pull qwen2.5:7b

# More capable but heavier (12-13B models)
ollama pull neural-chat:7b
ollama pull llama3:7b
ollama pull wizard-math:7b

# Very capable (but needs more VRAM)
ollama pull llama3.2:latest
ollama pull mistral:large
```

**Recommended for beginners:** `mistral:7b` (4GB, balanced speed/quality)

### Step 4: Verify Connection

Run the diagnostic tool:

```bash
python ollama_setup.py
```

This will:
- ✅ Check if Ollama is installed
- ✅ Verify Ollama is running
- ✅ List available models
- ✅ Test model connection
- ✅ Show your configuration

## Configuration

### Using Environment Variables

You can customize Ollama connection without editing code:

```bash
# Windows (PowerShell)
$env:OLLAMA_HOST = "localhost"
$env:OLLAMA_PORT = "11434"
$env:OLLAMA_SMALL_MODEL = "tinyllama"
$env:OLLAMA_LARGE_MODEL = "mistral:7b"
$env:OLLAMA_VIDEO_MODEL = "llava:latest"
python agent.py

# Or in command prompt
set OLLAMA_HOST=localhost
set OLLAMA_PORT=11434
set OLLAMA_SMALL_MODEL=tinyllama
set OLLAMA_LARGE_MODEL=mistral:7b
set OLLAMA_VIDEO_MODEL=llava:latest
python agent.py

# macOS/Linux (Bash)
export OLLAMA_HOST=localhost
export OLLAMA_PORT=11434
export OLLAMA_SMALL_MODEL=tinyllama
export OLLAMA_LARGE_MODEL=mistral:7b
export OLLAMA_VIDEO_MODEL=llava:latest
```

`OLLAMA_VIDEO_MODEL` is optional. When set, the model creates concise shot
directions for video rendering; it is kept separate from the small loading
model and the large problem-solving model. If it is unset or unavailable,
video generation continues with the built-in offline renderer.

For editing an existing video, the same model returns a constrained edit plan
(trim, speed, and a visual filter). FFmpeg applies that plan to the source
video and exports an MP4. The desktop Studio accepts a source video path and
an edit request under **Edit and export MP4**.
```

### Using Python Code

```python
from ollama_connector import OllamaConnector

# Custom configuration
ollama = OllamaConnector(
    host="localhost",
    port=11434,
    model="mistral:7b",
    temperature=0.0,
    timeout=30
)

# Verify connection
if ollama.verify_connection():
    print("✅ Connected!")
else:
    print("❌ Connection failed!")

# Get available models
models = ollama.get_available_models()
print(f"Available models: {models}")

# Send a message
response = ollama.chat([
    {"role": "user", "content": "Hello!"}
])
print(response)
```

## Using Ollama with Inquilab

### Method 1: Run Inquilab with Default Settings

```bash
python agent.py
```

This uses:
- Host: localhost
- Port: 11434
- Small loading model: tinyllama (or your configured OLLAMA_SMALL_MODEL)
- Large working model: tinyllama (or your configured OLLAMA_LARGE_MODEL)

By default, tinyllama is used for agent responses. Set OLLAMA_LARGE_MODEL to a
larger installed model when you need higher-quality output.
Install the warm-up model once with:

```bash
ollama pull tinyllama
```

### Method 2: Run with Custom Model

```bash
# Windows
set OLLAMA_LARGE_MODEL=mistral:7b
python agent.py

# macOS/Linux
OLLAMA_MODEL=mistral:7b python agent.py
```

### Method 3: Direct Usage in Python

```python
from ollama_connector import OllamaConnector

ollama = OllamaConnector(
    small_model="tinyllama",
    large_model="mistral:7b",
)
response = ollama.chat([
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is 2+2?"}
])
print(response)
```

## Model Recommendations

### By Hardware Tier

**Low-end (4GB VRAM)**
- `mistral:7b` (4.0 GB) - Best balanced option
- `llama2:7b` (3.8 GB) - Good quality
- `phi:2.7b` (1.6 GB) - Smallest, but lower quality

**Mid-range (8GB VRAM)**
- `neural-chat:7b` (4.8 GB)
- `qwen2.5:7b` (3.8 GB)
- `mistral:medium` (~6 GB)

**High-end (12GB+ VRAM)**
- `llama3:7b` (4.2 GB)
- `llama3.2:latest` (6 GB)
- `wizard-math:7b` (4 GB)
- `mistral:large` (26 GB)

### By Use Case

**General Purpose (Best for Inquilab)**
- `mistral:7b` ⭐ Recommended
- `llama2:7b`
- `neural-chat:7b`

**Coding**
- `codellama:7b`
- `wizard-math:7b`

**Fast Responses**
- `phi:2.7b`
- `mistral:7b`

**Highest Quality**
- `llama3:8b`
- `mistral:large`

## Troubleshooting

### Problem: "Could not connect to Ollama at http://localhost:11434"

**Solution:**
```bash
# 1. Check if Ollama is running
# Windows: Check System Tray or run
ollama serve

# macOS: Check Applications or run
open /Applications/Ollama.app

# Linux: Run
ollama serve

# 2. Verify Ollama is listening
curl http://localhost:11434/api/tags

# 3. If port 11434 is in use, change OLLAMA_PORT
set OLLAMA_PORT=11435
```

### Problem: "Model 'llama3.2' not found"

**Solution:**
```bash
# Pull the model first
ollama pull llama3.2

# Or use a different model
set OLLAMA_MODEL=mistral:7b
python agent.py

# List available models
ollama list
```

### Problem: "Request timed out"

**Solution:**
- Model is taking too long to respond
- Increase timeout: `OllamaConnector(timeout=60)`
- Switch to a smaller model: `ollama pull mistral:7b`
- Check system resources (RAM, CPU)

### Problem: "Out of memory" errors

**Solution:**
```bash
# Switch to a smaller model
ollama pull phi:2.7b    # Smallest (1.6 GB)
ollama pull mistral:7b  # Lightweight (4.0 GB)

# Or free up system RAM
# Close other applications
```

### Problem: Very slow responses

**Solution:**
- Check system resources (Run: `nvidia-smi` for GPU status)
- Enable GPU acceleration (see below)
- Use a smaller model
- Increase system RAM/swap

## GPU Acceleration

By default, Ollama uses CPU. For faster inference, enable GPU:

### NVIDIA GPU (CUDA)

**Windows:**
1. Download NVIDIA CUDA Toolkit
2. Download cuDNN
3. Ollama will auto-detect GPU

```bash
# Verify GPU is being used
# Check output for "using metal" or "using cuda"
ollama serve
```

### macOS (Metal)

No extra steps needed! Metal acceleration works automatically on Apple Silicon Macs.

### AMD GPU (ROCm)

```bash
# Install AMD ROCm
# Then run
ollama serve
```

## API Reference

### OllamaConnector Class

```python
from ollama_connector import OllamaConnector

# Initialize
ollama = OllamaConnector(
    host="localhost",
    port=11434,
    model="llama3.2",
    temperature=0.0,
    timeout=30
)

# Check connection
ollama.verify_connection()  # Returns: bool

# Get available models
ollama.get_available_models()  # Returns: List[str]

# Pull a model
ollama.pull_model("mistral:7b")  # Returns: bool

# Chat with model
response = ollama.chat([
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
])  # Returns: str or None

# Stream chat responses
for chunk in ollama.chat_streaming(messages):
    print(chunk, end="", flush=True)

# Generate from prompt
response = ollama.generate("Tell me a joke")  # Returns: str or None

# Get status
status = ollama.get_status()  # Returns: Dict with connection info
```

## Common Commands

```bash
# List all installed models
ollama list

# Show model details
ollama show llama3.2

# Delete a model to free space
ollama rm llama3.2

# Run model in interactive mode
ollama run mistral:7b

# Check version
ollama --version

# See logs
ollama logs
```

## Performance Tips

1. **Choose the right model size for your hardware**
   - 4GB VRAM: 7B models max
   - 8GB VRAM: 13B models
   - 16GB+ VRAM: 30B+ models

2. **Pre-warm the model** (load it into memory before requests)
   - First request is slower as model loads
   - Subsequent requests are faster

3. **Adjust temperature** based on use case
   - `temperature=0.0`: Deterministic (best for reasoning/tools)
   - `temperature=0.7`: More creative
   - `temperature=1.0`: Maximum randomness

4. **Monitor system resources**
   - Windows Task Manager
   - macOS Activity Monitor
   - Linux: `top` or `htop`

## Next Steps

1. ✅ Install Ollama from https://ollama.ai
2. ✅ Run `ollama pull mistral:7b`
3. ✅ Run `python ollama_setup.py`
4. ✅ Run `python agent.py`

## Additional Resources

- **Ollama Website**: https://ollama.ai
- **Model Library**: https://ollama.ai/library
- **GitHub**: https://github.com/ollama/ollama
- **Documentation**: https://github.com/ollama/ollama/blob/main/README.md

## Support

If you encounter issues:

1. Run the diagnostic: `python ollama_setup.py`
2. Check Ollama logs: `ollama logs` (macOS/Linux)
3. Restart Ollama service
4. Check GitHub issues: https://github.com/ollama/ollama/issues

---

Happy coding with Ollama! 🚀
