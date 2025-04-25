import os
import logging
import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# API Key configurations
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Gemini model configuration
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Caching
news_cache = {'timestamp': None, 'data': None}
weather_cache = {'timestamp': None, 'data': None}
CACHE_DURATION = timedelta(minutes=15)

# Personality prompt
BOT_PERSONALITY = """Saya adalah asisten AI yang profesional dan ramah, siap membantu Anda dengan berbagai informasi dan layanan."""
RESPONSE_INSTRUCTION = "Jawaban harus informatif, sopan, dan mudah dipahami."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Halo! Saya adalah asisten AI yang siap membantu Anda.\n'
        'Gunakan perintah seperti /berita untuk melihat berita terkini atau /cuaca [nama kota].'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '/berita - Tampilkan berita terbaru\n'
        '/cuaca [kota] - Tampilkan info cuaca\n'
        'Ketik pesan apa saja untuk berdiskusi dengan AI.'
    )

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not NEWS_API_KEY:
            await update.message.reply_text("Konfigurasi API berita belum tersedia.")
            return

        current_time = datetime.now()
        global news_cache

        if news_cache['timestamp'] and current_time - news_cache['timestamp'] < CACHE_DURATION:
            articles = news_cache['data']
        else:
            url = 'https://gnews.io/api/v4/top-headlines'
            params = {
                'token': NEWS_API_KEY,
                'lang': 'id',
                'country': 'id',
                'max': 5
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            news_data = response.json()

            raw_articles = news_data.get('articles', [])
            if not raw_articles:
                await update.message.reply_text("Tidak ada berita yang tersedia saat ini.")
                return

            articles = []
            for article in raw_articles:
                title = article.get('title', '')
                description = article.get('description', '')
                link = article.get('url', '')
                source = article.get('source', {}).get('name', '')

                summary = ""
                if description:
                    try:
                        prompt = f"Buatkan ringkasan singkat (maks 3 kalimat) dari berita berikut:\n\n{description}"
                        summary_result = model.generate_content(prompt)
                        summary = summary_result.text.strip()
                    except Exception as e:
                        logging.warning(f"Gagal merangkum dengan Gemini: {str(e)}")
                        summary = description if len(description) <= 200 else description[:200] + "..."

                articles.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'source': source
                })

            news_cache = {'timestamp': current_time, 'data': articles}

        if articles:
            response_text = "📰 *Berita Terkini:*\n\n"
            for i, article in enumerate(articles, start=1):
                response_text += f"{i}. *{article['title']}*\n"
                if article['source']:
                    response_text += f"   Sumber: {article['source']}\n"
                if article['summary']:
                    response_text += f"   Ringkasan: {article['summary']}\n"
                response_text += f"   Link: {article['link']}\n\n"
            await update.message.reply_text(response_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("Tidak ada berita yang dapat ditampilkan.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error request GNews: {str(e)}")
        await update.message.reply_text("Gagal terhubung ke layanan berita.")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        await update.message.reply_text("Terjadi kesalahan saat mengambil berita.")

async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text('Format: /cuaca [nama kota]')
            return

        city = ' '.join(context.args)
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=id'
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            humidity = data['main']['humidity']
            reply = (
                f"🌤️ Cuaca di {city} saat ini:\n"
                f"Suhu: {temp}°C\n"
                f"Kondisi: {desc}\n"
                f"Kelembaban: {humidity}%"
            )
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("Kota tidak ditemukan.")

    except Exception as e:
        logging.error(f"Error cuaca: {str(e)}")
        await update.message.reply_text("Terjadi kesalahan saat mengambil data cuaca.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        prompt = f"{BOT_PERSONALITY}\n{RESPONSE_INSTRUCTION}\n\nPengguna: {user_input}\n\nBalasan:"
        result = model.generate_content(prompt)
        await update.message.reply_text(result.text)
    except Exception as e:
        logging.error(f"Error AI: {str(e)}")
        await update.message.reply_text("Terjadi kesalahan saat memproses pesan Anda.")

def main():
    try:
        if not TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN tidak ditemukan di environment.")

        app = Application.builder().token(TELEGRAM_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("berita", get_news))
        app.add_handler(CommandHandler("cuaca", get_weather))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        app.run_polling()

    except Exception as e:
        logging.error(f"Startup error: {str(e)}")

if __name__ == '__main__':
    main()
