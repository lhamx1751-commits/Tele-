from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_jumlah_akun, get_total_pendapatan_bulan_ini
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_admin = user.id == ADMIN_ID

    total_akun = get_jumlah_akun()
    total_bulan = get_total_pendapatan_bulan_ini()

    teks = (
        f"🎬 *Netflix Account Manager*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Halo, *{user.first_name}*!\n\n"
    )

    if is_admin:
        teks += (
            f"📊 *Ringkasan Hari Ini:*\n"
            f"• Akun Aktif: *{total_akun}/20*\n"
            f"• Pendapatan Bulan Ini: *Rp {total_bulan:,}*\n\n"
            f"🔧 *Menu Admin tersedia*\n\n"
        )

    teks += "Pilih menu di bawah ini:"

    if is_admin:
        keyboard = [
            [
                InlineKeyboardButton("📋 Daftar Akun", callback_data="akun_list"),
                InlineKeyboardButton("➕ Tambah Akun", callback_data="akun_tambah"),
            ],
            [
                InlineKeyboardButton("💰 Pembayaran", callback_data="bayar_menu"),
                InlineKeyboardButton("🔔 Pengingat", callback_data="akun_pengingat"),
            ],
            [
                InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_menu"),
            ],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📋 Info Akun Saya", callback_data="akun_saya")],
            [InlineKeyboardButton("💰 Status Pembayaran", callback_data="bayar_status")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            teks, parse_mode='Markdown', reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            teks, parse_mode='Markdown', reply_markup=reply_markup
        )
        
