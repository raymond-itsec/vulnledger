# VulnLedger

[![CodeQL](https://github.com/raymond-itsec/vulnledger/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/raymond-itsec/vulnledger/actions/workflows/github-code-scanning/codeql)
[![Dependabot Updates](https://github.com/raymond-itsec/vulnledger/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/raymond-itsec/vulnledger/actions/workflows/dependabot/dependabot-updates)
[![Security Audits](https://github.com/raymond-itsec/vulnledger/actions/workflows/security-audit.yml/badge.svg)](https://github.com/raymond-itsec/vulnledger/actions/workflows/security-audit.yml)
[![Semgrep](https://github.com/raymond-itsec/vulnledger/actions/workflows/semgrep.yml/badge.svg)](https://github.com/raymond-itsec/vulnledger/actions/workflows/semgrep.yml)

A self-hosted security review platform for tracking vulnerability findings, managing review sessions, and producing client-ready reports.

**Fully self-hostable. No US Cloud Act dependencies. Your data stays yours.**

## Documentation

📖 **[Read the docs →](https://raymond-itsec.github.io/vulnledger/)**

- [Quickstart](https://raymond-itsec.github.io/vulnledger/quickstart/) - get a local instance running in 5 minutes
- [Architecture](https://raymond-itsec.github.io/vulnledger/architecture/) - design, request flow, data model
- [Deployment](https://raymond-itsec.github.io/vulnledger/deployment/) - single-server and multi-host options
- [Security](https://raymond-itsec.github.io/vulnledger/security/) - security model end to end

## Changelog

📋 **[CHANGELOG.md](CHANGELOG.md)** - release notes for every version.

## Wishlist & contributors wanted

VulnLedger is in active development. **I'm looking for testers** - security professionals or teams running real reviews who'd like to try it on actual workloads and tell me what's missing or broken. Setup takes ~15 minutes via Docker Compose; I'll help with any deploy questions.

Open ideas I'd love help on, in rough priority order:

1. **Scanner-import plugins** - anything that lets users pull existing scanner output into VulnLedger as findings. Burp Suite, OWASP ZAP, Nessus, Nuclei, Nmap, Trivy, Semgrep, CodeQL, dependency scanners, generic SARIF importer. **Sample exports from any scanner are very welcome at [support@vulnledger.app](mailto:support@vulnledger.app)** - the import plugin only needs to be as good as the test fixtures, and real-world exports are the test fixtures.
2. **Export connectors** - pushing findings into the systems developers already work in: Jira, GitLab Issues, GitHub Issues, Mattermost, Rocket.Chat.
3. **SBOM ingestion** - CycloneDX and SPDX, so a review can pin to the actual software inventory of the asset.
4. **Branded PDF reports** - letting consultancies and internal teams swap logo, colors, and report layout per Customer.
5. **Webhook outputs** - emit finding lifecycle events to whatever automation an operator already runs.
6. **Localization** - Dutch, German, French to start; community-translatable strings file. EU-first language coverage.

If anything on this list speaks to you, open a draft PR or an issue describing the shape of what you're thinking. **Sample exports, real-world workflow notes, and pain-point reports are at least as valuable as code.**

## Sponsor this project

❤️ Support development via the **Sponsor** button at the top of this repository, or directly on [GitHub Sponsors](https://github.com/sponsors/raymond-itsec).

## License

See [LICENSE](LICENSE).
