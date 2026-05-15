#!/usr/bin/env python3
"""
Divine Agent System — Deployment Orchestrator
==============================================

A practical deployment driver that wraps the common targets:

    python deploy.py docker
    python deploy.py compose       --profile dev
    python deploy.py kubernetes    --namespace sao
    python deploy.py aws           --region us-east-1
    python deploy.py azure         --resource-group sao-rg
    python deploy.py gcp           --project my-project
    python deploy.py multi-cloud   --providers aws,azure,gcp

All targets respect ``--dry-run``.  When invoked programmatically from
``agents.cli`` the :class:`DivineDeploymentOrchestrator` class exposes a
single :meth:`deploy` entry-point.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

log = logging.getLogger("sao.deploy")

ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""
    duration_s: float = 0.0


@dataclass
class DeployReport:
    target: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    dry_run: bool = False
    steps: List[StepResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(s.ok for s in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "ok": self.ok,
            "dry_run": self.dry_run,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [s.__dict__ for s in self.steps],
        }


def _run(cmd: List[str], *, dry_run: bool, cwd: Optional[Path] = None) -> StepResult:
    name = " ".join(cmd)
    log.info("$ %s%s", name, "  (dry-run)" if dry_run else "")
    start = time.perf_counter()
    if dry_run:
        return StepResult(name=name, ok=True, detail="dry-run", duration_s=0.0)
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False,
        )
        duration = time.perf_counter() - start
        ok = proc.returncode == 0
        detail = (proc.stdout + proc.stderr).strip().splitlines()
        return StepResult(
            name=name, ok=ok,
            detail="\n".join(detail[-20:]),     # last 20 lines is enough context
            duration_s=round(duration, 3),
        )
    except FileNotFoundError as exc:
        return StepResult(
            name=name, ok=False,
            detail=f"binary not found on PATH: {exc}",
            duration_s=round(time.perf_counter() - start, 3),
        )


def _which(binary: str) -> Optional[str]:
    return shutil.which(binary)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class DivineDeploymentOrchestrator:
    """Deployment driver — both CLI-callable and importable."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = ROOT / config_path
        self.config = self._load_config()
        self.deployment_id = f"sao-{int(time.time())}"
        self.image_tag = self.config.get("system", {}).get("version", "2.0.0")

    # -- config -------------------------------------------------------------
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            log.warning("config.yaml not found — falling back to defaults")
            return self._defaults()
        if yaml is None:                                           # pragma: no cover
            log.warning("PyYAML not installed — using default config")
            return self._defaults()
        try:
            with self.config_path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or self._defaults()
        except Exception as exc:                                   # pragma: no cover
            log.error("Failed to parse config: %s", exc)
            return self._defaults()

    @staticmethod
    def _defaults() -> Dict[str, Any]:
        return {
            "system": {
                "name": "Divine Agent System",
                "version": "2.0.0",
                "environment": "production",
            },
            "deployment": {
                "platform": "docker",
                "replicas": 3,
                "resources": {"cpu": "1000m", "memory": "2Gi"},
            },
        }

    # -- preflight ----------------------------------------------------------
    def preflight(self) -> List[StepResult]:
        checks = []
        for tool in ("python3", "pip"):
            checks.append(StepResult(
                name=f"which {tool}",
                ok=_which(tool) is not None,
                detail=_which(tool) or "missing",
            ))
        return checks

    # -- targets ------------------------------------------------------------
    def _deploy_docker(self, report: DeployReport) -> None:
        if not _which("docker"):
            report.steps.append(StepResult("docker available", False, "docker not on PATH"))
            return
        report.steps.append(_run(
            ["docker", "build", "--target", "production",
             "-t", f"sao:{self.image_tag}", "."],
            dry_run=report.dry_run, cwd=ROOT,
        ))

    def _deploy_compose(self, report: DeployReport, profile: Optional[str]) -> None:
        if not _which("docker"):
            report.steps.append(StepResult("docker available", False, "docker not on PATH"))
            return
        cmd = ["docker", "compose"]
        if profile:
            cmd += ["--profile", profile]
        cmd += ["up", "-d", "--build"]
        report.steps.append(_run(cmd, dry_run=report.dry_run, cwd=ROOT))

    def _deploy_kubernetes(self, report: DeployReport, namespace: str) -> None:
        if not _which("kubectl"):
            report.steps.append(StepResult("kubectl available", False, "kubectl not on PATH"))
            return
        # Ensure the namespace exists (idempotent)
        report.steps.append(_run(
            ["kubectl", "create", "namespace", namespace, "--dry-run=client", "-o", "yaml"],
            dry_run=report.dry_run,
        ))
        # Apply any manifests under k8s/ if they exist
        k8s_dir = ROOT / "k8s"
        if k8s_dir.exists():
            report.steps.append(_run(
                ["kubectl", "apply", "-n", namespace, "-f", str(k8s_dir)],
                dry_run=report.dry_run,
            ))
        else:
            report.steps.append(StepResult(
                "kubectl apply k8s/", True,
                "no k8s/ directory present — skipped",
            ))

    def _deploy_aws(self, report: DeployReport, region: str) -> None:
        if not _which("aws"):
            report.steps.append(StepResult("aws-cli available", False, "aws not on PATH"))
            return
        report.steps.append(_run(
            ["aws", "sts", "get-caller-identity", "--region", region],
            dry_run=report.dry_run,
        ))
        report.steps.append(StepResult(
            "aws deploy (placeholder)", True,
            f"Would push sao:{self.image_tag} to ECR and update ECS / EKS in {region}",
        ))

    def _deploy_azure(self, report: DeployReport, resource_group: str) -> None:
        if not _which("az"):
            report.steps.append(StepResult("az-cli available", False, "az not on PATH"))
            return
        report.steps.append(_run(
            ["az", "account", "show"], dry_run=report.dry_run,
        ))
        report.steps.append(StepResult(
            "azure deploy (placeholder)", True,
            f"Would push sao:{self.image_tag} to ACR and update AKS in {resource_group}",
        ))

    def _deploy_gcp(self, report: DeployReport, project: str) -> None:
        if not _which("gcloud"):
            report.steps.append(StepResult("gcloud available", False, "gcloud not on PATH"))
            return
        report.steps.append(_run(
            ["gcloud", "config", "set", "project", project],
            dry_run=report.dry_run,
        ))
        report.steps.append(StepResult(
            "gcp deploy (placeholder)", True,
            f"Would push sao:{self.image_tag} to Artifact Registry and update GKE / Cloud Run in {project}",
        ))

    # -- public API ---------------------------------------------------------
    def deploy(
        self,
        target: str,
        *,
        dry_run: bool = False,
        profile: Optional[str] = None,
        namespace: str = "sao",
        region: str = "us-east-1",
        resource_group: str = "sao-rg",
        project: str = "sao-project",
        providers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        report = DeployReport(target=target, dry_run=dry_run)
        report.steps.extend(self.preflight())

        if target == "docker":
            self._deploy_docker(report)
        elif target == "compose":
            self._deploy_compose(report, profile)
        elif target == "kubernetes":
            self._deploy_kubernetes(report, namespace)
        elif target == "aws":
            self._deploy_aws(report, region)
        elif target == "azure":
            self._deploy_azure(report, resource_group)
        elif target == "gcp":
            self._deploy_gcp(report, project)
        elif target == "multi-cloud":
            for prov in (providers or ["aws", "azure", "gcp"]):
                getattr(self, f"_deploy_{prov}")(report, **{
                    "aws":   {"region": region},
                    "azure": {"resource_group": resource_group},
                    "gcp":   {"project": project},
                }[prov])
        else:
            report.steps.append(StepResult(
                "validate target", False, f"unknown target: {target}",
            ))

        report.finished_at = datetime.now(timezone.utc).isoformat()
        result = report.to_dict()
        log.info("Deployment finished: ok=%s target=%s steps=%d",
                 result["ok"], target, len(result["steps"]))
        return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Divine Agent System — deployment driver",
    )
    p.add_argument(
        "target",
        choices=["docker", "compose", "kubernetes",
                 "aws", "azure", "gcp", "multi-cloud"],
        help="Deployment target",
    )
    p.add_argument("--dry-run", action="store_true",
                   help="Print commands without executing them")
    p.add_argument("--profile", default=None,
                   help="Docker Compose profile (dev, quantum, …)")
    p.add_argument("--namespace", default="sao",
                   help="Kubernetes namespace")
    p.add_argument("--region", default="us-east-1",
                   help="AWS region")
    p.add_argument("--resource-group", default="sao-rg",
                   help="Azure resource group")
    p.add_argument("--project", default="sao-project",
                   help="GCP project ID")
    p.add_argument("--providers", default="aws,azure,gcp",
                   help="Comma-separated provider list for multi-cloud")
    p.add_argument("--json", action="store_true",
                   help="Emit machine-readable JSON report")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )

    orch = DivineDeploymentOrchestrator()
    result = orch.deploy(
        args.target,
        dry_run=args.dry_run,
        profile=args.profile,
        namespace=args.namespace,
        region=args.region,
        resource_group=args.resource_group,
        project=args.project,
        providers=[p.strip() for p in args.providers.split(",") if p.strip()],
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\nTarget : {result['target']}")
        print(f"Dry-run: {result['dry_run']}")
        print(f"OK     : {result['ok']}")
        print("Steps  :")
        for s in result["steps"]:
            mark = "✓" if s["ok"] else "✗"
            detail = f" — {s['detail']}" if s["detail"] else ""
            print(f"  {mark} {s['name']}{detail}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
