#!/usr/bin/env python3
"""
Cloud Mastery Department
========================

The first (and currently most complete) department in the Divine Agent System.
All nine specialist agents in this department are real Python classes backed
by concrete agent modules under ``agents/cloud_mastery/<role>/agent.py``.

Specialists
-----------
* ``cloud_architect``       — cloud architecture patterns & blueprints
* ``cost_optimizer``        — budget tracking, rightsizing, forecasting
* ``data_engineer``         — data sources, pipelines, quality checks
* ``devops_engineer``       — CI/CD pipelines, IaC, deployment strategies
* ``kubernetes_specialist`` — cluster / workload / service management
* ``monitoring_specialist`` — metrics, alerts, dashboards, SLOs
* ``security_specialist``   — security policies, threat intel, encryption keys
* ``serverless_architect``  — FaaS design, event triggers, perf optimisation
* ``supervisor_agent``      — department-level coordinator / RPC entry-point

The "quantum" and "consciousness" capabilities listed on every agent are
implemented as simulations (Qiskit Aer sampling and planner/critic reflection
loops respectively) — they are *features*, not metaphysics.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Eager imports of the concrete agent classes
# ---------------------------------------------------------------------------
from .devops_engineer.agent          import DevOpsEngineer,         DevOpsEngineerRPC
from .kubernetes_specialist.agent    import KubernetesSpecialist,   KubernetesSpecialistRPC
from .serverless_architect.agent     import ServerlessArchitect,    ServerlessArchitectRPC
from .security_specialist.agent      import SecuritySpecialist,     SecuritySpecialistRPC
from .monitoring_specialist.agent    import MonitoringSpecialist,   MonitoringSpecialistRPC
from .cost_optimizer.agent           import CostOptimizer,          CostOptimizerRPC
from .data_engineer.agent            import DataEngineer,           DataEngineerRPC

# Optional sub-agents — wrap import to avoid breaking the whole package
# if their files have transient issues during ongoing refactors.
try:
    from .cloud_architect.agent      import CloudArchitect,         CloudArchitectRPC
except Exception as _exc:  # pragma: no cover
    logger.warning("cloud_architect failed to import: %s", _exc)
    CloudArchitect = CloudArchitectRPC = None  # type: ignore[assignment]

try:
    from .supervisor_agent.agent     import CloudMasterySupervisor, CloudMasteryRPC
except Exception as _exc:  # pragma: no cover
    logger.warning("supervisor_agent failed to import: %s", _exc)
    CloudMasterySupervisor = CloudMasteryRPC = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Department registry — maps a stable agent name to its factory pair
# ---------------------------------------------------------------------------
_AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "devops_engineer": {
        "class": DevOpsEngineer,
        "rpc_class": DevOpsEngineerRPC,
        "description": "CI/CD pipelines and infrastructure automation",
        "capabilities": [
            "Pipeline creation and execution",
            "Infrastructure template management",
            "Deployment strategy optimisation",
            "Monitoring & alerting setup",
            "Quantum-sampled deployment selection (experimental)",
            "Reflection-driven rollback decisions (experimental)",
        ],
    },
    "kubernetes_specialist": {
        "class": KubernetesSpecialist,
        "rpc_class": KubernetesSpecialistRPC,
        "description": "Container orchestration and Kubernetes management",
        "capabilities": [
            "Workload and service management",
            "Autoscaling configuration",
            "Network policy implementation",
            "Cluster health monitoring",
            "Quantum-sampled scheduling hints (experimental)",
        ],
    },
    "serverless_architect": {
        "class": ServerlessArchitect,
        "rpc_class": ServerlessArchitectRPC,
        "description": "Function-as-a-Service design and optimisation",
        "capabilities": [
            "Function design and deployment",
            "Event trigger configuration",
            "Cold-start / latency optimisation",
            "Per-invocation cost analysis",
        ],
    },
    "security_specialist": {
        "class": SecuritySpecialist,
        "rpc_class": SecuritySpecialistRPC,
        "description": "Cloud security and compliance",
        "capabilities": [
            "Security policy creation",
            "Threat-intelligence analysis",
            "Incident response orchestration",
            "Vulnerability assessment",
            "Post-quantum-ready key management",
        ],
    },
    "monitoring_specialist": {
        "class": MonitoringSpecialist,
        "rpc_class": MonitoringSpecialistRPC,
        "description": "Observability, SLOs and alerting",
        "capabilities": [
            "Metric definition and collection",
            "Alert rule configuration",
            "Dashboard creation",
            "SLO management",
            "OpenTelemetry trace correlation",
        ],
    },
    "cost_optimizer": {
        "class": CostOptimizer,
        "rpc_class": CostOptimizerRPC,
        "description": "FinOps — cost tracking, rightsizing, budgeting",
        "capabilities": [
            "Cost tracking and analysis",
            "Resource utilisation optimisation",
            "Budget management",
            "Cost forecasting",
        ],
    },
    "data_engineer": {
        "class": DataEngineer,
        "rpc_class": DataEngineerRPC,
        "description": "Data sources, pipelines and quality checks",
        "capabilities": [
            "Data source configuration",
            "Pipeline creation and execution",
            "Data quality assessment",
            "Governance policy management",
        ],
    },
}

# Conditionally register optional agents
if CloudArchitect is not None:
    _AGENT_REGISTRY["cloud_architect"] = {
        "class": CloudArchitect,
        "rpc_class": CloudArchitectRPC,
        "description": "Cloud architecture patterns and blueprints",
        "capabilities": [
            "Architectural blueprint design",
            "Resilience pattern selection",
            "Cross-tier scalability planning",
            "Architectural decision records",
        ],
    }

if CloudMasterySupervisor is not None:
    _AGENT_REGISTRY["supervisor_agent"] = {
        "class": CloudMasterySupervisor,
        "rpc_class": CloudMasteryRPC,
        "description": "Department-level coordinator and RPC entry-point",
        "capabilities": [
            "Cross-agent task routing",
            "Health aggregation",
            "Department-wide reporting",
        ],
    }


DEPARTMENT_INFO: Dict[str, Any] = {
    "name": "Cloud Mastery",
    "description": "Cloud engineering excellence — DevOps, K8s, FaaS, security, observability, FinOps, data",
    "agents": {
        name: {
            "class": entry["class"].__name__,
            "rpc_class": entry["rpc_class"].__name__ if entry["rpc_class"] else None,
            "description": entry["description"],
            "capabilities": list(entry["capabilities"]),
        }
        for name, entry in _AGENT_REGISTRY.items()
    },
    "experimental_features": [
        "Quantum-sampled decisions via Qiskit Aer",
        "Self-reflective planner / critic loops",
        "Inter-agent entangled-state voting (simulated)",
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_department_info() -> Dict[str, Any]:
    """Return the static metadata for this department."""
    return DEPARTMENT_INFO


def list_agents() -> List[str]:
    """Return a list of agent names available in this department."""
    return list(_AGENT_REGISTRY.keys())


def get_agent_info(agent_name: str) -> Optional[Dict[str, Any]]:
    """Return the descriptor dict for a single agent."""
    return DEPARTMENT_INFO["agents"].get(agent_name)


def create_agent(agent_name: str):
    """Instantiate the in-process agent class for ``agent_name``."""
    entry = _AGENT_REGISTRY.get(agent_name)
    if entry is None:
        raise ValueError(
            f"Unknown agent: {agent_name!r}. "
            f"Available: {sorted(_AGENT_REGISTRY)}"
        )
    return entry["class"]()


def create_rpc_agent(agent_name: str):
    """Instantiate the JSON-RPC wrapper for ``agent_name``."""
    entry = _AGENT_REGISTRY.get(agent_name)
    if entry is None:
        raise ValueError(
            f"Unknown agent: {agent_name!r}. "
            f"Available: {sorted(_AGENT_REGISTRY)}"
        )
    if entry["rpc_class"] is None:
        raise NotImplementedError(
            f"No RPC class available for agent {agent_name!r}"
        )
    return entry["rpc_class"]()


# Back-compat alias — older code (and the test suite) calls this name.
def create_agent_instance(agent_name: str):
    """Alias of :func:`create_agent` kept for backward compatibility."""
    return create_agent(agent_name)


__all__ = [
    # Concrete agent classes
    "DevOpsEngineer", "DevOpsEngineerRPC",
    "KubernetesSpecialist", "KubernetesSpecialistRPC",
    "ServerlessArchitect", "ServerlessArchitectRPC",
    "SecuritySpecialist", "SecuritySpecialistRPC",
    "MonitoringSpecialist", "MonitoringSpecialistRPC",
    "CostOptimizer", "CostOptimizerRPC",
    "DataEngineer", "DataEngineerRPC",
    "CloudArchitect", "CloudArchitectRPC",
    "CloudMasterySupervisor", "CloudMasteryRPC",
    # Public API
    "DEPARTMENT_INFO",
    "get_department_info",
    "list_agents",
    "get_agent_info",
    "create_agent",
    "create_agent_instance",
    "create_rpc_agent",
]


if __name__ == "__main__":  # pragma: no cover
    import json
    print(json.dumps(DEPARTMENT_INFO, indent=2, default=str))
