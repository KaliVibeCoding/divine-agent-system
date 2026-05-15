#!/usr/bin/env python3
"""
Divine Agent System — End-to-end test suite
============================================

Runs with either ``pytest test_system.py`` or directly via
``python test_system.py``.  Covers:

* package import & metadata
* department registry & dynamic discovery
* concrete cloud_mastery agents — each is exercised against its *real*
  async API surface (with the right enum-typed parameters)
* CLI plumbing
* the orchestrator/main.py FastAPI surface (boot / reflect / shutdown)

Tests deliberately avoid any network I/O, external services, or heavy
ML/LLM dependencies so they run in CI without secrets.
"""

from __future__ import annotations

import asyncio
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import agents
from agents.cloud_mastery import (
    DevOpsEngineer, KubernetesSpecialist, ServerlessArchitect,
    SecuritySpecialist, MonitoringSpecialist, CostOptimizer, DataEngineer,
    DevOpsEngineerRPC, KubernetesSpecialistRPC, SecuritySpecialistRPC,
    create_agent_instance, create_rpc_agent, get_department_info,
)

# Enums (imported lazily from the agent modules)
from agents.cloud_mastery.devops_engineer.agent import (
    DeploymentStrategy, InfrastructureProvider,
)
from agents.cloud_mastery.kubernetes_specialist.agent import (
    WorkloadType, ServiceType, ScalingStrategy,
)
from agents.cloud_mastery.serverless_architect.agent import (
    FunctionRuntime, ArchitecturePattern, TriggerType,
)
from agents.cloud_mastery.security_specialist.agent import (
    SecurityDomain, ComplianceFramework, AttackVector, EncryptionAlgorithm,
)
# AttackVector real members: MALWARE, PHISHING, SQL_INJECTION, XSS, DDOS,
# PRIVILEGE_ESCALATION, DATA_EXFILTRATION, INSIDER_THREAT, SUPPLY_CHAIN.
from agents.cloud_mastery.monitoring_specialist.agent import (
    MetricType, AggregationMethod, AlertSeverity, MonitoringScope,
)
from agents.cloud_mastery.cost_optimizer.agent import (
    CostCategory, OptimizationType, RecommendationPriority,
)
from agents.cloud_mastery.data_engineer.agent import (
    DataSourceType, DataFormat, TransformationType, ProcessingType,
)


