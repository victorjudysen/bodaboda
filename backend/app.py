

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db import get_db_connection
import logging

import pathlib

# Path to the frontend directory (relative to backend)
FRONTEND_DIR = pathlib.Path(__file__).parent.parent / "frontend"

app = Flask(__name__)
CORS(app)

# Simple logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


@app.before_request
def log_request_info():
    logging.info(f"{request.method} {request.path} - {request.remote_addr}")


# --- Serve Frontend ---
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/dashboard.html")
def serve_dashboard():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")

@app.route("/request.html")
def serve_request():
    return send_from_directory(FRONTEND_DIR, "request.html")

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(FRONTEND_DIR / "css", filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(FRONTEND_DIR / "js", filename)

# --- API Home (for health check) ---
@app.route("/api", methods=["GET"])
def api_home():
    return jsonify({"message": "BodaConnect API is running"})


@app.route("/request-ride", methods=["POST"])
def request_ride():
    data = request.get_json()
    pickup = data.get('pickup', '').strip() if data else ''
    destination = data.get('destination', '').strip() if data else ''
    # Input validation
    if not pickup or not destination:
        return jsonify({"error": "Pickup and destination are required."}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    try:
        with conn:
            with conn.cursor() as cur:
                # Fetch a random rider
                cur.execute("SELECT id FROM riders ORDER BY RANDOM() LIMIT 1")
                rider_row = cur.fetchone()
                if not rider_row:
                    return jsonify({"error": "No riders available."}), 500
                rider_id = rider_row['id']
                # Insert trip with dynamic rider_id
                cur.execute(
                    "INSERT INTO trips (pickup, destination, rider_id) VALUES (%s, %s, %s) RETURNING id",
                    (pickup, destination, rider_id)
                )
                trip_id = cur.fetchone()['id']
        return jsonify({"message": "Ride requested successfully.", "trip_id": trip_id})
    except Exception as e:
        logging.error(f"DB ERROR (request-ride): {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.route("/rider-dashboard", methods=["GET"])
def rider_dashboard():
    # For demo, still using rider_id=1 (could be dynamic in future)
    rider_id = 1
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM riders WHERE id = %s", (rider_id,))
                rider = cur.fetchone()
                if not rider:
                    return jsonify({"error": "Rider not found."}), 404
                # Limit to latest 10 trips, newest first
                cur.execute("SELECT pickup, destination FROM trips WHERE rider_id = %s ORDER BY created_at DESC LIMIT 10", (rider_id,))
                trips = cur.fetchall()
        return jsonify({
            "rider": rider['name'],
            "assigned_trips": trips
        })
    except Exception as e:
        logging.error(f"DB ERROR (rider-dashboard): {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

import os

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
