<div align="center">
  <img src=".github/banner.svg" alt="Divine Agent System Banner" width="100%" />
</div>

# Divine Agent System

> **Supreme Agentic Orchestrator (SAO)**
> A real, runnable multi-agent platform — LangGraph state machines, MCP tool calls,
> Qiskit-Aer quantum simulation, and a self-reflection layer — packaged with
> branding intact but every claim grounded.

<p align="center">
  <strong>v2.0.0 &nbsp;·&nbsp; released 2026-05-14 &nbsp;·&nbsp; Python 3.10 – 3.13</strong>
</p>

<p align="center">
  <a href="#getting-started">Getting Started</a>
  ·
  <a href="ARCHITECTURE.md">Architecture</a>
  ·
  <a href="CHANGELOG.md">Changelog</a>
  ·
  <a href="https://www.youtube.com/@KaliVibe-Coding">YouTube Build Series</a>
</p>

---

## // THE VIBE

This project was architected and built live during a "One-Song Build" session.

- **Soundtrack:** `Quantum Dreams` by `Neural Synthesis`
- **Vibe:** Cinematic AI orchestration — divine *branding*, honest *engineering*.

The "divine / quantum / consciousness" vocabulary is preserved as **branding**.
Every feature that ships in this repository is grounded in real, current tech:

| Brand term            | What it actually is                                              |
|-----------------------|------------------------------------------------------------------|
| "Divine consciousness" | Planner / critic self-reflection loop (LangGraph node)          |
| "Quantum sampling"    | Real `qiskit_aer.AerSimulator` superposition sampling           |
| "Transcendent stack"  | LangGraph 0.4 + MCP 1.2 + FastAPI 0.115 + Redis 7.4 + Postgres 16 |
| "Multi-cloud mastery" | Real `aws` / `az` / `gcloud` / `kubectl` invocations            |

---

## // THE BLUEPRINT

SAO is an opinionated multi-agent framework. It gives you:

- A **department / agent hierarchy** discovered automatically from disk
- A **LangGraph 0.4** orchestration graph with plan → execute → reflect → respond
- An **MCP 1.2** tool-call protocol, plus JSON-RPC and REST wrappers
- An optional **Qiskit-Aer 1.3** quantum-sampling layer for stochastic decisions
- A **FastAPI 0.115** HTTP surface (`/api/v1/...`) with OpenTelemetry tracing
- A **deploy driver** that talks to Docker, Compose, Kubernetes, AWS, Azure, GCP

---

## // THE STACK (May 2026)

| Layer          | Component                              | Version           |
|----------------|----------------------------------------|-------------------|
| Orchestration  | LangGraph                              | `>=0.4.0`         |
| LLM core       | LangChain Core                         | `>=0.3.0`         |
| Tool protocol  | Model Context Protocol (MCP)           | `>=1.2.0`         |
| HTTP API       | FastAPI / Starlette / uvicorn[standard]| `0.115` / `0.41` / `0.32` |
| Validation     | Pydantic                               | `>=2.10, <3.0`    |
| Memory         | Pinecone-client / Chroma / Supabase    | `5.x` / `0.5.x` / `2.10+` |
| Postgres       | psycopg                                | `>=3.2` (psycopg3) |
| Bus            | Redis 7.4 Streams                      | `redis>=5.2.0`    |
| Quantum sim    | Qiskit + qiskit-aer                    | `1.3.x` (Aer 0.15+) |
| Post-quantum   | NIST FIPS-203 (ML-KEM-768) / FIPS-204 (ML-DSA-65) | aware |
| Observability  | OpenTelemetry + Prometheus + Grafana   | OTLP 1.x          |
| LLM defaults   | OpenAI `gpt-5` / Anthropic `claude-sonnet-4.5` | May 2026 |
| Runtime        | Python                                 | `3.12-slim-bookworm` (3.10+ supported) |
| Container      | Docker BuildKit + Compose Spec v2      | -                 |

> Notes: `qiskit-ibmq-provider` was retired in 2024 — use `qiskit-ibm-runtime`
> instead. `qiskit.execute` / top-level `Aer` were removed in Qiskit 1.x —
> use `qiskit.transpile` + `qiskit_aer.AerSimulator`.

---

## // SYSTEM ARCHITECTURE

```
SupremeAgenticOrchestrator (facade)
  └── DivineOrchestrator (orchestrator.main)
        ├── Agent discovery     →  walks agents/<dept>/<agent>/agent.py
        ├── Department registry →  11 departments (1 fully implemented)
        ├── LangGraph runtime   →  plan / execute / reflect / respond
        ├── Quantum backend     →  Qiskit-Aer (optional, graceful fallback)
        └── FastAPI surface     →  /health · /api/v1/* · /api/v1/quantum/sample
```

**Departments (11 total, auto-discovered):**

| Department                | Status        | Specialist agents |
|---------------------------|---------------|-------------------|
| `cloud_mastery`           | **implemented** | 9 (devops_engineer, kubernetes_specialist, serverless_architect, security_specialist, monitoring_specialist, cost_optimizer, data_engineer, cloud_architect, supervisor_agent) |
| `ai_supremacy`            | stub (directories present, agents pending) | 10 |
| `ai_ml_mastery`           | stub | 9  |
| `automation_empire`       | stub | 10 |
| `blockchain_mastery`      | stub | 8  |
| `cloud_computing_mastery` | stub | 5  |
| `data_omniscience`        | stub | supervisor |
| `quantum_mastery`         | stub | 10 |
| `security_fortress`       | stub | supervisor |
| `system_orchestration`    | stub | supervisor |
| `web_mastery`             | stub | 11 |

