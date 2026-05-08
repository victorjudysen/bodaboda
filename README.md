# BodaConnect

A Bodaboda ride-hailing web app with CI/CD automation and infrastructure monitoring.

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

## Run Locally

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| App | http://localhost |
| Backend API | http://localhost:5000 |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |

## Run Tests

```bash
pip install -r backend/requirements.txt
pytest tests/ -v
```
