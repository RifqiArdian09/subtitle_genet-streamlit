import os
import io
import tempfile
from datetime import timedelta
from typing import Tuple, Optional
import hashlib

import streamlit as st
import whisper

try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
except Exception:
    from moviepy.editor import VideoFileClip

def format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def build_srt_from_segments(segments) -> str:
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_ts = format_timestamp(seg.get("start", 0.0))
        end_ts = format_timestamp(seg.get("end", 0.0))
        text = (seg.get("text") or "").strip()
        lines.append(str(i))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"

def extract_audio_if_needed(upload_path: str, suffix: str, progress=None) -> Tuple[str, Optional[tempfile.NamedTemporaryFile]]:
    ext = os.path.splitext(upload_path)[1].lower()
    if ext in [".mp3", ".wav"]:
        return upload_path, None

    if ext == ".mp4":
        if progress:
            progress.progress(20, text="Mengekstrak audio dari video...")
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio.close()
        with VideoFileClip(upload_path) as clip:
            clip.audio.write_audiofile(temp_audio.name, fps=16000)
        if progress:
            progress.progress(35, text="Audio berhasil diekstrak.")
        return temp_audio.name, temp_audio

    return upload_path, None


@st.cache_resource(show_spinner=False)
def load_whisper_model(model_size: str = "base"):
    return whisper.load_model(model_size)


def _md5_of_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    st.set_page_config(page_title="Subtitle Generator", page_icon="🎬", layout="wide")

    header = st.container()
    with header:
        st.markdown("""
        <div style="line-height:1.2">
          <h1 style="margin-bottom:2px;">Subtitle Generator</h1>
          <p style="color:#6b7280;margin-top:0;">Generate subtitle (.srt) otomatis dari audio/video menggunakan OpenAI Whisper</p>
        </div>
        """, unsafe_allow_html=True)

    controls = st.container()
    with controls:
        col1, col2 = st.columns([1, 1])
        with col1:
            model_size = st.selectbox(
                "Pilih model Whisper",
                options=["tiny", "base", "small", "medium", "large"],
                index=1,
                help="Model lebih besar lebih akurat tetapi lebih lambat."
            )
        with col2:
            uploaded_file = st.file_uploader(
                "Upload file (mp3, wav, mp4)",
                type=["mp3", "wav", "mp4"],
                accept_multiple_files=False
            )

    placeholder_progress = st.empty()
    progress_bar = None

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.read())
            temp_upload_path = tmp.name

        st.info(f"File diunggah: {uploaded_file.name}")
    
        col_preview, col_results = st.columns([1, 1.2], gap="large")

        with col_results:
            results_container = st.container()
            progress_placeholder = st.empty()

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
                st.info("Preview tidak tersedia.")
            st.caption(f"Ukuran file: {os.path.getsize(temp_upload_path)/1_000_000:.2f} MB")

        with col_results:
            progress_bar = progress_placeholder.empty()

        file_key = f"{_md5_of_file(temp_upload_path)}::{model_size}"
        if 'results_cache' not in st.session_state:
            st.session_state['results_cache'] = {}

        cached = st.session_state['results_cache'].get(file_key)

        if cached is None:
            progress_bar = progress_placeholder.progress(5, text="Menyiapkan transkripsi...")
            audio_path, temp_audio_file = extract_audio_if_needed(temp_upload_path, suffix=".wav", progress=progress_bar)

            progress_bar.progress(45, text=f"Memuat model Whisper ({model_size})...")
            try:
                model = load_whisper_model(model_size)
            except Exception as e:
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

            progress_bar.progress(65, text="Melakukan transkripsi audio... Ini bisa memakan waktu.")
            try:
                result = model.transcribe(audio_path)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat transkripsi: {e}")
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

            transcript_text = (result.get("text") or "").strip()
            segments = result.get("segments") or []
            srt_content = build_srt_from_segments(segments)

            st.session_state['results_cache'][file_key] = {
                'transcript_text': transcript_text,
                'srt_content': srt_content,
            }

            progress_bar.progress(100, text="Selesai!")

            try:
                if temp_audio_file is not None:
                    os.unlink(temp_audio_file.name)
            except Exception:
                pass
        else:
            transcript_text = cached['transcript_text']
            srt_content = cached['srt_content']
            progress_placeholder.info("Menggunakan hasil yang sudah diproses.")

        results_container.subheader("Hasil Transkripsi")
        if transcript_text:
            results_container.text_area("Teks Transkripsi", value=transcript_text, height=260)
        else:
            results_container.warning("Tidak ada teks yang dihasilkan dari transkripsi.")

        srt_filename = os.path.splitext(uploaded_file.name)[0] + ".srt"
        results_container.download_button(
            label="Download Subtitle (.srt)",
            data=srt_content.encode("utf-8"),
            file_name=srt_filename,
            mime="application/x-subrip",
        )

        txt_filename = os.path.splitext(uploaded_file.name)[0] + ".txt"
        results_container.download_button(
            label="Download Transkrip (.txt)",
            data=(transcript_text + "\n").encode("utf-8"),
            file_name=txt_filename,
            mime="text/plain",
        )

        with results_container.expander("Lihat isi file .srt"):
            st.code(srt_content, language="text")

        try:
            os.unlink(temp_upload_path)
        except Exception:
            pass

    else:
        st.info("Silakan unggah file audio/video untuk memulai.")


if __name__ == "__main__":
    main()
