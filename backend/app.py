import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from db import get_db_connection, init_db, seed_db

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── Prometheus metrics ───────────────────────────────────────────────────────
RIDE_REQUESTS  = Counter("bodaboda_ride_requests_total",      "Total ride requests submitted")
USER_REGS      = Counter("bodaboda_user_registrations_total", "Total user registrations")
LOGIN_ATTEMPTS = Counter("bodaboda_login_attempts_total",     "Total login attempts", ["result"])
REG_USERS      = Gauge("bodaboda_registered_users",           "Total registered users")
ACTIVE_RIDERS  = Gauge("bodaboda_active_riders",              "Riders with status=available")
TOTAL_TRIPS    = Gauge("bodaboda_total_trips",                "Total trips in the system")
TRIPS_STATUS   = Gauge("bodaboda_trips_by_status",            "Trips grouped by status", ["status"])


def refresh_gauges(cur):
    REG_USERS.set(cur.execute("SELECT COUNT(*) FROM users").fetchone()[0])
    ACTIVE_RIDERS.set(cur.execute("SELECT COUNT(*) FROM riders WHERE status='available'").fetchone()[0])
    TOTAL_TRIPS.set(cur.execute("SELECT COUNT(*) FROM trips").fetchone()[0])
    for row in cur.execute("SELECT status, COUNT(*) FROM trips GROUP BY status").fetchall():
        TRIPS_STATUS.labels(status=row[0]).set(row[1])


