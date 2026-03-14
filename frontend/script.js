const API_BASE_URL = "http://localhost:8000";

const urlInput = document.getElementById("youtube-url");
const summarizeBtn = document.getElementById("summarize-btn");
const statusEl = document.getElementById("status");

const loadingEl = document.getElementById("loading");
const resultsEl = document.getElementById("results");
const keyPointsEl = document.getElementById("key-points");
const shortSummaryEl = document.getElementById("short-summary");
const topicsEl = document.getElementById("topics");

function setStatus(message, type = "info") {
  statusEl.textContent = message;
  statusEl.classList.remove("status--success", "status--error");
  if (!message) return;
  if (type === "success") statusEl.classList.add("status--success");
  if (type === "error") statusEl.classList.add("status--error");
}

function clearResults() {
  keyPointsEl.innerHTML = "";
  shortSummaryEl.textContent = "";
  topicsEl.innerHTML = "";
  resultsEl.classList.add("hidden");
}

summarizeBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  if (!url) {
    setStatus("Please paste a YouTube URL first.", "error");
    return;
  }

  clearResults();
  setStatus("");
  loadingEl.classList.remove("hidden");
  summarizeBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_url: url }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => null);
      const detail = error && error.detail ? error.detail : "Unknown error";
      throw new Error(detail);
    }

    const data = await response.json();

    // Key points
    (data.key_points || []).forEach((point) => {
      const li = document.createElement("li");
      li.textContent = point;
      keyPointsEl.appendChild(li);
    });

    // Short summary
    shortSummaryEl.textContent = data.short_summary || "";

    // Topics
    (data.topics || []).forEach((topic) => {
      const span = document.createElement("span");
      span.classList.add("topic-pill");
      span.textContent = topic;
      topicsEl.appendChild(span);
    });

    resultsEl.classList.remove("hidden");
    setStatus("Summary generated successfully.", "success");
  } catch (err) {
    console.error(err);
    setStatus(
      `Could not summarize this video: ${err.message}. Check if the URL is valid and the video is public.`,
      "error"
    );
  } finally {
    loadingEl.classList.add("hidden");
    summarizeBtn.disabled = false;
  }
});

