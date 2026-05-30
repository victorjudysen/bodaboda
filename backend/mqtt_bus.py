import json
import logging
import os
import queue
import threading
from typing import Callable, Optional

try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover - optional dependency fallback
    mqtt = None


RideFilter = Optional[Callable[[dict], bool]]


class RideRequestHub:
    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers = []

    def subscribe(self, predicate: RideFilter = None):
        inbox = queue.Queue(maxsize=50)
        with self._lock:
            self._subscribers.append((inbox, predicate))
        return inbox

    def unsubscribe(self, inbox):
        with self._lock:
            self._subscribers = [
                (queue_obj, predicate)
                for queue_obj, predicate in self._subscribers
                if queue_obj is not inbox
            ]

    def publish(self, event: dict):
        with self._lock:
            subscribers = list(self._subscribers)

        for inbox, predicate in subscribers:
            if predicate is not None and not predicate(event):
                continue
            try:
                inbox.put_nowait(event)
            except queue.Full:
                logging.warning("Ride stream queue is full; dropping event %s", event.get("trip_id"))


class RideRequestMQTTBridge:
    def __init__(self, hub: RideRequestHub):
        self.hub = hub
        self.host = os.getenv("MQTT_HOST", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.topic = os.getenv("MQTT_TOPIC", "rides/requests")
        self.enabled = os.getenv("MQTT_ENABLED", "true").lower() not in {"0", "false", "no"}
        self._client = None
        self._started = False
        self._lock = threading.Lock()

    def start(self):
        if not self.enabled or mqtt is None or self._started:
            if mqtt is None and self.enabled:
                logging.warning("paho-mqtt is not installed; ride broadcasts will use the local fallback only")
            return

        with self._lock:
            if self._started:
                return

            try:
                client = mqtt.Client(client_id="bodaboda-backend")
                client.on_connect = self._on_connect
                client.on_disconnect = self._on_disconnect
                client.on_message = self._on_message
                client.connect_async(self.host, self.port, keepalive=60)
                client.loop_start()
                self._client = client
                self._started = True
                logging.info("MQTT bridge started for %s:%s topic %s", self.host, self.port, self.topic)
            except Exception as exc:  # pragma: no cover - connection issues depend on environment
                logging.warning("MQTT bridge could not start: %s", exc)
                self._client = None
                self._started = False

    def stop(self):
        with self._lock:
            client = self._client
            self._client = None
            self._started = False

        if client is not None:
            try:
                client.loop_stop()
                client.disconnect()
            except Exception:
                pass

    def publish_ride_request(self, event: dict) -> bool:
        client = self._client
        if client is None:
            return False

        try:
            info = client.publish(self.topic, json.dumps(event), qos=0, retain=False)
            rc = getattr(info, "rc", 0)
            if rc not in (0, None):
                logging.warning("MQTT publish returned rc=%s for trip %s", rc, event.get("trip_id"))
                return False
            return True
        except Exception as exc:
            logging.warning("MQTT publish failed for trip %s: %s", event.get("trip_id"), exc)
            return False

    def _on_connect(self, client, userdata, flags, rc, properties=None):  # pragma: no cover - callback
        if rc == 0:
            try:
                client.subscribe(self.topic)
                logging.info("MQTT subscribed to %s", self.topic)
            except Exception as exc:
                logging.warning("MQTT subscribe failed: %s", exc)
        else:
            logging.warning("MQTT connect returned rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc, properties=None):  # pragma: no cover - callback
        if rc != 0:
            logging.warning("MQTT disconnected unexpectedly: rc=%s", rc)

    def _on_message(self, client, userdata, msg):  # pragma: no cover - callback
        try:
            event = json.loads(msg.payload.decode("utf-8"))
        except Exception as exc:
            logging.warning("Could not decode MQTT payload: %s", exc)
            return

        self.hub.publish(event)


ride_request_hub = RideRequestHub()
ride_request_mqtt = RideRequestMQTTBridge(ride_request_hub)
