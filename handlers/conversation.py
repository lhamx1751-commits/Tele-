from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters, CallbackQueryHandler
)
from database import tambah_akun, catat_pembayaran, update_akun, get_akun_by_id
from utils import cek_admin, validasi_tanggal
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# States untuk tambah akun
(NAMA, HP, EMAIL, PASSWORD, PAKET, TGL_MULAI,
 TGL_EXPIRED, HARGA, SLOT, CATATAN, TELEGRAM_ID) = range(11)

# States untuk catat bayar
BAYAR_PILIH_AKUN, BAYAR_NOMINAL, BAYAR_TGL, BAYAR_METODE = range(4)

# States untuk edit akun
EDIT_FIELD, EDIT_VALUE = range(2)


# ─── TAMBAH AKUN ─────────────────────────────────────────

def tambah_akun_conv():
    return ConversationHandler(
        entry_points=[CommandHandler("tambahakun", mulai_tambah_akun)],
        states={
            NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_nama)],
            HP: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_hp)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_password)],
            PAKET: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_paket)],
            TGL_MULAI: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_tgl_mulai)],
            TGL_EXPIRED: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_tgl_expired)],
            HARGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_harga)],
            SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_slot)],
            CATATAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_catatan)],
            TELEGRAM_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_telegram_id)],
        },
        fallbacks=[CommandHandler("batal", batal)],
        name="tambah_akun",
        persistent=False,
    )


async def mulai_tambah_akun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Akses ditolak.")
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "➕ *Tambah Akun Netflix Baru*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Ketik /batal untuk membatalkan.\n\n"
        "👤 *Langkah 1/11*\nMasukkan *nama pelanggan*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return NAMA


async def input_nama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nama_pelanggan'] = update.message.text.strip()
    await update.message.reply_text(
        "📱 *Langkah 2/11*\nMasukkan *nomor HP* pelanggan:\n_(Ketik '-' jika tidak ada)_",
        parse_mode='Markdown'
    )
    return HP


async def input_hp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['no_hp'] = update.message.text.strip()
    await update.message.reply_text(
        "📧 *Langkah 3/11*\nMasukkan *email Netflix*:",
        parse_mode='Markdown'
    )
    return EMAIL


async def input_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email_netflix'] = update.message.text.strip()
    await update.message.reply_text(
        "🔑 *Langkah 4/11*\nMasukkan *password Netflix*:",
        parse_mode='Markdown'
    )
    return PASSWORD


