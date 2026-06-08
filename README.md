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

## Third-Party Deployment

Assignment 3 extends the pipeline with Docker Hub based release and deployment flow:

- The backend and frontend images are built and pushed to Docker Hub from the release workflow
- Images are tagged as `latest`, a release tag such as `v1.0` or `v2.0`, and the commit SHA
- The deployment workflow pulls the published images from Docker Hub and starts the app from `docker-compose.deploy.yml`
- MQTT remains active in the deployed stack, so ride requests still broadcast in real time
- You can trigger a new release tag from GitHub Actions with `workflow_dispatch` and a tag like `v2.0`

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
