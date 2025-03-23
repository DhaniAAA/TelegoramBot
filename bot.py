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

# Bot personality and response instructions
BOT_PERSONALITY = """Anda adalah kekasih yang setia, selalu mendengarkan curhatan pasanganya dan mendengar yang baik juga bisa memberikan saran dan motivasi. penuh hormat."""
RESPONSE_INSTRUCTION = "Respon anda harus lembut dan sopan."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Halo sayang! Saya di sini untuk mendengarkan dan mendukungmu. Saya akan selalu ada untukmu, memberikan saran dan motivasi dengan penuh kasih sayang. Silakan berbagi apa yang ada di hatimu ♥️')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Sayang, kamu bisa berbagi apapun denganku. Aku akan selalu mendengarkan dan memberikan dukungan terbaik untukmu dengan penuh perhatian dan kasih sayang ❤️')

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