import contextlib
import io
import json
import math
import os
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps
import imageio_ffmpeg
import requests

try:
    import inquilab_config as saved_config
except ImportError:
    saved_config = None


_LOCAL_IMAGE_PIPELINE = None
_LOCAL_IMAGE_PIPELINE_PATH = None
_LOCAL_IMAGE_PIPELINE_FAILED = False


def _create_huggingface_image(prompt: str, style: str, mood: str, aspect: str, model: str = None):
    """Generate and decode a real image through the Hugging Face Inference API."""
    token = os.getenv("HF_TOKEN", os.getenv("HUGGINGFACEHUB_API_TOKEN", "")).strip()
    if not token:
        raise RuntimeError("Set HF_TOKEN or enter a Hugging Face access token to generate images.")

    model_name = (model or os.getenv(
        "HF_IMAGE_MODEL",
        getattr(saved_config, "HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0"),
    )).strip()
    if not model_name:
        raise RuntimeError("Choose a Hugging Face text-to-image model.")

    endpoint = f"https://router.huggingface.co/hf-inference/models/{model_name}"
    request_prompt = f"{prompt}, {style} style, {mood} mood, {aspect} composition"
    timeout = float(os.getenv("HF_IMAGE_TIMEOUT", "120"))
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {token}"},
        json={"inputs": request_prompt},
        timeout=timeout,
    )
    if response.status_code != 200:
        detail = response.text[:300].strip()
        raise RuntimeError(f"Hugging Face image generation failed ({response.status_code}): {detail}")

    try:
        image = Image.open(io.BytesIO(response.content))
        image.load()
        image = image.convert("RGB")
        return ImageOps.fit(image, _aspect_size(aspect), method=Image.Resampling.LANCZOS)
    except (OSError, ValueError) as error:
        raise RuntimeError("Hugging Face returned an invalid image response") from error


def _aspect_size(aspect: str):
    aspect_map = {
        "16:9 widescreen": (1280, 720),
        "1:1 square": (960, 960),
        "9:16 portrait": (720, 1280),
    }
    return aspect_map.get(aspect, (1280, 720))


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned[:40] or "prompt"


def _create_local_model_image(prompt: str, style: str, mood: str, aspect: str):
    """Use a model already stored on disk; never downloads or calls an API."""
    global _LOCAL_IMAGE_PIPELINE, _LOCAL_IMAGE_PIPELINE_PATH, _LOCAL_IMAGE_PIPELINE_FAILED

    model_path = os.getenv("INQUILAB_LOCAL_IMAGE_MODEL", "").strip()
    if not model_path or not Path(model_path).is_dir() or _LOCAL_IMAGE_PIPELINE_FAILED:
        return None

    try:
        if _LOCAL_IMAGE_PIPELINE is None or _LOCAL_IMAGE_PIPELINE_PATH != model_path:
            import torch
            from diffusers import AutoPipelineForText2Image

            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32
            _LOCAL_IMAGE_PIPELINE = AutoPipelineForText2Image.from_pretrained(
                model_path,
                torch_dtype=dtype,
                local_files_only=True,
            ).to(device)
            _LOCAL_IMAGE_PIPELINE_PATH = model_path

        width, height = _aspect_size(aspect)
        result = _LOCAL_IMAGE_PIPELINE(
            prompt=f"{prompt}, {style} style, {mood} mood",
            negative_prompt="blurry, distorted, low quality, watermark, text",
            width=width,
            height=height,
            num_inference_steps=int(os.getenv("INQUILAB_IMAGE_STEPS", "25")),
        )
        return result.images[0].convert("RGB")
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f"Offline image model unavailable; using built-in renderer: {error}")
        _LOCAL_IMAGE_PIPELINE_FAILED = True
        return None


def _render_image(prompt: str, style: str, mood: str, aspect: str, image_provider: str = "auto", image_model: str = None):
    if image_provider not in {"auto", "huggingface", "local"}:
        raise ValueError(f"Unsupported image provider: {image_provider}")

    if image_provider in {"auto", "huggingface"}:
        try:
            image = _create_huggingface_image(prompt, style, mood, aspect, image_model)
            if image is not None:
                return image
            if image_provider == "huggingface":
                raise RuntimeError("Set HF_TOKEN to use Hugging Face image generation.")
        except (OSError, requests.RequestException, RuntimeError, ValueError) as error:
            if image_provider == "huggingface":
                raise RuntimeError(f"Hugging Face image generation failed: {error}") from error
            print(f"Hugging Face image model unavailable; trying a configured local model: {error}")

    local_image = _create_local_model_image(prompt, style, mood, aspect)
    if local_image is not None:
        return local_image
    raise RuntimeError(
        "No real image model is available. Set HF_TOKEN and select Hugging Face, "
        "or configure INQUILAB_LOCAL_IMAGE_MODEL with a downloaded Diffusers model."
    )


def _prepare_video_prompt(prompt: str, style: str, mood: str, aspect: str) -> str:
    """Use the optional video model for shot direction without changing offline rendering."""
    video_model = os.getenv("OLLAMA_VIDEO_MODEL", "").strip()
    if not video_model:
        return prompt

    try:
        from ollama_connector import OllamaConnector

        connector = OllamaConnector(model=video_model)
        direction_request = (
            "Create a concise visual shot direction for this video prompt. "
            "Return only the shot direction, with camera movement, subject motion, "
            f"lighting, and pacing: {prompt}. Style: {style}. Mood: {mood}. Aspect: {aspect}."
        )
        with contextlib.redirect_stdout(io.StringIO()):
            direction = connector.generate(direction_request)
        if direction and direction.strip():
            return f"{prompt}. Shot direction: {direction.strip()}"
    except Exception:
        pass
    return prompt


