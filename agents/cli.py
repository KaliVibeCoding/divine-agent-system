#!/usr/bin/env python3
"""
Divine Agent System — Command Line Interface
=============================================

Real, working CLI that mirrors :mod:`agents` and :mod:`orchestrator.main`.

Subcommands
-----------
* ``info``          Print system metadata as JSON.
* ``list-agents``   Tree view of every department and the agents it exposes.
* ``create-agent``  Instantiate ``<department> <agent>`` and dump capabilities.
* ``test-agent``    Probe an agent for the canonical ``run_tests()`` hook.
* ``start-system``  Bring up the in-process orchestrator (no network listeners).
* ``start-server``  Launch the FastAPI HTTP / JSON-RPC server.
* ``config``        Show or mutate the YAML config in-place (memory only).
* ``monitor``       Print a periodic status table; Ctrl-C to exit.
* ``deploy``        Hand off to ``deploy.py`` with a chosen target.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# ---------------------------------------------------------------------------
# Optional rich output
# ---------------------------------------------------------------------------
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    _RICH = True
except ImportError:                                                # pragma: no cover
    _RICH = False
    Console = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Agent system import (supports both ``python -m agents.cli`` and plain script)
# ---------------------------------------------------------------------------
try:
    from . import (
        SupremeAgenticOrchestrator,
        get_system_info,
        list_all_agents,
        get_department_info,
        create_department_agent,
        __version__ as _SAO_VERSION,
    )
except ImportError:                                                # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from agents import (                                            # type: ignore[no-redef]
        SupremeAgenticOrchestrator,
        get_system_info,
        list_all_agents,
        get_department_info,
        create_department_agent,
        __version__ as _SAO_VERSION,
    )

log = logging.getLogger("sao.cli")


# ---------------------------------------------------------------------------
# CLI implementation
# ---------------------------------------------------------------------------
class DivineAgentCLI:
    """Thin wrapper around the orchestrator API with pretty printing."""

    def __init__(self) -> None:
        self.console = Console() if _RICH else None
        self.orchestrator: Optional[SupremeAgenticOrchestrator] = None
        self.config: Dict[str, Any] = {}

    # -- helpers ------------------------------------------------------------
    def print(self, *args: Any, **kwargs: Any) -> None:
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            # Strip rich markup if rich isn't available
            cleaned = []
            for a in args:
                if isinstance(a, str):
                    a = a.replace("[/", "").replace("[", "").replace("]", "")
                cleaned.append(a)
            print(*cleaned, **kwargs)

    def banner(self) -> None:
        text = (
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                    Divine Agent System                       ║\n"
            f"║         Supreme Agentic Orchestrator (SAO) v{_SAO_VERSION:<8}        ║\n"
            "║   LangGraph + MCP + Qiskit-Aer  ·  2026 production stack    ║\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )
        if self.console:
            self.console.print(text, style="bold blue")
        else:
            print(text)

    # -- config -------------------------------------------------------------
    def load_config(self, path: Optional[str]) -> Dict[str, Any]:
        path = path or "config.yaml"
        if not os.path.exists(path):
            log.warning("Config file %s not found — using empty config", path)
            return {}
        try:
            with open(path, "r", encoding="utf-8") as fh:
                self.config = yaml.safe_load(fh) or {}
            log.info("Configuration loaded from %s", path)
            return self.config
        except Exception as exc:                                    # pragma: no cover
            log.error("Failed to load config: %s", exc)
            return {}

    def init_orchestrator(self) -> bool:
        try:
            self.orchestrator = SupremeAgenticOrchestrator()
            return True
        except Exception as exc:                                    # pragma: no cover
            log.error("Failed to init orchestrator: %s", exc)
            return False

    # -- commands -----------------------------------------------------------
    def cmd_info(self, _args: argparse.Namespace) -> None:
        self.banner()
        info = get_system_info()
        if self.console:
            table = Table(title="System Information", header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            for k, v in info.items():
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, indent=2, default=str)
                table.add_row(str(k), str(v))
            self.console.print(table)
        else:
            print(json.dumps(info, indent=2, default=str))

    def cmd_list_agents(self, _args: argparse.Namespace) -> None:
        agents = list_all_agents()
        if self.console:
            tree = Tree("[bold blue]Divine Agent System — Departments & Agents[/bold blue]")
            for dept_name, agent_names in agents.items():
                dept_meta = get_department_info(dept_name) or {}
                status = dept_meta.get("status", "stub")
                style = "green" if status == "implemented" else "yellow"
                branch = tree.add(f"[bold {style}]{dept_name}[/bold {style}] "
                                  f"[dim]({status}, {len(agent_names)} agents)[/dim]")
                for name in agent_names:
                    branch.add(f"[white]{name}[/white]")
            self.console.print(tree)
        else:
            for dept_name, agent_names in agents.items():
                print(f"\n{dept_name}:")
                for name in agent_names:
                    print(f"  - {name}")

    def cmd_create_agent(self, args: argparse.Namespace) -> None:
        try:
            agent = create_department_agent(args.department, args.agent)
        except Exception as exc:
            self.print(f"[red]✗ {exc}[/red]")
            return
        self.print(f"[green]✓ Created {args.agent} from {args.department}[/green]")

        caps = []
        if hasattr(agent, "get_capabilities"):
            try:
                caps = list(agent.get_capabilities())
            except Exception:                                       # pragma: no cover
                caps = []
        if not caps:
            dept = get_department_info(args.department) or {}
            caps = (dept.get("agents", {}).get(args.agent, {}) or {}).get("capabilities", [])

        if caps:
            body = "\n".join(f"• {c}" for c in caps)
            if self.console:
                self.console.print(Panel(body, title=f"{args.agent} capabilities",
                                         border_style="green"))
            else:
                print(f"\n{args.agent} capabilities:\n{body}")

    def cmd_test_agent(self, args: argparse.Namespace) -> None:
        try:
            agent = create_department_agent(args.department, args.agent)
        except Exception as exc:
            self.print(f"[red]✗ {exc}[/red]")
            return
        if not hasattr(agent, "run_tests"):
            self.print(f"[yellow]Agent {args.agent} has no run_tests() hook[/yellow]")
            return
        try:
            ok = bool(agent.run_tests())
        except Exception as exc:
            self.print(f"[red]✗ run_tests raised: {exc}[/red]")
            return
        symbol = "[green]✓[/green]" if ok else "[red]✗[/red]"
        self.print(f"{symbol} run_tests returned {ok}")

    def cmd_start_system(self, _args: argparse.Namespace) -> None:
        self.banner()
        if not self.init_orchestrator():
            return
        assert self.orchestrator is not None
        self.orchestrator.enable_quantum_processing()
        self.orchestrator.activate_consciousness_ethics()
        status = self.orchestrator.get_system_status()
        self.print("[bold blue]System started (in-process facade).[/bold blue]")
        for k, v in status.items():
            self.print(f"  • {k}: {v}")

    def cmd_start_server(self, args: argparse.Namespace) -> None:
        try:
            import uvicorn
            from orchestrator.main import build_app
        except ImportError as exc:                                  # pragma: no cover
            self.print(f"[red]✗ HTTP stack unavailable: {exc}[/red]")
            self.print("[yellow]Install with: pip install 'uvicorn[standard]' fastapi[/yellow]")
            return
        host = args.host or "0.0.0.0"
        port = args.port or 8000
        self.print(f"[blue]Starting FastAPI on {host}:{port}[/blue]")
        uvicorn.run(build_app(), host=host, port=port, log_level="info")

    def cmd_config(self, args: argparse.Namespace) -> None:
        if args.show:
            dumped = yaml.dump(self.config, default_flow_style=False, sort_keys=False)
            if self.console:
                self.console.print(Panel(Syntax(dumped, "yaml"),
                                         title="Current configuration",
                                         border_style="blue"))
            else:
                print(dumped)
        elif args.set:
            key, value = args.set
            cur: Any = self.config
            parts = key.split(".")
            for p in parts[:-1]:
                cur = cur.setdefault(p, {})
            cur[parts[-1]] = value
            self.print(f"[green]✓ {key} = {value}[/green]")

    def cmd_monitor(self, args: argparse.Namespace) -> None:
        interval = max(int(args.interval or 5), 1)
        self.print(f"[dim]Refreshing every {interval}s — Ctrl-C to stop[/dim]")
        try:
            while True:
                os.system("clear" if os.name == "posix" else "cls")
                now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                self.banner()
                self.print(f"[dim]{now}[/dim]")
                info = get_system_info()
                if self.console:
                    t = Table(title="Departments")
                    t.add_column("Name", style="cyan")
                    t.add_column("Status", style="green")
                    t.add_column("Agents", justify="right")
                    for n, d in info["departments"].items():
                        t.add_row(n, d.get("status", "?"), str(len(d.get("agents", []))))
                    self.console.print(t)
                else:
                    for n, d in info["departments"].items():
                        print(f"  {n}: {d.get('status')} ({len(d.get('agents', []))})")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.print("\n[yellow]Monitor stopped.[/yellow]")

    def cmd_deploy(self, args: argparse.Namespace) -> None:
        try:
            from deploy import DivineDeploymentOrchestrator  # type: ignore[import-not-found]
        except Exception as exc:                                    # pragma: no cover
            self.print(f"[red]✗ deploy module unavailable: {exc}[/red]")
            return
        orch = DivineDeploymentOrchestrator()
        self.print(f"[yellow]Deploying to {args.target}…[/yellow]")
        result = orch.deploy(target=args.target, dry_run=args.dry_run) \
            if hasattr(orch, "deploy") else {"status": "noop"}
        self.print(f"[green]✓ Deployment result: {result}[/green]")


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------
def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sao",
        description="Divine Agent System — Supreme Agentic Orchestrator CLI",
    )
    parser.add_argument("--config", "-c", help="Path to a YAML config file")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--version", action="version",
                        version=f"sao {_SAO_VERSION}")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("info", help="Display system information")
    sub.add_parser("list-agents", help="List all departments and agents")

    p_create = sub.add_parser("create-agent", help="Instantiate an agent")
    p_create.add_argument("department")
    p_create.add_argument("agent")

    p_test = sub.add_parser("test-agent", help="Run an agent's run_tests() hook")
    p_test.add_argument("department")
    p_test.add_argument("agent")

    sub.add_parser("start-system", help="Bring up the in-process orchestrator")

    p_server = sub.add_parser("start-server", help="Start the FastAPI server")
    p_server.add_argument("--host", default="0.0.0.0")
    p_server.add_argument("--port", type=int, default=8000)
    p_server.add_argument("--environment",
                          choices=["development", "staging", "production"],
                          default="development")

    p_cfg = sub.add_parser("config", help="Show or mutate the YAML config")
    group = p_cfg.add_mutually_exclusive_group(required=True)
    group.add_argument("--show", action="store_true")
    group.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"))

    p_mon = sub.add_parser("monitor", help="Live status table")
    p_mon.add_argument("--interval", type=int, default=5)

    p_dep = sub.add_parser("deploy", help="Run deploy.py")
    p_dep.add_argument("target", choices=["development", "staging", "production"])
    p_dep.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: Optional[list] = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else
              logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )

    cli = DivineAgentCLI()
    cli.load_config(args.config)

    handler = {
        "info":         cli.cmd_info,
        "list-agents":  cli.cmd_list_agents,
        "create-agent": cli.cmd_create_agent,
        "test-agent":   cli.cmd_test_agent,
        "start-system": cli.cmd_start_system,
        "start-server": cli.cmd_start_server,
        "config":       cli.cmd_config,
        "monitor":      cli.cmd_monitor,
        "deploy":       cli.cmd_deploy,
    }.get(args.command)

    if handler is None:
        cli.banner()
        parser.print_help()
        return
    handler(args)


if __name__ == "__main__":
    main()
