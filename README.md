# ⚡ Project 71 — Autonomous Incident Response & Root-Cause Intelligence Platform

![CI](https://github.com/dushyant2006/Mini_project_4th_sem/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/dushyant2006/Mini_project_4th_sem/actions/workflows/cd.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Kafka](https://img.shields.io/badge/Apache_Kafka-7.5-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![ML](https://img.shields.io/badge/ML-LSTM+IsolationForest+Prophet-orange)
![AI](https://img.shields.io/badge/AI-Groq_Llama3-purple)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Tests](https://img.shields.io/badge/Tests-40%20Passing-brightgreen)

> An enterprise-grade AIOps platform that autonomously detects anomalies, performs root cause analysis, and generates AI-written incident reports for cloud microservices — acting as an AI Site Reliability Engineer.

---

## 📌 Problem Statement

Modern cloud systems are composed of microservices, distributed databases, CI/CD pipelines, and third-party APIs. When failures occur, engineers spend hours manually correlating logs, metrics, traces, and deployment events to identify root causes.

### Pain Points
| Problem | Impact |
|---|---|
| Alert fatigue | Too many alerts with no root cause clarity |
| Manual investigation | Hours wasted per incident |
| Poor correlation | Logs, metrics, and traces not connected |
| Repeated incidents | No learning from past failures |

> **There is no reasoning-driven, self-learning incident intelligence system.**

---

## 💡 Solution

An end-to-end AIOps platform that acts as an **AI Site Reliability Engineer:**
```
Cloud Microservices (7 services)
    → Kafka Telemetry Ingestion (logs + metrics + traces | every 5s)
    → ML Anomaly Detection (Isolation Forest + LSTM + Prophet | <60s)
    → RCA Agent (NetworkX graph + RAG over incident history)
    → GenAI Incident Report (Groq Llama3 | auto-saved to knowledge base)
    → FastAPI REST API (12 endpoints) + React Dashboard (localhost:3000)
```

---

## ✅ Key Features

### i. Telemetry Ingestion Layer
- Real-time ingestion of **4 telemetry streams** (logs, metrics, traces, severity)
- Apache Kafka with **5-second** batching across **7 microservices**
- OpenTelemetry-compatible data models

### ii. 3-Model Anomaly Detection Ensemble
| Model | Detects | Best At |
|---|---|---|
| **Isolation Forest** | Sudden metric spikes | CPU > 85%, latency > 1000ms |
| **LSTM Autoencoder** | Time-series pattern breaks | Gradual degradation |
| **Prophet** | Seasonality violations | High CPU at 3am when it's always low |

All 3 models run simultaneously — any detection triggers the RCA agent.

### iii. Graph-Based RCA Agent
- **NetworkX** dependency graph across 7 microservices
- Calculates **blast radius** — directly and indirectly affected services
- **RAG retrieval** over auto-growing incident knowledge base
- Generates ranked hypotheses and recommended fixes

### iv. Auto-Learning Knowledge Base
- Every resolved incident is **automatically saved** to `data/incident_knowledge_base.json`
- Future similar incidents benefit from past resolutions
- System gets smarter with every incident handled

### v. GenAI Incident Reports
- **Groq Llama 3** generates professional SRE-quality incident reports
- Covers: summary, timeline, root cause, affected services, fixes, lessons learned
- Saved as both `.txt` (human-readable) and `.json` (machine-readable)

### vi. Full-Stack Dashboard
- **React.js** dashboard with 4 pages: Overview, Incidents, Anomalies, Services
- Live anomaly feed — auto-refreshes every 10 seconds
- Clickable service dependency graph with blast radius analysis
- Incident detail view with recommended fixes

### vii. REST API
- **FastAPI** backend with 12 endpoints
- Full Swagger/OpenAPI documentation
- Pydantic data validation

### viii. CI/CD Pipeline
- **GitHub Actions** CI — runs 40 tests on every push
- **GitHub Actions** CD — builds and pushes Docker images to GHCR

---

## 📊 Project Status
```
✅ Phase 1  — Environment Setup
✅ Phase 2  — Project Structure
✅ Phase 3  — Telemetry Pipeline (Kafka)
✅ Phase 4  — ML Anomaly Detection (Isolation Forest + LSTM)
✅ Phase 5  — RCA Agent (Graph + RAG)
✅ Phase 6  — GenAI Reports (Groq Llama 3)
✅ Phase 7  — FastAPI Backend (12 endpoints)
✅ Phase 8  — Documentation
✅ Phase 9A — Prophet ML Model
✅ Phase 9B — Auto-Learning RAG Knowledge Base
✅ Phase 9C — React Dashboard
✅ Phase 10 — Unit & Integration Testing (40/40)
✅ Phase 11 — CI/CD Pipeline (GitHub Actions)
```

---

## 🏗️ System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULATED MICROSERVICES                       │
│  api-gateway → auth-service     → user-service                  │
│  api-gateway → order-service    → payment-service ← ROOT CAUSE  │
│                                 → inventory-service              │
│               payment-service   → notification-service           │
└────────────────────────────┬────────────────────────────────────┘
                             │ 4 streams: logs + metrics + traces
                             │ every 5 seconds
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              TELEMETRY INGESTION LAYER (Apache Kafka)            │
│   Topics: telemetry.logs | telemetry.metrics | telemetry.traces  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               ML ANOMALY DETECTION ENGINE                        │
│                                                                  │
│   ┌──────────────────┐ ┌──────────────────┐ ┌────────────────┐  │
│   │ Isolation Forest │ │ LSTM Autoencoder  │ │    Prophet     │  │
│   │ (spike detect)   │ │ (pattern detect)  │ │ (seasonality)  │  │
│   └──────────────────┘ └──────────────────┘ └────────────────┘  │
│                         anomalies.detected                       │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RCA AGENT                                     │
│   Step 1: Group anomalies by service                             │
│   Step 2: Graph analysis → find root cause                       │
│   Step 3: Calculate blast radius                                 │
│   Step 4: RAG search over incident knowledge base               │
│   Step 5: Generate hypotheses + recommended fixes               │
│                         rca.results                              │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           GENAI REPORT GENERATOR (Groq Llama 3)                  │
│   Output: /reports/*.txt + /reports/*_raw.json                   │
│   Learns: auto-saved to incident knowledge base                  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│        FASTAPI REST API          REACT DASHBOARD                 │
│   http://localhost:8000/docs     http://localhost:3000           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Ingestion** | Apache Kafka, OpenTelemetry | Real-time telemetry streaming |
| **ML Detection** | Isolation Forest, LSTM, Prophet | 3-model anomaly detection |
| **RCA Agent** | NetworkX, RAG | Graph-based root cause reasoning |
| **GenAI** | Groq API (Llama 3) | AI incident report generation |
| **API** | FastAPI, Pydantic | 12 REST endpoints |
| **Dashboard** | React.js, Recharts | Live visualization |
| **Storage** | PostgreSQL, Redis | Data persistence |
| **Infra** | Docker Compose | Local infrastructure |
| **CI/CD** | GitHub Actions | Automated testing & Docker build |
| **Registry** | GitHub Container Registry | Docker image storage |
| **Language** | Python 3.11, Node.js 20 | Core implementation |

---

## 📁 Project Structure
```
project71/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI — runs 40 tests on every push
│       └── cd.yml              # CD — builds Docker images to GHCR
│
├── ingestion/                  # Kafka producers, consumers, data models
│   ├── consumer.py
│   ├── producer.py
│   └── models.py
│
├── detection/                  # ML anomaly detection
│   ├── isolation_forest.py     # Isolation Forest detector
│   ├── lstm_autoencoder.py     # LSTM Autoencoder detector
│   ├── prophet_baseline.py     # Prophet seasonality detector
│   ├── data_buffer.py          # Sliding window metric buffer
│   ├── anomaly_publisher.py    # Kafka publisher
│   └── detection_engine.py     # Main detection loop
│
├── rca/                        # Root cause analysis
│   ├── graph/
│   │   └── graph_builder.py    # NetworkX service dependency graph
│   ├── agent/
│   │   └── rca_agent.py        # RCA reasoning engine
│   ├── rag_retriever.py        # RAG over incident knowledge base
│   ├── incident_store.py       # Persistent JSON incident storage
│   └── rca_engine.py           # Main RCA loop
│
├── reporting/                  # GenAI incident reports
│   ├── genai_analyst.py        # Groq API client
│   ├── report_formatter.py     # Report formatting + saving
│   └── report_engine.py        # Main reporting loop
│
├── api/                        # FastAPI REST backend
│   ├── main.py                 # App entry point
│   ├── schemas.py              # Pydantic models
│   └── routes/
│       ├── incidents.py        # /incidents endpoints
│       ├── anomalies.py        # /anomalies endpoints
│       └── services.py         # /services endpoints
│
├── dashboard/                  # React.js frontend
│   ├── src/
│   │   ├── App.js
│   │   ├── api.js              # API helper
│   │   └── pages/
│   │       ├── OverviewPage.js
│   │       ├── IncidentsPage.js
│   │       ├── AnomaliesPage.js
│   │       └── ServicesPage.js
│   ├── Dockerfile              # Dashboard Docker image
│   └── nginx.conf              # Nginx with API proxy
│
├── data/                       # Telemetry simulator
│   ├── simulate_telemetry.py   # 7-service simulator with anomaly injection
│   └── incident_knowledge_base.json  # Auto-growing RAG knowledge base
│
├── tests/                      # 40 unit + integration tests
│   ├── test_models.py
│   ├── test_detection.py
│   ├── test_rca.py
│   ├── test_api.py
│   └── test_pipeline.py
│
├── docs/
│   ├── architecture.md
│   └── api_guide.md
│
├── reports/                    # Auto-generated incident reports
├── docker-compose.yml          # Local infrastructure
├── docker-compose.prod.yml     # Production deployment
├── Dockerfile.backend          # Backend Docker image
├── requirements.txt            # Python dependencies
├── start.bat                   # One-click Windows startup
└── .env.example                # Environment template
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.11+
- Docker Desktop
- Node.js 20+
- Git

### Step 1 — Clone Repository
```bash
git clone https://github.com/dushyant2006/Mini_project_4th_sem.git
cd Mini_project_4th_sem
```

### Step 2 — Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### Step 3 — Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment
```bash
cp .env.example .env
# Open .env and add your GROQ_API_KEY
# Get free key at: https://console.groq.com
```

### Step 5 — Install Dashboard Dependencies
```bash
cd dashboard
npm install
cd ..
```

---

## 🚀 How to Run

### Option A — One Click (Windows)
```bash
.\start.bat
```

### Option B — Manual (6 Terminals)

**Start Infrastructure:**
```bash
docker-compose up -d
# Wait 45 seconds, then verify:
docker logs kafka 2>&1 | findstr "started"
```

**Terminal 1 — Telemetry Simulator:**
```bash
python data/simulate_telemetry.py
```

**Terminal 2 — ML Detection Engine:**
```bash
python detection/detection_engine.py
```

**Terminal 3 — RCA Engine:**
```bash
python rca/rca_engine.py
```

**Terminal 4 — Report Engine:**
```bash
python reporting/report_engine.py
```

**Terminal 5 — FastAPI Backend:**
```bash
uvicorn api.main:app --reload --port 8000
```

**Terminal 6 — React Dashboard:**
```bash
cd dashboard && npm start
```

---

## 🎯 Example Usage

### Inject a Payment Service Failure
```bash
python data/simulate_telemetry.py --anomaly payment-service
```

### Watch the Pipeline React (60-90 seconds)
```
Terminal 2 → 🚨 ANOMALY DETECTED (Isolation Forest + LSTM + Prophet)
Terminal 3 → 🔍 RCA complete | 🧠 LEARNED: New incident saved to KB
Terminal 4 → ✅ Incident report generated → /reports/INC-XXXXXXXX.txt
```

### Access Points
| Interface | URL |
|---|---|
| **React Dashboard** | http://localhost:3000 |
| **API Swagger Docs** | http://localhost:8000/docs |
| **Kafka UI** | http://localhost:8080 |
| **Incident Reports** | `/reports/` folder |

---

## 📡 API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/incidents/` | List all incidents |
| GET | `/incidents/{id}` | Get incident detail + report |
| GET | `/incidents/recent` | Last 10 incidents |
| GET | `/incidents/stats` | Severity breakdown |
| GET | `/incidents/knowledge-base` | RAG learning statistics |
| GET | `/anomalies/live` | Live anomaly feed (last 20) |
| GET | `/anomalies/summary` | Anomaly type statistics |
| GET | `/services/graph` | Full dependency graph |
| GET | `/services/list` | All services + metadata |
| GET | `/services/{name}/blast-radius` | Failure impact analysis |
| GET | `/services/{name}/dependencies` | Upstream/downstream chain |
| GET | `/health` | System health check |

---

## 🧪 Running Tests
```bash
pytest tests/ -v
# Expected: 40 passed
```

Test coverage:
- `test_models.py` — Telemetry data models
- `test_detection.py` — MetricBuffer + Isolation Forest
- `test_rca.py` — Service graph + RAG retriever
- `test_api.py` — All 12 FastAPI endpoints

---

## 🔄 CI/CD Pipeline

| Pipeline | Trigger | Jobs |
|---|---|---|
| **CI** | Every push to main/feature | Backend lint + 40 tests |
| **CD** | Push to main | Build + push Docker images to GHCR |

Docker images published to:
```
ghcr.io/dushyant2006/mini_project_4th_sem/backend:latest
ghcr.io/dushyant2006/mini_project_4th_sem/dashboard:latest
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address | Yes |
| `GROQ_API_KEY` | Free at console.groq.com | Yes |
| `POSTGRES_HOST` | PostgreSQL host | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `REDIS_HOST` | Redis host | Yes |
| `LOG_LEVEL` | Logging level (INFO/DEBUG) | No |

---

## 🔮 Future Improvements

- **Vector DB RAG** — Replace keyword search with ChromaDB/FAISS embeddings
- **Slack/PagerDuty Integration** — Auto-alert on SEV-1 incidents
- **Multi-cluster Support** — Monitor multiple Kubernetes clusters
- **Prometheus Integration** — Real metrics instead of simulated
- **Fine-tuned LLM** — Train on domain-specific incident data
- **Incident Playbooks** — Auto-execute remediation scripts

---

## 🤝 Contribution Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit with clear messages: `git commit -m "feat: Add your feature"`
4. Push and open a Pull Request to `main`
5. Ensure all 40 tests pass before submitting PR

---

## 👤 Author

**Dushyant**
- Domain: Cloud Computing, AIOps, ML Systems
- Project: Autonomous Incident Response & Root-Cause Intelligence Platform

---

## 📄 License

MIT License — Free to use for educational purposes.

---

## 🙏 Acknowledgements

- Apache Kafka for real-time event streaming
- Groq for free Llama 3 API access
- FastAPI for the modern Python REST framework
- scikit-learn + PyTorch for ML models
- NetworkX for graph-based dependency analysis
- Facebook Prophet for time-series forecasting
- React.js for the frontend dashboard
