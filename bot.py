import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from database import init_db
from handlers.start import start_handler
from handlers.akun import akun_handler, akun_callback
from handlers.pembayaran import pembayaran_handler, pembayaran_callback
from handlers.pengingat import pengingat_handler, cek_pengingat
from handlers.admin import admin_handler, admin_callback
from handlers.conversation import (
    tambah_akun_conv, edit_akun_conv, catat_bayar_conv
)

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception:", exc_info=context.error)


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handlers
    app.add_handler(tambah_akun_conv())
    app.add_handler(edit_akun_conv())
    app.add_handler(catat_bayar_conv())

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("akun", akun_handler))
    app.add_handler(CommandHandler("pembayaran", pembayaran_handler))
    app.add_handler(CommandHandler("pengingat", pengingat_handler))
    app.add_handler(CommandHandler("admin", admin_handler))

    # Callback query handlers
    app.add_handler(CallbackQueryHandler(akun_callback, pattern="^akun_"))
    app.add_handler(CallbackQueryHandler(pembayaran_callback, pattern="^bayar_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    # Error handler
    app.add_error_handler(error_handler)

    # Job scheduler untuk pengingat otomatis
    job_queue = app.job_queue
    job_queue.run_repeating(cek_pengingat, interval=3600, first=10)

    logger.info("Bot Netflix Manager aktif!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
