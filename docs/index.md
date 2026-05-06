# VulnLedger

A self-hosted web application for managing security code review findings. Built for security consultants and teams who need to track clients, reviewed assets, code review sessions, and individual findings - with full edit history, report generation, and email notifications.

**Fully self-hostable. No US Cloud Act dependencies. Your data stays yours.**

## Features

### Core
- **Client Management** - Track clients with contact details and linked assets
- **Asset Tracking** - Catalog reviewed assets (web apps, APIs, mobile apps, infrastructure, etc.)
- **Review Sessions** - Organize findings per engagement with reviewer assignment and status tracking
- **Finding Management** - Full CRUD with risk levels (critical → informational), remediation statuses, markdown-rich descriptions, and file attachments
- **Change History** - Per-field audit trail on every finding edit (who changed what, when)
- **File Attachments** - Upload screenshots, evidence, and documents (stored in SeaweedFS S3-compatible object storage)

### Templates
- **25 Built-in Finding Templates** - Covering OWASP Top 10 categories: injection, authentication, access control, cryptography, misconfiguration, and more
- **Custom Templates** - Create, edit, and delete your own finding templates
- **YAML-based Sync** - Built-in templates managed via YAML files, idempotent sync on startup

### Reporting & Notifications
- **PDF Reports** - Professional, styled security review reports with executive summary, risk breakdown, and detailed findings (WeasyPrint)
- **CSV Export** - Spreadsheet-friendly export of all findings per session
- **JSON Export** - Structured data export for integration with other tools
- **Stored Export History** - Generated PDF/CSV/JSON exports are recorded per session with export date, file name, creator, and later download access
- **Email Notifications** - Via Mailjet: new finding alerts, status change notifications, report-ready notifications

### Dashboard
- **Risk Level Breakdown** - Visual bar charts of findings by severity
- **Status Breakdown** - At-a-glance remediation progress
- **Quick Actions** - One-click access to create clients, findings
- **Recent Activity** - Latest sessions and findings

### Security & Operations
- **JWT Authentication** - Access tokens (5 min) + HttpOnly refresh token cookies (7 days)
- **Role-Based Access Control** - Admin, Reviewer, Client User roles with data isolation
- **Versioned Taxonomies** - DB-managed risk, remediation, session-status, and asset-type taxonomies with explicit active versions
- **Availability Banner** - Shared top-of-page outage notice for backend, proxy, database-startup, or local network failures that should not be treated as normal per-request UI errors
- **Rate Limiting** - Brute-force protection on login, configurable API limits
- **Security Headers** - CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Optional OIDC SSO** - Integrate with any OpenID Connect provider (Keycloak, Authentik, Zitadel, etc.)
- **Virus Scanning** - ClamAV integration scans every file upload before storage and blocks uploads whenever the scanner is disabled, unreachable, or unhealthy
- **Automated Backups** - Scheduled PostgreSQL dumps with configurable retention

## Where to next

- New here? Start with the **[Quickstart](quickstart.md)** to get a local instance running in five minutes.
- Curious how it's built? Read the **[Architecture](architecture.md)** for the design decisions, request flow, and data model.
- Going to production? See **[Deployment](deployment.md)** for single-server and multi-host options.
- Day-two operator? **[Operations](operations.md)** covers backups, monitoring, upgrades, and templates.
- Need a specific knob? **[Configuration](configuration.md)** lists every environment variable.
- Concerned about security? The **[Security](security.md)** page documents the security model end to end.
- Building integrations? **[API Reference](api.md)** lists every endpoint.

## License

See the [LICENSE](https://github.com/raymond-itsec/vulnledger/blob/main/LICENSE) file in the repository.
