## YouTube AI Summarizer

This project is a small full‑stack app that summarizes **any YouTube video link**.

Backend uses **FastAPI** and the following pipeline:

1. Accept a YouTube URL from the user (`POST /summarize`).
2. Try extracting subtitles with **youtube-transcript-api**.
3. If subtitles are not available, download the audio using **yt‑dlp**.
4. Send the audio to **AssemblyAI** to generate a transcript.
5. Clean the transcript text.
6. Send the transcript to **OpenAI** to generate:
   - Key points
   - A short summary
   - Important topics.

Frontend is a simple **HTML/CSS/JS** page that:

- Lets you paste a YouTube link.
- Click **“Summarize Video”**.
- Shows the key points, short summary, and topics.

---

### Project structure

```text
youtube-ai-summarizer/
  backend/
    main.py
    transcript.py
    summarizer.py
    requirements.txt
    .env.example

  frontend/
    index.html
    style.css
    script.js
```

---

### 1. Backend setup

#### a) Go to the backend folder

```powershell
cd "C:\Users\G.susmitha\Documents\ChatbotUrl\youtube-ai-summarizer\backend"
```

#### b) (Optional but recommended) Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### c) Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### d) Configure environment variables

1. Copy the example file:

   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and put your real keys:

   ```text
   ASSEMBLYAI_API_KEY=your_real_assemblyai_key_here
   OPENAI_API_KEY=your_real_openai_key_here
   ```

> Do **not** commit real keys to source control.

#### e) Run the FastAPI backend with uvicorn

From the `backend` folder:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Check it in your browser:

```text
http://localhost:8000/health
```

You should see:

```json
{"status": "ok"}
```

---

### 2. Frontend setup

The frontend is a static site; no build tools are required.

#### Option A: Simple Python HTTP server (recommended)

Open a new terminal:

```powershell
cd "C:\Users\G.susmitha\Documents\ChatbotUrl\youtube-ai-summarizer\frontend"
python -m http.server 5501
```

Then open in your browser:

```text
http://localhost:5501/
```

#### Option B: Open `index.html` directly

- Double‑click `index.html` or open it via your browser’s “Open file…” menu.
- This works, but API calls might be blocked by some browsers’ file security policies; using a simple server is safer.

---

### 3. Using the app

1. Make sure the **backend** is running on `http://localhost:8000`.
2. Open the **frontend** in your browser (e.g., `http://localhost:5501/`).
3. Paste a **YouTube URL** like:

   ```text
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

4. Click **“Summarize Video”**.
5. Wait while the app:
   - Tries to read subtitles with youtube-transcript-api.
   - If needed, downloads audio and sends it to AssemblyAI.
   - Uses OpenAI to generate key points, a short summary, and topics.
6. When done, you’ll see:
   - A bullet list of key points.
   - A short summary paragraph.
   - Topic “pills” for the main subjects.

---

### 4. Error handling behavior

The backend and frontend try to give **friendly error messages**:

- **Invalid URLs**:
  - If the URL is not a valid YouTube URL, the request will fail with a 422/400 and the frontend will show an error.
- **No captions / transcripts disabled**:
  - The app automatically falls back to downloading audio and using AssemblyAI, so many videos still work.
- **Private or restricted videos**:
  - youtube-transcript-api / yt‑dlp / AssemblyAI may not be able to access these; you’ll see an error like “video unavailable” or “could not summarize this video.”
- **Missing API keys**:
  - If `ASSEMBLYAI_API_KEY` or `OPENAI_API_KEY` are missing, you’ll get a clear error message from the backend.

If something goes wrong, check:

- The browser console and Network tab.
- The terminal where uvicorn is running (it shows full tracebacks).

---

This project is intentionally written in a beginner‑friendly style with clear separation between:

- **`transcript.py`** – getting the video transcript (subtitles or audio + AssemblyAI).
- **`summarizer.py`** – turning that transcript into a structured summary with OpenAI.
- **`main.py`** – exposing a clean FastAPI endpoint for the frontend.

You can extend it further (e.g., store summaries, add authentication, or support multiple languages) as you get more comfortable. 

