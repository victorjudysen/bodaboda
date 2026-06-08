#!/usr/bin/env python3
"""Simple MQTT integration smoke test for the Bodaboda app."""

from __future__ import annotations

import http.client
import json
import os
import threading
import time
import urllib.parse
import urllib.request


BASE_URL = os.getenv("BASE_URL", "http://localhost:5001")
SEED_RIDERS = [
    ("juma@bodaboda.com", "pass123"),
    ("peter@bodaboda.com", "pass123"),
    ("grace@bodaboda.com", "pass123"),
    ("david@bodaboda.com", "pass123"),
    ("sarah@bodaboda.com", "pass123"),
]


def _parsed_base_url():
    parsed = urllib.parse.urlparse(BASE_URL)
    if not parsed.scheme or not parsed.hostname:
        raise RuntimeError(f"Invalid BASE_URL: {BASE_URL}")
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return parsed.scheme, parsed.hostname, port


def request_json(method: str, path: str, payload: dict | None = None) -> tuple[int, object]:
    scheme, host, port = _parsed_base_url()
    conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(host, port, timeout=15)
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    conn.close()
    if resp.status >= 400:
        raise RuntimeError(f"{method} {path} failed: {resp.status} {raw}")
    if not raw:
        return resp.status, None
    return resp.status, json.loads(raw)


def wait_for_health(timeout: int = 60) -> None:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            status, payload = request_json("GET", "/api/health")
            if status == 200 and payload == {"status": "ok"}:
                return
        except Exception as exc:  # pragma: no cover - integration retry loop
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"Backend never became healthy: {last_error}")


class SseWatcher(threading.Thread):
    def __init__(self, rider_id: int):
        super().__init__(daemon=True)
        self.rider_id = rider_id
        self.event = None
        self.error = None
        self.received = threading.Event()
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:  # pragma: no cover - integration helper
        scheme, host, port = _parsed_base_url()
        conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        conn = conn_cls(host, port, timeout=30)
        try:
            path = f"/api/rides/stream?rider_id={self.rider_id}"
            conn.request("GET", path, headers={"Accept": "text/event-stream"})
            resp = conn.getresponse()
            if resp.status != 200:
                self.error = RuntimeError(f"SSE stream failed with {resp.status}")
                self.received.set()
                return

            while not self._stop_event.is_set():
                line = resp.fp.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").strip()
                if not text.startswith("data: "):
                    continue
                try:
                    self.event = json.loads(text[6:])
                except json.JSONDecodeError as exc:
                    self.error = exc
                finally:
                    self.received.set()
                return
        except Exception as exc:
            self.error = exc
            self.received.set()
        finally:
            conn.close()


def main() -> None:
    wait_for_health()

    _, customer = request_json(
        "POST",
        "/api/register",
        {
            "name": "CI Smoke Customer",
            "email": "ci.smoke.customer@test.com",
            "password": "secret123",
            "role": "customer",
            "phone": "+255700000099",
        },
    )

    _, target_rider = request_json(
        "POST",
        "/api/register",
        {
            "name": "CI Smoke Rider",
            "email": "ci.smoke.rider@test.com",
            "password": "secret123",
            "role": "rider",
            "bike_plate": "T 999 CI",
        },
    )

    target_user_id = target_rider["user_id"]
    target_rider_id = target_rider["rider_id"]

    for email, password in SEED_RIDERS:
        _, login = request_json("POST", "/api/login", {"email": email, "password": password})
        if login["user_id"] != target_user_id:
            request_json(
                "PATCH",
                "/api/riders/status",
                {"user_id": login["user_id"], "status": "offline"},
            )

    request_json(
        "PATCH",
        "/api/riders/status",
        {"user_id": target_user_id, "status": "available"},
    )

    watcher = SseWatcher(target_rider_id)
    watcher.start()
    time.sleep(1)

    _, trip = request_json(
        "POST",
        "/api/trips",
        {
            "customer_id": customer["user_id"],
            "pickup": "Posta",
            "destination": "Sinza",
        },
    )

    if trip["rider"] != "CI Smoke Rider":
        raise RuntimeError(f"Expected CI Smoke Rider to receive the trip, got {trip['rider']}")

    if not watcher.received.wait(25):
        raise RuntimeError("Timed out waiting for ride-request SSE event")

    watcher.stop()
    if watcher.error is not None:
        raise RuntimeError(f"SSE watcher failed: {watcher.error}")

    event = watcher.event or {}
    if event.get("customer_id") != customer["user_id"]:
        raise RuntimeError(f"Unexpected customer_id in event: {event}")
    if event.get("rider_id") != target_rider_id:
        raise RuntimeError(f"Unexpected rider_id in event: {event}")
    if event.get("trip_id") != trip["trip_id"]:
        raise RuntimeError(f"Unexpected trip_id in event: {event}")

    print("MQTT smoke test passed")


if __name__ == "__main__":
    main()
