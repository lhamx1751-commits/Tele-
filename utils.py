from datetime import datetime, date
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


def cek_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def hitung_sisa_hari(tanggal_expired: str) -> int:
    try:
        expired = datetime.strptime(tanggal_expired, "%Y-%m-%d").date()
        today = date.today()
        return (expired - today).days
    except Exception:
        return -999


def format_tanggal(tanggal: str) -> str:
    try:
        dt = datetime.strptime(tanggal, "%Y-%m-%d")
        return dt.strftime("%d %B %Y")
    except Exception:
        return tanggal


def validasi_tanggal(tanggal: str) -> str | None:
    """Konversi DD-MM-YYYY ke YYYY-MM-DD. Return None jika invalid."""
    tanggal = tanggal.strip()
    formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(tanggal, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def format_rupiah(nominal: int) -> str:
    return f"Rp {nominal:,}".replace(",", ".")
