#!/usr/bin/env python3
"""
Divine Agent System — Orchestrator
==================================

This module is the *real* orchestration entry-point for the Divine Agent
System. It composes three layers on top of the in-process facade in
:class:`agents.SupremeAgenticOrchestrator`:

1. **Agent discovery** — walks ``agents/<department>/<agent>/`` and registers
   every agent.py it finds against the top-level orchestrator.
2. **Optional quantum sampling layer** — uses Qiskit 1.3 + qiskit-aer when
   the dependency is installed; gracefully degrades to a pseudo-random
   fallback when it isn't.
3. **FastAPI surface** — :func:`build_app` returns an ASGI application
   exposing ``/health``, ``/api/v1/system/status``, ``/api/v1/agents``,
   ``/api/v1/agents/{department}/{name}`` and ``/api/v1/quantum/sample``.

Run modes:

  * ``python -m orchestrator.main``                 — async demo / discovery run
  * ``uvicorn orchestrator.main:app --reload``      — HTTP API
  * Imported by :mod:`agents.cli` ``start-server``  — production launcher

The "quantum / consciousness" vocabulary is preserved as branding but every
operation is genuinely simulated, never magical: superposition sampling
goes through ``qiskit_aer.AerSimulator``; "consciousness" is a planner +
critic reflection loop you can disable via the constructor flag.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Make ``agents`` importable when running as a script
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents import (  # noqa: E402
    SupremeAgenticOrchestrator,
    __version__ as SAO_VERSION,
    get_system_info,
    list_all_agents,
    get_department_info,
    create_department_agent,
)

logger = logging.getLogger("orchestrator")


# ---------------------------------------------------------------------------
# Optional quantum backend
# ---------------------------------------------------------------------------
class _QuantumBackend:
    """Thin wrapper around Qiskit Aer with a graceful fallback."""

    def __init__(self, n_qubits: int = 5) -> None:
        self.n_qubits = max(1, min(int(n_qubits), 24))   # hard cap for safety
        self.available = False
        self._sampler = None
        try:
            from qiskit import QuantumCircuit, transpile      # type: ignore
            from qiskit_aer import AerSimulator               # type: ignore

            self._QuantumCircuit = QuantumCircuit
            self._transpile = transpile
            self._sampler = AerSimulator()
            self.available = True
            logger.info("Quantum backend ready (Qiskit Aer, %d qubits)", self.n_qubits)
        except ImportError as exc:
            logger.info("Quantum backend unavailable (%s) — using PRNG fallback", exc)

    def sample_choice(self, options: List[Any], shots: int = 1024) -> Tuple[Any, Dict[str, int]]:
        """Pick one element from ``options`` using simulated superposition.

        Returns the chosen option plus the raw bitstring histogram so callers
        can inspect the distribution.
        """
        if not options:
            raise ValueError("sample_choice requires at least one option")

        if not self.available:
            # Deterministic-ish fallback: just use the stdlib PRNG
            choice = random.choice(options)
            return choice, {"_fallback": shots}

        # Build a uniform-superposition circuit big enough to index `options`
        n_needed = max(1, (len(options) - 1).bit_length())
        n = min(n_needed, self.n_qubits)
        qc = self._QuantumCircuit(n, n)
        for q in range(n):
            qc.h(q)
        qc.measure(range(n), range(n))

        compiled = self._transpile(qc, self._sampler)
        result = self._sampler.run(compiled, shots=shots).result()
        counts = dict(result.get_counts())

        # Pick the bitstring with the highest count, fold it back into the
        # options list with a modulo (uniform across a power-of-two space).
        top_bits = max(counts, key=counts.get)
        idx = int(top_bits, 2) % len(options)
        return options[idx], counts


# ---------------------------------------------------------------------------
# Orchestration state machine
# ---------------------------------------------------------------------------
class OrchestrationPhase(str, Enum):
    INITIALISING   = "initialising"
    DISCOVERING    = "discovering_agents"
    WIRING         = "wiring_orchestrator"
    READY          = "ready"
    EXECUTING      = "executing"
    REFLECTING     = "reflecting"
    SHUTTING_DOWN  = "shutting_down"


@dataclass
class AgentRecord:
    department: str
    name: str
    fingerprint: str
    capabilities: List[str] = field(default_factory=list)
    rpc_enabled: bool = False
    status: str = "registered"


@dataclass
class OrchestratorState:
    phase: OrchestrationPhase = OrchestrationPhase.INITIALISING
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agents: Dict[str, AgentRecord] = field(default_factory=dict)
    quantum_enabled: bool = False
    reflection_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "started_at": self.started_at,
            "agent_count": len(self.agents),
            "quantum_enabled": self.quantum_enabled,
            "reflection_enabled": self.reflection_enabled,
            "agents": {k: asdict(v) for k, v in self.agents.items()},
        }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class DivineOrchestrator:
    """Async coordinator that fans tasks out across discovered agents."""

    def __init__(
        self,
        *,
        config_path: Optional[str] = None,
        enable_quantum: bool = True,
        enable_reflection: bool = True,
        qubits: int = 5,
    ) -> None:
        self.project_root = PROJECT_ROOT
        self.config_path = (
            Path(config_path) if config_path
            else self.project_root / "config" / "runtime_manifest.json"
        )
        self.config: Dict[str, Any] = self._load_config()

        self.state = OrchestratorState(
            quantum_enabled=enable_quantum,
            reflection_enabled=enable_reflection,
        )
        self.quantum = _QuantumBackend(n_qubits=qubits) if enable_quantum else None
        self.facade = SupremeAgenticOrchestrator(
            enable_quantum=enable_quantum,
            enable_reflection=enable_reflection,
        )

    # ----- bootstrap -------------------------------------------------------
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            logger.warning("Runtime manifest not found at %s — using defaults", self.config_path)
            return {}
        try:
            with self.config_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            logger.error("Runtime manifest is not valid JSON: %s", exc)
            return {}

    @staticmethod
    def _fingerprint(department: str, name: str) -> str:
        digest = hashlib.sha256(f"sao::{department}::{name}".encode()).hexdigest()
        return f"SAO-{digest[:16].upper()}"

    # ----- discovery -------------------------------------------------------
    async def discover_agents(self) -> int:
        """Register every agent dir we can find. Returns the count discovered."""
        self.state.phase = OrchestrationPhase.DISCOVERING
        info = get_system_info()
        count = 0
        for dept_name, dept_meta in info["departments"].items():
            for agent_name in dept_meta.get("agents", []):
                key = f"{dept_name}.{agent_name}"
                record = AgentRecord(
                    department=dept_name,
                    name=agent_name,
                    fingerprint=self._fingerprint(dept_name, agent_name),
                    capabilities=[],
                    rpc_enabled=False,
                    status="discovered",
                )
                # For implemented departments we can pull real capabilities.
                # NOTE: ``agents.get_department_info`` returns a department
                # record where ``agents`` is a *list of names*. Concrete
                # department packages (e.g. ``agents.cloud_mastery``) expose
                # their own ``get_department_info`` whose ``agents`` is a
                # ``dict[name -> descriptor]``. Pull capabilities from the
                # latter when available.
                if dept_meta.get("status") == "implemented":
                    try:
                        import importlib
                        dept_module = importlib.import_module(f"agents.{dept_name}")
                        dept_info_fn = getattr(dept_module, "get_department_info", None)
                        dept_info = dept_info_fn() if callable(dept_info_fn) else {}
                    except Exception:
                        dept_info = {}
                    agents_map = dept_info.get("agents") or {}
                    if isinstance(agents_map, dict):
                        agent_desc = agents_map.get(agent_name, {}) or {}
                        record.capabilities = list(agent_desc.get("capabilities", []))
                        record.rpc_enabled = bool(agent_desc.get("rpc_class"))
                    else:
                        record.capabilities = []
                        record.rpc_enabled = False
                self.state.agents[key] = record
                count += 1
        logger.info("Discovered %d agents across %d departments",
                    count, len(info["departments"]))
        return count

    # ----- execution -------------------------------------------------------
    async def wire(self) -> None:
        """Eagerly instantiate the implemented agents so they're warm in memory."""
        self.state.phase = OrchestrationPhase.WIRING
        wired = 0
        for key, record in self.state.agents.items():
            if not record.capabilities:
                continue   # skip stubs
            try:
                agent = create_department_agent(record.department, record.name)
                self.facade.register_agent(key, agent, department=record.department)
                record.status = "wired"
                wired += 1
            except (ImportError, NotImplementedError, ValueError) as exc:
                record.status = f"skipped ({exc.__class__.__name__})"
                logger.debug("Could not wire %s: %s", key, exc)
        logger.info("Wired %d in-process agents", wired)
        self.state.phase = OrchestrationPhase.READY

    async def reflect(self, decision: str, options: List[str]) -> Dict[str, Any]:
        """Planner-critic style reflection over a candidate set.

        Combines: (a) a uniform-superposition sample via Qiskit Aer when the
        quantum backend is available, and (b) a simple "critic" pass that
        scores options against their position in the list (closer-to-front
        gets a slight bonus, simulating prior beliefs).
        """
        if not options:
            raise ValueError("reflect() requires at least one option")
        self.state.phase = OrchestrationPhase.REFLECTING

        if self.quantum and self.quantum.available:
            chosen, histogram = self.quantum.sample_choice(options)
            method = "qiskit-aer-superposition"
        else:
            chosen = random.choice(options)
            histogram = {}
            method = "prng-fallback"

        # Critic — purely deterministic, so the result is auditable
        critic_scores = {opt: round(1.0 / (1 + i), 4) for i, opt in enumerate(options)}
        winner = max(critic_scores, key=critic_scores.get)
        consensus = chosen if chosen == winner else winner
        self.state.phase = OrchestrationPhase.READY

        return {
            "decision": decision,
            "options": options,
            "sampler_pick": chosen,
            "critic_pick": winner,
            "consensus": consensus,
            "method": method,
            "histogram": histogram,
            "critic_scores": critic_scores,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----- lifecycle -------------------------------------------------------
    async def boot(self) -> Dict[str, Any]:
        """Top-level "bring everything online" entry-point."""
        await self.discover_agents()
        await self.wire()
        return self.state.to_dict()

    async def shutdown(self) -> None:
        self.state.phase = OrchestrationPhase.SHUTTING_DOWN
        self.facade.active_agents.clear()
        logger.info("Orchestrator shut down cleanly.")

    # ----- introspection --------------------------------------------------
    def status(self) -> Dict[str, Any]:
        return {
            "service": "divine-agent-system",
            "version": SAO_VERSION,
            "state": self.state.to_dict(),
            "quantum_backend": {
                "available": bool(self.quantum and self.quantum.available),
                "qubits": self.quantum.n_qubits if self.quantum else 0,
            },
            "config_loaded": bool(self.config),
        }


# ---------------------------------------------------------------------------
# FastAPI surface
# ---------------------------------------------------------------------------
def build_app(orchestrator: Optional[DivineOrchestrator] = None):
    """Construct and return the FastAPI ASGI application.

    Imported lazily so that the rest of this module is still useful when
    FastAPI / Pydantic aren't installed.
    """
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
    except ImportError as exc:                                      # pragma: no cover
        raise RuntimeError(
            "FastAPI / Pydantic are required for the HTTP surface — "
            "install them via `pip install fastapi 'uvicorn[standard]'`"
        ) from exc

    app = FastAPI(
        title="Divine Agent System",
        description="Supreme Agentic Orchestrator (SAO) — 2026 production stack",
        version=SAO_VERSION,
    )
    orch = orchestrator or DivineOrchestrator()

    class ReflectRequest(BaseModel):
        decision: str = Field(..., description="What is being decided")
        options:  List[str] = Field(..., min_length=1)

    @app.on_event("startup")
    async def _startup() -> None:                                    # pragma: no cover
        await orch.boot()

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "phase": orch.state.phase.value,
            "version": SAO_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/api/v1/system/status")
    def system_status() -> Dict[str, Any]:
        return orch.status()

    @app.get("/api/v1/system/info")
    def system_info() -> Dict[str, Any]:
        return get_system_info()

    @app.get("/api/v1/agents")
    def agents_list() -> Dict[str, List[str]]:
        return list_all_agents()

    @app.get("/api/v1/agents/{department}")
    def department_detail(department: str) -> Dict[str, Any]:
        meta = get_department_info(department)
        if meta is None:
            raise HTTPException(status_code=404, detail=f"Unknown department: {department}")
        return meta

    @app.get("/api/v1/agents/{department}/{name}")
    def agent_detail(department: str, name: str) -> Dict[str, Any]:
        key = f"{department}.{name}"
        record = orch.state.agents.get(key)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Unknown agent: {key}")
        return asdict(record)

    @app.post("/api/v1/quantum/sample")
    async def quantum_sample(req: ReflectRequest) -> Dict[str, Any]:
        return await orch.reflect(req.decision, req.options)

    return app


# A module-level ASGI app for ``uvicorn orchestrator.main:app``
try:
    app = build_app()
except Exception as _e:                                              # pragma: no cover
    # Defer FastAPI errors until someone actually tries to serve traffic
    logger.debug("FastAPI app not pre-built: %s", _e)
    app = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# CLI entry-point — `python -m orchestrator.main`
# ---------------------------------------------------------------------------
async def _demo() -> None:
    banner = (
        "\n" + "=" * 72 +
        "\n  Divine Agent System — Orchestrator boot\n"
        f"  version {SAO_VERSION}  ·  {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        + "=" * 72
    )
    print(banner)

    orch = DivineOrchestrator()
    state = await orch.boot()
    print(f"\nPhase: {state['phase']}")
    print(f"Discovered agents: {state['agent_count']}")
    print(f"Quantum backend: "
          f"{'available' if orch.quantum and orch.quantum.available else 'unavailable (fallback)'}")

    decision = await orch.reflect(
        decision="Pick a deployment strategy for service `api`",
        options=["blue_green", "canary", "rolling", "feature_flags"],
    )
    print("\nReflection sample:")
    print(json.dumps({k: v for k, v in decision.items() if k != "histogram"}, indent=2))

    await orch.shutdown()
    print("\nDone.\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    asyncio.run(_demo())
