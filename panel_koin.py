
import os
import requests
from dotenv import load_dotenv

load_dotenv()
ADMIN_KEY = os.getenv("ADMIN_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://ganz-x-ofc-fsgd0.faable.link").rstrip("/")

def garis():
    print("\033[96m" + "━" * 38 + "\033[0m")

def tunggu():
    input("\nTekan Enter untuk kembali...")

def tambah_coins():
    username = input("Username akun: ").strip()
    try:
        amount = int(input("Jumlah coins: "))
    except ValueError:
        print("Jumlah harus angka.")
        return
    if not username or not 1 <= amount <= 1000000:
        print("Data tidak valid.")
        return
    if input("Lanjutkan? (y/n): ").lower() != "y":
        print("Dibatalkan.")
        return
    try:
        r = requests.post(
            BASE_URL + "/admin/add-coins",
            headers={"X-Admin-Key": ADMIN_KEY},
            json={"username": username, "amount": amount},
            timeout=20
        )
        d = r.json()
        if r.ok and d.get("ok"):
            print("BERHASIL! Username:", d["username"], "| Total coins:", d["coins"])
        else:
            print("GAGAL:", d.get("message", "Permintaan gagal"))
    except Exception as e:
        print("Koneksi gagal:", e)

def buat_redeem():
    try:
        amount = int(input("Coins per kode: "))
        quantity = int(input("Jumlah kode dibuat: "))
        max_uses = int(input("Maksimal username per kode: "))
    except ValueError:
        print("Masukkan angka yang benar.")
        return

    if not 1 <= amount <= 1000000 or not 1 <= quantity <= 100 or not 1 <= max_uses <= 100000:
        print("Batas angka tidak valid.")
        return

    print("\nCoins per kode:", amount)
    print("Jumlah kode:", quantity)
    print("Batas pemakai:", max_uses, "username")
    if input("Buat sekarang? (y/n): ").lower() != "y":
        print("Dibatalkan.")
        return

    try:
        r = requests.post(
            BASE_URL + "/admin/create-redeem-codes",
            headers={"X-Admin-Key": ADMIN_KEY},
            json={"amount": amount, "quantity": quantity, "max_uses": max_uses},
            timeout=30
        )
        d = r.json()
        if r.ok and d.get("ok"):
            garis()
            print("KODE REDEEM BERHASIL DIBUAT")
            for i, code in enumerate(d["codes"], 1):
                print(f"{i}. {code}")
            garis()
            print("Coins per kode:", d["coins"])
            print("Batas pemakai:", d["max_uses"], "username")
            print("Simpan kode ini. Kode hanya ditampilkan saat dibuat.")
        else:
            print("GAGAL:", d.get("message", "Permintaan gagal"))
    except Exception as e:
        print("Koneksi gagal:", e)

def main():
    if not ADMIN_KEY:
        print("ADMIN_KEY belum diatur di .env")
        return
    while True:
        os.system("clear")
        garis()
        print("       GANZ X - OFC COINS")
        garis()
        print("[1] Tambah coins akun")
        print("[2] Keluar dari panel")
        print("[3] Buat kode redeem")
        garis()
        pilihan = input("Pilih menu: ").strip()
        if pilihan == "1":
            tambah_coins()
        elif pilihan == "2":
            print("Panel ditutup.")
            break
        elif pilihan == "3":
            buat_redeem()
        else:
            print("Menu tidak tersedia.")
        tunggu()

if __name__ == "__main__":
    main()
