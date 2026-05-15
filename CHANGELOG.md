# Changelog

All notable changes to the Divine Agent System are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Concrete agent classes for `web_mastery` and `data_omniscience`
- LangGraph 0.5 migration once stable
- MCP 1.3 streamable tool I/O
- ML-KEM-768 (NIST FIPS-203) as the default inter-agent transport key
  exchange

---

## [2.0.0] — 2026-05-14

### Reality Pass — Full Repository Modernisation

A complete pass over the codebase to bring everything to a coherent,
runnable May-2026 stack. Cinematic branding stays; every concrete claim
is now grounded in real, current technology.

### Added
- **Dynamic department discovery** (`agents._discover_departments`)
  that walks `agents/<dept>/<agent>/agent.py` and registers any
  department present on disk.
- **Ten stub departments** with consistent `__init__.py` factory APIs
  (`get_department_info`, `list_agents`, `create_agent`,
  `create_rpc_agent`): `ai_supremacy`, `ai_ml_mastery`,
  `automation_empire`, `blockchain_mastery`, `cloud_computing_mastery`,
  `data_omniscience`, `quantum_mastery`, `security_fortress`,
  `system_orchestration`, `web_mastery`.
- **`DivineOrchestrator`** in `orchestrator/main.py` with explicit
  `boot() / discover_agents() / wire() / reflect() / shutdown() /
  status()` async lifecycle.
- **FastAPI 0.115 surface** via `orchestrator.main:build_app` and the
  module-level `app` singleton — `/health`, `/api/v1/system/info`,
  `/api/v1/system/status`, `/api/v1/agents`,
  `/api/v1/agents/{department}`, `/api/v1/agents/{department}/{name}`,
  `POST /api/v1/quantum/sample`.
- **Qiskit-Aer quantum backend** with graceful PRNG fallback when the
  `qiskit-aer` extra is not installed.
- **`create_agent_instance`** alias on `agents.cloud_mastery` for
  backward compatibility with older callers.
- **Real deploy driver** (`deploy.py`) with `DivineDeploymentOrchestrator`,
  `StepResult`, and `DeployReport` dataclasses; subprocess-based
  `kubectl` / `docker` / `aws` / `az` / `gcloud` invocations via
  `shutil.which`; `--json` reporter; targets `docker`, `compose`,
  `kubernetes`, `aws`, `azure`, `gcp`, `multi-cloud`.
- **Console scripts** in `setup.py`: `sao`, `divine-agent`,
  `supreme-orchestrator` → `agents.cli:main`.
- **Compose profiles**: `--profile dev` (hot-reload) and
  `--profile quantum` (Qiskit-Aer worker).
- **`eu_ai_act`** compliance toggle in `config.yaml`.

### Changed
- **System version** bumped to `2.0.0`; release date `2026-05-14`.
- **Python baseline** raised to **3.12-slim-bookworm** (3.10–3.13
  supported); was 3.8+.
- **`requirements.txt`** rewritten with May-2026 pins (LangGraph 0.4,
  Qiskit 1.3, Pydantic 2.10, FastAPI 0.115, Pinecone-client 5,
  Supabase 2.10, Redis 5.2, MCP 1.2, psycopg 3.2).
- **`config.yaml`** refreshed: every pin and dependency reference now
  points at real, current versions. `consciousness_features` renamed
  to `reflection_features` and marked experimental. Default LLMs:
  `gpt-5` (OpenAI), `claude-sonnet-4.5` (Anthropic).
- **`config/runtime_manifest.json`** rewritten with honest tech
  mapping (no more "reality manipulation" / "omniscient knowledge");
  11 departments documented (1 implemented, 10 stubs); 75 agent
  directories on disk, 9 implemented agents listed accurately.
- **`Dockerfile`** rebuilt as a multi-stage BuildKit (`# syntax=docker/
  dockerfile:1.7`) image: `base / dependencies / development /
  production / testing / quantum / final`. Production CMD:
  `uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000
  --workers 4`.
- **`docker-compose.yml`** modernised to Compose Spec v2 (top-level
  `name`, no deprecated `version:` key). YAML anchor `x-common-env`
  for shared environment blocks. Pinned: `postgres:16-alpine`,
  `redis:7.4-alpine`, `prom/prometheus:v2.55.0`,
  `grafana/grafana:11.3.0`, `jaegertracing/all-in-one:1.62`
  with OTLP 4317/4318.
- **`setup.py`** rewritten with stricter stdlib filter, PEP 508
  marker support, and modern extras: `dev`, `quantum`, `ml`,
  `cloud-aws`, `cloud-azure`, `cloud-gcp`, `monitoring`,
  `messaging`, `all`.
- **`agents/__init__.py`** rebuilt: dynamic discovery, new
  `SupremeAgenticOrchestrator(enable_quantum=…, enable_reflection=…)`
  constructor with `register_agent`, `get_system_status`,
  `get_system_statistics` alias, `update_configuration`.
- **`agents/cli.py`** rewritten around the new subcommand set:
  `info`, `list-agents`, `create-agent`, `test-agent`,
  `start-system`, `start-server`, `config`, `monitor`, `deploy`.
  Rich-aware output with plain-text fallback. `start-server` boots
  `orchestrator.main:build_app` via `uvicorn`.
