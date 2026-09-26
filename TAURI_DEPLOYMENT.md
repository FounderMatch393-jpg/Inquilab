# Tauri Deployment

## Prerequisites

Install Node.js and Rust with Cargo. On Windows, install the WebView2 runtime if it is not already present.

Install Python build dependencies in the project virtual environment:

```powershell
& .\.venv\Scripts\python.exe -m pip install pyinstaller
npm install
```

## Development

Run the desktop app with a local Python backend:

```powershell
npm run tauri:dev
```

The app expects Ollama at `http://localhost:11434` and starts it automatically when possible.

## Windows Release

Build the Python sidecar first, then create the Tauri installer:

```powershell
.\build_backend.ps1
npm run tauri:build
```

The installer is written under `src-tauri/target/release/bundle/`. The bundled backend uses the same local memory, web scraper, Python execution, and Ollama integration as the CLI.
