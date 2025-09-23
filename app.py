import os
import io
import tempfile
from datetime import timedelta
from typing import Tuple, Optional

import streamlit as st

# Whisper (openai-whisper)
import whisper

# MoviePy for audio extraction from video (compatible with MoviePy v2+ and v1)
try:
    # MoviePy v2+ recommended import path
    from moviepy.video.io.VideoFileClip import VideoFileClip
except Exception:  # fallback for older MoviePy versions
    from moviepy.editor import VideoFileClip


# -----------------------------
# Utilities
# -----------------------------

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds (float) to SRT timestamp format: HH:MM:SS,mmm
    """
    if seconds < 0:
        seconds = 0
    td = timedelta(seconds=seconds)
    # Extract hours, minutes, seconds, milliseconds
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def build_srt_from_segments(segments) -> str:
    """
    Build an SRT formatted string from Whisper result segments.
    Each segment should have 'id', 'start', 'end', and 'text'.
    """
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_ts = format_timestamp(seg.get("start", 0.0))
        end_ts = format_timestamp(seg.get("end", 0.0))
        text = (seg.get("text") or "").strip()
        lines.append(str(i))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")  # blank line between entries
    return "\n".join(lines).strip() + "\n"


def extract_audio_if_needed(upload_path: str, suffix: str, progress=None) -> Tuple[str, Optional[tempfile.NamedTemporaryFile]]:
    """
    If the uploaded file is a video (mp4), extract audio to a temporary .wav file.
    Returns (audio_path, temp_file_obj). Caller should clean up temp file if provided.
    If already an audio file (mp3/wav), returns original path and None.
    """
    ext = os.path.splitext(upload_path)[1].lower()
    if ext in [".mp3", ".wav"]:
        return upload_path, None

    if ext == ".mp4":
        if progress:
            progress.progress(20, text="Mengekstrak audio dari video...")
        # Create temp WAV file
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio.close()  # will write via moviepy/ffmpeg
        # Extract with MoviePy (use context manager to ensure closure)
        with VideoFileClip(upload_path) as clip:
            # For WAV output, no codec arg is needed in MoviePy v2; set fps for consistency
            clip.audio.write_audiofile(
                temp_audio.name,
                fps=16000,
                verbose=False,
                logger=None,
            )
        if progress:
            progress.progress(35, text="Audio berhasil diekstrak.")
        return temp_audio.name, temp_audio

    # Unknown extension: treat as audio path pass-through
    return upload_path, None


@st.cache_resource(show_spinner=False)
def load_whisper_model(model_size: str = "base"):
    return whisper.load_model(model_size)


def main():
    st.set_page_config(page_title="Subtitle Generator", page_icon="🎬", layout="wide")

    # Sidebar UI
    st.sidebar.title("Subtitle Generator")
    st.sidebar.markdown("Unggah file audio/video Anda untuk menghasilkan subtitle .srt secara otomatis.")

    model_size = st.sidebar.selectbox(
        "Pilih model Whisper",
        options=["tiny", "base", "small", "medium", "large"],
        index=1,
        help="Model lebih besar lebih akurat tetapi lebih lambat."
    )

    uploaded_file = st.sidebar.file_uploader(
        "Upload file (mp3, wav, mp4)",
        type=["mp3", "wav", "mp4"],
        accept_multiple_files=False
    )

    st.title("Subtitle Generator")
    st.write("Aplikasi untuk men-generate subtitle (.srt) otomatis menggunakan OpenAI Whisper.")

    placeholder_progress = st.empty()
    progress_bar = None

    if uploaded_file is not None:
        # Save upload to a temp file on disk (Whisper expects a file path or bytes; file path is more stable)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.read())
            temp_upload_path = tmp.name

        # Show file details
        st.info(f"File diunggah: {uploaded_file.name}")

        # Layout: two columns (left: media preview & info, right: progress & results)
        col_preview, col_results = st.columns([1, 1.2], gap="large")

        # Prepare results container and progress placeholder on the right column
        with col_results:
            results_container = st.container()
            progress_placeholder = st.empty()

        # Preview media (video for MP4, audio for MP3/WAV) on the left column
        with col_preview:
            st.markdown("### Preview")
            ext_uploaded = os.path.splitext(uploaded_file.name)[1].lower()
            try:
                with open(temp_upload_path, "rb") as f:
                    media_bytes = f.read()
                if ext_uploaded == ".mp4":
                    st.video(media_bytes)
                elif ext_uploaded in [".mp3", ".wav"]:
                    st.audio(media_bytes)
            except Exception:
                # If preview fails, continue without blocking the workflow
                st.info("Preview tidak tersedia.")
            # Basic file info
            st.caption(f"Ukuran file: {os.path.getsize(temp_upload_path)/1_000_000:.2f} MB")

        # Create a progress bar in the right column
        with col_results:
            progress_bar = progress_placeholder.progress(5, text="Menyiapkan transkripsi...")

        # Extract audio if needed
        audio_path, temp_audio_file = extract_audio_if_needed(temp_upload_path, suffix=".wav", progress=progress_bar)

        # Load whisper model (cached)
        progress_bar.progress(45, text=f"Memuat model Whisper ({model_size})...")
        try:
            model = load_whisper_model(model_size)
        except Exception as e:
            # Clean up temp files before raising
            try:
                if temp_audio_file is not None:
                    os.unlink(temp_audio_file.name)
            except Exception:
                pass
            try:
                os.unlink(temp_upload_path)
            except Exception:
                pass
            st.error(f"Gagal memuat model Whisper: {e}")
            return

        # Transcribe
        progress_bar.progress(65, text="Melakukan transkripsi audio... Ini bisa memakan waktu.")
        try:
            # Whisper accepts file path
            result = model.transcribe(audio_path)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat transkripsi: {e}")
            # Cleanup
            try:
                if temp_audio_file is not None:
                    os.unlink(temp_audio_file.name)
            except Exception:
                pass
            try:
                os.unlink(temp_upload_path)
            except Exception:
                pass
            return

        progress_bar.progress(85, text="Menyusun hasil dan membuat file .srt...")

        # Prepare transcript text
        transcript_text = (result.get("text") or "").strip()
        segments = result.get("segments") or []
        srt_content = build_srt_from_segments(segments)

        # Show results in the right column
        results_container.subheader("Hasil Transkripsi")
        if transcript_text:
            results_container.text_area("Teks Transkripsi", value=transcript_text, height=260)
        else:
            results_container.warning("Tidak ada teks yang dihasilkan dari transkripsi.")

        # Download button for SRT
        srt_filename = os.path.splitext(uploaded_file.name)[0] + ".srt"
        results_container.download_button(
            label="Download Subtitle (.srt)",
            data=srt_content.encode("utf-8"),
            file_name=srt_filename,
            mime="application/x-subrip",
        )

        # Optional: SRT preview inside an expander
        with results_container.expander("Lihat isi file .srt"):
            st.code(srt_content, language="text")

        progress_bar.progress(100, text="Selesai!")

        # Cleanup temp files
        try:
            if temp_audio_file is not None:
                os.unlink(temp_audio_file.name)
        except Exception:
            pass
        try:
            os.unlink(temp_upload_path)
        except Exception:
            pass

    else:
        st.info("Silakan unggah file audio/video dari sidebar untuk memulai.")


if __name__ == "__main__":
    main()