async def input_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password_netflix'] = update.message.text.strip()

    keyboard = ReplyKeyboardMarkup(
        [["Basic", "Standard"], ["Premium", "Ultimate"]],
        one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "📦 *Langkah 5/11*\nPilih *paket Netflix*:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    return PAKET


async def input_paket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['paket'] = update.message.text.strip()
    await update.message.reply_text(
        "📅 *Langkah 6/11*\nMasukkan *tanggal mulai* langganan:\n_(Format: DD-MM-YYYY, contoh: 01-01-2025)_",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return TGL_MULAI


async def input_tgl_mulai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tgl = update.message.text.strip()
    tgl_db = validasi_tanggal(tgl)
    if not tgl_db:
        await update.message.reply_text("❌ Format salah! Gunakan DD-MM-YYYY\nContoh: 01-01-2025")
        return TGL_MULAI
    context.user_data['tanggal_mulai'] = tgl_db
    await update.message.reply_text(
        "⏰ *Langkah 7/11*\nMasukkan *tanggal expired*:\n_(Format: DD-MM-YYYY, contoh: 01-02-2025)_",
        parse_mode='Markdown'
    )
    return TGL_EXPIRED


async def input_tgl_expired(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tgl = update.message.text.strip()
    tgl_db = validasi_tanggal(tgl)
    if not tgl_db:
        await update.message.reply_text("❌ Format salah! Gunakan DD-MM-YYYY\nContoh: 01-02-2025")
        return TGL_EXPIRED
    context.user_data['tanggal_expired'] = tgl_db
    await update.message.reply_text(
        "💰 *Langkah 8/11*\nMasukkan *harga langganan* (angka saja):\n_(Contoh: 50000)_",
        parse_mode='Markdown'
    )
    return HARGA


async def input_harga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        harga = int(update.message.text.strip().replace('.', '').replace(',', ''))
        context.user_data['harga'] = harga
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka saja! Contoh: 50000")
        return HARGA
    await update.message.reply_text(
        "🎭 *Langkah 9/11*\nMasukkan *slot profil* yang digunakan:\n_(Contoh: Profil 1, atau ketik '-' jika tidak ada)_",
        parse_mode='Markdown'
    )
    return SLOT


async def input_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['slot_profil'] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Langkah 10/11*\nMasukkan *catatan* tambahan:\n_(Ketik '-' jika tidak ada)_",
        parse_mode='Markdown'
    )
    return CATATAN


async def input_catatan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['catatan'] = update.message.text.strip()
    await update.message.reply_text(
        "📲 *Langkah 11/11*\nMasukkan *Telegram ID* pelanggan:\n_(Untuk notifikasi otomatis ke pelanggan)\n(Ketik '-' jika tidak ada)_\n\n"
        "_Cara cek Telegram ID: forward pesan ke @userinfobot_",
        parse_mode='Markdown'
    )
    return TELEGRAM_ID


async def input_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.message.text.strip()
    context.user_data['telegram_id'] = '' if tg_id == '-' else tg_id

    data = context.user_data

    # Konfirmasi data
    teks = (
        f"✅ *Konfirmasi Data Akun*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Nama: {data['nama_pelanggan']}\n"
        f"📱 HP: {data['no_hp']}\n"
        f"📧 Email: {data['email_netflix']}\n"
        f"🔑 Password: {data['password_netflix']}\n"
        f"📦 Paket: {data['paket']}\n"
        f"📅 Mulai: {data['tanggal_mulai']}\n"
        f"⏰ Expired: {data['tanggal_expired']}\n"
        f"💰 Harga: Rp {data['harga']:,}\n"
        f"🎭 Slot: {data['slot_profil']}\n"
        f"📲 Telegram ID: {data['telegram_id'] or '-'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Simpan akun ini?"
    )

    keyboard = ReplyKeyboardMarkup(
        [["✅ Simpan", "❌ Batal"]],
        one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(teks, parse_mode='Markdown', reply_markup=keyboard)

    # Simpan langsung
    akun_id = tambah_akun(context.user_data)
    await update.message.reply_text(
        f"🎉 *Akun berhasil ditambahkan!*\n\nID Akun: #{akun_id}\n"
        f"Gunakan /akun untuk melihat daftar.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─── CATAT PEMBAYARAN ────────────────────────────────────

def catat_bayar_conv():
    return ConversationHandler(
        entry_points=[CommandHandler("catatbayar", mulai_catat_bayar)],
        states={
            BAYAR_PILIH_AKUN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bayar_pilih_akun)],
            BAYAR_NOMINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bayar_nominal)],
            BAYAR_TGL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bayar_tgl)],
            BAYAR_METODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bayar_metode)],
        },
        fallbacks=[CommandHandler("batal", batal)],
        name="catat_bayar",
        persistent=False,
    )


