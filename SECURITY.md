# Security Policy

> Cinematic branding stays. Security claims are deliberately conservative
> and honest. Last refreshed: **2026-05-14** (v2.0.0 reality pass).

## Supported Versions

| Version | Status              | Notes                                              |
|---------|---------------------|----------------------------------------------------|
| 2.0.x   | Full support        | Current; security + bug fixes                      |
| 1.x.x   | End-of-life         | No further updates; upgrade to 2.0+ recommended    |

The project follows [Semantic Versioning](https://semver.org/). Security
patches are released on the latest minor of the supported major.

## Scope

### In scope
- Core agent system (`agents/`)
- Orchestrator and FastAPI surface (`orchestrator/`)
- CLI and deploy driver (`agents/cli.py`, `deploy.py`)
- Container images and Compose / Kubernetes manifests shipped in-repo
- Inter-agent transport (Redis Streams + JSON-RPC)
- Authentication and authorisation flows
- Build, CI, and release tooling (`.github/`)

### Out of scope
- Vulnerabilities in third-party dependencies (please report upstream;
  we will, of course, bump the pin once patched)
- Cloud provider infrastructure (AWS, Azure, GCP, IBM)
- Vulnerabilities introduced by user customisations
- Social engineering, physical security, denial-of-service from raw
  bandwidth saturation
- Anything labelled `experimental` (quantum sampling, reflection layer)
  unless it leaks data or escalates privileges

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

- **Email**: `security@kalivibecoding.com`
- **GitHub Security Advisories**: use the "Report a vulnerability"
  button on the repository's *Security* tab — this creates a private
  advisory and is the preferred channel for coordinated fixes.
- **Acknowledgement target**: within **48 hours** (business days).

### What to include
1. Affected component and version (`agents`, `orchestrator`, CLI, etc.)
2. Reproduction steps or proof of concept
3. Expected vs. observed behaviour
4. Suggested severity (CVSS v3.1 if you have one) and your view of impact
5. Your preferred name/handle for credit (or "anonymous")

We do **not** currently run a paid bug-bounty program. We will credit
disclosers in advisories and the release notes.

## Coordinated Disclosure Process

| Phase                 | Target time     |
|-----------------------|-----------------|
| Acknowledge receipt   | 48 hours        |
| Initial triage        | 5 business days |
| Fix in private branch | 2-4 weeks       |
| Coordinated release   | 30-90 days from initial report |
| Public advisory + CVE | Same day as fix release |

If a vulnerability is being actively exploited in the wild we will
shorten this timeline aggressively and coordinate disclosure with the
reporter.

## Security Controls

### Authentication & authorisation
- **JWT (RS256)** verified against a JWKS URL — no shared secrets
  baked into pods
- **RBAC** with department-scoped roles enforced in middleware before
  the agent dispatcher sees the request
- MFA / OAuth2 federation is supported via the deployer's preferred
  identity provider (we do not ship our own IdP)

### Cryptography
- **TLS** terminated at the ingress (`Caddy` / `Traefik` / cloud LB).
  In-cluster traffic uses mesh mTLS where available.
- **At rest**: AES-256-GCM (via the `cryptography` library) for
  application-managed secrets; cloud provider KMS for blob storage
- **Post-quantum awareness**: the `EncryptionAlgorithm` enum surfaces
  NIST FIPS-203 (ML-KEM-768, formerly Kyber) and FIPS-204 (ML-DSA-65,
  formerly Dilithium). PQC is **not yet enforced on the wire** as of
  May 2026 — the spec landed but stable, audited Python bindings are
  still maturing. Tracked for Q4 2026.

### Supply-chain
- `pip-audit` runs in CI on every PR
- `trivy` scans container images on every build
- SBOMs are produced per release (`cyclonedx-bom` format)
- Images are signed with `cosign` (keyless OIDC) starting v2.0.0

### Runtime hardening
- Containers run as non-root (UID 1000, no `--privileged`)
- Read-only root filesystem in production stage of the Dockerfile
- Network policies (Kubernetes `NetworkPolicy`) gate inter-namespace
  traffic; defaults to deny-all-ingress except `:8000`
- Secrets sourced from environment / KMS / Vault, never from `config.yaml`

## Known Sensitive Areas

These deserve extra scrutiny if you are auditing the codebase:

- `deploy.py` — invokes `kubectl` / `aws` / `az` / `gcloud` via
  `subprocess.run`. All user-supplied arguments are passed through a
  whitelist; do not allow caller-controlled flags here.
- `orchestrator.main:build_app` — the FastAPI surface; ensure any new
  endpoint enforces the same auth middleware.
- `agents/cloud_mastery/security_specialist/agent.py` —
  `manage_encryption_keys` deliberately accepts user-supplied key
  material descriptors; verify the rotation schedule on every change.
- Redis bus serialisation — JSON only, never `pickle`. Reject any PR
  that swaps the codec.

## Compliance Targets

- **SOC 2 Type II** — internal controls aligned; external audit per
  customer demand
- **ISO 27001** — control mapping documented; full certification on
  enterprise tier
- **GDPR** — data-subject-rights endpoints exposed under
  `/api/v1/privacy/*`
- **HIPAA** — covered when the deployment is configured with the
  `hipaa` profile (sets stricter audit logging + retention)
- **EU AI Act** — risk classification surfaced in `config.yaml`
  (`eu_ai_act:` block, new in 2.0.0)

## Hall of Fame

We will credit responsible disclosures here as they happen. Empty as
of the 2.0.0 release — be the first!

## References

- [OWASP Top 10 (2024)](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [NIST Cybersecurity Framework 2.0](https://www.nist.gov/cyberframework)
- [NIST FIPS-203 (ML-KEM)](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST FIPS-204 (ML-DSA)](https://csrc.nist.gov/pubs/fips/204/final)
- [CISA Secure-by-Design](https://www.cisa.gov/securebydesign)

---

**Last updated**: 2026-05-14
**Next scheduled review**: 2026-11-14
**Security contact**: `security@kalivibecoding.com`
