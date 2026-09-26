"""Project-local Inquilab runtime configuration."""

OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
OLLAMA_SMALL_MODEL = "tinyllama:latest"
OLLAMA_LARGE_MODEL = "llama3.2:latest"
# Optional model used only to prepare video shot directions.
OLLAMA_VIDEO_MODEL = ""
# Fully downloaded local Diffusers text-to-image model directory.
INQUILAB_IMAGE_MODEL_PATH = ""
# Optional Hugging Face Inference API model used before local/offline rendering.
HF_IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
OLLAMA_TEMPERATURE = 0.0
OLLAMA_TIMEOUT = 45
OLLAMA_WARMUP_TIMEOUT = 60