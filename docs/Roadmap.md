# Roadmap

What VulnLedger looks like today, what we're building next, and where it's heading. Plain-language overview for users, contributors, and anyone evaluating the project.

## Where we are: v0.2.2 (today)

VulnLedger is a self-hosted security review platform: clients, reviewed assets, review sessions, and findings, with full edit history, file attachments, PDF/CSV/JSON exports, and email notifications. Optional SSO. Encrypted backups. ClamAV-scanned uploads.

What's solid:

- Single-server deployment via Docker Compose
- Production-shaped security: JWT with rotating refresh tokens, role-based access, edge rate limiting, hardened HTTP headers, password strength enforcement
- Visual design overhaul: pastel-glass aesthetic, design tokens, dark sidebar
- 25 built-in finding templates plus custom template support
- Documentation site you're reading now
- Active internal security audit program (findings tracked publicly with stable IDs)

What's intentionally minimal at this stage:

- One server, one database, one deployment topology
- Monitoring is liveness-only
- Backups cover the database; object storage requires manual snapshot
- No public traffic yet (zero users)

## What's next: v0.3.0 (in progress)

The headline shift is from "single host that works" to "multi-host that scales". Three themes:

### Theme 1: Production-shaped infrastructure

Move from one box to a four-host topology with proper isolation:

- **Edge** host (the public face)
- **Application** host (the workload)
- **Data** host (database and file storage)
- **Monitoring** host (observability and alerting)

Hosts are connected by an encrypted private network. The public internet only ever sees the edge. This is the architecture you'd want for any real customer-facing deployment.

A single-host mode is preserved for development and demos.

### Theme 2: Real observability

Replace today's liveness-only monitoring with a full stack: time-series metrics, structured logs, dashboards, and alerts that route to Slack. The "we didn't notice the backup container was failing for a week" class of problem becomes impossible.

Two dashboard surfaces:

- A public status page anyone can see ("are services up?")
- An internal dashboard that requires sign-in for full operational detail

### Theme 3: Polish that compounds

Smaller changes that pay off over time:

- API URL versioning (so future API changes don't break clients)
- Request tracing so debugging across services is fast
- Soft-delete pattern (so accidental deletes are recoverable and GDPR right-to-be-forgotten is supportable)
- Safe retries on creates (so a client retrying after a network blip doesn't create duplicate records)
- Container images built once in CI and deployed by digest (no per-host builds, full audit trail)
- Database column rename from internal jargon ("Clients", "ReviewSessions") to user-facing terms ("Customers", "Projects")

### What v0.3.0 is **not**

- Not a feature release in the marketing sense. The user-facing functionality stays largely the same.
- Not a smooth in-place upgrade. Going from v0.2.x to v0.3.0 means deploying fresh on the new topology and restoring from a backup. Database data restores cleanly; object storage requires a separate manual snapshot.
- Not a hosted SaaS - VulnLedger remains self-hosted only.

## Beyond v0.3.0

Items already on the radar but not in the v0.3.0 scope:

- **Workspace search** (the topbar input is currently a placeholder)
- **Per-role password length tiers** (admin / reviewer accounts at higher floor than regular users)
- **Multi-instance app tier** with PgBouncer in front of Postgres for horizontal scaling
- **Distributed tracing** (OpenTelemetry-style) for cross-service request paths
- **Backup retention tiering** (daily, weekly, monthly snapshots; off-host storage)
- **Quarterly backup restore drills** as part of operations

## What's intentionally not on the roadmap

- **Hosted SaaS offering**: VulnLedger is self-hosted. No managed cloud version is planned.
- **Mobile app**: the web app is responsive and works on mobile; a native app is not in scope.
- **Marketplace integrations** (Jira, ServiceNow, etc.): possible later via the API, not a near-term priority.
- **Real-time collaboration** (multiple reviewers editing the same finding live): not a priority for the target use case.

## How to follow along

- **GitHub Issues** filtered by `v0.3.x` label show what's in scope for the next release: <https://github.com/raymond-itsec/vulnledger/labels/v0.3.x>
- **Changelog** at the repo root documents every release
- **Security findings register** at [Security → Findings register](SECURITY-FINDINGS.md) is updated whenever a finding is raised or fixed

## Support the project

If VulnLedger is useful to you, the **Sponsor** button at the top of the GitHub repository links to GitHub Sponsors. Funds go to ongoing development and infrastructure.
