use serde::Serialize;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use tauri::{AppHandle, Manager};
use tauri_plugin_dialog::DialogExt;

#[derive(serde::Deserialize, Serialize)]
struct AgentResponse {
    ok: bool,
    answer: String,
    error: Option<String>,
}

#[tauri::command]
fn ask_question(app: AppHandle, question: String) -> Result<AgentResponse, String> {
    let question = question.trim();
    if question.is_empty() {
        return Err("Question cannot be empty".into());
    }

    let resource_dir = app
        .path()
        .resource_dir()
        .map_err(|error| error.to_string())?;
    let bundled_backend = [
        resource_dir.join("inquilab-backend.exe"),
        resource_dir.join("resources").join("inquilab-backend.exe"),
        std::env::current_exe()
            .ok()
            .and_then(|path| {
                path.parent()
                    .map(|parent| parent.join("resources").join("inquilab-backend.exe"))
            })
            .unwrap_or_default(),
    ]
    .into_iter()
    .find(|path| path.exists());
    let (program, args): (PathBuf, Vec<String>) = if let Some(bundled_backend) = bundled_backend {
        (bundled_backend, Vec::new())
    } else {
        let script = resource_dir.join("desktop_backend.py");
        let script = if script.exists() {
            script
        } else {
            PathBuf::from("desktop_backend.py")
        };
        (
            PathBuf::from("python"),
            vec![script.to_string_lossy().into_owned()],
        )
    };

    let mut child = Command::new(program)
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| format!("Could not start Inquilab backend: {error}"))?;

    let request = serde_json::json!({ "question": question });
    child
        .stdin
        .take()
        .ok_or_else(|| "Could not open backend input".to_string())?
        .write_all(format!("{}\n", request).as_bytes())
        .map_err(|error| format!("Could not send question: {error}"))?;

    let output = child
        .wait_with_output()
        .map_err(|error| format!("Could not read backend response: {error}"))?;
    let status = output.status;
    let line = String::from_utf8_lossy(&output.stdout);

    if line.trim().is_empty() {
        let error_output = String::from_utf8_lossy(&output.stderr);
        return Err(format!(
            "Backend returned no response (exit status {status}). {}",
            error_output.trim()
        ));
    }

    serde_json::from_str(&line).map_err(|error| format!("Invalid backend response: {error}"))
}

#[derive(serde::Deserialize, Serialize)]
struct MediaGenerationResult {
    ok: bool,
    image_path: String,
    video_path: String,
    prompt: String,
    error: Option<String>,
}

