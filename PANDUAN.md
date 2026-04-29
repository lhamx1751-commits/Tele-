# 🎬 Netflix Bot Telegram - Panduan Deploy

## 📁 Struktur File
```
netflix-bot/
├── bot.py               ← File utama
├── database.py          ← Database & query
├── utils.py             ← Helper functions
├── requirements.txt     ← Library Python
├── Procfile             ← Untuk Railway
├── .env.example         ← Template environment
├── .gitignore           ← File yang diabaikan Git
└── handlers/
    ├── __init__.py
    ├── start.py         ← Menu utama
    ├── akun.py          ← Kelola akun
    ├── pembayaran.py    ← Pembayaran
    ├── pengingat.py     ← Notifikasi otomatis
    ├── admin.py         ← Panel admin
    └── conversation.py  ← Input data (tambah/edit/bayar)
```

---

## 🚀 LANGKAH DEPLOY KE RAILWAY

### Step 1: Buat Bot Token
1. Buka Telegram, cari @BotFather
2. Ketik /newbot
3. Ikuti instruksi, beri nama bot
4. Simpan TOKEN yang diberikan

### Step 2: Cek Telegram ID Kamu
1. Cari @userinfobot di Telegram
2. Forward sembarang pesan ke bot itu
3. Catat angka "Id" yang muncul

### Step 3: Upload ke GitHub
1. Buka github.com di HP
2. Buat repository baru (klik tanda +)
3. Nama: netflix-bot (jangan centang README)
4. Upload semua file KECUALI .env

### Step 4: Deploy ke Railway
1. Buka railway.app
2. Login dengan GitHub
3. Klik "New Project" → "Deploy from GitHub repo"
4. Pilih repo netflix-bot kamu
5. Tunggu deploy selesai

### Step 5: Tambah Environment Variables di Railway
Di Railway, klik project → Variables → Add:
```
BOT_TOKEN    = (paste token dari BotFather)
ADMIN_ID     = (paste Telegram ID kamu)
DB_PATH      = netflix_bot.db
```

### Step 6: Restart dan Test
1. Di Railway, klik "Redeploy"
2. Buka bot kamu di Telegram
3. Ketik /start

---

## 📱 CARA PAKAI BOT

### Perintah Admin:
| Perintah | Fungsi |
|---|---|
| /start | Menu utama |
| /tambahakun | Tambah akun Netflix baru |
| /editakun [ID] | Edit akun (contoh: /editakun 1) |
| /catatbayar | Catat pembayaran |
| /akun | Lihat daftar akun |
| /pembayaran | Menu pembayaran |
| /pengingat | Status pengingat |
| /admin | Panel admin |
| /batal | Batalkan proses input |

### Alur Tambah Akun Baru:
1. Ketik /tambahakun
2. Isi data satu per satu (ikuti instruksi bot)
3. Konfirmasi → tersimpan otomatis

### Alur Catat Pembayaran:
1. Ketik /catatbayar
2. Pilih ID akun
3. Isi nominal, tanggal, metode

---

## 🔔 PENGINGAT OTOMATIS

Bot akan otomatis kirim notifikasi ke admin:
- **H-7** sebelum expired → ikon 🟠
- **H-3** sebelum expired → ikon 🟡  
- **H-1** sebelum expired → ikon 🔴

Jika pelanggan punya Telegram ID tersimpan,
mereka juga otomatis dapat notifikasi!

---

## ⚠️ KEAMANAN

- JANGAN share file .env ke siapapun
- JANGAN upload .env ke GitHub
- Bot hanya bisa diakses oleh ADMIN_ID

---

## 🐛 Troubleshooting

**Bot tidak merespons:**
- Cek Logs di Railway
- Pastikan BOT_TOKEN dan ADMIN_ID benar

**Error database:**
- Di Railway, cek apakah DB_PATH sudah diset
- Coba redeploy

**Pengingat tidak jalan:**
- Normal, pengingat cek setiap 1 jam
- Pastikan bot aktif (tidak sleep)
