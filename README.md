# 🛡️ AI Security Monitor

> AI-powered real-time security monitoring platform with automated DevSecOps pipeline, attack simulation, ML anomaly detection, Docker orchestration, and self-hosted CI/CD deployment.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)

---

# 🚀 DevSecOps CI/CD Pipeline (Highest Priority)

This project includes a fully automated DevSecOps-style CI/CD pipeline using:

- GitHub Actions
- Self-hosted GitHub Runner
- Docker Compose
- Automated security testing
- Automated deployment

---

## 🔄 CI/CD Workflow

```text
Developer Push
       ↓
GitHub Actions Triggered
       ↓
Backend Tests (pytest)
       ↓
Security Simulation Tests
       ↓
Frontend Build Validation
       ↓
Docker Build Validation
       ↓
Self-hosted Runner
       ↓
Automatic Local Deployment
       ↓
Docker Containers Restarted
```

---

## ✅ CI Features

### Automated Backend Testing
- Pytest integration
- Async security detector tests
- Import validation
- Dependency validation

### Automated Frontend Validation
- React build validation
- npm dependency checks
- Production build verification

### Security-Aware CI
The pipeline automatically simulates:

- Brute-force attacks
- SQL injection attempts
- XSS payloads
- High-risk login behavior

Example:
```python
assert result.attack_type == "brute_force"
assert result.should_block is True
```

---

## 🚀 CD Features

### Self-hosted Deployment Runner
GitHub Actions deploys directly to the local machine using:

```yaml
runs-on: self-hosted
```

### Automatic Deployment Flow

```text
git push
    ↓
CI Tests Pass
    ↓
Docker Containers Rebuilt
    ↓
Containers Restart Automatically
    ↓
Application Updated
```

---

## ⚙️ GitHub Actions Workflow

Location:

```text
.github/workflows/ci.yml
```

Pipeline stages:

| Stage | Purpose |
|---|---|
| test-backend | Backend validation |
| test-frontend | Frontend validation |
| docker-build | Docker verification |
| deploy-local | Self-hosted deployment |

---

## 🖥️ Self-hosted Runner

This project uses a self-hosted GitHub Actions runner for real CD deployment.

Runner status:
```text
Listening for Jobs
```

Deployment machine:
```text
Windows Local Machine
```

---

# 🐳 Docker Implementation

The platform is fully containerized using Docker Compose.

---

## Docker Services

| Container | Purpose |
|---|---|
| frontend | React dashboard |
| backend | FastAPI API + ML engine |
| nginx | Reverse proxy |
| sqlite | Lightweight local database |

---

## Docker Workflow

```text
Frontend Container
        ↓
Nginx Reverse Proxy
        ↓
Backend API Container
        ↓
AI Security Detector
        ↓
SQLite Database
```

---

## Start Containers

```bash
docker compose up --build
```

---

## Stop Containers

```bash
docker compose down
```

---

## Automatic Deployment Script

Location:

```text
scripts/deploy.bat
```

Responsibilities:
- Pull latest code
- Stop containers
- Rebuild containers
- Restart containers

---

# 🌐 Application URLs

---

## 🔐 Login Page

```text
http://localhost/login
```

Used for:
- login testing
- brute-force simulation
- security event generation

---

## 📊 Dashboard

```text
http://localhost/dashboard
```

Features:
- live alerts
- attack analytics
- charts
- suspicious IP monitoring
- attack simulation controls

---

## 📡 Swagger API Docs

```text
http://localhost:8000/docs
```

Interactive FastAPI API documentation.

---

# 📡 Main API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/login` | POST | User authentication |
| `/api/alerts` | GET | Security alerts |
| `/api/stats` | GET | Dashboard statistics |
| `/api/logs` | GET | Security logs |
| `/api/simulate/brute-force` | POST | Simulate brute-force |
| `/api/simulate/sqli` | POST | Simulate SQL injection |
| `/api/simulate/xss` | POST | Simulate XSS attack |
| `/api/simulate/ddos` | POST | Simulate DDoS traffic |

---

# ✨ Features

- 🔐 Real-time login monitoring
- 🤖 Hybrid AI detection engine
- 🚨 Brute-force detection
- 💉 SQL injection detection
- 🧠 IsolationForest anomaly detection
- 📊 Live security dashboard
- 🐳 Fully Dockerized
- ⚙️ Automated CI/CD
- 🛡️ Self-hosted DevSecOps pipeline
- 🔬 Attack simulator
- 📈 Real-time statistics
- 📜 Log monitoring system

