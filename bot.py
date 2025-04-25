import os
import logging
import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from bs4 import BeautifulSoup

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
cnn_cache = {'timestamp': None, 'data': None}

CACHE_DURATION = timedelta(minutes=15)

# Bot personality and response instructions
BOT_PERSONALITY = """Saya adalah asisten AI yang profesional dan ramah, siap membantu Anda dengan berbagai informasi dan layanan. Saya akan memberikan respon yang informatif dan bermanfaat."""
RESPONSE_INSTRUCTION = "Respon harus profesional, informatif, dan tetap ramah."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Halo! Saya adalah asisten AI yang siap membantu Anda. Saya dapat memberikan informasi, saran, dan bantuan sesuai kebutuhan Anda. Silakan ajukan pertanyaan atau gunakan perintah yang tersedia.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        'Selamat datang! Saya siap membantu Anda dengan layanan berikut:\n\n'
        'Perintah yang tersedia:\n'
        '/berita - Mendapatkan berita terbaru\n'
        '/cuaca [kota] - Cek cuaca di kota yang Anda inginkan'
    )
    await update.message.reply_text(help_text)

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get and summarize latest news from CNN Indonesia."""
    try:
        global cnn_cache
        current_time = datetime.now()

        if cnn_cache['timestamp'] and current_time - cnn_cache['timestamp'] < CACHE_DURATION:
            articles = cnn_cache['data']
        else:
            url = 'https://www.cnnindonesia.com/'
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            articles = []

            # Get articles from main section
            main_articles = soup.select('article.text-gray-800')
            for article in main_articles[:5]:  # Limit to 5 articles
                title_elem = article.select_one('h2')
                if title_elem:
                    title = title_elem.text.strip()
                    link = article.find('a')['href'] if article.find('a') else ''
                    
                    # Get article content
                    if link:
                        article_response = requests.get(link)
                        article_soup = BeautifulSoup(article_response.text, 'lxml')
                        content_elem = article_soup.select_one('div.detail-text')
                        content = content_elem.get_text(strip=True) if content_elem else ''
                        
                        # Generate summary using Gemini AI
                        prompt = f"Buatkan ringkasan singkat dan informatif (maksimal 3 kalimat) dari berita berikut:\n\n{content}"
                        summary_response = model.generate_content(prompt)
                        summary = summary_response.text if summary_response else ''
                    else:
                        content = ''
                        summary = ''
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'summary': summary
                    })

            cnn_cache = {'timestamp': current_time, 'data': articles}

        if articles:
            news_text = '📰 Berita Terkini dari CNN Indonesia:\n\n'
            for i, article in enumerate(articles, 1):
                news_text += f"{i}. {article['title']}\n"
                if article['summary']:
                    news_text += f"   Ringkasan: {article['summary']}\n"
                news_text += f"   Sumber: {article['link']}\n\n"
            await update.message.reply_text(news_text)
        else:
            await update.message.reply_text('Mohon maaf, tidak ada berita yang dapat diambil saat ini.')
    except Exception as e:
        logging.error(f"Error fetching CNN news: {str(e)}")
        await update.message.reply_text('Mohon maaf, terjadi kesalahan saat mengambil berita dari CNN Indonesia.')

async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get weather information from OpenWeatherMap."""
    try:
        if not context.args:
            await update.message.reply_text('Silakan berikan nama kota. Contoh: /cuaca Jakarta')
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
            await update.message.reply_text('Mohon maaf, kota yang Anda cari tidak ditemukan.')
    except Exception as e:
        logging.error(f"Error fetching weather: {str(e)}")
        await update.message.reply_text('Mohon maaf, terjadi kesalahan saat mengecek cuaca.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and respond using Gemini AI."""
    try:
        # Get user message
        user_message = update.message.text

        # Prepare message with personality and instructions
        prompt = f"{BOT_PERSONALITY}\n{RESPONSE_INSTRUCTION}\n\nPesan dari pengguna: {user_message}\n\nBerikan respon:"

        # Generate response using Gemini AI
        response = model.generate_content(prompt)

        # Send response back to user
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        await update.message.reply_text('Mohon maaf, terjadi kesalahan dalam memproses pesan Anda. Silakan coba lagi.')

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