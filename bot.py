import os
import logging
import google.generativeai as genai
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

# Initialize Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Halo! Saya adalah bot yang terintegrasi dengan Gemini AI. Silakan kirim pesan, dan saya akan merespons menggunakan AI!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Kirim pesan apapun dan saya akan merespons menggunakan Gemini AI!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and respond using Gemini AI."""
    try:
        # Get user message
        user_message = update.message.text

        # Generate response using Gemini AI
        response = model.generate_content(user_message)

        # Send response back to user
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        await update.message.reply_text('Maaf, terjadi kesalahan dalam memproses pesan Anda. Silakan coba lagi.')

def main():
    """Start the bot."""
    # Create application and pass bot token
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()