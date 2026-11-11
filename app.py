import os
import hashlib
import psycopg
from psycopg.rows import dict_row
import secrets
import requests
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, Response, redirect
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
        db.execute("SET statement_timeout = '60s'")
        db.execute("SET lock_timeout = '10s'")
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
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS avatar_data BYTEA
        """)
        db.execute("""
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS avatar_mime TEXT
        """)
        db.execute("""
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS avatar_version BIGINT NOT NULL DEFAULT 0
        """)
        db.execute("""
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS display_name TEXT
        """)
        db.execute("""
            UPDATE accounts SET display_name='Ganz X - OFC'
            WHERE display_name IS NULL OR BTRIM(display_name)=''
        """)
        db.execute("""
            ALTER TABLE accounts ALTER COLUMN display_name SET DEFAULT 'Ganz X - OFC'
        """)
        db.execute("""
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS name_color TEXT NOT NULL DEFAULT 'white'
        """)
        db.execute("""
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS crown_enabled BOOLEAN NOT NULL DEFAULT FALSE
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
            CREATE INDEX IF NOT EXISTS like_history_account_success_idx
            ON like_history (account_id)
            WHERE status='success' AND likes_given > 0
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

        db.execute("""
            CREATE TABLE IF NOT EXISTS chat_conversations (
                id BIGSERIAL PRIMARY KEY,
                account_id BIGINT REFERENCES accounts(id) ON DELETE CASCADE,
                guest_token_hash TEXT,
                guest_name TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK (
                    (account_id IS NOT NULL AND guest_token_hash IS NULL)
                    OR
                    (account_id IS NULL AND guest_token_hash IS NOT NULL)
                )
            )
        """)

        db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS chat_conversations_account_idx
            ON chat_conversations(account_id)
            WHERE account_id IS NOT NULL
        """)

        db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS chat_conversations_guest_idx
            ON chat_conversations(guest_token_hash)
            WHERE guest_token_hash IS NOT NULL
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id BIGSERIAL PRIMARY KEY,
                conversation_id BIGINT NOT NULL
                    REFERENCES chat_conversations(id) ON DELETE CASCADE,
                sender TEXT NOT NULL CHECK(sender IN ('customer', 'admin')),
                message TEXT NOT NULL CHECK(char_length(message) BETWEEN 1 AND 1000),
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS chat_messages_conversation_idx
            ON chat_messages(conversation_id, id)
        """)


