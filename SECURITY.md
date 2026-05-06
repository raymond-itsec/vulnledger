# Security Policy

VulnLedger is a pentest tracking and code review security platform. We take vulnerability reports
in our own software seriously and aim to handle them responsibly under
a coordinated-disclosure model.

## Reporting a Vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**
Public issues are visible to everyone, including potential attackers,
before a fix is available.

### Preferred channel: GitHub Security Advisories

Use GitHub's private vulnerability reporting form on this repository:

1. Open the **Security** tab on the repository
2. Click **Report a vulnerability**
3. Fill in the report - include reproduction steps, affected versions,
 and any proposed mitigations

This routes directly to the maintainers without exposing the issue
publicly. We can collaborate on the fix privately before disclosure.

### Email fallback

If you cannot use GitHub Security Advisories, email:

**support@vulnledger.app**

Use plaintext for initial contact; we will reply with a secure channel
for sensitive details if needed.

## What to Include

To help us triage and reproduce quickly:

- Affected version (commit SHA or tag if known)
- Deployment context (self-hosted version, dev / staging / production)
- Reproduction steps with concrete inputs
- Observed vs. expected behavior
- Logs, screenshots, or proof-of-concept code, sanitized of real
 user data
- Suggested fix or mitigation, if you have one
- Whether you intend to publish disclosure later, and on what timeline

## Response Timeline

We aim for:

- **48 hours** - initial acknowledgment of your report
- **7 days** - preliminary assessment with a severity estimate (CVSS 3.1
 or qualitative low/medium/high/critical)
- **30 days** - a fix or coordinated mitigation plan for high and
 critical issues; longer for low/medium where appropriate

If a vulnerability is being actively exploited in the wild, we will
prioritize an emergency patch ahead of these targets.

## Coordinated Disclosure

We follow a coordinated-disclosure model:

1. You report privately
2. We confirm and develop a fix
3. We agree on a public disclosure date with you (typically up to
 90 days from the initial report, sooner if we have a fix ready)
4. We release the patch and publish a security advisory crediting you,
 with your permission

If we cannot reach agreement on disclosure timing, you are free to
publish independently after 90 days from the initial report - please
give us a chance to coordinate first.

## Scope

In scope:

- This repository's code: backend (FastAPI/Python), frontend
 (SvelteKit), edge proxy (Caddy), database schema and migrations
- The default Docker Compose deployment configuration
- Authentication, session management, and authorization logic
- Data handling: input validation, output encoding, encryption at rest
 and in transit
- Supply-chain integrity of dependencies we explicitly pin

Out of scope:

- Third-party services VulnLedger optionally integrates with - report
 those to the respective vendors
- Self-hosted deployments that have been substantially modified from
 the default stack; please report against what we ship, not your
 downstream modifications
- Issues requiring physical access to the host running VulnLedger
- Social engineering attacks against operators
- Denial of service via exhausting host resources at the infrastructure
 layer (network, disk, memory) where we don't control the underlying
 capacity
- Vulnerabilities in development-mode configurations explicitly
 documented as insecure (e.g., plain HTTP localhost setups)
- Findings already tracked publicly in `docs/SECURITY-FINDINGS.md`

## Recognition

We're happy to credit reporters in published advisories. Tell us when
reporting whether you'd like:

- Public credit by name and, optionally, link to your profile/blog
- Anonymous "external researcher" attribution
- No credit at all

## Bugs, UX issues, feature requests

For findings that are not security vulnerabilities, please use the
public Issues tab on this repository instead.

---

Last updated: 2026-04-30
