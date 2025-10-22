import os
import re
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# ----------------- LOAD ENV -----------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "").split(",")))

# ----------------- CONFIG -----------------
WARN_LIMIT = 3
MUTE_SECONDS = 10 * 60  # 10 minutes
user_warns = {}  # {(chat_id, user_id): warn_count}

# Regex to detect links
LINK_RE = re.compile(r"(?:(?:https?://)|(?:www\.)|(?:t\.me/)|(?:telegram\.me/)|(?:\S+@\S+\.\S+))", re.IGNORECASE)

# ----------------- HELPERS -----------------
def is_link(text: str) -> bool:
    if not text:
        return False
    return bool(LINK_RE.search(text))

async def warn_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, username: str, warn_count: int):
    remaining = WARN_LIMIT - warn_count
    if remaining > 0:
        text = (
            f"@{username or user_id}, STEM Warning {warn_count}/{WARN_LIMIT}. "
            f"You have {remaining} warning(s) left. Do not post external links."
        )
    else:
        text = (
            f"@{username or user_id}, STEM Warning {warn_count}/{WARN_LIMIT}. "
            "You have reached the maximum warnings. You will be muted for 10 minutes."
        )
    await context.bot.send_message(chat_id=chat_id, text=text)

async def restrict_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, duration_seconds: int):
    permissions = ChatPermissions(can_send_messages=False)
    until_date = datetime.utcnow() + timedelta(seconds=duration_seconds)
    await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=permissions, until_date=until_date)
    await context.bot.send_message(chat_id=chat_id, text=f"User [{user_id}] has been muted for 10 minutes by STEM rules.")

async def ban_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
    await context.bot.send_message(chat_id=chat_id, text=f"User [{user_id}] has been banned by STEM for repeated link violations.")

# ----------------- HANDLER -----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    # Only for groups
    if chat.type not in ("group", "supergroup"):
        return

    # Exempt admins
    if user.id in ADMIN_IDS:
        return

    text = message.text_html or message.text
    if not is_link(text):
        return

    key = (chat.id, user.id)
    warn_count = user_warns.get(key, 0) + 1
    user_warns[key] = warn_count

    if warn_count < WARN_LIMIT:
        await warn_user(context, chat.id, user.id, user.username or str(user.id), warn_count)
    elif warn_count == WARN_LIMIT:
        await warn_user(context, chat.id, user.id, user.username or str(user.id), warn_count)
        await restrict_user(context, chat.id, user.id, MUTE_SECONDS)

        # Schedule post-mute check
        async def post_mute_check():
            await asyncio.sleep(MUTE_SECONDS + 1)
            # If user posts another link -> ban
            current_warn = user_warns.get(key, 0)
            if current_warn > WARN_LIMIT:
                await ban_user(context, chat.id, user.id)
                user_warns.pop(key, None)
            else:
                user_warns.pop(key, None)

        context.application.create_task(post_mute_check())
    else:
        await ban_user(context, chat.id, user.id)
        user_warns.pop(key, None)

# ----------------- START BOT -----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("STEM Link Moderator Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