# ── Auth ─────────────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data       = request.get_json() or {}
    name       = data.get("name", "").strip()
    email      = data.get("email", "").strip().lower()
    password   = data.get("password", "")
    role       = data.get("role", "customer")
    phone      = data.get("phone", "").strip()
    bike_plate = data.get("bike_plate", "").strip()

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if role not in ("customer", "rider"):
        return jsonify({"error": "role must be customer or rider"}), 400

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if cur.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            return jsonify({"error": "Email already registered"}), 409
        pwd_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (name,email,password_hash,role,phone) VALUES (?,?,?,?,?)",
            (name, email, pwd_hash, role, phone),
        )
        user_id  = cur.lastrowid
        rider_id = None
        if role == "rider":
            cur.execute(
                "INSERT INTO riders (user_id,bike_plate) VALUES (?,?)",
                (user_id, bike_plate or "N/A"),
            )
            rider_id = cur.lastrowid
        conn.commit()
        USER_REGS.inc()
        logging.info(f"New user registered: {email} ({role})")
        return jsonify({"user_id": user_id, "name": name, "role": role, "rider_id": rider_id}), 201
    except Exception as e:
        conn.rollback()
        logging.error(f"Register error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    conn = get_db_connection()
    try:
        cur  = conn.cursor()
        row  = cur.execute(
            "SELECT id,name,password_hash,role,phone FROM users WHERE email=?", (email,)
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            LOGIN_ATTEMPTS.labels(result="failure").inc()
            return jsonify({"error": "Invalid email or password"}), 401
        rider_id = None
        if row["role"] == "rider":
            r = cur.execute("SELECT id FROM riders WHERE user_id=?", (row["id"],)).fetchone()
            if r:
                rider_id = r["id"]
        LOGIN_ATTEMPTS.labels(result="success").inc()
        return jsonify({
            "user_id":  row["id"],
            "name":     row["name"],
            "role":     row["role"],
            "phone":    row["phone"],
            "rider_id": rider_id,
        })
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


# ── Trips ────────────────────────────────────────────────────────────────────

@app.route("/api/trips", methods=["POST"])
def create_trip():
    data        = request.get_json() or {}
    customer_id = data.get("customer_id")
    pickup      = data.get("pickup", "").strip()
    destination = data.get("destination", "").strip()

    if not customer_id or not pickup or not destination:
        return jsonify({"error": "customer_id, pickup and destination are required"}), 400

    conn = get_db_connection()
    try:
        cur   = conn.cursor()
        rider = cur.execute(
            "SELECT r.id, r.user_id FROM riders r WHERE r.status='available' ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if not rider:
            return jsonify({"error": "No riders available right now"}), 503
        fare = round(150 + (len(pickup) + len(destination)) * 2.5)
        cur.execute(
            "INSERT INTO trips (customer_id,rider_id,pickup,destination,status,fare) VALUES (?,?,?,?,'pending',?)",
            (customer_id, rider["id"], pickup, destination, fare),
        )
        trip_id = cur.lastrowid
        cur.execute("UPDATE riders SET status='busy' WHERE id=?", (rider["id"],))
        rider_user = cur.execute("SELECT name FROM users WHERE id=?", (rider["user_id"],)).fetchone()
        conn.commit()
        RIDE_REQUESTS.inc()
        return jsonify({
            "trip_id": trip_id,
            "rider":   rider_user["name"] if rider_user else "Unknown",
            "fare":    fare,
            "message": "Ride requested! Your rider is on the way.",
        }), 201
    except Exception as e:
        conn.rollback()
        logging.error(f"Create trip error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


@app.route("/api/trips", methods=["GET"])
def get_trips():
    customer_id = request.args.get("customer_id")
    if not customer_id:
        return jsonify({"error": "customer_id is required"}), 400

    conn = get_db_connection()
    try:
        cur   = conn.cursor()
        rows  = cur.execute(
            """SELECT t.id, t.pickup, t.destination, t.status, t.fare,
                      t.created_at, u.name AS rider_name
               FROM trips t
               LEFT JOIN riders r ON t.rider_id  = r.id
               LEFT JOIN users  u ON r.user_id   = u.id
               WHERE t.customer_id = ?
               ORDER BY t.created_at DESC LIMIT 20""",
            (customer_id,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        logging.error(f"Get trips error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


# ── Riders ───────────────────────────────────────────────────────────────────

@app.route("/api/riders", methods=["GET"])
def get_riders():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """SELECT r.id, u.name, r.bike_plate, r.rating, r.status
               FROM riders r JOIN users u ON r.user_id = u.id
               ORDER BY (r.status='available') DESC, r.rating DESC"""
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        logging.error(f"Get riders error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


@app.route("/api/riders/status", methods=["PATCH"])
def update_rider_status():
    data    = request.get_json() or {}
    user_id = data.get("user_id")
    status  = data.get("status")
    if not user_id or status not in ("available", "busy", "offline"):
        return jsonify({"error": "user_id and valid status are required"}), 400

    conn = get_db_connection()
    try:
        conn.execute("UPDATE riders SET status=? WHERE user_id=?", (status, user_id))
        conn.commit()
        return jsonify({"message": f"Status updated to {status}"})
    except Exception as e:
        conn.rollback()
        logging.error(f"Update rider status error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


# ── Dashboards ───────────────────────────────────────────────────────────────

@app.route("/api/dashboard/rider", methods=["GET"])
def rider_dashboard():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db_connection()
    try:
        cur  = conn.cursor()
        user = cur.execute("SELECT name FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        rider = cur.execute(
            "SELECT id,status,rating,bike_plate FROM riders WHERE user_id=?", (user_id,)
        ).fetchone()
        if not rider:
            return jsonify({"error": "Rider profile not found"}), 404

        trips = cur.execute(
            """SELECT t.id, t.pickup, t.destination, t.status, t.fare, t.created_at,
                      u.name AS customer_name
               FROM trips t LEFT JOIN users u ON t.customer_id = u.id
               WHERE t.rider_id = ? ORDER BY t.created_at DESC LIMIT 15""",
            (rider["id"],),
        ).fetchall()
        completed = cur.execute(
            "SELECT COUNT(*) FROM trips WHERE rider_id=? AND status='completed'", (rider["id"],)
        ).fetchone()[0]
        pending = cur.execute(
            "SELECT COUNT(*) FROM trips WHERE rider_id=? AND status='pending'", (rider["id"],)
        ).fetchone()[0]

        return jsonify({
            "name":       user["name"],
            "status":     rider["status"],
            "rating":     float(rider["rating"]),
            "bike_plate": rider["bike_plate"],
            "completed":  completed,
            "pending":    pending,
            "trips":      [dict(t) for t in trips],
        })
    except Exception as e:
        logging.error(f"Rider dashboard error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


@app.route("/api/dashboard/customer", methods=["GET"])
def customer_dashboard():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_db_connection()
    try:
        cur  = conn.cursor()
        user = cur.execute("SELECT name, phone FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        trips = cur.execute(
            """SELECT t.id, t.pickup, t.destination, t.status, t.fare, t.created_at,
                      u.name AS rider_name
               FROM trips t
               LEFT JOIN riders r ON t.rider_id  = r.id
               LEFT JOIN users  u ON r.user_id   = u.id
               WHERE t.customer_id = ? ORDER BY t.created_at DESC LIMIT 15""",
            (user_id,),
        ).fetchall()
        completed = cur.execute(
            "SELECT COUNT(*) FROM trips WHERE customer_id=? AND status='completed'", (user_id,)
        ).fetchone()[0]

        return jsonify({
            "name":      user["name"],
            "phone":     user["phone"],
            "completed": completed,
            "trips":     [dict(t) for t in trips],
        })
    except Exception as e:
        logging.error(f"Customer dashboard error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()


# ── Public stats ──────────────────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def public_stats():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        riders    = cur.execute("SELECT COUNT(*) FROM riders WHERE status='available'").fetchone()[0]
        trips     = cur.execute("SELECT COUNT(*) FROM trips WHERE status='completed'").fetchone()[0]
        customers = cur.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0]
        return jsonify({"riders": riders, "trips": trips, "customers": customers})
    except Exception as e:
        logging.error(f"Stats error: {e}")
        return jsonify({"riders": 0, "trips": 0, "customers": 0})
    finally:
        conn.close()


# ── Prometheus ────────────────────────────────────────────────────────────────

@app.route("/metrics")
def metrics():
    conn = get_db_connection()
    try:
        refresh_gauges(conn.cursor())
    except Exception as e:
        logging.error(f"Metrics refresh error: {e}")
    finally:
        conn.close()
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    seed_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