def _video_edit_plan(prompt: str) -> dict:
    """Ask the dedicated video model for bounded FFmpeg edit instructions."""
    default_plan = {"start_seconds": 0, "end_seconds": None, "speed": 1, "filter": "none"}
    video_model = os.getenv("OLLAMA_VIDEO_MODEL", "").strip()
    if not video_model:
        return default_plan

    try:
        from ollama_connector import OllamaConnector

        request = (
            "Return only valid JSON for editing a video. Use exactly these keys: "
            "start_seconds (number >= 0), end_seconds (number or null), "
            "speed (one of 0.5, 1, 1.5, 2), filter (one of none, grayscale, "
            f"negate, sepia). User edit request: {prompt}"
        )
        connector = OllamaConnector(model=video_model)
        with contextlib.redirect_stdout(io.StringIO()):
            response = connector.generate(request)
        plan = json.loads(response or "")
        if not isinstance(plan, dict):
            return default_plan
        return {
            "start_seconds": max(0, float(plan.get("start_seconds", 0))),
            "end_seconds": (
                max(0, float(plan["end_seconds"]))
                if plan.get("end_seconds") is not None else None
            ),
            "speed": float(plan.get("speed", 1)) if float(plan.get("speed", 1)) in {0.5, 1, 1.5, 2} else 1,
            "filter": plan.get("filter") if plan.get("filter") in {"none", "grayscale", "negate", "sepia"} else "none",
        }
    except (ValueError, TypeError, json.JSONDecodeError, ImportError, OSError, RuntimeError):
        return default_plan


def edit_video(
    source_video: str,
    edit_prompt: str,
    output_dir: str = "generated_media",
    start_seconds: float = None,
    end_seconds: float = None,
    speed: float = None,
    video_filter: str = None,
):
    """Apply a model-selected edit to an existing video and export an MP4."""
    source_path = Path(source_video).expanduser()
    if not source_path.is_file():
        raise FileNotFoundError(f"Source video was not found: {source_video}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    safe_name = _slugify(edit_prompt or source_path.stem)
    exported_path = output_path / f"edited-{safe_name}-{uuid4().hex[:8]}.mp4"
    plan = _video_edit_plan(edit_prompt or "make a clean export")
    if start_seconds is not None:
        plan["start_seconds"] = float(start_seconds)
    if end_seconds is not None:
        plan["end_seconds"] = float(end_seconds)
    if speed is not None:
        plan["speed"] = float(speed)
    if video_filter is not None:
        plan["filter"] = video_filter

    if not math.isfinite(plan["start_seconds"]) or plan["start_seconds"] < 0:
        raise ValueError("Start time must be a finite number greater than or equal to zero")
    if plan["end_seconds"] is not None and (
        not math.isfinite(plan["end_seconds"]) or plan["end_seconds"] <= plan["start_seconds"]
    ):
        raise ValueError("End time must be greater than the start time")
    if plan["speed"] not in {0.5, 1, 1.5, 2}:
        raise ValueError("Speed must be one of 0.5, 1, 1.5, or 2")
    if plan["filter"] not in {"none", "grayscale", "negate", "sepia"}:
        raise ValueError("Unsupported video filter")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    video_filters = []
    if plan["speed"] != 1:
        video_filters.append(f"setpts={1 / plan['speed']:.6f}*PTS")
    video_filters.extend({
        "grayscale": "hue=s=0",
        "negate": "negate",
        "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    }.get(plan["filter"], "") for _ in [0])
    video_filters = [item for item in video_filters if item]
    command = [ffmpeg, "-y", "-i", str(source_path)]
    if plan["start_seconds"]:
        command.extend(["-ss", str(plan["start_seconds"])])
    if plan["end_seconds"] is not None and plan["end_seconds"] > plan["start_seconds"]:
        command.extend(["-t", str(plan["end_seconds"] - plan["start_seconds"])])
    if video_filters:
        command.extend(["-vf", ",".join(video_filters)])
    if plan["speed"] != 1:
        command.extend(["-af", f"atempo={plan['speed']:.6f}"])
    command.extend(["-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(exported_path)])
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"FFmpeg could not export video: {error}")
    if not exported_path.is_file() or exported_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg completed without producing an edited video")
    return {
        "source_video": str(source_path),
        "video_path": str(exported_path),
        "edit_prompt": edit_prompt,
        "video_model": os.getenv("OLLAMA_VIDEO_MODEL", "").strip(),
        "edit_plan": plan,
    }


def generate_prompt_image(prompt: str, style: str = "photorealistic", mood: str = "dreamy", aspect: str = "16:9 widescreen", output_dir: str = "generated_media", image_provider: str = "auto", image_model: str = None):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    prompt_text = (prompt or "A cinematic rooftop cityscape at dusk").strip()
    safe_name = _slugify(prompt_text or "prompt")
    image_path = output_path / f"{safe_name}-{style}-{mood}-{uuid4().hex[:8]}.png"

    image = _render_image(prompt_text, style, mood, aspect, image_provider, image_model)
    image.save(image_path)
    return {
        "prompt": prompt_text,
        "style": style,
        "mood": mood,
        "aspect": aspect,
        "image_path": str(image_path),
    }


