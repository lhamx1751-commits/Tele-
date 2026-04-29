from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_jumlah_akun, get_total_pendapatan_bulan_ini, get_semua_akun
from utils import cek_admin, hitung_sisa_hari
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Akses ditolak.")
        return
    await tampil_admin_panel(update, context)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not cek_admin(query.from_user.id):
        await query.edit_message_text("⛔ Akses ditolak.")
        return

    if data == "admin_menu":
        await tampil_admin_panel(update, context)

    elif data == "admin_statistik":
        await tampil_statistik(update, context)

    elif data == "admin_akun_expired":
        await tampil_akun_expired(update, context)


async def tampil_admin_panel(update, context):
    query = update.callback_query if update.callback_query else None

    total_akun = get_jumlah_akun()
    total_bulan = get_total_pendapatan_bulan_ini()

    # Hitung akun akan expired
    from database import get_akun_akan_expired
    expired_1 = len(get_akun_akan_expired(1))
    expired_3 = len(get_akun_akan_expired(3))
    expired_7 = len(get_akun_akan_expired(7))

    teks = (
        f"⚙️ *Admin Panel*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Status Sistem:*\n"
        f"• Total Akun: *{total_akun}/20*\n"
        f"• Pendapatan Bulan Ini: *Rp {total_bulan:,}*\n\n"
        f"⚠️ *Perlu Perhatian:*\n"
        f"• 🔴 Expired besok: {expired_1} akun\n"
        f"• 🟡 Expired 3 hari: {expired_3} akun\n"
        f"• 🟠 Expired 7 hari: {expired_7} akun\n"
    )

    keyboard = [
        [InlineKeyboardButton("📊 Statistik Lengkap", callback_data="admin_statistik")],
        [InlineKeyboardButton("⚠️ Akun Akan Expired", callback_data="admin_akun_expired")],
        [
            InlineKeyboardButton("📋 Semua Akun", callback_data="akun_list"),
            InlineKeyboardButton("💰 Pembayaran", callback_data="bayar_menu"),
        ],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="start_menu")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(teks, parse_mode='Markdown', reply_markup=reply_markup)


async def tampil_statistik(update, context):
    query = update.callback_query
    akun_list = get_semua_akun()

    if not akun_list:
        teks = "📊 *Statistik*\n\nBelum ada data akun."
    else:
        total = len(akun_list)
        aktif = sum(1 for a in akun_list if hitung_sisa_hari(a['tanggal_expired']) > 0)
        expired = total - aktif
        total_harga = sum(a['harga'] for a in akun_list if hitung_sisa_hari(a['tanggal_expired']) > 0)
        pendapatan = get_total_pendapatan_bulan_ini()

        # Distribusi paket
        paket_count = {}
        for a in akun_list:
            p = a['paket']
            paket_count[p] = paket_count.get(p, 0) + 1

        teks = (
            f"📊 *Statistik Lengkap*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 *Akun:*\n"
            f"• Total: {total}\n"
            f"• Aktif: {aktif}\n"
            f"• Expired: {expired}\n\n"
            f"💰 *Keuangan:*\n"
            f"• Potensi/bulan: Rp {total_harga:,}\n"
            f"• Terkumpul bulan ini: Rp {pendapatan:,}\n\n"
            f"📦 *Distribusi Paket:*\n"
        )
        for paket, jumlah in paket_count.items():
            teks += f"• {paket}: {jumlah} akun\n"

    keyboard = [[InlineKeyboardButton("« Kembali", callback_data="admin_menu")]]
    await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


async def tampil_akun_expired(update, context):
    query = update.callback_query
    from database import get_akun_akan_expired

    semua_expired = []
    for hari in [1, 3, 7]:
        for akun in get_akun_akan_expired(hari):
            semua_expired.append((hari, akun))

    if not semua_expired:
        teks = "✅ *Tidak ada akun yang akan expired dalam 7 hari ke depan.*"
    else:
        teks = "⚠️ *Akun Akan Expired*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for hari, akun in semua_expired:
            ikon = "🔴" if hari == 1 else "🟡" if hari == 3 else "🟠"
            teks += (
                f"{ikon} *{akun['nama_pelanggan']}* (H-{hari})\n"
                f"   📱 {akun['no_hp'] or '-'} | Rp {akun['harga']:,}\n\n"
            )

    keyboard = [[InlineKeyboardButton("« Kembali", callback_data="admin_menu")]]
    await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
