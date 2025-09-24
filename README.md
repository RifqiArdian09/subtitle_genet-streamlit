# Subtitle Generator 🎬

Aplikasi web untuk men-generate subtitle (.srt) otomatis dari file audio/video menggunakan OpenAI Whisper.

## Fitur

- ✅ Support format file: MP3, WAV, MP4
- ✅ Ekstraksi audio otomatis dari video
- ✅ Multiple model Whisper (tiny, base, small, medium, large)
- ✅ Preview media sebelum diproses
- ✅ Download hasil subtitle dalam format .srt
- ✅ Interface yang user-friendly dengan Streamlit

## Instalasi

1. Clone repository ini
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Pastikan ffmpeg terinstall di sistem Anda

## Cara Penggunaan

1. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

2. Buka browser dan akses `http://localhost:8501`

3. Pilih model Whisper (base direkomendasikan untuk keseimbangan akurasi dan kecepatan)

4. Upload file audio/video Anda

5. Tunggu proses transkripsi selesai

6. Download file subtitle (.srt) yang dihasilkan

## Requirements

- Python 3.8+
- Streamlit
- OpenAI Whisper
- MoviePy
- FFmpeg

## Model Whisper

| Model | Ukuran | Kecepatan | Akurasi |
|-------|--------|-----------|---------|
| tiny  | 39 MB  | Sangat Cepat | Rendah |
| base  | 74 MB  | Cepat | Sedang |
| small | 244 MB | Sedang | Baik |
| medium| 769 MB | Lambat | Sangat Baik |
| large | 1550 MB| Sangat Lambat | Excellent |

## Catatan

- File video akan diekstrak audionya secara otomatis
- Proses transkripsi membutuhkan waktu tergantung ukuran file dan model yang dipilih
- Hasil terbaik didapat dengan audio yang jernih dan minim noise
