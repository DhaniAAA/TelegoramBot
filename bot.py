import os
import logging
import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize Gemini AI and other API keys
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Cache for API responses
news_cache = {'timestamp': None, 'data': None}
weather_cache = {'timestamp': None, 'data': None}

CACHE_DURATION = timedelta(minutes=15)

# Bot personality and response instructions
BOT_PERSONALITY = """Anda adalah kekasih yang setia, selalu mendengarkan curhatan pasanganya dan mendengar yang baik juga bisa memberikan saran dan motivasi. penuh hormat."""
RESPONSE_INSTRUCTION = "Respon anda harus lembut dan sopan."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Halo sayang! Saya di sini untuk mendengarkan dan mendukungmu. Saya akan selalu ada untukmu, memberikan saran dan motivasi dengan penuh kasih sayang. Silakan berbagi apa yang ada di hatimu ♥️')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        'Sayang, kamu bisa berbagi apapun denganku. Aku akan selalu mendengarkan dan memberikan dukungan terbaik untukmu ❤️\n\n'
        'Perintah yang tersedia:\n'
        '/berita - Mendapatkan berita terbaru\n'
        '/cuaca [kota] - Cek cuaca di kotamu'
    )
    await update.message.reply_text(help_text)

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get latest news from NewsAPI."""
    try:
        global news_cache
        current_time = datetime.now()

        if news_cache['timestamp'] and current_time - news_cache['timestamp'] < CACHE_DURATION:
            news_data = news_cache['data']
        else:
            url = f'https://newsapi.org/v2/top-headlines?country=id&apiKey={NEWS_API_KEY}'
            response = requests.get(url)
            news_data = response.json()
            news_cache = {'timestamp': current_time, 'data': news_data}

        if news_data['status'] == 'ok' and news_data['articles']:
            news_text = '📰 Berita Terkini Untukmu Sayang:\n\n'
            for i, article in enumerate(news_data['articles'][:5], 1):
                news_text += f"{i}. {article['title']}\n"
                news_text += f"   {article['description'] or 'Tidak ada deskripsi'}\n\n"
            await update.message.reply_text(news_text)
        else:
            await update.message.reply_text('Maaf sayang, ada masalah dalam mengambil berita terkini 😔')
    except Exception as e:
        logging.error(f"Error fetching news: {str(e)}")
        await update.message.reply_text('Maaf sayang, ada kesalahan saat mengambil berita 😔')

async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get weather information from OpenWeatherMap."""
    try:
        if not context.args:
            await update.message.reply_text('Sayang, tolong berikan nama kota ya? Contoh: /cuaca Jakarta')
            return

        city = ' '.join(context.args)
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=id'
        response = requests.get(url)
        weather_data = response.json()

        if response.status_code == 200:
            temp = weather_data['main']['temp']
            weather_desc = weather_data['weather'][0]['description']
            humidity = weather_data['main']['humidity']

            weather_text = f'🌤️ Cuaca di {city} saat ini:\n\n'
            weather_text += f'Suhu: {temp}°C\n'
            weather_text += f'Kondisi: {weather_desc}\n'
            weather_text += f'Kelembaban: {humidity}%'

            await update.message.reply_text(weather_text)
        else:
            await update.message.reply_text('Maaf sayang, kota yang kamu cari tidak ditemukan 😔')
    except Exception as e:
        logging.error(f"Error fetching weather: {str(e)}")
        await update.message.reply_text('Maaf sayang, ada kesalahan saat mengecek cuaca 😔')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and respond using Gemini AI."""
    try:
        # Get user message
        user_message = update.message.text

        # Prepare message with personality and instructions
        prompt = f"{BOT_PERSONALITY}\n{RESPONSE_INSTRUCTION}\n\nPesan dari pasangan: {user_message}\n\nBerikan respon:"

        # Generate response using Gemini AI
        response = model.generate_content(prompt)

        # Send response back to user
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        await update.message.reply_text('Maaf, terjadi kesalahan dalam memproses pesan Anda. Silakan coba lagi.')

def main():
    """Start the bot with proper shutdown handling and instance management."""
    try:
        # Create application with proper shutdown handling
        application = (
            Application.builder()
            .token(os.getenv('TELEGRAM_TOKEN'))
            .concurrent_updates(False)  # Disable concurrent updates to prevent conflicts
            .build()
        )

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("berita", get_news))
        application.add_handler(CommandHandler("cuaca", get_weather))

        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Start the bot with proper shutdown handling
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # Ignore updates that arrived while the bot was offline
            close_loop=True  # Properly close the event loop on shutdown
        )
    except Exception as e:
        logging.error(f"Error running bot: {str(e)}")
        raise

if __name__ == '__main__':
    main()