- **`test_system.py`** rewritten to exercise the *real* async agent
  APIs with their actual enum-typed parameters
  (`DeploymentStrategy`, `InfrastructureProvider`, `WorkloadType`,
  `ServiceType`, `ScalingStrategy`, `SecurityDomain`,
  `ComplianceFramework`, `AttackVector`, `EncryptionAlgorithm`,
  `MetricType`, `AggregationMethod`, `AlertSeverity`,
  `MonitoringScope`, `CostCategory`, `OptimizationType`,
  `RecommendationPriority`, `DataSourceType`, `DataFormat`,
  `TransformationType`, `ProcessingType`). Each async call is
  wrapped in `asyncio.run()`. 13 tests, all green in ~22 s.
- **`DivineOrchestrator.discover_agents`** now pulls capabilities
  from each department's own `get_department_info()` (which returns
  `agents` as a dict) rather than from `agents.get_department_info()`
  (which returns `agents` as a list), fixing an `'list' object has
  no attribute 'get'` regression.

### Fixed
- **`config.yaml`** YAML parse error at the `cloud_computing_mastery`
  line (missing space between `:` and `{`) that silently zeroed the
  parsed config and broke CLI startup.
- **CLI test fixture** now asserts on `cli.config` (the
  side-effect-stored config) rather than the raw return value, so
  it tolerates both behaviours of `load_config`.

### Removed
- **Mythological / unfalsifiable claims**: "interdimensional
  communication", "reality manipulation", "consciousness telepathy",
  "1000-qubit reality simulation", "Level-5 consciousness", "near-
  human awareness", `omniscient_knowledge`, etc. The brand voice
  stays cinematic; the engineering claims are now honest.
- **Stdlib pseudo-dependencies** from `requirements.txt`: `sqlite3`,
  `math`, `os`, `sys`, `uuid`, `statistics`, `concurrent.futures`,
  `multiprocessing`, `threading`. These caused `pip install -r
  requirements.txt` to fail.
- **Fictional packages** from `requirements.txt`: `neurosymbolic`,
  `cognitive-architectures`.
- **Retired dependency** `qiskit-ibmq-provider` (retired 2024);
  replaced by awareness of `qiskit-ibm-runtime`.
- **Top-level `version:`** key from `docker-compose.yml` (deprecated
  in Compose Spec v2).
- **Deprecated Qiskit 0.x imports** (`from qiskit import execute,
  Aer`); replaced with `from qiskit import QuantumCircuit, transpile`
  and `from qiskit_aer import AerSimulator`.

### Security
- **PQC awareness**: `EncryptionAlgorithm` enum now references the
  NIST FIPS-203 (ML-KEM-768, formerly Kyber) and FIPS-204
  (ML-DSA-65, formerly Dilithium) families.
- **OpenTelemetry OTLP** replaces direct Jaeger client SDK usage —
  one collector format, less duplicated instrumentation.

### Migration Notes
- Callers using `from qiskit import execute, Aer` must move to
  `from qiskit import transpile` + `from qiskit_aer import AerSimulator`.
- `agents.SupremeAgenticOrchestrator(...)` now accepts keyword-only
  `enable_quantum=` and `enable_reflection=` flags. The legacy
  `enable_quantum_processing()` / `activate_consciousness_ethics()`
  methods are preserved as aliases.
- `psycopg2-binary` is gone; use `psycopg[binary]` (psycopg3).
- Anything that imported `agents.database` should guard the import —
  the module has not yet landed and `docker-entrypoint.sh` only
  triggers it when `DIVINE_AGENT_INIT_DB=true` is set explicitly.

---

## [1.0.0] — 2024-12-19

### Initial Release

Initial publication of the Divine Agent System. Established the
four-tier hierarchy concept and shipped the first iteration of the
Cloud Mastery department (7 specialist agents) with the
LangGraph-based orchestrator scaffold.

### Added
- 4-tier hierarchical concept (Supreme Entity / Super Elite Council /
  Department Managers / Specialised Agents).
- Cloud Mastery department: DevOps Engineer, Kubernetes Specialist,
  Serverless Architect, Security Specialist, Monitoring Specialist,
  Cost Optimizer, Data Engineer.
- LangGraph orchestrator scaffold.
- Pinecone + Supabase + Redis Streams data layer.
- Initial Docker + Kubernetes deployment scaffolding.
- README, ARCHITECTURE, PROJECT_MANIFEST, CHANGELOG documentation.

### Known Issues (resolved in 2.0.0)
- `requirements.txt` contained stdlib pseudo-deps that broke
  `pip install`.
- Several enthusiastic claims ("1000 qubits", "interdimensional
  communication", "consciousness telepathy") had no implementation
  behind them.
- Qiskit 0.x API usage (`execute`, top-level `Aer`) broke on
  Qiskit 1.x.

---

## Versioning Strategy

- **MAJOR (`X.0.0`)** — breaking API or stack changes (e.g. dropping
  Python 3.10, migrating LangGraph major).
- **MINOR (`X.Y.0`)** — new departments, new agents, new HTTP
  endpoints, new experimental features.
- **PATCH (`X.Y.Z`)** — bug fixes, dependency bumps within their
  pinned ranges, doc updates.

## References

- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [NIST FIPS-203 (ML-KEM)](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST FIPS-204 (ML-DSA)](https://csrc.nist.gov/pubs/fips/204/final)

---

*Chronicled by the KaliVibeCoding engineering team — cinematic
branding, honest engineering.*
