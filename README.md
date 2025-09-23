# Subtitle Generator (Streamlit + Whisper)

A simple web app to generate subtitles (`.srt`) from audio/video using [OpenAI Whisper](https://github.com/openai/whisper) and [MoviePy](https://github.com/Zulko/moviepy). Built with [Streamlit](https://streamlit.io/).

## Features
- Upload audio/video (`.mp3`, `.wav`, `.mp4`)
- Auto-extract audio from video via MoviePy
- Transcribe with OpenAI Whisper
- Display full transcript on the page
- Generate and download `.srt` with timestamps
- Progress updates during processing

## Requirements
- Python 3.9–3.12 recommended
- For Python 3.13: install a compatible PyTorch build manually (see below)
- Windows/macOS/Linux supported

## Installation

1) Create and activate a virtual environment (recommended)
```
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

2) Install dependencies
```
pip install -r requirements.txt
```

Notes:
- Whisper depends on PyTorch. The `requirements.txt` will install `torch` automatically on Python < 3.13.
- On Python 3.13, install PyTorch manually from the official website: https://pytorch.org/get-started/locally/
  - Choose your OS, Package = `pip`, Language = `Python`, and CUDA (or CPU) to get the right command.
  - Example CPU-only (version may change):
    ```
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    ```
- MoviePy uses `ffmpeg`. The `imageio-ffmpeg` package bundled in requirements typically handles this automatically.

## Run the app
```
streamlit run app.py
```
Then open the local URL shown in the terminal (usually http://localhost:8501).

## Usage
1. In the sidebar, upload an `mp3`, `wav`, or `mp4` file.
2. Optionally select the Whisper model size (larger models are slower but more accurate).
3. Wait for processing to finish (watch the progress text/bar).
4. Review the transcript shown on the page.
5. Download the `.srt` subtitle file.

## Troubleshooting
- If you encounter a message about PyTorch not found on Python 3.13, install it manually from the PyTorch website.
- For GPU acceleration on Windows, install a CUDA-enabled PyTorch build compatible with your GPU and drivers.
- If MoviePy complains about `ffmpeg`, ensure `imageio-ffmpeg` is installed (it is included in `requirements.txt`).
- On first run, Whisper may download model weights; this can take time based on model size and your internet speed.

## Project structure
- `app.py` — Streamlit application
- `requirements.txt` — Python dependencies
- `README.md` — Setup and usage guide
