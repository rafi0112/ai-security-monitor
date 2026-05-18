# 🛡️ AI Security Monitor

> Real-time AI-powered security monitoring system — 100% free & open-source, runs fully locally.

![Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Stack](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Stack](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![Stack](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

## ✨ Features

- 🔐 **Login page** with real-time AI analysis of every attempt
- 🤖 **Two-layer AI detection**: rule-based (regex) + IsolationForest ML
- 🚨 **Auto-blocking** of malicious IPs (SQLi, XSS, brute-force)
- 📊 **Live dashboard** with charts, alerts, and stats (8s auto-refresh)
- 🔬 **Attack simulator** — brute force, SQLi, XSS, DDoS, mixed scenarios
- 🐳 **Fully dockerized** with Nginx reverse proxy
- ⚙️ **CI/CD** via GitHub Actions

## 🚀 Quick Start

### Option A — Local dev (no Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Option B — Docker Compose

```bash
docker compose up --build
```

Open http://localhost

## 🧪 Test Credentials

| Username | Password | Result |
|---|---|---|
| `alice` | `alice_pass` | ✅ Success |
| `admin` | `admin123` | ✅ Success |
| `admin' OR '1'='1--` | anything | 🚨 SQLi CRITICAL |
| Any user | wrong × 10 | 🔨 Brute Force CRITICAL |

## 🔬 Simulate Attacks

**In dashboard:** Use the Attack Simulator panel buttons.

**CLI simulator (real HTTP requests):**
```bash
python scripts/simulate_attacks.py --mode all
python scripts/simulate_attacks.py --mode brute --attempts 25
python scripts/simulate_attacks.py --mode sqli
python scripts/simulate_attacks.py --mode ddos --attempts 80
```

## 📁 Project Structure

```
ai-security-monitor/
├── backend/              # FastAPI + ML
│   ├── app/
│   │   ├── api/          # auth, logs, alerts, stats, simulate
│   │   ├── core/         # config, database
│   │   ├── ml/           # IsolationForest detector
│   │   └── services/     # log monitor background service
│   └── requirements.txt
├── frontend/             # React + Tailwind + Recharts
│   └── src/
│       ├── pages/        # LoginPage, DashboardPage
│       ├── components/   # StatCard, Charts, AlertsPanel, etc.
│       ├── hooks/        # usePolling
│       └── services/     # api.js (axios)
├── nginx/                # Reverse proxy config
├── scripts/              # Attack simulator CLI
└── docker-compose.yml
```

## 🏗️ Architecture

```
Browser → Nginx (rate-limit) → FastAPI → ML Detector → SQLite
                ↓
           Nginx Logs → Log Monitor → ML Detector
```

**Detection layers:**
1. Rule-based: regex patterns for SQLi, XSS, command injection, path traversal
2. ML: IsolationForest on 8-dimensional feature vector (unsupervised, no labels needed)

## 📡 API Docs

FastAPI auto-docs: http://localhost:8000/api/docs

## 🛣️ Roadmap

- **Phase 1** ✅ — Local MVP (this repo)
- **Phase 2** — Real Nginx logs, Random Forest, WebSockets, PostgreSQL
- **Phase 3** — Kubernetes, Kafka, Elasticsearch, MLflow, Grafana