fn run_media_backend(
    app: &AppHandle,
    request: serde_json::Value,
    image_token: Option<&str>,
) -> Result<serde_json::Value, String> {
    let resource_dir = app
        .path()
        .resource_dir()
        .map_err(|error| error.to_string())?;
    let bundled_backend = [
        resource_dir.join("inquilab-backend.exe"),
        resource_dir.join("resources").join("inquilab-backend.exe"),
        std::env::current_exe()
            .ok()
            .and_then(|path| {
                path.parent()
                    .map(|parent| parent.join("resources").join("inquilab-backend.exe"))
            })
            .unwrap_or_default(),
    ]
    .into_iter()
    .find(|path| path.exists());

    let (program, args, working_dir) = if let Some(backend) = bundled_backend {
        (backend, Vec::new(), resource_dir.clone())
    } else {
        let script = resource_dir.join("desktop_backend.py");
        if !script.exists() {
            return Err("The Inquilab media backend was not found in app resources".into());
        }
        (
            PathBuf::from("python"),
            vec![script.to_string_lossy().into_owned()],
            resource_dir.clone(),
        )
    };

    let mut command = Command::new(program);
    command
        .args(args)
        .current_dir(&working_dir)
        .env("PYTHONPATH", &working_dir)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    if let Some(token) = image_token.filter(|value| !value.trim().is_empty()) {
        command.env("HF_TOKEN", token.trim());
    }

    let mut child = command
        .spawn()
        .map_err(|error| format!("Could not start Inquilab media backend: {error}"))?;
    child
        .stdin
        .take()
        .ok_or_else(|| "Could not open media backend input".to_string())?
        .write_all(format!("{}\n", request).as_bytes())
        .map_err(|error| format!("Could not send media request: {error}"))?;

    let output = child
        .wait_with_output()
        .map_err(|error| format!("Could not read media backend response: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "Media backend exited with {}: {}",
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    let value: serde_json::Value = serde_json::from_slice(&output.stdout)
        .map_err(|error| format!("Invalid media backend response: {error}"))?;
    if value.get("ok").and_then(serde_json::Value::as_bool) != Some(true) {
        return Err(value
            .get("error")
            .and_then(serde_json::Value::as_str)
            .unwrap_or("Media operation failed")
            .to_string());
    }
    Ok(value)
}

fn run_media_generation(
    app: AppHandle,
    prompt: String,
    style: String,
    mood: String,
    aspect: String,
    image_provider: String,
    image_model: String,
    image_token: String,
) -> Result<MediaGenerationResult, String> {
    let prompt = prompt.trim();
    if prompt.is_empty() {
        return Err("Prompt cannot be empty".into());
    }

    let output_dir = app
        .path()
        .app_data_dir()
        .map_err(|error| error.to_string())?
        .join("generated_media");
    std::fs::create_dir_all(&output_dir)
        .map_err(|error| format!("Could not create media output directory: {error}"))?;
    let value = run_media_backend(
        &app,
        serde_json::json!({
            "operation": "generate_image",
            "prompt": prompt,
            "style": style,
            "mood": mood,
            "aspect": aspect,
            "output_dir": output_dir,
            "image_provider": image_provider,
            "image_model": image_model,
        }),
        Some(&image_token),
    )?;
    let image_path = value["image_path"].as_str().unwrap_or("").to_string();
    let video_path = value["video_path"].as_str().unwrap_or("").to_string();

    if image_path.is_empty() {
        return Err("Image generation did not return a valid output path".to_string());
    }

    let normalized_image = image_path.replace('\\', "/");
    let normalized_video = video_path.replace('\\', "/");

    Ok(MediaGenerationResult {
        ok: true,
        image_path: normalized_image,
        video_path: normalized_video,
        prompt: prompt.to_string(),
        error: None,
    })
}

#[tauri::command]
fn generate_image(
    app: AppHandle,
    prompt: String,
    style: String,
    mood: String,
    aspect: String,
    image_provider: String,
    image_model: String,
    image_token: String,
) -> Result<MediaGenerationResult, String> {
    run_media_generation(
        app,
        prompt,
        style,
        mood,
        aspect,
        image_provider,
        image_model,
        image_token,
    )
}

#[tauri::command]
fn pick_video_file(app: AppHandle) -> Result<Option<String>, String> {
    let selected = app
        .dialog()
        .file()
        .add_filter("Video", &["mp4", "mov", "mkv", "avi", "webm"])
        .blocking_pick_file();
    let Some(selected) = selected else {
        return Ok(None);
    };
    let source = selected
        .into_path()
        .map_err(|error| format!("Could not access the selected video: {error}"))?;
    let import_dir = app
        .path()
        .app_data_dir()
        .map_err(|error| error.to_string())?
        .join("imported_media");
    std::fs::create_dir_all(&import_dir)
        .map_err(|error| format!("Could not create import directory: {error}"))?;
    let file_name = source
        .file_name()
        .ok_or_else(|| "Selected video has no file name".to_string())?
        .to_string_lossy();
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_millis();
    let imported = import_dir.join(format!("{timestamp}-{file_name}"));
    std::fs::copy(&source, &imported)
        .map_err(|error| format!("Could not import selected video: {error}"))?;
    Ok(Some(imported.to_string_lossy().into_owned()))
}

#[tauri::command]
fn edit_video(
    app: AppHandle,
    source_video: String,
    edit_prompt: String,
    start_seconds: Option<f64>,
    end_seconds: Option<f64>,
    speed: Option<f64>,
    video_filter: Option<String>,
) -> Result<serde_json::Value, String> {
    let output_dir = app
        .path()
        .app_data_dir()
        .map_err(|error| error.to_string())?
        .join("generated_media");
    std::fs::create_dir_all(&output_dir)
        .map_err(|error| format!("Could not create media output directory: {error}"))?;
    run_media_backend(
        &app,
        serde_json::json!({
            "operation": "edit_video",
            "source_video": source_video,
            "edit_prompt": edit_prompt,
            "output_dir": output_dir,
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "speed": speed,
            "video_filter": video_filter,
        }),
        None,
    )
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            ask_question,
            generate_image,
            pick_video_file,
            edit_video
        ])
        .run(tauri::generate_context!())
        .expect("error while running Inquilab desktop application");
}
