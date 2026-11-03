import os
import psycopg
from psycopg.rows import dict_row
import secrets
import requests
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

DATABASE_URL = os.getenv("DATABASE_URL", "")
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
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL belum disetel.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with db_connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                coins BIGINT NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS accounts_username_lower_idx
            ON accounts (LOWER(username))
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS account_sessions (
                token TEXT PRIMARY KEY,
                account_id BIGINT NOT NULL REFERENCES accounts(id),
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS like_history (
                id BIGSERIAL PRIMARY KEY,
                account_id BIGINT NOT NULL REFERENCES accounts(id),
                service TEXT NOT NULL,
                uid TEXT NOT NULL,
                region TEXT,
                status TEXT NOT NULL DEFAULT 'success',
                likes_given BIGINT NOT NULL DEFAULT 0,
                likes_before BIGINT,
                likes_after BIGINT,
                message TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                key_hash TEXT
            )
        """)


        db.execute("""
            CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY,
                coins BIGINT NOT NULL CHECK(coins > 0),
                max_uses INT NOT NULL CHECK(max_uses > 0),
                used_count INT NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS redeem_redemptions (
                id BIGSERIAL PRIMARY KEY,
                code TEXT NOT NULL REFERENCES redeem_codes(code),
                account_id BIGINT NOT NULL REFERENCES accounts(id),
                redeemed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, account_id)
            )
        """)


def current_account():
    token = request.headers.get("X-Account-Token", "")
    if not token:
        return None
    with db_connect() as db:
        return db.execute("""
            SELECT a.id, a.username, a.coins
            FROM account_sessions s JOIN accounts a ON a.id=s.account_id
            WHERE s.token=%s
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
                "INSERT INTO accounts(username,password_hash,coins) VALUES(%s,%s,0) RETURNING id",
                (username, generate_password_hash(password))
            )
            account_id = cur.fetchone()["id"]
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO account_sessions(token,account_id) VALUES(%s,%s)", (token, account_id))
        return jsonify({"ok": True, "token": token, "username": username, "coins": 0})
    except psycopg.IntegrityError:
        return jsonify({"ok": False, "message": "Username sudah dipakai."}), 409

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    with db_connect() as db:
        row = db.execute("SELECT * FROM accounts WHERE LOWER(username)=LOWER(%s)", (username,)).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return jsonify({"ok": False, "message": "Username atau password salah."}), 401
        token = secrets.token_urlsafe(32)
        db.execute("INSERT INTO account_sessions(token,account_id) VALUES(%s,%s)", (token, row["id"]))
    return jsonify({"ok": True, "token": token, "username": row["username"], "coins": row["coins"]})

@app.post("/api/logout")
@login_required
def logout(account):
    token = request.headers.get("X-Account-Token", "")
    with db_connect() as db:
        db.execute("DELETE FROM account_sessions WHERE token=%s", (token,))
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
        cur = db.execute("UPDATE accounts SET coins=coins+%s WHERE LOWER(username)=LOWER(%s)", (amount, username))
        if cur.rowcount == 0:
            return jsonify({"ok": False, "message": "Username tidak ditemukan."}), 404
        row = db.execute("SELECT username,coins FROM accounts WHERE LOWER(username)=LOWER(%s)", (username,)).fetchone()
    return jsonify({"ok": True, "username": row["username"], "coins": row["coins"]})


@app.post("/admin/create-redeem-codes")
def admin_create_redeem_codes():
    if not ADMIN_KEY or not secrets.compare_digest(
        request.headers.get("X-Admin-Key", ""), ADMIN_KEY
    ):
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    data = request.get_json(silent=True) or {}
    try:
        amount = int(data.get("amount", 0))
        quantity = int(data.get("quantity", 0))
        max_uses = int(data.get("max_uses", 0))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "message": "Masukkan angka yang benar."}), 400

    if not 1 <= amount <= 1000000:
        return jsonify({"ok": False, "message": "Coins harus 1–1.000.000."}), 400
    if not 1 <= quantity <= 100:
        return jsonify({"ok": False, "message": "Jumlah kode harus 1–100."}), 400
    if not 1 <= max_uses <= 100000:
        return jsonify({"ok": False, "message": "Batas pemakai harus 1–100.000."}), 400

    codes = []
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    with db_connect() as db:
        while len(codes) < quantity:
            code = "".join(secrets.choice(alphabet) for _ in range(8))
            cur = db.execute(
                """INSERT INTO redeem_codes(code, coins, max_uses)
                   VALUES(%s, %s, %s) ON CONFLICT(code) DO NOTHING
                   RETURNING code""",
                (code, amount, max_uses)
            )
            if cur.fetchone():
                codes.append(code)

    return jsonify({
        "ok": True, "coins": amount, "quantity": len(codes),
        "max_uses": max_uses, "codes": codes
    })


