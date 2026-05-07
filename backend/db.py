import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.getenv("DB_PATH", "/app/data/bodaboda.db")

_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'customer'
                          CHECK (role IN ('customer','rider')),
    phone         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS riders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    bike_plate TEXT,
    rating     REAL    DEFAULT 5.0,
    status     TEXT    NOT NULL DEFAULT 'available'
                       CHECK (status IN ('available','busy','offline'))
);

CREATE TABLE IF NOT EXISTS trips (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  INTEGER REFERENCES users(id),
    rider_id     INTEGER REFERENCES riders(id),
    pickup       TEXT    NOT NULL,
    destination  TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending','active','completed','cancelled')),
    fare         REAL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
"""


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def wait_for_db(*_, **__):
    return True


def init_db():
    conn = get_db_connection()
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialised at {DB_PATH}")


def seed_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        print("Database already seeded.")
        return

    pwd = generate_password_hash("pass123")

    riders_seed = [
        ("Juma Hassan",   "juma@bodaboda.com",  "rider",    "+255712345001", "T 123 ABC"),
        ("Peter Kimani",  "peter@bodaboda.com", "rider",    "+254712345002", "KCA 456X"),
        ("Grace Wanjiku", "grace@bodaboda.com", "rider",    "+254712345003", "KDC 789Y"),
        ("David Otieno",  "david@bodaboda.com", "rider",    "+254712345004", "KBZ 321M"),
        ("Sarah Mwangi",  "sarah@bodaboda.com", "rider",    "+254712345005", "T 654 DEF"),
    ]
    customers_seed = [
        ("Amina Salim",      "amina@example.com",   "customer", "+255722111001"),
        ("Brian Odhiambo",   "brian@example.com",   "customer", "+254722111002"),
        ("Cynthia Njeri",    "cynthia@example.com", "customer", "+254722111003"),
        ("Dennis Mutua",     "dennis@example.com",  "customer", "+254722111004"),
        ("Esther Akinyi",    "esther@example.com",  "customer", "+254722111005"),
    ]

    try:
        cust_ids = []
        for name, email, role, phone in customers_seed:
            cur.execute(
                "INSERT INTO users (name,email,password_hash,role,phone) VALUES (?,?,?,?,?)",
                (name, email, pwd, role, phone),
            )
            cust_ids.append(cur.lastrowid)

        rider_ids = []
        for i, (name, email, role, phone, plate) in enumerate(riders_seed):
            cur.execute(
                "INSERT INTO users (name,email,password_hash,role,phone) VALUES (?,?,?,?,?)",
                (name, email, pwd, role, phone),
            )
            uid = cur.lastrowid
            rating = round(4.5 + i * 0.1, 1)
            cur.execute(
                "INSERT INTO riders (user_id,bike_plate,rating,status) VALUES (?,?,?,'available')",
                (uid, plate, rating),
            )
            rider_ids.append(cur.lastrowid)

        locations = [
            ("Kariakoo Market",      "Mwenge Bus Terminal"),
            ("Ubungo Interchange",   "Msasani Peninsula"),
            ("Posta Kuu",            "Oyster Bay"),
            ("Kinondoni",            "Tabata"),
            ("Mlimani City",         "Tegeta"),
            ("Ferry Terminal",       "Masaki"),
            ("Gongo la Mboto",       "Kijitonyama"),
            ("Sinza",                "Mikocheni"),
            ("Mwananyamala",         "Kawe Beach"),
            ("Chang'ombe",           "Magomeni"),
        ]
        statuses = ["completed","completed","completed","active","pending",
                    "cancelled","completed","completed","active","pending"]

        for i, ((pickup, dest), status) in enumerate(zip(locations, statuses)):
            cur.execute(
                "INSERT INTO trips (customer_id,rider_id,pickup,destination,status,fare) VALUES (?,?,?,?,?,?)",
                (cust_ids[i % len(cust_ids)], rider_ids[i % len(rider_ids)],
                 pickup, dest, status, round(150 + (i * 37) % 350)),
            )

        conn.commit()
        print("Database seeded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Seed error: {e}")
    finally:
        conn.close()