async def mulai_catat_bayar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Akses ditolak.")
        return ConversationHandler.END

    from database import get_semua_akun
    akun_list = get_semua_akun()

    if not akun_list:
        await update.message.reply_text("❌ Belum ada akun. Tambah akun dulu dengan /tambahakun")
        return ConversationHandler.END

    teks = "💰 *Catat Pembayaran*\n━━━━━━━━━━━━━━━━━━━━\n\nPilih akun (ketik nomor ID):\n\n"
    for a in akun_list:
        teks += f"*#{a['id']}* - {a['nama_pelanggan']} ({a['email_netflix']})\n"

    await update.message.reply_text(teks, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    return BAYAR_PILIH_AKUN


async def bayar_pilih_akun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        akun_id = int(update.message.text.strip().replace('#', ''))
        akun = get_akun_by_id(akun_id)
        if not akun:
            await update.message.reply_text("❌ ID akun tidak ditemukan. Coba lagi:")
            return BAYAR_PILIH_AKUN
        context.user_data['bayar_akun_id'] = akun_id
        context.user_data['bayar_nama'] = akun['nama_pelanggan']
        await update.message.reply_text(
            f"✅ Akun: *{akun['nama_pelanggan']}*\n\n"
            f"💵 Masukkan *nominal pembayaran* (angka saja):\n"
            f"_(Harga normal: Rp {akun['harga']:,})_",
            parse_mode='Markdown'
        )
        return BAYAR_NOMINAL
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka ID saja. Contoh: 1")
        return BAYAR_PILIH_AKUN


async def bayar_nominal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        nominal = int(update.message.text.strip().replace('.', '').replace(',', ''))
        context.user_data['bayar_nominal'] = nominal
        await update.message.reply_text(
            "📅 Masukkan *tanggal bayar*:\n_(Format: DD-MM-YYYY, atau ketik 'hari ini')_",
            parse_mode='Markdown'
        )
        return BAYAR_TGL
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka saja. Contoh: 50000")
        return BAYAR_NOMINAL


async def bayar_tgl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tgl_input = update.message.text.strip().lower()
    if tgl_input in ['hari ini', 'today']:
        from datetime import date
        tgl_db = date.today().strftime("%Y-%m-%d")
    else:
        tgl_db = validasi_tanggal(tgl_input)
        if not tgl_db:
            await update.message.reply_text("❌ Format salah! Gunakan DD-MM-YYYY atau ketik 'hari ini'")
            return BAYAR_TGL

    context.user_data['bayar_tgl'] = tgl_db

    keyboard = ReplyKeyboardMarkup(
        [["Transfer", "QRIS"], ["Cash", "Dana/OVO"]],
        one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "💳 Pilih *metode pembayaran*:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    return BAYAR_METODE


async def bayar_metode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    metode = update.message.text.strip()
    data = context.user_data

    catat_pembayaran({
        'akun_id': data['bayar_akun_id'],
        'nominal': data['bayar_nominal'],
        'tanggal_bayar': data['bayar_tgl'],
        'metode': metode,
        'status': 'lunas'
    })

    await update.message.reply_text(
        f"✅ *Pembayaran Tercatat!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {data['bayar_nama']}\n"
        f"💰 Rp {data['bayar_nominal']:,}\n"
        f"💳 {metode}\n"
        f"📅 {data['bayar_tgl']}",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─── EDIT AKUN ────────────────────────────────────────────

def edit_akun_conv():
    return ConversationHandler(
        entry_points=[CommandHandler("editakun", mulai_edit_akun)],
        states={
            EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_pilih_field)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_input_value)],
        },
        fallbacks=[CommandHandler("batal", batal)],
        name="edit_akun",
        persistent=False,
    )


async def mulai_edit_akun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Akses ditolak.")
        return ConversationHandler.END

    args = context.args
    if not args:
        await update.message.reply_text(
            "Gunakan: /editakun [ID]\nContoh: /editakun 1"
        )
        return ConversationHandler.END

    try:
        akun_id = int(args[0])
        akun = get_akun_by_id(akun_id)
        if not akun:
            await update.message.reply_text("❌ Akun tidak ditemukan.")
            return ConversationHandler.END

        context.user_data['edit_akun_id'] = akun_id
        keyboard = ReplyKeyboardMarkup(
            [["nama", "hp"], ["email", "password"],
             ["paket", "expired"], ["harga", "slot"], ["catatan"]],
            one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(
            f"✏️ *Edit Akun - {akun['nama_pelanggan']}*\n\nPilih field yang mau diedit:",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        return EDIT_FIELD
    except ValueError:
        await update.message.reply_text("❌ ID harus angka. Contoh: /editakun 1")
        return ConversationHandler.END


FIELD_MAP = {
    'nama': 'nama_pelanggan',
    'hp': 'no_hp',
    'email': 'email_netflix',
    'password': 'password_netflix',
    'paket': 'paket',
    'expired': 'tanggal_expired',
    'harga': 'harga',
    'slot': 'slot_profil',
    'catatan': 'catatan',
}


async def edit_pilih_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.strip().lower()
    if field not in FIELD_MAP:
        await update.message.reply_text("❌ Field tidak valid. Pilih dari tombol yang tersedia.")
        return EDIT_FIELD

    context.user_data['edit_field'] = field
    await update.message.reply_text(
        f"✏️ Masukkan nilai baru untuk *{field}*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return EDIT_VALUE


async def edit_input_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    field = context.user_data['edit_field']
    db_field = FIELD_MAP[field]
    akun_id = context.user_data['edit_akun_id']

    # Konversi khusus
    if field == 'harga':
        try:
            value = int(value.replace('.', '').replace(',', ''))
        except ValueError:
            await update.message.reply_text("❌ Harga harus angka.")
            return EDIT_VALUE
    elif field == 'expired':
        value = validasi_tanggal(value)
        if not value:
            await update.message.reply_text("❌ Format tanggal salah. Gunakan DD-MM-YYYY")
            return EDIT_VALUE

    update_akun(akun_id, {db_field: value})

    await update.message.reply_text(
        f"✅ *{field}* berhasil diupdate!\n\nGunakan /akun untuk melihat daftar.",
        parse_mode='Markdown'
    )
    context.user_data.clear()
    return ConversationHandler.END


async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Dibatalkan.\nGunakan /start untuk menu utama.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
