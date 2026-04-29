from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_semua_akun, get_akun_by_id, hapus_akun, get_jumlah_akun
from utils import format_tanggal, hitung_sisa_hari, cek_admin
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MAX_AKUN = 20


async def akun_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cek_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Akses ditolak.")
        return
    await tampil_daftar_akun(update, context)


async def akun_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not cek_admin(query.from_user.id):
        await query.edit_message_text("⛔ Akses ditolak.")
        return

    if data == "akun_list":
        await tampil_daftar_akun(update, context)

    elif data == "akun_tambah":
        total = get_jumlah_akun()
        if total >= MAX_AKUN:
            await query.edit_message_text(
                f"⚠️ *Batas maksimal {MAX_AKUN} akun tercapai!*\n"
                f"Hapus akun yang tidak aktif terlebih dahulu.",
                parse_mode='Markdown'
            )
            return
        await query.edit_message_text(
            "➕ *Tambah Akun Baru*\n\n"
            "Gunakan perintah /tambahakun untuk memulai.\n"
            "Saya akan tanya satu per satu 😊",
            parse_mode='Markdown'
        )

    elif data.startswith("akun_detail_"):
        akun_id = int(data.split("_")[2])
        await tampil_detail_akun(update, context, akun_id)

    elif data.startswith("akun_hapus_konfirm_"):
        akun_id = int(data.split("_")[3])
        akun = get_akun_by_id(akun_id)
        keyboard = [
            [
                InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"akun_hapus_{akun_id}"),
                InlineKeyboardButton("❌ Batal", callback_data=f"akun_detail_{akun_id}"),
            ]
        ]
        await query.edit_message_text(
            f"⚠️ *Yakin hapus akun ini?*\n\n"
            f"👤 {akun['nama_pelanggan']}\n"
            f"📧 {akun['email_netflix']}\n\n"
            f"Semua data pembayaran juga akan terhapus!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("akun_hapus_"):
        akun_id = int(data.split("_")[2])
        akun = get_akun_by_id(akun_id)
        nama = akun['nama_pelanggan'] if akun else "?"
        hapus_akun(akun_id)
        keyboard = [[InlineKeyboardButton("« Kembali ke Daftar", callback_data="akun_list")]]
        await query.edit_message_text(
            f"✅ Akun *{nama}* berhasil dihapus.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "akun_pengingat":
        await tampil_akun_akan_expired(update, context)

    elif data == "start_menu":
        from handlers.start import start_handler
        await start_handler(update, context)


async def tampil_daftar_akun(update, context):
    akun_list = get_semua_akun()
    query = update.callback_query if update.callback_query else None

    if not akun_list:
        teks = "📋 *Daftar Akun Netflix*\n\n❌ Belum ada akun yang ditambahkan."
        keyboard = [
            [InlineKeyboardButton("➕ Tambah Akun Pertama", callback_data="akun_tambah")],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="start_menu")],
        ]
    else:
        teks = f"📋 *Daftar Akun Netflix* ({len(akun_list)}/{MAX_AKUN})\n"
        teks += "━━━━━━━━━━━━━━━━━━━━\n\n"

        keyboard = []
        for akun in akun_list:
            sisa = hitung_sisa_hari(akun['tanggal_expired'])
            if sisa < 0:
                ikon = "🔴"
            elif sisa <= 3:
                ikon = "🟡"
            elif sisa <= 7:
                ikon = "🟠"
            else:
                ikon = "🟢"

            label = f"{ikon} {akun['nama_pelanggan']} ({sisa}hr)"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"akun_detail_{akun['id']}")])

        keyboard.append([
            InlineKeyboardButton("➕ Tambah Akun", callback_data="akun_tambah"),
            InlineKeyboardButton("🏠 Menu", callback_data="start_menu"),
        ])

        teks += "🟢 = Aman  🟠 = 7 hari  🟡 = 3 hari  🔴 = Expired"

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(teks, parse_mode='Markdown', reply_markup=reply_markup)


async def tampil_detail_akun(update, context, akun_id: int):
    query = update.callback_query
    akun = get_akun_by_id(akun_id)

    if not akun:
        await query.edit_message_text("❌ Akun tidak ditemukan.")
        return

    sisa = hitung_sisa_hari(akun['tanggal_expired'])
    status_icon = "🟢" if sisa > 7 else "🟡" if sisa > 3 else "🔴"

    teks = (
        f"📋 *Detail Akun Netflix*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Pelanggan:* {akun['nama_pelanggan']}\n"
        f"📱 *No. HP:* {akun['no_hp'] or '-'}\n"
        f"📧 *Email:* `{akun['email_netflix']}`\n"
        f"🔑 *Password:* `{akun['password_netflix']}`\n"
        f"📦 *Paket:* {akun['paket']}\n"
        f"🎭 *Slot Profil:* {akun['slot_profil'] or '-'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 *Mulai:* {format_tanggal(akun['tanggal_mulai'])}\n"
        f"⏰ *Expired:* {format_tanggal(akun['tanggal_expired'])}\n"
        f"{status_icon} *Sisa:* {sisa} hari\n"
        f"💰 *Harga:* Rp {akun['harga']:,}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Catatan:* {akun['catatan'] or '-'}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_akun_{akun_id}"),
            InlineKeyboardButton("💰 Bayar", callback_data=f"bayar_akun_{akun_id}"),
        ],
        [
            InlineKeyboardButton("📜 Riwayat Bayar", callback_data=f"bayar_riwayat_{akun_id}"),
            InlineKeyboardButton("🗑️ Hapus", callback_data=f"akun_hapus_konfirm_{akun_id}"),
        ],
        [InlineKeyboardButton("« Kembali", callback_data="akun_list")],
    ]

    await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


async def tampil_akun_akan_expired(update, context):
    query = update.callback_query
    from database import get_akun_akan_expired

    akun_7 = get_akun_akan_expired(7)
    akun_3 = get_akun_akan_expired(3)
    akun_1 = get_akun_akan_expired(1)

    teks = "🔔 *Status Pengingat Aktif*\n━━━━━━━━━━━━━━━━━━━━\n\n"

    if akun_1:
        teks += "🔴 *Expired BESOK:*\n"
        for a in akun_1:
            teks += f"  • {a['nama_pelanggan']} ({a['email_netflix']})\n"
        teks += "\n"

    if akun_3:
        teks += "🟡 *Expired 3 hari lagi:*\n"
        for a in akun_3:
            teks += f"  • {a['nama_pelanggan']} ({a['email_netflix']})\n"
        teks += "\n"

    if akun_7:
        teks += "🟠 *Expired 7 hari lagi:*\n"
        for a in akun_7:
            teks += f"  • {a['nama_pelanggan']} ({a['email_netflix']})\n"

    if not akun_1 and not akun_3 and not akun_7:
        teks += "✅ Tidak ada akun yang akan expired dalam 7 hari ke depan."

    keyboard = [[InlineKeyboardButton("« Kembali", callback_data="start_menu")]]
    await query.edit_message_text(teks, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
