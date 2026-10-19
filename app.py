import os
import sqlite3
import secrets
import requests
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

DB = os.path.join(os.path.dirname(__file__), "ganzx.db")
API20_URL = os.getenv("LIKE_API_URL", "https://two0likeapifreebyzexxyh4x.onrender.com/like")
API20_KEY = os.getenv("LIKE_API_KEY", "")
API220_URL = "https://www.silent-codex-api.shop/like"
from dotenv import load_dotenv
load_dotenv()
API50_URL = "https://www.silent-codex-api.shop/like"
API50_KEY = os.getenv("LIKE50_API_KEY", "")
API220_KEY = os.getenv("LIKE220_API_KEY") or os.getenv("VIP_API_KEY", "")
ADMIN_KEY = os.getenv("ADMIN_KEY", "")
WA_ADMIN = "6285819385168"

def db_connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with db_connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE COLLATE NOCASE NOT NULL,
            password_hash TEXT NOT NULL,
            coins INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS account_sessions(
            token TEXT PRIMARY KEY,
            account_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS like_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            uid TEXT NOT NULL,
            region TEXT,
            status TEXT NOT NULL DEFAULT 'success',
            likes_given INTEGER NOT NULL DEFAULT 0,
            likes_before INTEGER,
            likes_after INTEGER,
            message TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_id) REFERENCES accounts(id)
        )""")

def current_account():
    token = request.headers.get("X-Account-Token", "")
    if not token:
        return None
    with db_connect() as db:
        return db.execute("""
            SELECT a.id, a.username, a.coins
            FROM account_sessions s JOIN accounts a ON a.id=s.account_id
            WHERE s.token=?
        """, (token,)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        account = current_account()
        if not account:
            return jsonify({"ok": False, "message": "Login terlebih dahulu untuk melanjutkan."}), 401
        return fn(account, *args, **kwargs)
    return wrapper

@app.get("/api/account")
def account_info():
    account = current_account()
    if not account:
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in": True,
        "username": account["username"],
        "coins": account["coins"]
    })

@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    if not 3 <= len(username) <= 24 or not username.replace("_", "").isalnum():
        return jsonify({"ok": False, "message": "Username 3–24 karakter; gunakan huruf, angka, atau _."}), 400
    try:
        with db_connect() as db:
            cur = db.execute(
                "INSERT INTO accounts(username,password_hash,coins) VALUES(?,?,0)",
                (username, generate_password_hash(password))
            )
            account_id = cur.lastrowid
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO account_sessions(token,account_id) VALUES(?,?)", (token, account_id))
        return jsonify({"ok": True, "token": token, "username": username, "coins": 0})
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "message": "Username sudah dipakai."}), 409

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    with db_connect() as db:
        row = db.execute("SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return jsonify({"ok": False, "message": "Username atau password salah."}), 401
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO account_sessions(token,account_id) VALUES(?,?)", (token, row["id"]))
    return jsonify({"ok": True, "token": token, "username": row["username"], "coins": row["coins"]})

@app.post("/api/logout")
@login_required
def logout(account):
    token = request.headers.get("X-Account-Token", "")
    with db_connect() as db:
        db.execute("DELETE FROM account_sessions WHERE token=?", (token,))
    return jsonify({"ok": True})

@app.get("/api/coins")
@login_required
def coins(account):
    return jsonify({"ok": True, "coins": account["coins"]})

@app.post("/admin/add-coins")
def admin_add_coins():
    if not ADMIN_KEY or not secrets.compare_digest(request.headers.get("X-Admin-Key", ""), ADMIN_KEY):
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    try:
        amount = int(data.get("amount", 0))
    except (ValueError, TypeError):
        amount = 0
    if amount <= 0 or amount > 1000000:
        return jsonify({"ok": False, "message": "Jumlah coin tidak valid."}), 400
    with db_connect() as db:
        cur = db.execute("UPDATE accounts SET coins=coins+? WHERE username=? COLLATE NOCASE", (amount, username))
        if cur.rowcount == 0:
            return jsonify({"ok": False, "message": "Username tidak ditemukan."}), 404
        row = db.execute("SELECT username,coins FROM accounts WHERE username=? COLLATE NOCASE", (username,)).fetchone()
    return jsonify({"ok": True, "username": row["username"], "coins": row["coins"]})

@app.get("/api/buy-coins")
def buy_coins():
    from flask import redirect
    return redirect("https://wa.me/" + WA_ADMIN)

@app.post("/api/like")
@login_required
def send_like(account):
    data = request.get_json(silent=True) or {}
    uid = str(data.get("uid", "")).strip()
    region = str(data.get("region", "ID")).strip().upper()
    service = str(data.get("service", "free")).strip().lower()

    if not uid.isdigit() or not 5 <= len(uid) <= 20:
        return jsonify({"ok": False, "message": "UID harus berupa 5–20 digit angka."}), 400
    if service not in ("free", "vip"):
        return jsonify({"ok": False, "message": "Jenis layanan tidak valid."}), 400

    display_region = "ID" if service == "free" else region
    cost = 1 if service == "free" else 5
    # Reserve coin atomically so simultaneous requests cannot spend the same balance.
    with db_connect() as db:
        cur = db.execute("UPDATE accounts SET coins=coins-? WHERE id=? AND coins>=?", (cost, account["id"], cost))
        if cur.rowcount != 1:
            return jsonify({"ok": False, "message": "Coin tidak cukup. Beli coin melalui WhatsApp."}), 402

    try:
        if service == "free":
            response = requests.get(
                API50_URL,
                params={"uid": uid, "server_name": "bd", "key": API50_KEY},
                timeout=30
            )
        else:
            region_map = {"ID": "bd", "BD": "bd", "SG": "sg", "TH": "th", "VN": "vn", "BR": "br", "US": "us", "EU": "eu", "ME": "me", "PK": "pk", "TW": "tw", "IND": "ind"}
            response = requests.get(API220_URL, params={"uid": uid, "server_name": region_map.get(region, region.lower()), "key": API220_KEY}, timeout=30)
        try:
            result = response.json()
        except ValueError:
            raise RuntimeError("Respons API bukan JSON.")
        if not response.ok:
            print("[LIKE-API-REJECT] http=", response.status_code, "body=", response.text[:300], flush=True)
            raise RuntimeError("Penyedia API menolak permintaan (HTTP " + str(response.status_code) + ").")
        item = result[0] if isinstance(result, list) and result and isinstance(result[0], dict) else result if isinstance(result, dict) else {}
        given = item.get("LikesGivenByAPI")
        before = item.get("LikesbeforeCommand", item.get("LikesBeforeCommand", item.get("likes_before")))
        after = item.get("LikesafterCommand", item.get("LikesAfterCommand", item.get("likes_after")))
        nickname = item.get("PlayerNickname") or item.get("player_nickname") or item.get("nickname")
        print("[LIKE-DIAG] service=", service, "http=", response.status_code, flush=True)
        print("[LIKE-DIAG] response_fields=", list(item.keys()) if isinstance(item, dict) else type(item).__name__, flush=True)
        print("[LIKE-DIAG] given=", given, "before=", before, "after=", after, flush=True)

        try:
            given_num = int(given) if given is not None else 0
        except (ValueError, TypeError):
            given_num = 0

        try:
            before_num = int(before) if before is not None else None
            after_num = int(after) if after is not None else None
        except (ValueError, TypeError):
            before_num = after_num = None

        increased = before_num is not None and after_num is not None and after_num > before_num
        if given_num <= 0 or not increased:
            with db_connect() as db:
                db.execute("UPDATE accounts SET coins=coins+? WHERE id=?", (cost, account["id"]))
            return jsonify({
                "ok": False, "service": service, "likes_given": 0,
                "nickname": nickname, "uid": uid, "region": display_region,
                "likes_before": before, "likes_after": after,
                "coins_refunded": True,
                "message": "LIKE VIP GAGAL: like diberikan 0 atau jumlah like tidak bertambah. Koin dikembalikan."
            }), 502

        with db_connect() as db:
            db.execute("""
                INSERT INTO like_history
                (key_hash, account_id, service, uid, region, status, likes_given,
                 likes_before, likes_after, message)
                VALUES (?, ?, ?, ?, ?, 'success', ?, ?, ?, ?)
            """, (
                __import__("hashlib").sha256(str(account["id"]).encode()).hexdigest(),
                account["id"], service, uid, display_region, given_num,
                before_num, after_num, "Like berhasil dikirim."
            ))

        return jsonify({
            "ok": True, "service": service, "likes_given": given_num,
            "nickname": nickname, "uid": uid, "region": display_region,
            "likes_before": before, "likes_after": after,
            "coins_spent": cost, "message": "Like berhasil dikirim."
        })
    except (requests.RequestException, RuntimeError) as exc:
        print("[LIKE-ERROR] service=", service, "type=", type(exc).__name__, "message=", str(exc), "http=", getattr(locals().get("response"), "status_code", "none"), flush=True)
        with db_connect() as db:
            db.execute("UPDATE accounts SET coins=coins+? WHERE id=?", (cost, account["id"]))
        return jsonify({"ok": False, "message": str(exc), "coins_refunded": True}), 502


@app.get("/api/history")
@login_required
def like_history(account):
    with db_connect() as db:
        rows = db.execute("""
            SELECT id, service, uid, region, status, likes_given,
                   likes_before, likes_after, message, created_at
            FROM like_history
            WHERE account_id = ? AND likes_given > 0
            ORDER BY id DESC
            LIMIT 50
        """, (account["id"],)).fetchall()
    return jsonify([dict(row) for row in rows])

@app.get("/")
def home_page():
    from flask import send_from_directory
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.get("/health")
def health():
    return jsonify({"name": "GANZ X - OFC", "status": "online", "version": "new-accounts"})

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
