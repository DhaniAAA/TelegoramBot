import os
import logging
import feedparser
import google.generativeai as genai
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Inisialisasi Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')  # atau gemini-pro

# API Keys
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Cache
news_cache = {'timestamp': None, 'data': None}
CACHE_DURATION = timedelta(minutes=15)

# Bot personality
BOT_PERSONALITY = "Saya adalah asisten AI profesional yang ramah dan siap membantu Anda."
RESPONSE_INSTRUCTION = "Respon harus profesional, informatif, dan tetap ramah."

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya adalah asisten AI. Ketik /berita untuk melihat berita terbaru atau /cuaca [kota] untuk cek cuaca."
    )

# Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Perintah:\n"
        "/berita - Menampilkan berita terbaru dari CNN Indonesia\n"
        "/cuaca [kota] - Melihat cuaca di kota Anda\n"
        "Tanya apa saja, saya akan bantu jawab!"
    )
    await update.message.reply_text(help_text)

# Fungsi berita dari RSS CNN Indonesia
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global news_cache
        current_time = datetime.now()

        if news_cache['timestamp'] and current_time - news_cache['timestamp'] < CACHE_DURATION:
            articles = news_cache['data']
        else:
            rss_url = 'https://www.cnnindonesia.com/nasional/rss'
            feed = feedparser.parse(rss_url)

            articles = []
            for entry in feed.entries[:5]:
                title = entry.title
                link = entry.link
                content = entry.summary

                prompt = f"Buat ringkasan singkat (maksimal 3 kalimat) dari berita berikut:\n\n{content}"
                try:
                    response = model.generate_content(prompt)
                    summary = response.text.strip() if response else ''
                except Exception as e:
                    logging.warning(f"Ringkasan gagal: {str(e)}")
                    summary = ''

                articles.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'source': "CNN Indonesia"
                })

            news_cache = {'timestamp': current_time, 'data': articles}

        if articles:
            news_text = '📰 Berita Terkini dari CNN Indonesia:\n\n'
            for i, article in enumerate(articles, 1):
                news_text += f"{i}. {article['title']}\n"
                news_text += f"   Sumber: {article['source']}\n"
                if article['summary']:
                    news_text += f"   Ringkasan: {article['summary']}\n"
                news_text += f"   Link: {article['link']}\n\n"
            await update.message.reply_text(news_text)
        else:
            await update.message.reply_text("Mohon maaf, tidak ada berita saat ini.")
    except Exception as e:
        logging.error(f"Gagal mengambil berita: {str(e)}")
        await update.message.reply_text("Terjadi kesalahan saat mengambil berita.")

# Cuaca
async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Gunakan format: /cuaca [nama kota]")
            return

        city = ' '.join(context.args)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=id"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            desc = data['weather'][0]['description']
            temp = data['main']['temp']
            humidity = data['main']['humidity']

            cuaca_text = (
                f"🌤️ Cuaca di {city.title()}:\n"
                f"Suhu: {temp}°C\n"
                f"Kondisi: {desc}\n"
                f"Kelembaban: {humidity}%"
            )
            await update.message.reply_text(cuaca_text)
        else:
            await update.message.reply_text("Kota tidak ditemukan.")
    except Exception as e:
        logging.error(f"Cuaca error: {str(e)}")
        await update.message.reply_text("Gagal mengambil informasi cuaca.")

# AI Chat
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        prompt = f"{BOT_PERSONALITY}\n{RESPONSE_INSTRUCTION}\n\nPesan dari pengguna: {user_message}\n\nBalasan:"
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"AI error: {str(e)}")
        await update.message.reply_text("Maaf, terjadi kesalahan dalam memproses pesan.")

# Main
def main():
    try:
        app = (
            Application.builder()
            .token(TELEGRAM_TOKEN)
            .concurrent_updates(False)
            .build()
        )

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("berita", get_news))
        app.add_handler(CommandHandler("cuaca", get_weather))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True, close_loop=True)
    except Exception as e:
        logging.error(f"Bot gagal dijalankan: {str(e)}")

if __name__ == '__main__':
    main()