---

# 🧠 AI/ML Detection Engine

Two-layer detection architecture:

---

## Layer 1 — Rule-based Detection

Detects:
- SQL injection
- XSS
- Command injection
- Path traversal
- Brute-force attacks
- Credential stuffing

Uses:
- regex pattern analysis
- sliding window rate tracking

---

## Layer 2 — ML Anomaly Detection

Algorithm:
```text
IsolationForest
```

Why IsolationForest?

- Unsupervised learning
- No labeled data required
- Lightweight
- CPU-friendly
- Ideal for anomaly detection

---

## ML Feature Vector

```text
[
  hour_of_day,
  failures_last_60s,
  unique_ips_last_5min,
  is_known_bad_user,
  has_sqli_pattern,
  has_xss_pattern,
  request_rate_last_60s,
  payload_length
]
```

---

# 🔬 Attack Simulation

The project supports realistic cyberattack simulation.

---

## Supported Attack Types

| Attack | Supported |
|---|---|
| Brute Force | ✅ |
| SQL Injection | ✅ |
| XSS | ✅ |
| DDoS-like traffic | ✅ |
| Mixed attacks | ✅ |

---

## CLI Simulation

```bash
python scripts/simulate_attacks.py --mode all

python scripts/simulate_attacks.py --mode brute --attempts 25

python scripts/simulate_attacks.py --mode sqli

python scripts/simulate_attacks.py --mode ddos --attempts 80
```

---

# 🧪 Security Testing

Security tests run automatically inside CI pipeline.

---

## Example Security Test

```python
@pytest.mark.asyncio
async def test_bruteforce_detection():

    detector = SecurityDetector()

    for i in range(12):

        event = LoginEvent(
            ip_address="192.168.1.100",
            username="admin",
            success=False,
        )

        result = await detector.analyze_login(event)

    assert result.attack_type == "brute_force"
```

---

# 📁 Project Structure

```text
ai-security-monitor/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   │
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── ml/
│   │   ├── services/
│   │   └── utils/
│   │
│   ├── tests/
│   │   ├── test_basic.py
│   │   ├── test_security_detector.py
│   │   ├── test_sqli.py
│   │   └── test_simulation.py
│   │
│   └── logs/
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── hooks/
│       └── services/
│
├── nginx/
│   └── nginx.conf
│
├── scripts/
│   ├── deploy.bat
│   └── simulate_attacks.py
│
└── docker-compose.yml
```

---

# 🏗️ Architecture

```text
Browser
   ↓
Nginx Reverse Proxy
   ↓
FastAPI Backend
   ↓
AI Security Detector
   ↓
SQLite Database

Nginx Logs
   ↓
Log Monitor Service
   ↓
AI Detection Engine
   ↓
Dashboard Alerts
```

---

# 🛣️ Roadmap

## Phase 1 — Local DevSecOps Platform ✅
- FastAPI backend
- React dashboard
- Docker containers
- Security detector
- CI/CD pipeline
- Self-hosted deployment

---

## Phase 2 — Advanced Monitoring
- Real Nginx log ingestion
- WebSockets
- PostgreSQL
- Advanced analytics
- RandomForest/XGBoost

---

## Phase 3 — Cloud Native Security
- Kubernetes
- Helm
- Grafana
- Prometheus
- Kafka
- Elasticsearch

---

## Phase 4 — Enterprise AI Security
- MLflow
- Explainable AI
- Distributed detection
- Multi-node deployment
- Cloud-native scaling

---

# 🧑‍💻 Tech Stack

| Category | Technology |
|---|---|
| Frontend | React + Tailwind |
| Backend | FastAPI |
| AI/ML | scikit-learn |
| Database | SQLite |
| DevOps | Docker + GitHub Actions |
| Reverse Proxy | Nginx |
| Testing | Pytest |
| CI/CD | GitHub Actions + Self-hosted Runner |

---

# 📜 License

MIT License

---

# ⭐ Project Goal

This project was built to demonstrate:

- DevSecOps
- AI Security Monitoring
- ML-based anomaly detection
- Automated CI/CD
- Docker orchestration
- Security-aware testing
- Real-world infrastructure workflows