A "stub" department has its `__init__.py` and agent directories in place but
the concrete agent classes have not yet been wired. The orchestrator and CLI
still see them and treat them as a consistent registry; `create_agent()`
raises `NotImplementedError` until the agent class is filled in.

---

## // EXPERIMENTAL FEATURES (real, but flagged)

These ship enabled-but-opt-in. Each is a real implementation — not magic — and
falls back gracefully when its optional dependency is missing.

**Quantum-sampled decisions (`enable_quantum=True`)**
- Builds a uniform-superposition circuit over your candidate options
- Runs it on `qiskit_aer.AerSimulator` (1024 shots by default)
- Returns the sampled choice + the full measurement histogram
- Falls back to a seeded PRNG if `qiskit` is not installed

**Self-reflection (`enable_reflection=True`)**
- A planner node proposes options; a critic node scores them
- The orchestrator returns both picks plus a consensus and the method used
- Auditable: critic scores are deterministic and always exposed

---

## // GETTING STARTED

```bash
# 1. Clone
git clone https://github.com/KaliVibeCoding/divine-agent-system.git
cd divine-agent-system

# 2. Install (pick one)
pip install -r requirements.txt
pip install -e ".[all]"            # all extras
pip install -e ".[dev,quantum]"    # dev + Qiskit Aer

# 3. Configure (config.yaml is already in-repo; edit in place)
$EDITOR config.yaml

# 4. Smoke-test
python test_system.py              # 13 unit tests, ~22 s

# 5. Run
python -m agents.cli info          # print system metadata
python -m agents.cli list-agents   # tree view of all departments
python -m agents.cli start-server  # FastAPI on :8000
```

The CLI is also installed as `sao`, `divine-agent`, and `supreme-orchestrator`
console scripts after `pip install -e .`.

---

## // DEPLOYMENT

```bash
# Docker (single container)
docker build -t sao:2.0.0 --target production .
docker run --rm -p 8000:8000 sao:2.0.0

# Compose (full stack: app + postgres-16 + redis-7.4 + prom + grafana + otel)
docker compose up -d

# Compose with the optional Qiskit-Aer profile
docker compose --profile quantum up -d

# Kubernetes / AWS / Azure / GCP via the deploy driver
python deploy.py kubernetes
python deploy.py aws --json
python deploy.py multi-cloud --dry-run
```

---

## // HTTP API

The FastAPI surface in `orchestrator.main:app`:

| Method | Path                                       | Purpose                          |
|--------|--------------------------------------------|----------------------------------|
| GET    | `/health`                                  | liveness probe                   |
| GET    | `/api/v1/system/info`                      | full system metadata             |
| GET    | `/api/v1/system/status`                    | live orchestrator state          |
| GET    | `/api/v1/agents`                           | every department + agent list    |
| GET    | `/api/v1/agents/{department}`              | one department                   |
| GET    | `/api/v1/agents/{department}/{name}`       | one agent (capabilities, status) |
| POST   | `/api/v1/quantum/sample`                   | run a Qiskit-Aer superposition sample |

Run with: `uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000`.

---

## // MONITORING & OBSERVABILITY

The Compose stack ships these out of the box:

- **Grafana 11.3** — `http://localhost:3000` (admin/admin)
- **Prometheus v2.55** — `http://localhost:9090`
- **Jaeger 1.62 (OTLP 4317/4318)** — `http://localhost:16686`
- **App health** — `http://localhost:8000/health`

Tracing is wired through OpenTelemetry (OTLP) rather than direct Jaeger
client SDKs.

---

## // SECURITY & COMPLIANCE

- TLS termination at the edge (proxy / ingress, not in-app)
- JWT (RS256) — verified against a JWKS URL
- RBAC with department-scoped roles
- Per-request audit logging via OpenTelemetry attributes
- Trivy + `pip-audit` wired into CI
- **Post-quantum aware:** ML-KEM-768 / ML-DSA-65 (NIST FIPS-203 / FIPS-204) noted
  in agent capabilities; not yet enforced on the wire (May 2026)
- Compliance targets: SOC 2 Type II, ISO 27001, GDPR, HIPAA, EU AI Act

See [SECURITY.md](SECURITY.md) for the full posture and the disclosure policy.

---

## // ROADMAP

| Quarter   | Theme                                                           |
|-----------|-----------------------------------------------------------------|
| Q2 2026   | Wire `web_mastery` and `data_omniscience` concrete agents       |
| Q3 2026   | LangGraph 0.5 migration; MCP 1.3 (streamable tool I/O)          |
| Q4 2026   | First-class ML-KEM-768 transport for inter-agent messaging      |
| Q1 2027   | `quantum_mastery` department: real `qiskit-ibm-runtime` access  |

---

## // CONTRIBUTING

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version:

1. Branch from `main`, target `genspark_ai_developer` for AI-assisted patches.
2. `python test_system.py` must stay green.
3. Conventional Commits (`feat:`, `fix:`, `chore:`, …).
4. Keep claims honest — if a feature is experimental, label it.

---

## // LICENSE

MIT — see [LICENSE](LICENSE).

---

## // THE ARCHITECT

<p align="center">
  <a href="https://www.kalivibecoding.com" target="_blank">
    <img src="https://cdn.abacus.ai/images/df46850a-d15d-437b-8d04-688c8d10f31d.png" alt="Rick Jefferson" width="120" style="border-radius: 50%; border: 3px solid #FF69B4;">
  </a>
</p>
<p align="center">
  Architected and built by <strong>Rick Jefferson</strong> for <strong>KaliVibeCoding</strong>.
  <br>
  <em>Code to the Rhythm. Build by the Beat.</em>
</p>

---

<p align="center">
  <strong>Cinematic branding. Honest engineering. Real tech, May 2026.</strong>
</p>
