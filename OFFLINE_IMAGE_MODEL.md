# Inquilab Media Studio

## Hugging Face Image Generation

Select **Hugging Face** in Prompt Studio and enter a model ID such as `stabilityai/stable-diffusion-xl-base-1.0`. The app reads the access token from the `HF_TOKEN` environment variable; set it in Windows Environment Variables, then restart Inquilab. Keep the token out of source files and screenshots. The **Automatic fallback** provider tries Hugging Face first, then the local renderer.

## Offline Image Model

Inquilab can use a locally stored Diffusers text-to-image model without an API.

1. Install the optional local runtime in the Python environment used by Inquilab:

```powershell
python -m pip install torch diffusers transformers safetensors accelerate
```

2. Place a fully downloaded Diffusers model folder on the machine. Keep it outside the packaged app, for example:

```text
D:\Inquilab\models\image-model
```

3. Set the model path before launching Inquilab:

```powershell
$env:INQUILAB_LOCAL_IMAGE_MODEL = "D:\Inquilab\models\image-model"
```

The folder must already contain the model files. Inquilab uses `local_files_only=True`, so it never contacts an API or downloads files at generation time. If the optional runtime or model is unavailable, the built-in offline renderer remains available.

## Video Import and Editing

Choose **Import video** in Prompt Studio to select a source clip. Inquilab copies the source into its app data, leaves the original untouched, and exports edited MP4 copies to the app's `generated_media` folder. Set a start/end time, speed, or filter before exporting. Leave controls on **Automatic** to use `OLLAMA_VIDEO_MODEL` for an edit plan when configured; without it, the defaults preserve the full clip.