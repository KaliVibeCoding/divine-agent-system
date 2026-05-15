#!/usr/bin/env python3
"""
Divine Agent System — packaging metadata.

Note: this file is kept for tools that still drive ``python setup.py``;
modern installs use the same ``requirements.txt`` and the file paths above.
A ``pyproject.toml`` is the right long-term home, but the project's
established workflow already uses setup.py + requirements.txt.
"""

from __future__ import annotations

import sys
from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent

# ----------------------------------------------------------------------
# Long description
# ----------------------------------------------------------------------
LONG_DESCRIPTION = (ROOT / "README.md").read_text(encoding="utf-8") \
    if (ROOT / "README.md").exists() else ""


# ----------------------------------------------------------------------
# Requirements
# ----------------------------------------------------------------------
def _read_requirements() -> list[str]:
    """Parse requirements.txt while ignoring comments, blank lines, and
    anything that's actually a stdlib module."""
    req_path = ROOT / "requirements.txt"
    if not req_path.exists():
        return []

    STDLIB = {
        "asyncio", "os", "sys", "pathlib", "uuid", "statistics",
        "math", "random", "concurrent.futures", "multiprocessing",
        "threading", "sqlite3", "json", "logging", "datetime",
    }
    requirements: list[str] = []
    for raw in req_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # PEP 508 marker support — keep the whole line, only strip extras for name lookup
        pkg = (
            line.split(";", 1)[0]   # drop env marker
                .split(">=", 1)[0]
                .split("==", 1)[0]
                .split("<", 1)[0]
                .split(">", 1)[0]
                .split("[", 1)[0]
                .strip()
        )
        if pkg.lower() in STDLIB:
            continue
        requirements.append(line)
    return requirements


# ----------------------------------------------------------------------
# Package metadata
# ----------------------------------------------------------------------
VERSION = "2.0.0"
AUTHOR = "KaliVibeCoding"
AUTHOR_EMAIL = "contact@kalivibecoding.com"
DESCRIPTION = "Supreme Agentic Orchestrator (SAO) — multi-agent system on LangGraph + MCP"
URL = "https://github.com/KaliVibeCoding/divine-agent-system"
PYTHON_REQUIRES = ">=3.10"

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Distributed Computing",
    "Topic :: System :: Monitoring",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Framework :: AsyncIO",
    "Framework :: FastAPI",
]

EXTRAS_REQUIRE: dict[str, list[str]] = {
    "dev": [
        "pytest>=8.3.0",
        "pytest-asyncio>=0.25.0",
        "pytest-cov>=6.0.0",
        "pytest-mock>=3.14.0",
        "ruff>=0.8.0",
        "black>=24.10.0",
        "mypy>=1.13.0",
    ],
    "quantum": [
        "qiskit>=1.3.0",
        "qiskit-aer>=0.15.0",
        "qiskit-ibm-runtime>=0.34.0",
        "cirq>=1.4.0",
        "pennylane>=0.39.0",
    ],
    "ml": [
        "scikit-learn>=1.6.0",
        "torch>=2.5.0",
        "transformers>=4.46.0",
    ],
    "cloud-aws":   ["boto3>=1.36.0"],
    "cloud-azure": ["azure-identity>=1.19.0", "azure-storage-blob>=12.24.0"],
    "cloud-gcp":   ["google-cloud-storage>=2.19.0"],
    "monitoring":  ["prometheus-client>=0.21.0",
                    "opentelemetry-api>=1.29.0",
                    "opentelemetry-sdk>=1.29.0",
                    "opentelemetry-exporter-otlp>=1.29.0"],
    "messaging":   ["redis>=5.2.0", "aiokafka>=0.12.0", "pika>=1.3.2"],
}
EXTRAS_REQUIRE["all"] = sorted({pkg for group in EXTRAS_REQUIRE.values() for pkg in group})

ENTRY_POINTS = {
    "console_scripts": [
        "sao=agents.cli:main",
        "divine-agent=agents.cli:main",
        "supreme-orchestrator=agents.cli:main",
    ],
}


def _check_python_version() -> None:
    if sys.version_info < (3, 10):
        sys.stderr.write(
            f"Divine Agent System requires Python 3.10+ (current: {sys.version}).\n"
        )
        sys.exit(1)


def main() -> None:
    _check_python_version()
    setup(
        name="divine-agent-system",
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        url=URL,
        project_urls={
            "Source":        URL,
            "Bug Reports":  f"{URL}/issues",
            "Documentation": f"{URL}#readme",
        },
        packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
        include_package_data=True,
        classifiers=CLASSIFIERS,
        python_requires=PYTHON_REQUIRES,
        install_requires=_read_requirements(),
        extras_require=EXTRAS_REQUIRE,
        entry_points=ENTRY_POINTS,
        license="MIT",
        platforms=["any"],
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
