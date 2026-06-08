# BodaConnect

A Bodaboda ride-hailing web app with CI/CD automation, infrastructure monitoring, and MQTT-based real-time ride request broadcasting.

[![CI](https://github.com/victorjudysen/bodaboda/actions/workflows/ci.yml/badge.svg)](https://github.com/victorjudysen/bodaboda/actions/workflows/ci.yml)
[![CD](https://github.com/victorjudysen/bodaboda/actions/workflows/cd.yml/badge.svg)](https://github.com/victorjudysen/bodaboda/actions/workflows/cd.yml)

## Stack

| Service | Technology |
|---|---|
| Backend | Python / Flask |
| Frontend | HTML, CSS, Vanilla JS (Nginx) |
| Database | SQLite |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions + Docker Hub |
| Realtime | MQTT + Server-Sent Events |

## Run Locally

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| App | http://localhost |
| Backend API | http://localhost:5001 |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |
| MQTT TCP | `localhost:1883` |
| MQTT WebSocket | `ws://localhost:9001` |

## MQTT Flow

This project implements Assignment 2, Option A:

- Customer ride requests are published to the MQTT topic `rides/requests`
- The backend also subscribes to that topic and forwards matching events to the rider dashboard in real time
- If MQTT is unavailable, the trip still gets saved and the backend logs the publish failure

## Live Demo Steps

1. Start the stack with `docker compose up --build`
2. Log in as a rider in one browser tab
3. Open the rider dashboard and keep it on the `Live Ride Requests` panel
4. Log in as a customer in another tab
5. Submit a new ride request from `request.html`
6. The rider dashboard should show the incoming request without refreshing

## Run Tests

```bash
pip install -r backend/requirements.txt
pytest tests/ -v
```
