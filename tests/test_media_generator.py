import io
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

from media_generator import generate_prompt_image


def test_generate_prompt_image_saves_huggingface_output(tmp_path, monkeypatch):
    import media_generator

    image_bytes = io.BytesIO()
    Image.new("RGB", (64, 64), (20, 110, 70)).save(image_bytes, format="PNG")
    captured = {}

    def fake_post(endpoint, headers, json, timeout):
        captured.update(endpoint=endpoint, headers=headers, json=json, timeout=timeout)

        class Response:
            status_code = 200
            text = ""
            content = image_bytes.getvalue()

        return Response()

    monkeypatch.setenv("HF_TOKEN", "demo-token")
    monkeypatch.setattr(media_generator.requests, "post", fake_post)
    output_dir = tmp_path / "generated"
    result = generate_prompt_image(
        prompt="sunset skyline with neon lights",
        style="photorealistic",
        mood="dreamy",
        aspect="16:9 widescreen",
        output_dir=str(output_dir),
        image_provider="huggingface",
        image_model="demo/model",
    )

    assert result["image_path"].endswith(".png")
    assert Path(result["image_path"]).exists()
    assert Image.open(result["image_path"]).size == (1280, 720)
    assert captured["endpoint"].endswith("/demo/model")
    assert captured["headers"]["Authorization"] == "Bearer demo-token"
    assert "sunset skyline" in captured["json"]["inputs"]
    assert "16:9" in captured["json"]["inputs"]


def test_edit_video_from_system_source(tmp_path):
    import subprocess

    from media_generator import edit_video

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    source = tmp_path / "source.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=128x72:d=1",
            "-frames:v",
            "1",
            str(source),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    result = edit_video(str(source), "make a clean export", output_dir=str(tmp_path / "edited"))

    assert result["video_path"].endswith(".mp4")
    assert Path(result["video_path"]).exists()
    assert result["source_video"] == str(source)


def test_edit_video_applies_trim_speed_and_filter(tmp_path):
    import subprocess

    from media_generator import edit_video

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    source = tmp_path / "source.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=128x72:d=2",
            "-pix_fmt",
            "yuv420p",
            str(source),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    result = edit_video(
        str(source),
        "slow monochrome clip",
        output_dir=str(tmp_path / "edited"),
        start_seconds=0.25,
        end_seconds=1.5,
        speed=0.5,
        video_filter="grayscale",
    )

    assert Path(result["video_path"]).is_file()
    assert result["edit_plan"] == {
        "start_seconds": 0.25,
        "end_seconds": 1.5,
        "speed": 0.5,
        "filter": "grayscale",
    }


def test_video_edit_plan_uses_configured_ollama_model(monkeypatch):
    import ollama_connector
    from media_generator import _video_edit_plan

    class FakeConnector:
        def __init__(self, model):
            assert model == "qwen2.5:7b"

        def generate(self, prompt):
            assert "slow down" in prompt
            return '{"start_seconds": 1, "end_seconds": 4, "speed": 0.5, "filter": "sepia"}'

    monkeypatch.setenv("OLLAMA_VIDEO_MODEL", "qwen2.5:7b")
    monkeypatch.setattr(ollama_connector, "OllamaConnector", FakeConnector)

    assert _video_edit_plan("slow down and warm the clip") == {
        "start_seconds": 1,
        "end_seconds": 4,
        "speed": 0.5,
        "filter": "sepia",
    }


def test_huggingface_image_generation_uses_inference_api(monkeypatch):
    import media_generator

    captured = {}

    def fake_post(endpoint, headers, json, timeout):
        captured["endpoint"] = endpoint
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout

        image_bytes = io.BytesIO()
        Image.new("RGB", (64, 64), (20, 110, 70)).save(image_bytes, format="PNG")

        class DummyResponse:
            status_code = 200
            text = ""
            content = image_bytes.getvalue()

        return DummyResponse()

    monkeypatch.setenv("HF_TOKEN", "demo-token")
    monkeypatch.setenv("HF_IMAGE_MODEL", "demo/model")
    monkeypatch.setattr(media_generator.requests, "post", fake_post)
    result = media_generator._create_huggingface_image("sunset skyline", "photorealistic", "dreamy", "16:9 widescreen", "demo/model")

    assert result.size == (1280, 720)
    assert captured["endpoint"].endswith("/demo/model")
    assert captured["headers"]["Authorization"] == "Bearer demo-token"
    assert "sunset skyline" in captured["json"]["inputs"]


def test_explicit_huggingface_provider_does_not_silently_fall_back(monkeypatch):
    import media_generator

    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACEHUB_API_TOKEN", raising=False)

    try:
        media_generator._render_image("test prompt", "photorealistic", "calm", "1:1 square", "huggingface")
    except RuntimeError as error:
        assert "HF_TOKEN" in str(error)
    else:
        raise AssertionError("Explicit Hugging Face selection must report missing credentials")


def test_auto_provider_does_not_return_a_synthetic_placeholder(monkeypatch):
    import media_generator

    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACEHUB_API_TOKEN", raising=False)
    monkeypatch.setattr(media_generator, "_create_local_model_image", lambda *args: None)

    try:
        media_generator._render_image("test prompt", "photorealistic", "calm", "1:1 square")
    except RuntimeError as error:
        assert "No real image model is available" in str(error)
    else:
        raise AssertionError("Auto mode must not return a synthetic placeholder image")
