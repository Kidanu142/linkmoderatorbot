from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Command function ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Viper Mode Activated ⚡")

# --- Main code ---
def main():
    app = ApplicationBuilder().token("8473199054:AAH93VsFFGmgtSZXJtG6nzJWT4eaCyZ_2h8").build()

    app.add_handler(CommandHandler("start", start))

    print("Bot is running... (Press CTRL+C to stop)")
    app.run_polling()

if __name__ == "__main__":
    main()
