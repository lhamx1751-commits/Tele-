import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "netflix_bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Tabel akun Netflix
    c.execute('''
        CREATE TABLE IF NOT EXISTS akun (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_pelanggan TEXT NOT NULL,
            no_hp TEXT,
            email_netflix TEXT NOT NULL,
            password_netflix TEXT NOT NULL,
            paket TEXT DEFAULT 'Standard',
            tanggal_mulai TEXT NOT NULL,
            tanggal_expired TEXT NOT NULL,
            harga INTEGER NOT NULL,
            slot_profil TEXT,
            catatan TEXT,
            status TEXT DEFAULT 'aktif',
            telegram_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabel pembayaran
    c.execute('''
        CREATE TABLE IF NOT EXISTS pembayaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            akun_id INTEGER NOT NULL,
            nominal INTEGER NOT NULL,
            tanggal_bayar TEXT NOT NULL,
            metode TEXT DEFAULT 'Transfer',
            status TEXT DEFAULT 'lunas',
            catatan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (akun_id) REFERENCES akun(id)
        )
    ''')

    # Tabel pengingat yang sudah dikirim (hindari duplikat)
    c.execute('''
        CREATE TABLE IF NOT EXISTS pengingat_terkirim (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            akun_id INTEGER NOT NULL,
            jenis TEXT NOT NULL,
            tanggal_kirim TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database berhasil diinisialisasi")


# ─── FUNGSI AKUN ─────────────────────────────────────────

def tambah_akun(data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO akun 
        (nama_pelanggan, no_hp, email_netflix, password_netflix, paket,
         tanggal_mulai, tanggal_expired, harga, slot_profil, catatan, telegram_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['nama_pelanggan'], data.get('no_hp', ''),
        data['email_netflix'], data['password_netflix'],
        data.get('paket', 'Standard'), data['tanggal_mulai'],
        data['tanggal_expired'], data['harga'],
        data.get('slot_profil', ''), data.get('catatan', ''),
        data.get('telegram_id', '')
    ))
    akun_id = c.lastrowid
    conn.commit()
    conn.close()
    return akun_id


def get_semua_akun():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM akun ORDER BY tanggal_expired ASC')
    result = c.fetchall()
    conn.close()
    return result


def get_akun_by_id(akun_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM akun WHERE id = ?', (akun_id,))
    result = c.fetchone()
    conn.close()
    return result


def update_akun(akun_id: int, data: dict):
    conn = get_conn()
    c = conn.cursor()
    fields = ', '.join([f"{k} = ?" for k in data.keys()])
    values = list(data.values()) + [akun_id]
    c.execute(f'UPDATE akun SET {fields} WHERE id = ?', values)
    conn.commit()
    conn.close()


def hapus_akun(akun_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM akun WHERE id = ?', (akun_id,))
    c.execute('DELETE FROM pembayaran WHERE akun_id = ?', (akun_id,))
    conn.commit()
    conn.close()


def get_akun_akan_expired(hari: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM akun 
        WHERE status = 'aktif'
        AND date(tanggal_expired) = date('now', ? || ' days')
    ''', (f'+{hari}',))
    result = c.fetchall()
    conn.close()
    return result


def get_jumlah_akun():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as total FROM akun WHERE status = "aktif"')
    result = c.fetchone()
    conn.close()
    return result['total'] if result else 0


# ─── FUNGSI PEMBAYARAN ────────────────────────────────────

def catat_pembayaran(data: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO pembayaran (akun_id, nominal, tanggal_bayar, metode, status, catatan)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['akun_id'], data['nominal'], data['tanggal_bayar'],
        data.get('metode', 'Transfer'), data.get('status', 'lunas'),
        data.get('catatan', '')
    ))
    conn.commit()
    conn.close()


def get_riwayat_pembayaran(akun_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, a.nama_pelanggan FROM pembayaran p
        JOIN akun a ON p.akun_id = a.id
        WHERE p.akun_id = ?
        ORDER BY p.tanggal_bayar DESC
    ''', (akun_id,))
    result = c.fetchall()
    conn.close()
    return result


def get_semua_pembayaran_bulan_ini():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, a.nama_pelanggan FROM pembayaran p
        JOIN akun a ON p.akun_id = a.id
        WHERE strftime('%Y-%m', p.tanggal_bayar) = strftime('%Y-%m', 'now')
        ORDER BY p.tanggal_bayar DESC
    ''')
    result = c.fetchall()
    conn.close()
    return result


def get_total_pendapatan_bulan_ini():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT SUM(nominal) as total FROM pembayaran
        WHERE strftime('%Y-%m', tanggal_bayar) = strftime('%Y-%m', 'now')
        AND status = 'lunas'
    ''')
    result = c.fetchone()
    conn.close()
    return result['total'] or 0


def sudah_kirim_pengingat(akun_id: int, jenis: str, tanggal: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        SELECT id FROM pengingat_terkirim
        WHERE akun_id = ? AND jenis = ? AND tanggal_kirim = ?
    ''', (akun_id, jenis, tanggal))
    result = c.fetchone()
    conn.close()
    return result is not None


def simpan_pengingat_terkirim(akun_id: int, jenis: str, tanggal: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO pengingat_terkirim (akun_id, jenis, tanggal_kirim)
        VALUES (?, ?, ?)
    ''', (akun_id, jenis, tanggal))
    conn.commit()
    conn.close()
