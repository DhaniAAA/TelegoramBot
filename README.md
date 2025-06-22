# TelegoramBot

## Deskripsi
Bot Telegram yang dapat memberikan informasi berita, cuaca, dan menjawab pertanyaan menggunakan AI Gemini.

## Fitur
- Menampilkan berita terbaru dari CNN Indonesia
- Menampilkan informasi cuaca berdasarkan kota
- Menjawab pertanyaan menggunakan AI Gemini

## Cara Deploy ke Render

### Persiapan
1. Buat akun di [Render](https://render.com/) jika belum memilikinya
2. Pastikan repository sudah di-push ke GitHub

### Langkah-langkah Deploy
1. Login ke dashboard Render
2. Klik "New +" dan pilih "Blueprint"
3. Hubungkan repository GitHub yang berisi kode bot ini
4. Render akan otomatis mendeteksi file `render.yaml` dan mengonfigurasi service
5. Isi environment variables yang diperlukan:
   - `TELEGRAM_TOKEN`: Token bot Telegram dari BotFather
   - `GEMINI_API_KEY`: API key dari Google AI Studio
   - `WEATHER_API_KEY`: API key dari OpenWeatherMap
6. Klik "Apply" untuk memulai proses deployment

### Alternatif (Tanpa Blueprint)
1. Login ke dashboard Render
2. Klik "New +" dan pilih "Web Service"
3. Hubungkan repository GitHub
4. Isi konfigurasi berikut:
   - **Name**: Nama untuk service Anda
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Di bagian "Environment Variables", tambahkan semua variabel yang diperlukan
6. Klik "Create Web Service"

## Memantau Bot
Setelah deployment berhasil, Anda dapat memantau log bot dari dashboard Render untuk memastikan bot berjalan dengan baik.

## Troubleshooting
Jika bot tidak berjalan dengan baik:
1. Periksa log di dashboard Render
2. Pastikan semua environment variables sudah diisi dengan benar
3. Pastikan bot sudah diaktifkan di BotFather