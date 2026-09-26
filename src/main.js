import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import "./styles.css";

const app = document.querySelector("#app");

app.innerHTML = `
  <section class="shell">
    <header class="topbar">
      <div class="brand"><span class="mark">I</span><span>INQUILAB</span></div>
      <nav class="mode-switch" aria-label="Workspace mode">
        <button class="mode-button active" data-mode="ask">Ask</button>
        <button class="mode-button" data-mode="studio">Prompt Studio</button>
      </nav>
      <div class="status"><span class="status-dot"></span><span>LOCAL RUNTIME</span></div>
    </header>
    <section class="workspace mode-panel active" data-panel="ask">
      <div class="intro">
        <p class="eyebrow">PRIVATE DESKTOP AGENT</p>
        <h1>Ask without leaving<br><em>your machine.</em></h1>
        <p class="lede">Reasoning, memory, web research, and Python tools through your private local runtime.</p>
      </div>
      <form id="ask-form" class="composer">
        <label for="question">Your question</label>
        <textarea id="question" rows="5" placeholder="What should Inquilab investigate?" autofocus></textarea>
        <div class="composer-footer">
          <span class="hint">Enter a clear request to begin</span>
          <button type="submit" id="ask-button"><span>Ask Inquilab</span><span class="arrow">↗</span></button>
        </div>
      </form>
      <section class="answer-wrap" aria-live="polite">
        <div class="answer-meta"><span>RESPONSE</span><span id="runtime-status">READY</span></div>
        <div id="answer" class="answer">Your answer will appear here.</div>
      </section>
    </section>
    <section class="studio mode-panel" data-panel="studio">
      <div class="studio-heading">
        <div>
          <p class="eyebrow">IMAGE + VIDEO GENERATION</p>
          <h2>Prompt the <em>perfect frame.</em></h2>
        </div>
      </div>
      <div class="image-studio">
        <section class="prompt-panel">
          <div class="panel-label">PROMPT EDITOR</div>
          <label class="control-label" for="image-prompt">Main idea</label>
          <textarea id="image-prompt" rows="5" placeholder="A cinematic rooftop view at sunset, futuristic signage, warm fog, ultra detailed">A cinematic rooftop view at sunset, futuristic signage, warm fog, ultra detailed</textarea>
          <div class="prompt-options">
            <div>
              <label class="control-label" for="style-select">Style</label>
              <select id="style-select">
                <option value="photorealistic">Photorealistic</option>
                <option value="oil painting">Oil painting</option>
                <option value="anime">Anime</option>
                <option value="minimalist">Minimalist</option>
                <option value="cyberpunk">Cyberpunk</option>
              </select>
            </div>
            <div>
              <label class="control-label" for="mood-select">Mood</label>
              <select id="mood-select">
                <option value="dreamy">Dreamy</option>
                <option value="dramatic">Dramatic</option>
                <option value="calm">Calm</option>
                <option value="energetic">Energetic</option>
              </select>
            </div>
            <div>
              <label class="control-label" for="aspect-select">Aspect</label>
              <select id="aspect-select">
                <option value="16:9 widescreen">16:9</option>
                <option value="1:1 square">1:1</option>
                <option value="9:16 portrait">9:16</option>
              </select>
            </div>
          </div>
          <div class="provider-controls">
            <div>
              <label class="control-label" for="image-provider">Image provider</label>
              <select id="image-provider">
                <option value="huggingface">Hugging Face</option>
                <option value="auto">Automatic fallback</option>
                <option value="local">Local / offline</option>
              </select>
            </div>
            <div id="image-model-field">
              <label class="control-label" for="image-model">Hugging Face model</label>
              <input id="image-model" type="text" value="stabilityai/stable-diffusion-xl-base-1.0" autocomplete="off">
            </div>
            <div id="image-token-field" class="provider-secret">
              <label class="control-label" for="image-token">Hugging Face access token</label>
              <input id="image-token" type="password" autocomplete="new-password" spellcheck="false">
              <small>Used for this session only; not saved.</small>
            </div>
          </div>
          <div class="prompt-actions">
            <button type="button" class="secondary-button" id="apply-prompt-button">Apply prompt</button>
            <button type="button" class="secondary-button" id="reset-prompt-button">Reset</button>
            <button type="button" id="generate-image-button">Generate image</button>
          </div>
          <p id="image-generation-status" aria-live="polite">Hugging Face generation requires an access token.</p>
          <div class="edit-video-controls">
            <div class="panel-label">VIDEO EDITOR</div>
            <div class="video-import-row">
              <button type="button" class="secondary-button" id="import-video-button">Import video</button>
              <span id="imported-video-name" role="status">No source selected</span>
            </div>
            <label class="control-label" for="edit-prompt">Edit instruction</label>
            <input id="edit-prompt" type="text" placeholder="Describe the edit for the optional video model" autocomplete="off">
            <div class="video-edit-options">
              <div>
                <label class="control-label" for="edit-start">Start (seconds)</label>
                <input id="edit-start" type="number" min="0" step="0.1" placeholder="Automatic / 0">
              </div>
              <div>
                <label class="control-label" for="edit-end">End (seconds)</label>
                <input id="edit-end" type="number" min="0" step="0.1" placeholder="Full clip">
              </div>
              <div>
                <label class="control-label" for="edit-speed">Speed</label>
                <select id="edit-speed">
                  <option value="" selected>Automatic</option>
                  <option value="0.5">0.5x</option>
                  <option value="1">1x</option>
                  <option value="1.5">1.5x</option>
                  <option value="2">2x</option>
                </select>
              </div>
              <div>
                <label class="control-label" for="edit-filter">Filter</label>
                <select id="edit-filter">
                  <option value="" selected>Automatic</option>
                  <option value="none">Original</option>
                  <option value="grayscale">Grayscale</option>
                  <option value="sepia">Sepia</option>
                  <option value="negate">Invert</option>
                </select>
              </div>
            </div>
            <button type="button" id="apply-video-edit-button" disabled>Export edited video</button>
            <p id="video-edit-status" aria-live="polite">Choose a source clip to begin.</p>
          </div>
        </section>
        <aside class="media-panel">
          <div class="panel-label">GENERATED OUTPUT</div>
          <div class="media-grid">
            <div class="output-block">
              <div class="output-header">IMAGE</div>
              <div class="image-stage" id="image-stage">
                <img id="generated-image" alt="Generated prompt preview" hidden>
                <div class="image-placeholder" id="image-placeholder">
                  <span class="film-icon">✦</span>
                  <strong>No image generated yet</strong>
                  <small>Prompt-based composition only</small>
                </div>
              </div>
            </div>
            <div class="output-block">
              <div class="output-header">VIDEO</div>
              <div class="video-stage" id="video-stage">
                <video id="generated-video" controls playsinline hidden></video>
                <div class="video-placeholder" id="video-placeholder">
                  <span class="film-icon">▶</span>
                  <strong>No source clip imported</strong>
                  <small>Import a video to preview and edit</small>
                </div>
              </div>
            </div>
          </div>
          <div class="prompt-output">
            <label for="final-prompt">Final prompt</label>
            <textarea id="final-prompt" rows="4" readonly></textarea>
          </div>
        </aside>
      </div>
    </section>
    <footer><span>INQUILAB / LOCAL INTELLIGENCE</span><span>PRIVATE RUNTIME + PYTHON</span></footer>
  </section>
`;