def current_account():
    token = request.headers.get("X-Account-Token", "")
    if not token:
        return None
    with db_connect() as db:
        return db.execute("""
            SELECT a.id, a.username, a.coins, a.display_name, a.avatar_version, a.name_color, a.crown_enabled
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


def chat_admin_authorized():
    supplied = request.headers.get("X-Admin-Key", "")
    return bool(ADMIN_KEY) and secrets.compare_digest(supplied, ADMIN_KEY)


def chat_find_customer_conversation(db, account, guest_token):
    if account:
        return db.execute(
            "SELECT id FROM chat_conversations WHERE account_id=%s",
            (account["id"],)
        ).fetchone()

    if not guest_token or len(guest_token) > 200:
        return None

    token_hash = hashlib.sha256(guest_token.encode()).hexdigest()
    return db.execute(
        "SELECT id FROM chat_conversations WHERE guest_token_hash=%s",
        (token_hash,)
    ).fetchone()


@app.post("/api/chat/session")
def chat_customer_session():
    data = request.get_json(silent=True) or {}
    account = current_account()
    guest_token = request.headers.get("X-Chat-Guest-Token", "").strip()

    with db_connect() as db:
        if account:
            conversation = db.execute(
                "SELECT id FROM chat_conversations WHERE account_id=%s",
                (account["id"],)
            ).fetchone()

            if not conversation:
                conversation = db.execute(
                    """INSERT INTO chat_conversations (account_id)
                       VALUES (%s) RETURNING id""",
                    (account["id"],)
                ).fetchone()

            return jsonify({
                "ok": True,
                "conversation_id": conversation["id"],
                "customer_name": account.get("display_name") or "Ganz X - OFC",
                "guest": False
            })

        if not guest_token:
            guest_name = str(data.get("guest_name", "")).strip()
            if not 2 <= len(guest_name) <= 30:
                return jsonify({
                    "ok": False,
                    "message": "Nama tamu harus 2–30 karakter."
                }), 400
            guest_token = secrets.token_urlsafe(32)
        else:
            guest_name = str(data.get("guest_name", "")).strip()[:30]

        token_hash = hashlib.sha256(guest_token.encode()).hexdigest()
        conversation = db.execute(
            "SELECT id, guest_name FROM chat_conversations WHERE guest_token_hash=%s",
            (token_hash,)
        ).fetchone()

        if not conversation:
            if not 2 <= len(guest_name) <= 30:
                return jsonify({
                    "ok": False,
                    "message": "Masukkan nama tamu terlebih dahulu."
                }), 400

            conversation = db.execute(
                """INSERT INTO chat_conversations (guest_token_hash, guest_name)
                   VALUES (%s, %s) RETURNING id, guest_name""",
                (token_hash, guest_name)
            ).fetchone()

        return jsonify({
            "ok": True,
            "conversation_id": conversation["id"],
            "customer_name": conversation["guest_name"],
            "guest": True,
            "guest_token": guest_token
        })



CHAT_STATUS_SCHEMA_READY = False

def ensure_chat_status_schema():
    global CHAT_STATUS_SCHEMA_READY
    if CHAT_STATUS_SCHEMA_READY:
        return

    with db_connect() as db:
        db.execute(
            "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ"
        )
        db.execute("""
            CREATE TABLE IF NOT EXISTS chat_admin_presence (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS chat_customer_presence (
                conversation_id BIGINT PRIMARY KEY,
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

    CHAT_STATUS_SCHEMA_READY = True


@app.get("/api/chat/messages")
def chat_customer_messages():
    account = current_account()
    guest_token = request.headers.get("X-Chat-Guest-Token", "").strip()
    ensure_chat_status_schema()

    with db_connect() as db:
        conversation = chat_find_customer_conversation(db, account, guest_token)
        if not conversation:
            return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

        db.execute("""
            INSERT INTO chat_customer_presence (conversation_id, last_seen_at)
            VALUES (%s, CURRENT_TIMESTAMP)
            ON CONFLICT (conversation_id)
            DO UPDATE SET last_seen_at=CURRENT_TIMESTAMP
        """, (conversation["id"],))

        admin_online = db.execute("""
            SELECT EXISTS (
                SELECT 1 FROM chat_admin_presence
                WHERE id=1
                  AND last_seen_at > CURRENT_TIMESTAMP - INTERVAL '45 seconds'
            ) AS online
        """).fetchone()["online"]

        rows = db.execute(
            """SELECT id, sender, message,
                      (image_data IS NOT NULL) AS has_photo,
                      to_char(created_at AT TIME ZONE 'Asia/Jakarta', 'HH24:MI') AS created_time,
                      read_at
               FROM chat_messages
               WHERE conversation_id=%s
               ORDER BY id DESC LIMIT 100""",
            (conversation["id"],)
        ).fetchall()

    return jsonify({
        "ok": True,
        "admin_online": admin_online,
        "messages": list(reversed(rows))
    })


@app.post("/api/chat/read")
def chat_customer_mark_read():
    account = current_account()
    guest_token = request.headers.get("X-Chat-Guest-Token", "").strip()
    ensure_chat_status_schema()

    with db_connect() as db:
        conversation = chat_find_customer_conversation(db, account, guest_token)
        if not conversation:
            return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

        db.execute(
            """UPDATE chat_messages
               SET read_at=CURRENT_TIMESTAMP
               WHERE conversation_id=%s
                 AND sender='admin'
                 AND read_at IS NULL""",
            (conversation["id"],)
        )

    return jsonify({"ok": True})


@app.post("/api/chat/messages")
def chat_customer_send_message():
    account = current_account()
    guest_token = request.headers.get("X-Chat-Guest-Token", "").strip()
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message or len(message) > 1000:
        return jsonify({
            "ok": False,
            "message": "Pesan harus 1–1000 karakter."
        }), 400

    with db_connect() as db:
        conversation = chat_find_customer_conversation(db, account, guest_token)
        if not conversation:
            return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

        db.execute(
            """INSERT INTO chat_messages (conversation_id, sender, message)
               VALUES (%s, 'customer', %s)""",
            (conversation["id"], message)
        )
        db.execute(
            "UPDATE chat_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            (conversation["id"],)
        )

    return jsonify({"ok": True, "message": "Pesan terkirim."})



@app.post("/api/chat/photo")
def chat_customer_send_photo():
    account = current_account()
    guest_token = request.headers.get("X-Chat-Guest-Token", "").strip()
    photo = request.files.get("photo")

    if not photo:
        return jsonify({"ok": False, "message": "Pilih foto terlebih dahulu."}), 400

    image_data = photo.stream.read(3 * 1024 * 1024 + 1)
    if not image_data or len(image_data) > 3 * 1024 * 1024:
        return jsonify({"ok": False, "message": "Ukuran foto maksimal 3 MB."}), 400

    if image_data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif len(image_data) >= 12 and image_data[:4] == b"RIFF" and image_data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return jsonify({"ok": False, "message": "Format foto harus JPEG, PNG, atau WEBP."}), 400

    with db_connect() as db:
        conversation = chat_find_customer_conversation(db, account, guest_token)
        if not conversation:
            return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

        db.execute("""
            INSERT INTO chat_messages
                (conversation_id, sender, message, image_data, image_mime)
            VALUES (%s, 'customer', '[Foto]', %s, %s)
        """, (conversation["id"], image_data, mime))
        db.execute(
            "UPDATE chat_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            (conversation["id"],)
        )

    return jsonify({"ok": True, "message": "Foto terkirim."})


@app.get("/api/chat/photo/<int:message_id>")
def chat_customer_get_photo(message_id):
    account = current_account()
    guest_token = request.headers.get("X-Chat-Guest-Token", "").strip()

    with db_connect() as db:
        conversation = chat_find_customer_conversation(db, account, guest_token)
        if not conversation:
            return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

        row = db.execute("""
            SELECT image_data, image_mime FROM chat_messages
            WHERE id=%s AND conversation_id=%s AND image_data IS NOT NULL
        """, (message_id, conversation["id"])).fetchone()

    if not row:
        return jsonify({"ok": False, "message": "Foto tidak ditemukan."}), 404

    return Response(row["image_data"], mimetype=row["image_mime"],
                    headers={"Cache-Control": "private, no-store",
                             "X-Content-Type-Options": "nosniff"})


@app.get("/admin/chat/conversations")
def chat_admin_conversations():
    if not chat_admin_authorized():
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    with db_connect() as db:
        rows = db.execute("""
            SELECT c.id,
                   CASE WHEN c.account_id IS NOT NULL THEN COALESCE(NULLIF(BTRIM(a.display_name), ''), 'Pelanggan') ELSE COALESCE(NULLIF(BTRIM(c.guest_name), ''), 'Tamu') END AS customer_name,
                   CASE WHEN c.account_id IS NULL THEN TRUE ELSE FALSE END AS guest,
                   CASE
                       WHEN c.account_id IS NOT NULL AND a.avatar_data IS NOT NULL
                       THEN '/api/avatar/' || a.id::text || '?v=' || COALESCE(a.avatar_version, 0)::text
                       ELSE NULL
                   END AS avatar_url,
                   COALESCE(m.message, '') AS last_message,
                   c.updated_at::text AS updated_at
            FROM chat_conversations c
            LEFT JOIN accounts a ON a.id=c.account_id
            LEFT JOIN LATERAL (
                SELECT message FROM chat_messages
                WHERE conversation_id=c.id
                ORDER BY id DESC LIMIT 1
            ) m ON TRUE
            ORDER BY c.updated_at DESC
            LIMIT 100
        """).fetchall()

    return jsonify({"ok": True, "conversations": rows})



@app.post("/admin/chat/presence")
def chat_admin_presence():
    if not chat_admin_authorized():
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    ensure_chat_status_schema()

    with db_connect() as db:
        db.execute("""
            INSERT INTO chat_admin_presence (id, last_seen_at)
            VALUES (1, CURRENT_TIMESTAMP)
            ON CONFLICT (id)
            DO UPDATE SET last_seen_at=CURRENT_TIMESTAMP
        """)

    return jsonify({"ok": True})


@app.route("/admin/chat/<int:conversation_id>/messages", methods=["GET", "POST"])
def chat_admin_messages(conversation_id):
    if not chat_admin_authorized():
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()

        if not message or len(message) > 1000:
            return jsonify({
                "ok": False,
                "message": "Pesan harus 1–1000 karakter."
            }), 400

        with db_connect() as db:
            exists = db.execute(
                "SELECT id FROM chat_conversations WHERE id=%s",
                (conversation_id,)
            ).fetchone()
            if not exists:
                return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

            db.execute(
                """INSERT INTO chat_messages (conversation_id, sender, message)
                   VALUES (%s, 'admin', %s)""",
                (conversation_id, message)
            )
            db.execute(
                """UPDATE chat_messages
                   SET read_at=CURRENT_TIMESTAMP
                   WHERE conversation_id=%s
                     AND sender='customer'
                     AND read_at IS NULL""",
                (conversation_id,)
            )
            db.execute(
                "UPDATE chat_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (conversation_id,)
            )

        return jsonify({"ok": True, "message": "Balasan terkirim."})

    ensure_chat_status_schema()
    with db_connect() as db:
        db.execute("""
            INSERT INTO chat_admin_presence (id, last_seen_at)
            VALUES (1, CURRENT_TIMESTAMP)
            ON CONFLICT (id)
            DO UPDATE SET last_seen_at=CURRENT_TIMESTAMP
        """)
        exists = db.execute(
            "SELECT id FROM chat_conversations WHERE id=%s",
            (conversation_id,)
        ).fetchone()
        if not exists:
            return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

        customer_online = db.execute("""
            SELECT EXISTS (
                SELECT 1 FROM chat_customer_presence
                WHERE conversation_id=%s
                  AND last_seen_at > CURRENT_TIMESTAMP - INTERVAL '45 seconds'
            ) AS online
        """, (conversation_id,)).fetchone()["online"]

        rows = db.execute(
            """SELECT id, sender, message,
                      (image_data IS NOT NULL) AS has_photo,
                      to_char(created_at AT TIME ZONE 'Asia/Jakarta', 'HH24:MI') AS created_time,
                      read_at
               FROM chat_messages
               WHERE conversation_id=%s
               ORDER BY id DESC LIMIT 100""",
            (conversation_id,)
        ).fetchall()

    return jsonify({
        "ok": True,
        "customer_online": customer_online,
        "messages": list(reversed(rows))
    })



@app.post("/admin/chat/<int:conversation_id>/read")
def chat_admin_mark_read(conversation_id):
    if not chat_admin_authorized():
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    ensure_chat_status_schema()

    with db_connect() as db:
        db.execute(
            """UPDATE chat_messages
               SET read_at=CURRENT_TIMESTAMP
               WHERE conversation_id=%s
                 AND sender='customer'
                 AND read_at IS NULL""",
            (conversation_id,)
        )

    return jsonify({"ok": True})


@app.post("/admin/chat/<int:conversation_id>/photo")
def chat_admin_send_photo(conversation_id):
    if not chat_admin_authorized():
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    photo = request.files.get("photo")
    if not photo:
        return jsonify({"ok": False, "message": "Pilih foto terlebih dahulu."}), 400

    image_data = photo.stream.read(3 * 1024 * 1024 + 1)
    if not image_data or len(image_data) > 3 * 1024 * 1024:
        return jsonify({"ok": False, "message": "Ukuran foto maksimal 3 MB."}), 400

    if image_data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif len(image_data) >= 12 and image_data[:4] == b"RIFF" and image_data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return jsonify({"ok": False, "message": "Format foto harus JPEG, PNG, atau WEBP."}), 400

    with db_connect() as db:
        exists = db.execute(
            "SELECT id FROM chat_conversations WHERE id=%s",
            (conversation_id,)
        ).fetchone()
        if not exists:
            return jsonify({"ok": False, "message": "Percakapan tidak ditemukan."}), 404

        db.execute("""
            INSERT INTO chat_messages
                (conversation_id, sender, message, image_data, image_mime)
            VALUES (%s, 'admin', '[Foto]', %s, %s)
        """, (conversation_id, image_data, mime))
        db.execute(
            """UPDATE chat_messages
               SET read_at=CURRENT_TIMESTAMP
               WHERE conversation_id=%s
                 AND sender='customer'
                 AND read_at IS NULL""",
            (conversation_id,)
        )
        db.execute(
            "UPDATE chat_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            (conversation_id,)
        )

    return jsonify({"ok": True, "message": "Foto terkirim."})


@app.get("/admin/chat/photo/<int:message_id>")
def chat_admin_get_photo(message_id):
    if not chat_admin_authorized():
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    with db_connect() as db:
        row = db.execute("""
            SELECT image_data, image_mime FROM chat_messages
            WHERE id=%s AND image_data IS NOT NULL
        """, (message_id,)).fetchone()

    if not row:
        return jsonify({"ok": False, "message": "Foto tidak ditemukan."}), 404

    return Response(row["image_data"], mimetype=row["image_mime"],
                    headers={"Cache-Control": "private, no-store",
                             "X-Content-Type-Options": "nosniff"})


@app.get("/api/account")
def account_info():
    account = current_account()
    if not account:
        return jsonify({"logged_in": False})

    with db_connect() as db:
        row = db.execute("""
            SELECT COALESCE(SUM(CASE WHEN service='vip' THEN 5 ELSE 1 END), 0) AS total_spent
            FROM like_history
            WHERE account_id=%s AND status='success' AND likes_given > 0
        """, (account["id"],)).fetchone()

    total_spent = int(row["total_spent"] or 0)
    return jsonify({
        "logged_in": True,
        "username": account["username"],
        "display_name": account.get("display_name") or "Ganz X - OFC",
        "coins": account["coins"],
        "name_color": account.get("name_color") or "white",
        "crown_enabled": bool(account.get("crown_enabled", False)),
        "total_spent": total_spent,
        "avatar_url": f"/api/avatar/{account['id']}?v={secrets.token_hex(8)}"
    })

@app.post("/api/account/name")
@login_required
def update_account_name(account):
    data = request.get_json(silent=True) or {}
    display_name = str(data.get("display_name", "")).strip()
    if not display_name or len(display_name) > 30:
        return jsonify({"ok": False, "message": "Nama harus 1–30 karakter."}), 400

    with db_connect() as db:
        db.execute(
            "UPDATE accounts SET display_name=%s WHERE id=%s",
            (display_name, account["id"])
        )
    return jsonify({"ok": True, "display_name": display_name,
                    "message": "Nama tampilan berhasil disimpan."})


@app.post("/api/account/name-color")
@login_required
def update_account_name_color(account):
    data = request.get_json(silent=True) or {}
    color = str(data.get("color", "white")).strip().lower()
    thresholds = {"white": 0, "red": 20, "blue": 50, "gradient": 100}
    if color not in thresholds:
        return jsonify({"ok": False, "message": "Warna tidak valid."}), 400

    with db_connect() as db:
        row = db.execute("""
            SELECT COALESCE(SUM(CASE WHEN service='vip' THEN 5 ELSE 1 END), 0) AS total_spent
            FROM like_history
            WHERE account_id=%s AND status='success' AND likes_given > 0
        """, (account["id"],)).fetchone()
        total_spent = int(row["total_spent"] or 0)

        if total_spent < thresholds[color]:
            return jsonify({
                "ok": False,
                "message": f"Warna ini terbuka setelah menghabiskan {thresholds[color]} Coins.",
                "total_spent": total_spent
            }), 403

        db.execute(
            "UPDATE accounts SET name_color=%s WHERE id=%s",
            (color, account["id"])
        )

    unlocked = [name for name, cost in thresholds.items() if total_spent >= cost]
    return jsonify({
        "ok": True,
        "name_color": color,
        "total_spent": total_spent,
        "unlocked_colors": unlocked,
        "message": "Warna nama berhasil diganti."
    })


@app.post("/api/account/crown")
@login_required
def update_account_crown(account):
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled", False))

    with db_connect() as db:
        row = db.execute("""
            SELECT COALESCE(SUM(CASE WHEN service='vip' THEN 5 ELSE 1 END), 0) AS total_spent
            FROM like_history
            WHERE account_id=%s AND status='success' AND likes_given > 0
        """, (account["id"],)).fetchone()

        total_spent = int(row["total_spent"] or 0)

        if enabled and total_spent < 500:
            return jsonify({
                "ok": False,
                "message": "Mahkota terbuka setelah menggunakan 500 Coins.",
                "total_spent": total_spent
            }), 403

        db.execute(
            "UPDATE accounts SET crown_enabled=%s WHERE id=%s",
            (enabled, account["id"])
        )

    return jsonify({
        "ok": True,
        "crown_enabled": enabled,
        "total_spent": total_spent,
        "message": "Mahkota berhasil diaktifkan." if enabled else "Mahkota berhasil dinonaktifkan."
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


@app.get("/api/avatar/<int:account_id>")
def account_avatar(account_id):
    with db_connect() as db:
        row = db.execute(
            "SELECT avatar_data, avatar_mime FROM accounts WHERE id=%s",
            (account_id,)
        ).fetchone()
    if not row or not row["avatar_data"]:
        response = redirect("/static/profil.webp")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response
    return Response(
        bytes(row["avatar_data"]),
        mimetype=row["avatar_mime"] or "image/jpeg",
        headers={"Cache-Control": "public, max-age=2592000, immutable"}
    )


@app.post("/api/account/avatar")
@login_required
def upload_account_avatar(account):
    file = request.files.get("avatar")
    if not file:
        return jsonify({"ok": False, "message": "Pilih foto terlebih dahulu."}), 400

    data = file.read(5 * 1024 * 1024 + 1)
    if not data or len(data) > 5 * 1024 * 1024:
        return jsonify({"ok": False, "message": "Ukuran foto maksimal 5 MB."}), 400

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return jsonify({"ok": False, "message": "Format foto harus JPG, PNG, atau WEBP."}), 400

    with db_connect() as db:
        row = db.execute(
            "UPDATE accounts SET avatar_data=%s, avatar_mime=%s, avatar_version=avatar_version+1 WHERE id=%s RETURNING avatar_version",
            (data, mime, account["id"])
        ).fetchone()
    avatar_version = row["avatar_version"]
    return jsonify({
        "ok": True,
        "avatar_url": f"/api/avatar/{account['id']}?v={avatar_version}"
    })


@app.post("/api/account/password")
@login_required
def change_account_password(account):
    data = request.get_json(silent=True) or {}
    old_password = str(data.get("current_password", ""))
    new_password = str(data.get("new_password", ""))

    if not 8 <= len(new_password) <= 128:
        return jsonify({"ok": False, "message": "Password baru harus 8–128 karakter."}), 400

    with db_connect() as db:
        row = db.execute(
            "SELECT password_hash FROM accounts WHERE id=%s",
            (account["id"],)
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], old_password):
            return jsonify({"ok": False, "message": "Password lama salah."}), 400
        db.execute(
            "UPDATE accounts SET password_hash=%s WHERE id=%s",
            (generate_password_hash(new_password), account["id"])
        )

    return jsonify({"ok": True, "message": "Password berhasil diganti."})


@app.get("/api/leaderboard")
def account_leaderboard():
    with db_connect() as db:
        rows = db.execute("""
            SELECT id, display_name, name_color, coins, avatar_version, crown_enabled
            FROM accounts
            ORDER BY coins DESC, id ASC
            LIMIT 100
        """).fetchall()

    result = []
    allowed_colors = {"white", "red", "blue", "gradient"}
    for rank, row in enumerate(rows, 1):
        name_color = str(row["name_color"] or "white").lower()
        if name_color not in allowed_colors:
            name_color = "white"

        result.append({
            "rank": rank,
            "display_name": row["display_name"] or "Ganz X - OFC",
            "name_color": name_color,
            "coins": row["coins"],
            "avatar_url": f"/api/avatar/{row['id']}?v={row['avatar_version']}",
            "crown_enabled": bool(row["crown_enabled"])
        })
    return jsonify({"ok": True, "users": result})


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

@app.get("/admin/search-accounts")
def admin_search_accounts():
    if not ADMIN_KEY or not secrets.compare_digest(
        request.headers.get("X-Admin-Key", ""), ADMIN_KEY
    ):
        return jsonify({"ok": False, "message": "Akses admin ditolak."}), 403

    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"ok": True, "users": []})

    with db_connect() as db:
        rows = db.execute(
            """SELECT username, coins
               FROM accounts
               WHERE username ILIKE %s
               ORDER BY username
               LIMIT 20""",
            (f"%{query}%",)
        ).fetchall()

    return jsonify({
        "ok": True,
        "users": [
            {"username": row["username"], "coins": row["coins"]}
            for row in rows
        ]
    })


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
def like_history():
    with db_connect() as db:
        rows = db.execute("""
            SELECT h.id, h.service, h.uid, h.region, h.status, h.likes_given,
                   h.likes_before, h.likes_after, h.message,
                   COALESCE(h.created_at, CURRENT_TIMESTAMP) AS created_at,
                   COALESCE(NULLIF(a.display_name, ''), a.username) AS username
            FROM like_history h
            JOIN accounts a ON a.id = h.account_id
            WHERE h.status = 'success' AND h.likes_given > 0
              AND h.service IN ('free', 'vip')
              AND h.id IN (
                  SELECT id
                  FROM like_history
                  WHERE status = 'success' AND likes_given > 0
                    AND service = h.service
                  ORDER BY id DESC
                  LIMIT 25
              )
            ORDER BY h.id DESC
        """).fetchall()
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


@app.get("/admin/chat")
def admin_chat_page():
    from flask import send_from_directory
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
        "admin-chat.html"
    )


@app.get("/")
def home_page():
    from flask import send_from_directory
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.get("/health")
def health():
    return jsonify({"name": "GANZ X - OFC", "status": "online", "version": "new-accounts"})

if os.environ.get('RUN_DB_INIT') == '1':
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
