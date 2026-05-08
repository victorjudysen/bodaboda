# BodaConnect

A minimal, functional ride-hailing web app with infrastructure monitoring.

[![CI](https://github.com/victorjudysen/bodaboda/actions/workflows/ci.yml/badge.svg)](https://github.com/victorjudysen/bodaboda/actions/workflows/ci.yml)
[![CD](https://github.com/victorjudysen/bodaboda/actions/workflows/cd.yml/badge.svg)](https://github.com/victorjudysen/bodaboda/actions/workflows/cd.yml)

## Project Structure

```
bodaboda/
├── frontend/
│   ├── index.html
│   ├── request.html
│   ├── dashboard.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── requirements.txt
│   └── Dockerfile
├── monitoring/
│   ├── docker-compose.yml
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── provisioning/
│           ├── datasources/
│           │   └── prometheus.yml
│           └── dashboards/
│               ├── dashboards.yml
│               └── system-metrics.json
└── README.md
```

## 🚀 How to Run

1. **Ensure the backend is running at `http://localhost:5000`**
   - Start the backend server as per backend instructions.
2. **Open the frontend:**
   - Open `index.html` in your browser directly, or
   - For best results, use a local server (e.g. VS Code Live Server, or `python -m http.server` in this folder).
3. **Navigate the app:**
   - Homepage: Welcome and navigation
   - Request Ride: Fill the form and submit
   - Rider Dashboard: View rider name and trips

## 📝 Features

- **No frameworks:** Pure HTML, CSS, and vanilla JS
- **Responsive, clean UI**
- **API integration:**
  - POST `/request-ride`
  - GET `/rider-dashboard`
- **Error handling and loading states**

## 🛠️ Development

- All JS in `js/app.js`
- All CSS in `css/styles.css`
- Edit HTML files for page content

## 🤝 Contributing

- Make changes in a feature branch, open a PR for review.
- Keep UI minimal and functional.
- No frameworks or unnecessary libraries.

---

## Monitoring (Prometheus + Grafana)

The `monitoring/` directory contains a Docker Compose stack that collects and visualises CPU, RAM, and Storage metrics from the host machine.

### Architecture

| Container | Image | Purpose |
|---|---|---|
| `node-exporter` | `prom/node-exporter` | Exposes host OS metrics (CPU, memory, disk, network) on port 9100 |
| `prometheus` | `prom/prometheus` | Scrapes node-exporter every 15 s; retains 15 days of data |
| `grafana` | `grafana/grafana` | Visualises metrics; auto-provisions datasource and dashboard |

### How to Run

**Prerequisites:** Docker and Docker Compose must be installed.

```bash
cd monitoring
docker compose up -d
```

### Accessing the UIs

| Service | URL | Credentials |
|---|---|---|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| Node Exporter (raw metrics) | http://localhost:9100/metrics | — |

On first login, Grafana will prompt you to change the admin password.

### Pre-provisioned Dashboard

The **System Metrics** dashboard is automatically loaded under the **Monitoring** folder in Grafana. It provides:

- **CPU Usage %** — rolling 5-minute average across all cores
- **RAM Usage %** — used vs available memory
- **Disk Usage %** — used vs available space on the root filesystem
- Time-series graphs for all three metrics with 1-hour default window, refreshing every 10 seconds

### Key Prometheus Queries

| Metric | PromQL |
|---|---|
| CPU % | `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` |
| RAM used % | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` |
| Disk used % | `(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100` |

### Stopping the Stack

```bash
cd monitoring
docker compose down
```

To also remove persisted data volumes:

```bash
docker compose down -v
```

### Notes on Windows (Docker Desktop)

Node Exporter mounts `/proc`, `/sys`, and `/` from the host. On Windows with Docker Desktop, these paths resolve to the WSL2 Linux VM, so the metrics reflect that VM rather than the bare-metal Windows host. For native Windows host metrics, the [windows_exporter](https://github.com/prometheus-community/windows_exporter) can be installed directly on the Windows machine and targeted by Prometheus as an additional scrape job.

---

For any issues, contact the team lead or open an issue in the repository.
