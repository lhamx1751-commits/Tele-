from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_riwayat_pembayaran, get_semua_pembayaran_bulan_ini,
    get_total_pendapatan_bulan_ini, get_akun_by_id
)
from utils import format_tanggal, cek_admin
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


async def pembayaran_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Akses ditolak.")
        return
    await tampil_menu_pembayaran(update, context)


async def pembayaran_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not cek_admin(query.from_user.id):
        await query.edit_message_text("⛔ Akses ditolak.")
        return

    if data == "bayar_menu":
        await tampil_menu_pembayaran(update, context)

    elif data == "bayar_laporan":
        await tampil_laporan_bulan(update, context)

    elif data.startswith("bayar_riwayat_"):
        akun_id = int(data.split("_")[2])
        await tampil_riwayat(update, context, akun_id)

    elif data.startswith("bayar_akun_"):
        akun_id = int(data.split("_")[2])
        context.user_data['bayar_akun_id'] = akun_id
        akun = get_akun_by_id(akun_id)
        await query.edit_message_text(
            f"💰 *Catat Pembayaran*\n\n"
            f"👤 *Pelanggan:* {akun['nama_pelanggan']}\n"
            f"💵 *Harga normal:* Rp {akun['harga']:,}\n\n"
            f"Gunakan /catatbayar untuk mencatat pembayaran.",
            parse_mode='Markdown'
        )

    elif data == "bayar_status":
        # Untuk user biasa - cek status bayar mereka
        await tampil_status_bayar_user(update, context)


async def tampil_menu_pembayaran(update, context):
    query = update.callback_query if update.callback_query else None
    total = get_total_pendapatan_bulan_ini()

    teks = (
        f"💰 *Menu Pembayaran*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📆 Pendapatan Bulan Ini: *Rp {total:,}*\n\n"
        f"Pilih opsi:"
    )

    keyboard = [
        [InlineKeyboardButton("📊 Laporan Bulan Ini", callback_data="bayar_laporan")],
        [InlineKeyboardButton("📋 Daftar Akun (Catat Bayar)", callback_data="akun_list")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="start_menu")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(teks, parse_mode='Markdown', reply_markup=reply_markup)


async def tampil_laporan_bulan(update, context):
    query = update.callback_query
    pembayaran_list = get_semua_pembayaran_bulan_ini()
    total = get_total_pendapatan_bulan_ini()

    if not pembayaran_list:
        teks = "💰 *Laporan Bulan Ini*\n\n❌ Belum ada pembayaran bulan ini."
    else:
        teks = f"💰 *Laporan Pembayaran Bulan Ini*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for p in pembayaran_list:
            status_icon = "✅" if p['status'] == 'lunas' else "⏳"
            teks += (
                f"{status_icon} *{p['nama_pelanggan']}*\n"
                f"   Rp {p['nominal']:,} • {p['metode']} • {format_tanggal(p['tanggal_bayar'])}\n\n"
            )
        teks += f"━━━━━━━━━━━━━━━━━━━━\n💵 *Total: Rp {total:,}*"

    keyboard = [[InlineKeyboardButton("« Kembali", callback_data="bayar_menu")]]
    await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


async def tampil_riwayat(update, context, akun_id: int):
    query = update.callback_query
    akun = get_akun_by_id(akun_id)
    riwayat = get_riwayat_pembayaran(akun_id)

    if not riwayat:
        teks = f"📜 *Riwayat Bayar - {akun['nama_pelanggan']}*\n\n❌ Belum ada riwayat pembayaran."
    else:
        teks = f"📜 *Riwayat Bayar - {akun['nama_pelanggan']}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for p in riwayat:
            status_icon = "✅" if p['status'] == 'lunas' else "⏳"
            teks += (
                f"{status_icon} Rp {p['nominal']:,}\n"
                f"   📅 {format_tanggal(p['tanggal_bayar'])} • {p['metode']}\n"
                f"   📝 {p['catatan'] or '-'}\n\n"
            )

    keyboard = [
        [InlineKeyboardButton("💰 Catat Bayar Baru", callback_data=f"bayar_akun_{akun_id}")],
        [InlineKeyboardButton("« Kembali", callback_data=f"akun_detail_{akun_id}")],
    ]
    await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


async def tampil_status_bayar_user(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)

    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM akun WHERE telegram_id = ?', (user_id,))
    akun = c.fetchone()
    conn.close()

    if not akun:
        teks = (
            "❓ *Akun Tidak Ditemukan*\n\n"
            "Telegram ID kamu belum terhubung ke akun Netflix manapun.\n"
            "Hubungi admin untuk info lebih lanjut."
        )
    else:
        from utils import hitung_sisa_hari
        sisa = hitung_sisa_hari(akun['tanggal_expired'])
        riwayat = get_riwayat_pembayaran(akun['id'])
        bayar_terakhir = riwayat[0] if riwayat else None

        teks = (
            f"📋 *Info Akun Kamu*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 {akun['nama_pelanggan']}\n"
            f"📦 Paket: {akun['paket']}\n"
            f"⏰ Expired: {format_tanggal(akun['tanggal_expired'])}\n"
            f"📆 Sisa: *{sisa} hari*\n"
            f"💰 Harga: Rp {akun['harga']:,}\n"
        )
        if bayar_terakhir:
            teks += f"\n✅ Bayar terakhir: {format_tanggal(bayar_terakhir['tanggal_bayar'])}"

    keyboard = [[InlineKeyboardButton("« Kembali", callback_data="start_menu")]]
    await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