@app.post("/api/redeem")
@login_required
def redeem_code(account):
    data = request.get_json(silent=True) or {}
    code = str(data.get("code", "")).strip().upper()

    if len(code) != 8 or not code.isascii() or not code.isalpha():
        return jsonify({"ok": False, "message": "Kode harus terdiri dari 8 huruf."}), 400

    with db_connect() as db:
        row = db.execute(
            "SELECT * FROM redeem_codes WHERE code=%s FOR UPDATE",
            (code,)
        ).fetchone()

        if not row:
            return jsonify({"ok": False, "message": "Kode redeem tidak ditemukan."}), 404

        if row["used_count"] >= row["max_uses"]:
            return jsonify({"ok": False, "message": "Kode sudah mencapai batas pemakaian."}), 400

        inserted = db.execute(
            """INSERT INTO redeem_redemptions(code, account_id)
               VALUES(%s, %s) ON CONFLICT(code, account_id) DO NOTHING
               RETURNING id""",
            (code, account["id"])
        ).fetchone()

        if not inserted:
            return jsonify({"ok": False, "message": "Username ini sudah pernah memakai kode tersebut."}), 409

        db.execute(
            "UPDATE accounts SET coins=coins+%s WHERE id=%s",
            (row["coins"], account["id"])
        )
        db.execute(
            "UPDATE redeem_codes SET used_count=used_count+1 WHERE code=%s",
            (code,)
        )
        balance = db.execute(
            "SELECT coins FROM accounts WHERE id=%s",
            (account["id"],)
        ).fetchone()["coins"]

    return jsonify({
        "ok": True,
        "message": f"Berhasil! {row['coins']} coins ditambahkan.",
        "added": row["coins"],
        "coins": balance
    })


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
    if service not in ("free", "vip", "like20"):
        return jsonify({"ok": False, "message": "Jenis layanan tidak valid."}), 400

    display_region = "ID" if service == "free" else region
    cost = 5 if service == "vip" else 1
    # Reserve coin atomically so simultaneous requests cannot spend the same balance.
    with db_connect() as db:
        cur = db.execute("UPDATE accounts SET coins=coins-%s WHERE id=%s AND coins>=%s", (cost, account["id"], cost))
        if cur.rowcount != 1:
            return jsonify({"ok": False, "message": "Coin tidak cukup. Beli coin melalui WhatsApp."}), 402

    try:
        if service == "like20":
            response = requests.get(
                API20_URL,
                params={"uid": uid, "region": region, "key": API20_KEY},
                timeout=30
            )
        elif service == "free":
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
        print("[LIKE-DIAG] uid=", uid, "nickname=", nickname, "before=", before, "after=", after, "given=", given, "status=", item.get("status"), "key_limit=", item.get("KEY LIMIT"), "region=", item.get("PlayerRegion"), flush=True)

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
                db.execute("UPDATE accounts SET coins=coins+%s WHERE id=%s", (cost, account["id"]))
            return jsonify({
                "ok": False, "service": service, "likes_given": 0,
                "nickname": nickname, "uid": uid, "region": display_region,
                "likes_before": before, "likes_after": after,
                "coins_refunded": True,
                "message": "LIKE GAGAL: like tidak bertambah. Koin dikembalikan."
            }), 409

        with db_connect() as db:
            db.execute("""
                INSERT INTO like_history
                (key_hash, account_id, service, uid, region, status, likes_given,
                 likes_before, likes_after, message)
                VALUES (%s, %s, %s, %s, %s, 'success', %s, %s, %s, %s)
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
            db.execute("UPDATE accounts SET coins=coins+%s WHERE id=%s", (cost, account["id"]))
        return jsonify({"ok": False, "message": str(exc), "coins_refunded": True}), 502


@app.get("/api/history")
@login_required
def like_history(account):
    with db_connect() as db:
        rows = db.execute("""
            SELECT id, service, uid, region, status, likes_given,
                   likes_before, likes_after, message,
                   COALESCE(created_at, CURRENT_TIMESTAMP) AS created_at
            FROM like_history
            WHERE account_id = %s AND likes_given > 0
            ORDER BY id DESC
            LIMIT 50
        """, (account["id"],)).fetchall()
    return jsonify([dict(row) for row in rows])

@app.get("/manifest.json")
def pwa_manifest():
    from flask import send_from_directory
    response = send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "manifest.json",
        mimetype="application/manifest+json"
    )
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/sw.js")
def pwa_service_worker():
    from flask import send_from_directory
    response = send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "sw.js",
        mimetype="application/javascript"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


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
