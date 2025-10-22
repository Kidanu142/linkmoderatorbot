import os
import logging
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
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 8443))

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        "I'm a simple Telegram bot deployed on Render!\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
🤖 Available Commands:

/start - Start the bot
/help - Show this help message
/echo [text] - Echo your text
/about - About this bot

You can also just send me any message and I'll repeat it!
    """
    await update.message.reply_text(help_text)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    text = update.message.text
    if text.startswith('/echo'):
        # Remove the command part if used with /echo
        text = ' '.join(text.split()[1:]) or "You didn't provide any text!"
    
    await update.message.reply_text(f"🔁 You said: {text}")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show information about the bot."""
    about_text = """
🤖 Simple Telegram Bot

This is a basic Telegram bot deployed on Render using:
- Python-telegram-bot
- Environment variables
- Webhook setup

Built with ❤️ for deployment on Render!
    """
    await update.message.reply_text(about_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        return

    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("echo", echo))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    if os.getenv('RENDER'):  # Running on Render
        webhook_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/{BOT_TOKEN}"
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url
        )
    else:  # Running locally
        application.run_polling()

if __name__ == '__main__':
    main()
