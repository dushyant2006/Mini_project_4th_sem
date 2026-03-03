# 🚀 Project 71 — Autonomous Incident Response & Root-Cause Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Kafka](https://img.shields.io/badge/Apache_Kafka-7.5-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![ML](https://img.shields.io/badge/ML-LSTM_+_IsolationForest-orange)
![AI](https://img.shields.io/badge/AI-Groq_Llama3-purple)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## 📌 Problem Statement

Modern cloud systems are composed of microservices, distributed databases,
CI/CD pipelines, and third-party APIs. When failures occur, engineers spend
**hours manually correlating logs, metrics, traces, and deployment events**
to identify root causes.

### Current Pain Points:
- ⚠️ **Alert fatigue** — too many alerts, no root cause clarity
- ⏱️ **Hours wasted** on manual incident investigation
- 🔗 **Poor correlation** across logs, metrics, and deployments
- 🔁 **Repeated incidents** due to lack of learning from history

> **There is no reasoning-driven, self-learning incident intelligence system.**

---

## 💡 Solution

An **end-to-end AIOps platform** that acts as an **AI Site Reliability Engineer**:
```
Cloud Systems → Telemetry → ML Detection → AI Agent → GenAI Report → Dashboard
```

- 📡 **Ingests** real-time telemetry (logs, metrics, traces) via Kafka
- 🤖 **Detects** anomalies automatically using LSTM + Isolation Forest
- 🧠 **Reasons** about root causes using graph-based dependency analysis
- 📝 **Generates** human-readable incident reports using Groq (Llama 3)
- 🌐 **Exposes** everything via a REST API with Swagger documentation

---

## 🎯 Key Objectives

| Objective | How We Achieve It |
|---|---|
| Reduce MTTR | Automated detection in <60 seconds |
| Automate RCA | Graph-based AI agent + RAG |
| Learn from history | RAG over past incidents |
| Improve reliability | Continuous ML model adaptation |

---

## 📊 Project Status
```
✅ Phase 1 — Environment Setup
✅ Phase 2 — Project Structure  
✅ Phase 3 — Telemetry Pipeline (Kafka)
✅ Phase 4 — ML Anomaly Detection
✅ Phase 5 — RCA Agent
✅ Phase 6 — GenAI Incident Reports
✅ Phase 7 — FastAPI Backend
✅ Phase 8 — Documentation


## 🏗️ System Architecture
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULATED MICROSERVICES                      |
│  api-gateway → auth-service → user-service                      │
│  api-gateway → order-service → payment-service ← ROOT CAUSE     │
│                             → inventory-service                 |
│               payment-service → notification-service            |
└────────────────────────────┬────────────────────────────────────┘
                             │ logs + metrics + traces
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TELEMETRY INGESTION (Kafka)                    |
│                                                                 │
│   telemetry.logs   telemetry.metrics   telemetry.traces         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               ML ANOMALY DETECTION ENGINE                       │
│                                                                 │
│   ┌─────────────────────┐   ┌─────────────────────────┐         │
│   │  Isolation Forest   │   │   LSTM Autoencoder       │        │
│   │  (metric spikes)    │   │   (time-series patterns) │        │
│   └─────────────────────┘   └─────────────────────────┘         │
│                    │                    │                       │
│                    └────────┬───────────┘                       │
│                             ▼                                   │
│                   anomalies.detected (Kafka)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RCA AGENT                                    │
│                                                                 │
│   Step 1: Group anomalies by service                            │
│   Step 2: Find root cause (graph analysis)                      │
│   Step 3: Calculate blast radius                                │
│   Step 4: Search past incidents (RAG)                           │
│   Step 5: Generate hypotheses + fixes                           │
│                    │                                            │
│                   rca.results (Kafka)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              GENAI REPORT GENERATOR (Groq Llama 3)              │
│                                                                 │
│   Input:  Structured RCA data                                   │
│   Output: Professional incident report                          │
│   Saved:  /reports/*.txt + /reports/*_raw.json                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI REST API                              │
│                                                                 │
│   GET /incidents          GET /anomalies/live                   │
│   GET /incidents/{id}     GET /services/graph                   │
│   GET /incidents/stats    GET /services/{name}/blast-radius     │
│                                                                 │
│   Swagger UI: http://localhost:8000/docs                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Ingestion** | Apache Kafka, OpenTelemetry | Real-time telemetry streaming |
| **ML Detection** | LSTM Autoencoder, Isolation Forest | Anomaly detection |
| **RCA Agent** | NetworkX, RAG | Root cause reasoning |
| **GenAI** | Groq API (Llama 3) | Incident report generation |
| **API** | FastAPI, Pydantic | REST endpoints |
| **Storage** | PostgreSQL, Redis | Data persistence |
| **Infra** | Docker Compose | Local infrastructure |
| **Language** | Python 3.11 | Core implementation |


## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- Docker Desktop
- Git

### Step 1 — Clone Repository
```bash
git clone https://github.com/YOURUSERNAME/project71.git
cd project71
```

### Step 2 — Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Step 5 — Start Infrastructure
```bash
docker-compose up -d
# Wait 45 seconds for Kafka to initialize
```

### Step 6 — Verify Kafka is Ready
```bash
docker logs kafka | findstr "started"    # Windows
docker logs kafka | grep "started"       # Mac/Linux
```

### Step 7 — Run All Components
Open 4 separate terminals:

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

**Terminal 5 — FastAPI Server:**
```bash
uvicorn api.main:app --reload --port 8000
```

### Step 8 — Test Anomaly Detection
```bash
# In a new terminal — inject payment-service failure
python data/simulate_telemetry.py --anomaly payment-service


### Step 9 — View Results
| Interface | URL |
|---|---|
| **Swagger API Docs** | http://localhost:8000/docs |
| **Kafka UI** | http://localhost:8080 |
| **Incident Reports** | `/reports/` folder |

## 📡 API Reference
Base URL: `http://localhost:8000`

### Incidents
| Method | Endpoint | Description |
|---|---|---|
| GET | `/incidents` | List all incidents |
| GET | `/incidents/{id}` | Get incident by ID |
| GET | `/incidents/recent` | Last 10 incidents |
| GET | `/incidents/stats` | Incident statistics |

### Anomalies
| Method | Endpoint | Description |
|---|---|---|
| GET | `/anomalies/live` | Live anomaly feed |
| GET | `/anomalies/by-service/{name}` | Anomalies by service |
| GET | `/anomalies/summary` | Anomaly statistics |

### Services
| Method | Endpoint | Description |
|---|---|---|
| GET | `/services/graph` | Full dependency graph |
| GET | `/services/list` | All services + metadata |
| GET | `/services/{name}/blast-radius` | Failure impact analysis |
| GET | `/services/{name}/dependencies` | Dependency chain |

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome + endpoint list |
| GET | `/health` | System health check |

> 📖 Full interactive docs available at: http://localhost:8000/docs

---

## 🤖 ML Models

### 1. Isolation Forest
- **Type:** Unsupervised anomaly detection
- **Input:** Last 20 metric readings per service
- **Detects:** Sudden spikes in CPU, latency, error rate, memory
- **Threshold:** Dynamic (hard threshold + statistical outlier)

### 2. LSTM Autoencoder
- **Type:** Deep learning sequence model
- **Input:** Time-series windows of metric values
- **Detects:** Abnormal patterns that don't match historical behavior
- **Training:** Continuous online learning on live data

---

## 📁 Project Structure
```
project71/
├── ingestion/          # Kafka producers, consumers, data models
├── detection/          # ML anomaly detection (Isolation Forest + LSTM)
├── rca/                # Root cause analysis agent + graph builder
├── reporting/          # GenAI incident report generator
├── api/                # FastAPI REST endpoints
├── data/               # Telemetry simulator
├── reports/            # Generated incident reports (auto-created)
├── tests/              # Unit and integration tests
├── docs/               # Additional documentation
├── docker-compose.yml  # Infrastructure setup
├── requirements.txt    # Python dependencies
└── .env                # Configuration (not committed)



## 🔑 Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address | Yes |
| `GROQ_API_KEY` | Free API key from console.groq.com | Yes |
| `POSTGRES_*` | PostgreSQL connection details | Yes |
| `REDIS_HOST` | Redis host | Yes |

---

## 👥 Author

**Your Name**
- Domain: Cloud Computing, AIOps, ML Systems
- Project: Autonomous Incident Response Platform

---

## 📄 License

MIT License — Free to use for educational purposes.

---

## 🙏 Acknowledgements

- Apache Kafka for real-time streaming
- Groq for free Llama 3 API access
- FastAPI for the REST framework
- scikit-learn + PyTorch for ML models