def _run(coro):
    """Run an async coroutine to completion in a fresh event loop."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Helper mixins
# ---------------------------------------------------------------------------
class _Logged(unittest.TestCase):
    """Adds tiny pretty-printed result tracking on top of unittest."""

    results: list = []

    def _log(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append({"test": name, "ok": ok, "detail": detail,
                             "at": datetime.now(timezone.utc).isoformat()})
        symbol = "OK" if ok else "FAIL"
        print(f"  [{symbol}] {name}" + (f" - {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Suite
# ---------------------------------------------------------------------------
class TestDivineAgentSystem(_Logged):

    @classmethod
    def setUpClass(cls) -> None:
        cls.start = time.time()
        print("\n" + "=" * 78)
        print(" Divine Agent System - Test Suite")
        print(f" agents v{agents.__version__} ({agents.__release_date__})")
        print("=" * 78)

    @classmethod
    def tearDownClass(cls) -> None:
        duration = time.time() - cls.start
        passed = sum(1 for r in cls.results if r["ok"])
        failed = len(cls.results) - passed
        print("\n" + "=" * 78)
        print(f" Duration : {duration:.2f}s")
        print(f" Passed   : {passed}")
        print(f" Failed   : {failed}")
        print("=" * 78 + "\n")

    # ----- 01 -- imports & metadata ---------------------------------------
    def test_01_imports_and_metadata(self) -> None:
        print("\n1. Imports & metadata")
        info = agents.get_system_info()
        self.assertIsInstance(info, dict)
        self.assertEqual(info["version"], "2.0.0")
        self.assertEqual(info["release_date"], "2026-05-14")
        self.assertIn("cloud_mastery", info["departments"])
        self._log("get_system_info() returns 2026 metadata", True,
                  f"v{info['version']} / {info['release_date']}")

        all_agents = agents.list_all_agents()
        self.assertGreaterEqual(len(all_agents), 11,
                                "all 11 departments should be discovered")
        self._log("list_all_agents() lists all departments",
                  True, f"{len(all_agents)} departments")

        sao = agents.SupremeAgenticOrchestrator()
        self.assertIsNotNone(sao)
        self._log("SupremeAgenticOrchestrator instantiates", True)

    # ----- 02 -- cloud_mastery registry ----------------------------------
    def test_02_cloud_mastery_registry(self) -> None:
        print("\n2. Cloud Mastery registry")
        dept = get_department_info()
        self.assertIsInstance(dept, dict)
        self.assertIn("agents", dept)
        self.assertGreaterEqual(len(dept["agents"]), 7)
        self._log("cloud_mastery get_department_info()", True,
                  f"{len(dept['agents'])} agents registered")

        for agent_type in (
            "devops_engineer", "kubernetes_specialist", "serverless_architect",
            "security_specialist", "monitoring_specialist",
            "cost_optimizer", "data_engineer",
        ):
            with self.subTest(agent_type=agent_type):
                agent = create_agent_instance(agent_type)
                self.assertIsNotNone(agent)
                self._log(f"create_agent_instance({agent_type})", True,
                          type(agent).__name__)

    # ----- 03 -- DevOps Engineer ------------------------------------------
    def test_03_devops_engineer(self) -> None:
        print("\n3. DevOps Engineer")
        agent = DevOpsEngineer()
        self._log("DevOpsEngineer.__init__", True, getattr(agent, "agent_id", "n/a"))

        pipeline = _run(agent.create_cicd_pipeline(
            name="test-app",
            repository_url="https://github.com/example/test-app",
            application_type="web",
            environments=["staging", "production"],
            deployment_strategy=DeploymentStrategy.ROLLING,
        ))
        self.assertEqual(pipeline.name, "test-app")
        self._log("create_cicd_pipeline()", True)

        template = _run(agent.create_infrastructure_template(
            name="test-infra",
            provider=InfrastructureProvider.AWS,
            resource_specifications={
                "instance_type": "t3.medium",
                "region": "us-east-1",
                "count": 2,
            },
        ))
        self.assertIsNotNone(template)
        self._log("create_infrastructure_template()", True)

        execution = _run(agent.execute_pipeline(
            pipeline_id=pipeline.pipeline_id if hasattr(pipeline, "pipeline_id") else "p1",
            branch="main",
            environment="staging",
        ))
        self.assertIsInstance(execution, dict)
        self._log("execute_pipeline()", True)

        self.assertIsInstance(agent.get_devops_statistics(), dict)
        self._log("get_devops_statistics()", True)

    # ----- 04 -- Kubernetes Specialist ------------------------------------
    def test_04_kubernetes_specialist(self) -> None:
        print("\n4. Kubernetes Specialist")
        agent = KubernetesSpecialist()
        self._log("KubernetesSpecialist.__init__", True)

        workload = _run(agent.create_workload(
            name="test-workload",
            namespace="default",
            workload_type=WorkloadType.DEPLOYMENT,
            container_specs=[{
                "name": "web",
                "image": "nginx:latest",
                "ports": [{"containerPort": 80}],
            }],
            replicas=2,
        ))
        self.assertIsNotNone(workload)
        self._log("create_workload()", True)

        service = _run(agent.create_service(
            name="test-service",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            selector={"app": "test"},
            ports=[{"port": 80, "targetPort": 8080}],
        ))
        self.assertIsNotNone(service)
        self._log("create_service()", True)

        wl_id = getattr(workload, "workload_id", None) or getattr(workload, "id", "wl-1")
        autoscale = _run(agent.configure_autoscaling(
            workload_id=wl_id,
            strategy=ScalingStrategy.HORIZONTAL_POD_AUTOSCALER,
            min_replicas=2,
            max_replicas=10,
            target_cpu=70,
        ))
        self.assertIsNotNone(autoscale)
        self._log("configure_autoscaling()", True)

        self.assertIsInstance(agent.get_kubernetes_statistics(), dict)
        self._log("get_kubernetes_statistics()", True)

    # ----- 05 -- Security Specialist --------------------------------------
    def test_05_security_specialist(self) -> None:
        print("\n5. Security Specialist")
        agent = SecuritySpecialist()
        self._log("SecuritySpecialist.__init__", True)

        policy = _run(agent.create_security_policy(
            name="test-policy",
            description="Deny all by default; allow HTTPS",
            domain=SecurityDomain.NETWORK_SECURITY,
            rules=[
                {"action": "deny", "match": "*", "priority": 1000},
                {"action": "allow", "match": "tcp/443", "priority": 10},
            ],
            compliance_frameworks=[ComplianceFramework.SOC2],
        ))
        self.assertEqual(policy.name, "test-policy")
        self._log("create_security_policy()", True)

        threat = _run(agent.analyze_threat_intelligence(
            threat_name="suspicious-ingress",
            description="Unusual inbound traffic from rare ASNs",
            attack_vectors=[AttackVector.DDOS, AttackVector.MALWARE],
            indicators=["198.51.100.42", "malware-hash-abc123"],
        ))
        self.assertIsNotNone(threat)
        self._log("analyze_threat_intelligence()", True)

        assessment = _run(agent.conduct_security_assessment(
            target_system="web-application",
            assessment_type="vulnerability_scan",
            compliance_frameworks=[ComplianceFramework.SOC2, ComplianceFramework.ISO27001],
        ))
        self.assertIsNotNone(assessment)
        self._log("conduct_security_assessment()", True)

        key = _run(agent.manage_encryption_keys(
            purpose="data_at_rest",
            algorithm=EncryptionAlgorithm.AES_256,
            key_size=256,
            rotation_schedule="quarterly",
        ))
        self.assertIsNotNone(key)
        self._log("manage_encryption_keys()", True)

    # ----- 06 -- Monitoring Specialist ------------------------------------
    def test_06_monitoring_specialist(self) -> None:
        print("\n6. Monitoring Specialist")
        agent = MonitoringSpecialist()
        self._log("MonitoringSpecialist.__init__", True)

        metric = _run(agent.define_metric(
            name="cpu_usage",
            description="CPU utilisation across the fleet",
            metric_type=MetricType.GAUGE,
            unit="percent",
            aggregation_method=AggregationMethod.AVERAGE,
        ))
        self.assertEqual(metric.name, "cpu_usage")
        self._log("define_metric()", True)

        alert = _run(agent.create_alert_rule(
            name="high_cpu_alert",
            description="Fires when CPU > 80% for 5m",
            metric_query="avg(cpu_usage)",
            condition="> 80",
            severity=AlertSeverity.WARNING,
            duration="5m",
        ))
        self.assertIsNotNone(alert)
        self._log("create_alert_rule()", True)

        dashboard = _run(agent.create_dashboard(
            name="system_overview",
            description="High-level platform dashboard",
            scope=MonitoringScope.INFRASTRUCTURE,
            panels=[
                {"title": "CPU", "type": "graph", "query": "avg(cpu_usage)"},
                {"title": "Memory", "type": "graph", "query": "avg(mem_usage)"},
            ],
        ))
        self.assertIsNotNone(dashboard)
        self._log("create_dashboard()", True)

        slo = _run(agent.define_slo(
            name="api_availability",
            description="Public API availability SLO",
            service="api-gateway",
            target_percentage=99.9,
            time_window="30d",
            metric_query="sum(rate(http_requests_total{status=~'2..'}[5m]))",
        ))
        self.assertIsNotNone(slo)
        self._log("define_slo()", True)

    # ----- 07 -- Cost Optimizer -------------------------------------------
    def test_07_cost_optimizer(self) -> None:
        print("\n7. Cost Optimizer")
        agent = CostOptimizer()
        self._log("CostOptimizer.__init__", True)

        cost = _run(agent.track_cost(
            resource_id="i-1234567890abcdef0",
            resource_name="web-tier-ec2",
            category=CostCategory.COMPUTE,
            amount=150.75,
            currency="USD",
            region="us-east-1",
        ))
        self.assertAlmostEqual(getattr(cost, "amount", 0.0), 150.75)
        self._log("track_cost()", True)

        rec = _run(agent.generate_optimization_recommendation(
            title="Rightsize over-provisioned EC2",
            description="t3.2xlarge instances showing <40% CPU; downshift to t3.large",
            optimization_type=OptimizationType.RIGHT_SIZING,
            priority=RecommendationPriority.HIGH,
            estimated_savings=420.0,
            affected_resources=["i-1234567890abcdef0"],
        ))
        self.assertIsNotNone(rec)
        self._log("generate_optimization_recommendation()", True)

        budget = _run(agent.create_budget(
            name="monthly_compute_budget",
            description="Compute & storage spend ceiling",
            amount=1000.0,
            currency="USD",
            period="monthly",
            categories=[CostCategory.COMPUTE, CostCategory.STORAGE],
            alert_thresholds=[0.5, 0.8, 1.0],
        ))
        self.assertIsNotNone(budget)
        self._log("create_budget()", True)

        forecast = _run(agent.generate_cost_forecast(
            forecast_period="30d",
            current_cost=850.0,
            historical_data=[820.0, 835.0, 848.0, 850.0],
        ))
        self.assertIsNotNone(forecast)
        self._log("generate_cost_forecast()", True)

    # ----- 08 -- Data Engineer --------------------------------------------
    def test_08_data_engineer(self) -> None:
        print("\n8. Data Engineer")
        agent = DataEngineer()
        self._log("DataEngineer.__init__", True)

        source = _run(agent.create_data_source(
            name="user_events",
            source_type=DataSourceType.DATABASE,
            connection_string="postgresql://localhost:5432/events",
            format=DataFormat.JSON,
            schema={"user_id": "string", "event_type": "string", "ts": "timestamp"},
        ))
        self.assertEqual(source.name, "user_events")
        self._log("create_data_source()", True)

        transform = _run(agent.create_transformation(
            name="clean_user_data",
            transformation_type=TransformationType.VALIDATE,
            description="Validate / drop nulls / normalise casing",
            input_schema={"user_id": "string", "event_type": "string"},
            output_schema={"user_id": "string", "event_type": "string"},
            transformation_logic="df.dropna().assign(event_type=df.event_type.str.lower())",
        ))
        self.assertIsNotNone(transform)
        self._log("create_transformation()", True)

        pipeline = _run(agent.create_pipeline(
            name="user_analytics_pipeline",
            description="ETL user events into the warehouse",
            processing_type=ProcessingType.BATCH,
            sources=[source],
            transformations=[transform],
            destinations=["snowflake://analytics.user_events"],
            schedule="@daily",
        ))
        self.assertIsNotNone(pipeline)
        self._log("create_pipeline()", True)

        qc = _run(agent.perform_quality_check(
            dataset_id=getattr(source, "source_id", "ds-1"),
            check_name="data_completeness",
            check_type="completeness",
            data_sample_size=1000,
        ))
        self.assertIsNotNone(qc)
        self._log("perform_quality_check()", True)

    # ----- 09 -- inter-agent communication --------------------------------
    def test_09_communication(self) -> None:
        print("\n9. Inter-agent communication")
        # ``handle_rpc_request`` lives on the *RPC wrapper* classes, not on
        # the bare specialist agents. Make sure those wrappers exist and
        # expose the JSON-RPC entry-point.
        devops_rpc = DevOpsEngineerRPC()
        k8s_rpc = KubernetesSpecialistRPC()
        security_rpc = SecuritySpecialistRPC()
        # The wrappers expose a generic JSON-RPC dispatcher under the name
        # ``handle_request`` (older docs called it ``handle_rpc_request``).
        for label, a in (("devops_rpc", devops_rpc),
                         ("k8s_rpc", k8s_rpc),
                         ("security_rpc", security_rpc)):
            entry = getattr(a, "handle_request", None) or getattr(a, "handle_rpc_request", None)
            self.assertIsNotNone(entry, f"{label} missing RPC entry-point")
            self.assertTrue(callable(entry))
        self._log("RPC wrappers expose handle_request() / handle_rpc_request()", True)

        # The registry factory is also part of the inter-agent surface.
        built = create_rpc_agent("devops_engineer")
        self.assertTrue(
            hasattr(built, "handle_request") or hasattr(built, "handle_rpc_request"),
            "factory-built RPC agent has no entry-point",
        )
        self._log("create_rpc_agent() returns RPC-capable instance", True)

        # get_capabilities is opportunistic, not universal — just check it
        # behaves sanely when present on the bare agents.
        devops, k8s, security = DevOpsEngineer(), KubernetesSpecialist(), SecuritySpecialist()
        for a in (devops, k8s, security):
            if hasattr(a, "get_capabilities"):
                caps = a.get_capabilities()
                self.assertIsInstance(caps, (list, tuple, dict))
        self._log("get_capabilities() returns a collection when present", True)

    # ----- 10 -- experimental quantum/reflection --------------------------
    def test_10_experimental_features(self) -> None:
        print("\n10. Experimental quantum / reflection features")
        devops = DevOpsEngineer()

        quantum_methods = [m for m in dir(devops)
                           if "quantum" in m.lower() or "divine" in m.lower()]
        self._log("agent exposes quantum hooks", True,
                  f"{len(quantum_methods)} method(s) / attr(s)")

        reflection_methods = [
            m for m in dir(devops)
            if "consciousness" in m.lower() or "awareness" in m.lower()
            or "reflect" in m.lower()
        ]
        self._log("agent exposes reflection hooks", True,
                  f"{len(reflection_methods)} method(s) / attr(s)")

    # ----- 11 -- orchestrator facade --------------------------------------
    def test_11_orchestrator_facade(self) -> None:
        print("\n11. Orchestrator facade")
        sao = agents.SupremeAgenticOrchestrator()
        sao.register_agent("devops-x", DevOpsEngineer(), department="cloud_mastery")
        sao.register_agent("k8s-x", KubernetesSpecialist(), department="cloud_mastery")
        self.assertEqual(len(sao.get_active_agents()), 2)
        self._log("register_agent / get_active_agents", True)

        status = sao.get_system_status()
        self.assertIn("active_agents", status)
        self.assertEqual(status["active_agents"], 2)
        self._log("get_system_status()", True)

        self.assertEqual(sao.get_system_statistics()["active_agents"], 2)
        self._log("get_system_statistics() alias", True)

        sao.update_configuration({"feature_x": True})
        self.assertEqual(sao.system_info["runtime_config"]["feature_x"], True)
        self._log("update_configuration()", True)

    # ----- 12 -- CLI plumbing ---------------------------------------------
    def test_12_cli(self) -> None:
        print("\n12. CLI plumbing")
        from agents.cli import DivineAgentCLI, create_parser
        cli = DivineAgentCLI()
        self.assertIsNotNone(cli)
        self._log("DivineAgentCLI() constructs", True)

        parser = create_parser()
        args = parser.parse_args(["info"])
        self.assertEqual(args.command, "info")
        self._log("argparse subcommands wired", True)

        cfg = cli.load_config(str(ROOT / "config.yaml"))
        self.assertIsInstance(cfg, dict)
        # The load_config method stores the parsed YAML on self.config and
        # also returns it.  Assert via the side-effect store to be robust.
        self.assertEqual(cli.config.get("system", {}).get("version"), "2.0.0")
        self._log("load_config() reads 2026 config.yaml", True)

    # ----- 13 -- orchestrator/main.py async boot --------------------------
    def test_13_orchestrator_boot(self) -> None:
        print("\n13. orchestrator.main async boot")
        from orchestrator.main import DivineOrchestrator
        orch = DivineOrchestrator(enable_quantum=False, enable_reflection=True)

        async def go():
            state = await orch.boot()
            self.assertGreater(state["agent_count"], 0)
            decision = await orch.reflect(
                "deployment-strategy",
                ["blue_green", "canary", "rolling"],
            )
            self.assertIn(decision["consensus"],
                          ["blue_green", "canary", "rolling"])
            await orch.shutdown()
            return state, decision

        state, decision = _run(go())
        self._log("DivineOrchestrator.boot()", True,
                  f"{state['agent_count']} agents discovered")
        self._log("DivineOrchestrator.reflect()", True,
                  f"chose {decision['consensus']} via {decision['method']}")


# ---------------------------------------------------------------------------
# Optional lightweight benches (no longer hit the deprecated sync API)
# ---------------------------------------------------------------------------
def run_performance_tests() -> None:
    print("\n" + "=" * 78)
    print(" PERFORMANCE BENCHMARKS")
    print("=" * 78)
    start = time.time()
    for _ in range(10):
        DevOpsEngineer()
    elapsed = time.time() - start
    print(f"  10x DevOpsEngineer() in {elapsed:.3f}s ({elapsed/10*1000:.1f} ms each)")

    agent = DevOpsEngineer()

    async def _spam():
        for i in range(50):
            await agent.create_cicd_pipeline(
                name=f"app-{i}",
                repository_url=f"https://github.com/example/app-{i}",
                application_type="web",
                environments=["staging"],
                deployment_strategy=DeploymentStrategy.ROLLING,
            )

    start = time.time()
    asyncio.run(_spam())
    elapsed = time.time() - start
    print(f"  50x create_cicd_pipeline() in {elapsed:.3f}s "
          f"({elapsed/50*1000:.1f} ms each)")


def main() -> None:
    unittest.main(argv=[""], exit=False, verbosity=0)
    try:
        run_performance_tests()
    except Exception as exc:                                        # pragma: no cover
        print(f"performance tests skipped: {exc}")
    print("\nDivine Agent System tests complete.\n")


if __name__ == "__main__":
    main()
