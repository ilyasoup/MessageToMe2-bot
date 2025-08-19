import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import os

# --- Храни токен в переменных окружения ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8389234141:AAHm35p7eaKP1Riub6LQq6MF_bryzN4Xxys")

# Хранилище сообщений и статистики
user_data = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- меню с ссылкой ---
async def send_main_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    link = f"https://t.me/{context.bot.username}?start={user_id}"
    keyboard = [
        [InlineKeyboardButton("🔗 Поделиться ссылкой", url=f"https://t.me/share/url?url={link}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"Начните получать анонимные вопросы прямо сейчас!\n\n"
        f"👉 {link}\n\n"
        f"Разместите эту ссылку ☝️ в описании своего профиля Telegram, TikTok, Instagram (stories), "
        f"чтобы вам могли написать 💬"
    )

    if isinstance(update_or_query, Update) and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update_or_query.edit_message_text(text, reply_markup=reply_markup)


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data.setdefault(user_id, {"received": 0, "sent": 0, "users": set()})

    # Если пришли с параметром
    if context.args:
        target_id = int(context.args[0])
        sender_id = update.effective_user.id

        # Статистика
        user_data.setdefault(sender_id, {"received": 0, "sent": 0, "users": set()})
        user_data[sender_id]["sent"] += 1
        user_data[sender_id]["users"].add(target_id)

        keyboard = [
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🚀 Здесь можно отправить анонимное сообщение человеку, который опубликовал эту ссылку\n\n"
            "🖊 Напишите сюда всё, что хотите ему передать, и через несколько секунд он получит ваше сообщение, "
            "но не будет знать от кого\n\n"
            "Отправить можно:\n"
            "📸 фото, 🎥 видео, 💬 текст, 🔊 голосовые, 📷 видеосообщения (кружки), ✨ стикеры",
            reply_markup=reply_markup
        )

        context.user_data["reply_to"] = target_id
    else:
        await send_main_menu(update, context, user_id)


# --- кнопки ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        user_id = query.from_user.id
        await send_main_menu(query, context, user_id)


# --- пересылка сообщений ---
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_to = context.user_data.get("reply_to")

    if reply_to:
        # Уведомление получателю
        await context.bot.send_message(chat_id=reply_to, text="📩 Получено новое анонимное сообщение!")
        # Само сообщение
        await update.message.copy(chat_id=reply_to)

        user_data.setdefault(reply_to, {"received": 0, "sent": 0, "users": set()})
        user_data[reply_to]["received"] += 1
        context.user_data["reply_to"] = None

        await update.message.reply_text("✅ Сообщение отправлено анонимно!")
    else:
        user_id = update.effective_user.id
        await send_main_menu(update, context, user_id)


# --- статистика ---
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.ALL, forward_message))

    app.run_polling()


if __name__ == "__main__":
    main()