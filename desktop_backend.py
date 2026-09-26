"""JSON-lines bridge between the Tauri desktop UI and the Inquilab agent."""

import contextlib
import io
import json
import sys


def main():
    protocol_stdout = sys.stdout
    with contextlib.redirect_stdout(sys.stderr):
        for line in sys.stdin:
            try:
                request = json.loads(line)
                operation = request.get("operation", "ask")
                if operation == "generate_image":
                    from media_generator import generate_prompt_image

                    result = generate_prompt_image(
                        prompt=str(request.get("prompt", "")),
                        style=str(request.get("style", "photorealistic")),
                        mood=str(request.get("mood", "dreamy")),
                        aspect=str(request.get("aspect", "16:9 widescreen")),
                        output_dir=str(request["output_dir"]),
                        image_provider=str(request.get("image_provider", "huggingface")),
                        image_model=str(request.get("image_model", "")),
                    )
                    response = {"ok": True, **result}
                elif operation == "edit_video":
                    from media_generator import edit_video

                    result = edit_video(
                        source_video=str(request["source_video"]),
                        edit_prompt=str(request.get("edit_prompt", "")),
                        output_dir=str(request["output_dir"]),
                        start_seconds=request.get("start_seconds"),
                        end_seconds=request.get("end_seconds"),
                        speed=request.get("speed"),
                        video_filter=request.get("video_filter"),
                    )
                    response = {"ok": True, **result}
                elif operation == "ask":
                    question = str(request.get("question", "")).strip()
                    if not question:
                        raise ValueError("Question cannot be empty")
                    with contextlib.redirect_stdout(sys.stderr):
                        from main import run_inquilab

                        answer = run_inquilab(question)
                    response = {"ok": answer is not None, "answer": answer or ""}
                else:
                    raise ValueError(f"Unsupported backend operation: {operation}")
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            protocol_stdout.write(json.dumps(response) + "\n")
            protocol_stdout.flush()


if __name__ == "__main__":
    main()