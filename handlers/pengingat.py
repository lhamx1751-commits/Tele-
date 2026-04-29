from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_akun_akan_expired, sudah_kirim_pengingat,
    simpan_pengingat_terkirim
)
from utils import cek_admin
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


async def pengingat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Akses ditolak.")
        return

    teks = (
        "🔔 *Sistem Pengingat Otomatis*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Pengingat aktif berjalan otomatis\n\n"
        "*Jadwal pengingat:*\n"
        "• 🟠 H-7 sebelum expired\n"
        "• 🟡 H-3 sebelum expired\n"
        "• 🔴 H-1 sebelum expired\n\n"
        "Bot akan kirim pesan otomatis setiap jam ke admin.\n"
        "Jika akun punya Telegram ID, pelanggan juga dinotifikasi."
    )

    keyboard = [
        [InlineKeyboardButton("📋 Cek Sekarang", callback_data="akun_pengingat")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="start_menu")],
    ]

    await update.message.reply_text(
        teks,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cek_pengingat(context: ContextTypes.DEFAULT_TYPE):
    """Job yang berjalan otomatis setiap jam untuk cek expired"""
    today = datetime.now().strftime("%Y-%m-%d")
    notif_hari = [7, 3, 1]

    for hari in notif_hari:
        akun_list = get_akun_akan_expired(hari)

        for akun in akun_list:
            jenis = f"H-{hari}"
            akun_id = akun['id']

            # Cek apakah sudah kirim hari ini
            if sudah_kirim_pengingat(akun_id, jenis, today):
                continue

            # Kirim ke admin
            teks_admin = buat_pesan_pengingat(akun, hari, is_admin=True)
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=teks_admin,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Gagal kirim pengingat ke admin: {e}")

            # Kirim ke pelanggan (jika ada telegram_id)
            if akun['telegram_id']:
                teks_user = buat_pesan_pengingat(akun, hari, is_admin=False)
                try:
                    await context.bot.send_message(
                        chat_id=int(akun['telegram_id']),
                        text=teks_user,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Gagal kirim pengingat ke user {akun['telegram_id']}: {e}")

            # Tandai sudah dikirim
            simpan_pengingat_terkirim(akun_id, jenis, today)
            logger.info(f"Pengingat {jenis} terkirim untuk akun {akun['nama_pelanggan']}")


def buat_pesan_pengingat(akun, hari: int, is_admin: bool) -> str:
    if hari == 1:
        ikon = "🔴"
        judul = "BESOK EXPIRED!"
    elif hari == 3:
        ikon = "🟡"
        judul = f"{hari} HARI LAGI EXPIRED"
    else:
        ikon = "🟠"
        judul = f"{hari} HARI LAGI EXPIRED"

    if is_admin:
        return (
            f"{ikon} *PENGINGAT - {judul}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Pelanggan:* {akun['nama_pelanggan']}\n"
            f"📱 *No. HP:* {akun['no_hp'] or '-'}\n"
            f"📧 *Email:* {akun['email_netflix']}\n"
            f"📦 *Paket:* {akun['paket']}\n"
            f"⏰ *Expired:* {akun['tanggal_expired']}\n"
            f"💰 *Harga:* Rp {akun['harga']:,}\n\n"
            f"_Segera hubungi pelanggan untuk perpanjang!_"
        )
    else:
        return (
            f"{ikon} *Pengingat Langganan Netflix*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Halo *{akun['nama_pelanggan']}*! 👋\n\n"
            f"Langganan Netflix kamu akan *{judul.lower()}*\n\n"
            f"📦 Paket: {akun['paket']}\n"
            f"⏰ Expired: {akun['tanggal_expired']}\n"
            f"💰 Biaya perpanjang: *Rp {akun['harga']:,}*\n\n"
            f"Segera lakukan pembayaran untuk melanjutkan layanan.\n"
            f"Hubungi admin untuk info lebih lanjut. 🙏"
        )
