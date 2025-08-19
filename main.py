import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- Вставь сюда свой токен ---
BOT_TOKEN = "8389234141:AAHm35p7eaKP1Riub6LQq6MF_bryzN4Xxys"

# Хранилище сообщений и статистики
user_data = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data.setdefault(user_id, {"received": 0, "sent": 0, "users": set()})
    await update.message.reply_text(
        "👋🏼 Привет, чтобы начать, отправь ссылку друзьям, чтобы они могли написать тебе анонимное сообщение:\n\n"
        f"https://t.me/{context.bot.username}?start={user_id}"
    )


async def handle_start_param(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка перехода по чужой ссылке"""
    args = context.args
    if not args:
        await start(update, context)
        return

    target_id = int(args[0])
    sender_id = update.effective_user.id

    # Увеличиваем статистику
    user_data.setdefault(sender_id, {"received": 0, "sent": 0, "users": set()})
    user_data[sender_id]["sent"] += 1
    user_data[sender_id]["users"].add(target_id)

    keyboard = [[InlineKeyboardButton("✍️ Чтобы написать сообщение тыкни тут", callback_data=f"reply_{target_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Погнали 👇",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка «Ответить»"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("reply_"):
        target_id = int(query.data.split("_")[1])
        context.user_data["reply_to"] = target_id
        await query.edit_message_text("✍️ Напиши сообщение, оно будет доставлено анонимно, так же можешь отправить фото, голосовое, или кружок.")


async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылка любых сообщений"""
    sender_id = update.effective_user.id
    reply_to = context.user_data.get("reply_to")

    if reply_to:
        await update.message.copy(chat_id=reply_to)
        user_data.setdefault(reply_to, {"received": 0, "sent": 0, "users": set()})
        user_data[reply_to]["received"] += 1
        context.user_data["reply_to"] = None
        await update.message.reply_text("✅ Сообщение отправлено анонимно!")
    else:
        await update.message.reply_text("Используй команду /start, чтобы отправить анонимное сообщение, или получить свою ссылку.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = user_data.get(user_id, {"received": 0, "sent": 0, "users": set()})
    await update.message.reply_text(
        f"📊 Твоя статистика:\n"
        f"Получено сообщений всего: {stats['received']}\n"
        f"Отправлено сообщений: {stats['sent']}\n"
        f"Уникальных отправителей: {len(stats['users'])}"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start_param))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.ALL, forward_message))

    app.run_polling()


if __name__ == "__main__":
    main()