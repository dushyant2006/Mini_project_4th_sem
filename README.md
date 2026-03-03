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
hours manually correlating logs, metrics, traces, and deployment events to identify root causes.

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