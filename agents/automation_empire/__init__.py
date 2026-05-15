#!/usr/bin/env python3
"""
Automation Empire Department
============================

Stub department for the Divine Agent System.

This package is registered with the top-level orchestrator (see
``agents/__init__.py``) but the concrete agent classes under each
sub-directory have not been wired up yet.  The directory layout is
preserved so that, as agents are implemented, they can be exposed
through :func:`create_agent` / :func:`create_rpc_agent` without
changing the public API.

To implement an agent in this department:

1. Place the agent module at ``agents/automation_empire/<role>/agent.py`` exporting
   a class (and optionally a matching ``...RPC`` class).
2. Add an entry to ``_AGENT_REGISTRY`` below.
3. The top-level ``SupremeAgenticOrchestrator`` will pick it up
   automatically via the lazy ``create_department_agent`` path.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEPARTMENT_NAME = "automation_empire"
DEPARTMENT_DESCRIPTION = "Workflow orchestration & RPA-style task automation"

# Map of agent_name -> dict with keys: class, rpc_class, description, capabilities
_AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _discovered_agent_dirs() -> List[str]:
    """Return the agent sub-directories present on disk."""
    here = Path(__file__).parent
    return sorted(
        sub.name for sub in here.iterdir()
        if sub.is_dir() and (sub / "agent.py").exists()
    )


DEPARTMENT_INFO: Dict[str, Any] = {
    "name": DEPARTMENT_NAME,
    "description": DEPARTMENT_DESCRIPTION,
    "status": "stub",
    "agents_on_disk": _discovered_agent_dirs(),
    "agents": {
        name: {
            "class": entry["class"].__name__,
            "rpc_class": entry["rpc_class"].__name__ if entry.get("rpc_class") else None,
            "description": entry.get("description", ""),
            "capabilities": list(entry.get("capabilities", [])),
        }
        for name, entry in _AGENT_REGISTRY.items()
    },
}


def get_department_info() -> Dict[str, Any]:
    return DEPARTMENT_INFO


def list_agents() -> List[str]:
    return list(_AGENT_REGISTRY.keys())


def get_agent_info(agent_name: str) -> Optional[Dict[str, Any]]:
    return DEPARTMENT_INFO["agents"].get(agent_name)


def create_agent(agent_name: str):
    entry = _AGENT_REGISTRY.get(agent_name)
    if entry is None:
        raise NotImplementedError(
            f"Agent {agent_name!r} is not yet implemented in the "
            f"{DEPARTMENT_NAME!r} department. Agent directories present on "
            f"disk: {_discovered_agent_dirs()}"
        )
    return entry["class"]()


def create_rpc_agent(agent_name: str):
    entry = _AGENT_REGISTRY.get(agent_name)
    if entry is None or not entry.get("rpc_class"):
        raise NotImplementedError(
            f"No RPC class registered for {agent_name!r} in "
            f"{DEPARTMENT_NAME!r}."
        )
    return entry["rpc_class"]()


__all__ = [
    "DEPARTMENT_INFO",
    "get_department_info",
    "list_agents",
    "get_agent_info",
    "create_agent",
    "create_rpc_agent",
]