const form = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const answer = document.querySelector("#answer");
const button = document.querySelector("#ask-button");
const runtimeStatus = document.querySelector("#runtime-status");

document.querySelectorAll(".mode-button").forEach((modeButton) => {
  modeButton.addEventListener("click", () => {
    const mode = modeButton.dataset.mode;
    document.querySelectorAll(".mode-button").forEach((button) => button.classList.toggle("active", button === modeButton));
    document.querySelectorAll(".mode-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === mode));
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value || button.disabled) return;

  button.disabled = true;
  runtimeStatus.textContent = "THINKING";
  answer.classList.add("loading");
  answer.textContent = "Inquilab is working...";

  try {
    const result = await invoke("ask_question", { question: value });
    if (!result.ok) throw new Error(result.error || "The agent could not answer.");
    answer.textContent = result.answer || "No answer was returned.";
    runtimeStatus.textContent = "COMPLETE";
  } catch (error) {
    answer.textContent = error.message || String(error);
    runtimeStatus.textContent = "ERROR";
  } finally {
    answer.classList.remove("loading");
    button.disabled = false;
  }
});

const imagePrompt = document.querySelector("#image-prompt");
const styleSelect = document.querySelector("#style-select");
const moodSelect = document.querySelector("#mood-select");
const aspectSelect = document.querySelector("#aspect-select");
const finalPrompt = document.querySelector("#final-prompt");
const generatedImage = document.querySelector("#generated-image");
const imagePlaceholder = document.querySelector("#image-placeholder");
const generateImageButton = document.querySelector("#generate-image-button");
const imageGenerationStatus = document.querySelector("#image-generation-status");
const applyPromptButton = document.querySelector("#apply-prompt-button");
const resetPromptButton = document.querySelector("#reset-prompt-button");
const generatedVideo = document.querySelector("#generated-video");
const videoPlaceholder = document.querySelector("#video-placeholder");
const imageProvider = document.querySelector("#image-provider");
const imageModel = document.querySelector("#image-model");
const imageModelField = document.querySelector("#image-model-field");
const imageToken = document.querySelector("#image-token");
const imageTokenField = document.querySelector("#image-token-field");
const importVideoButton = document.querySelector("#import-video-button");
const importedVideoName = document.querySelector("#imported-video-name");
const editPrompt = document.querySelector("#edit-prompt");
const editStart = document.querySelector("#edit-start");
const editEnd = document.querySelector("#edit-end");
const editSpeed = document.querySelector("#edit-speed");
const editFilter = document.querySelector("#edit-filter");
const applyVideoEditButton = document.querySelector("#apply-video-edit-button");
const videoEditStatus = document.querySelector("#video-edit-status");
let activeVideoPath = "";

const mediaUrl = (path) => {
  if (!path) return "";
  if (path.startsWith("asset:") || path.startsWith("http:") || path.startsWith("https:")) {
    return path;
  }
  return convertFileSrc(path);
};

const buildPromptText = () => {
  const basePrompt = imagePrompt.value.trim() || "A cinematic rooftop view at sunset, futuristic signage, warm fog, ultra detailed";
  return `${basePrompt}, ${styleSelect.value}, ${moodSelect.value}, ${aspectSelect.value}`;
};

const syncPromptPreview = () => {
  finalPrompt.value = buildPromptText();
};

const buildGeneratedImage = async () => {
  const prompt = buildPromptText();
  syncPromptPreview();
  generateImageButton.disabled = true;
  imageGenerationStatus.textContent = "Generating with a real image model...";

  try {
    const result = await invoke("generate_image", {
      prompt,
      style: styleSelect.value,
      mood: moodSelect.value,
      aspect: aspectSelect.value,
      imageProvider: imageProvider.value,
      imageModel: imageModel.value.trim(),
      imageToken: imageToken.value.trim(),
    });

    if (!result.ok) {
      throw new Error(result.error || "Image generation failed.");
    }

    generatedImage.src = mediaUrl(result.image_path);
    generatedImage.hidden = false;
    imagePlaceholder.hidden = true;
    imageGenerationStatus.textContent = "Image generated and saved.";
  } catch (error) {
    generatedImage.hidden = true;
    imagePlaceholder.hidden = false;
    imagePlaceholder.querySelector("strong").textContent = "Image generation failed";
    imagePlaceholder.querySelector("small").textContent = error.message || String(error);
    imageGenerationStatus.textContent = error.message || String(error);
  } finally {
    generateImageButton.disabled = false;
  }
};

applyPromptButton.addEventListener("click", syncPromptPreview);
resetPromptButton.addEventListener("click", () => {
  imagePrompt.value = "A cinematic rooftop view at sunset, futuristic signage, warm fog, ultra detailed";
  styleSelect.value = "photorealistic";
  moodSelect.value = "dreamy";
  aspectSelect.value = "16:9 widescreen";
  syncPromptPreview();
  generatedImage.hidden = true;
  imagePlaceholder.hidden = false;
  imagePlaceholder.querySelector("strong").textContent = "No image generated yet";
  imagePlaceholder.querySelector("small").textContent = "Generate with Hugging Face or an offline renderer";
  generatedVideo.hidden = true;
  videoPlaceholder.hidden = false;
  videoPlaceholder.querySelector("strong").textContent = "No source clip imported";
  videoPlaceholder.querySelector("small").textContent = "Import a video to preview and edit";
  activeVideoPath = "";
  importedVideoName.textContent = "No source selected";
  applyVideoEditButton.disabled = true;
  videoEditStatus.textContent = "Choose a source clip to begin.";
});
generateImageButton.addEventListener("click", () => {
  buildGeneratedImage();
});

imageProvider.addEventListener("change", () => {
  imageModelField.hidden = imageProvider.value === "local";
  imageTokenField.hidden = imageProvider.value === "local";
});

importVideoButton.addEventListener("click", async () => {
  importVideoButton.disabled = true;
  videoEditStatus.textContent = "Opening video picker...";
  try {
    const selectedPath = await invoke("pick_video_file");
    if (!selectedPath) {
      videoEditStatus.textContent = "Import cancelled.";
      return;
    }
    activeVideoPath = selectedPath;
    importedVideoName.textContent = selectedPath.split(/[\\/]/).pop();
    generatedVideo.src = mediaUrl(selectedPath);
    generatedVideo.hidden = false;
    videoPlaceholder.hidden = true;
    generatedVideo.load();
    applyVideoEditButton.disabled = false;
    videoEditStatus.textContent = "Source loaded. Adjust the clip and export a copy.";
  } catch (error) {
    videoEditStatus.textContent = error.message || String(error);
  } finally {
    importVideoButton.disabled = false;
  }
});

applyVideoEditButton.addEventListener("click", async () => {
  if (!activeVideoPath || applyVideoEditButton.disabled) return;
  const startSeconds = editStart.value === "" ? null : Number(editStart.value);
  const endSeconds = editEnd.value === "" ? null : Number(editEnd.value);
  const validationStart = startSeconds ?? 0;
  if ((startSeconds !== null && (!Number.isFinite(startSeconds) || startSeconds < 0)) || (endSeconds !== null && (!Number.isFinite(endSeconds) || endSeconds <= validationStart))) {
    videoEditStatus.textContent = "Enter a valid end time greater than the start time.";
    return;
  }

  applyVideoEditButton.disabled = true;
  videoEditStatus.textContent = "Rendering edited video...";
  try {
    const result = await invoke("edit_video", {
      sourceVideo: activeVideoPath,
      editPrompt: editPrompt.value.trim(),
      startSeconds,
      endSeconds,
      speed: editSpeed.value === "" ? null : Number(editSpeed.value),
      videoFilter: editFilter.value || null,
    });
    activeVideoPath = result.video_path;
    importedVideoName.textContent = result.video_path.split(/[\\/]/).pop();
    generatedVideo.src = mediaUrl(result.video_path);
    generatedVideo.hidden = false;
    videoPlaceholder.hidden = true;
    generatedVideo.load();
    videoEditStatus.textContent = "Export complete. The edited copy is saved in Inquilab media.";
  } catch (error) {
    videoEditStatus.textContent = error.message || String(error);
  } finally {
    applyVideoEditButton.disabled = false;
  }
});

generatedVideo.addEventListener("error", () => {
  generatedVideo.hidden = true;
  videoPlaceholder.hidden = false;
  videoPlaceholder.querySelector("strong").textContent = "Video could not be loaded";
  videoPlaceholder.querySelector("small").textContent = "Check the source or exported file";
});

imageModelField.hidden = imageProvider.value === "local";
imageTokenField.hidden = imageProvider.value === "local";
syncPromptPreview();
