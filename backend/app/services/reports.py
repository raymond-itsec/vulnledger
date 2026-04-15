"""Report generation service — PDF (WeasyPrint), CSV, and JSON exports."""

import csv
import io
import json
from datetime import datetime

import mistune
from weasyprint import HTML

from app.models.finding import Finding
from app.models.review_session import ReviewSession

RISK_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}

RISK_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#d97706",
    "low": "#2563eb",
    "informational": "#6b7280",
}

STATUS_LABELS = {
    "open": "Open",
    "in_progress": "In Progress",
    "resolved": "Resolved",
    "accepted_risk": "Accepted Risk",
    "false_positive": "False Positive",
}


def _sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: RISK_ORDER.get(f.risk_level, 99))


def _render_md(text: str | None) -> str:
    if not text:
        return ""
    return mistune.html(text)


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def generate_json(session: ReviewSession, findings: list[Finding]) -> bytes:
    findings = _sort_findings(findings)
    data = {
        "report_generated_at": datetime.utcnow().isoformat(),
        "session": {
            "session_id": str(session.session_id),
            "review_name": session.review_name,
            "review_date": str(session.review_date),
            "reviewer": session.reviewer.full_name if session.reviewer else None,
            "status": session.status,
            "notes": session.notes,
        },
        "asset": {
            "asset_id": str(session.asset.asset_id) if session.asset else None,
            "asset_name": session.asset.asset_name if session.asset else None,
            "asset_type": session.asset.asset_type if session.asset else None,
        },
        "summary": {
            "total_findings": len(findings),
            "by_risk_level": {},
            "by_status": {},
        },
        "findings": [],
    }

    for f in findings:
        data["summary"]["by_risk_level"][f.risk_level] = (
            data["summary"]["by_risk_level"].get(f.risk_level, 0) + 1
        )
        data["summary"]["by_status"][f.remediation_status] = (
            data["summary"]["by_status"].get(f.remediation_status, 0) + 1
        )
        data["findings"].append({
            "finding_id": str(f.finding_id),
            "title": f.title,
            "risk_level": f.risk_level,
            "remediation_status": f.remediation_status,
            "description": f.description,
            "impact": f.impact,
            "recommendation": f.recommendation,
            "references": f.references or [],
            "created_at": f.created_at.isoformat() if f.created_at else None,
        })

    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def generate_csv(session: ReviewSession, findings: list[Finding]) -> bytes:
    findings = _sort_findings(findings)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Finding ID", "Title", "Risk Level", "Remediation Status",
        "Description", "Impact", "Recommendation", "References", "Created At",
    ])
    for f in findings:
        writer.writerow([
            str(f.finding_id),
            f.title,
            f.risk_level,
            f.remediation_status,
            f.description,
            f.impact or "",
            f.recommendation or "",
            "; ".join(f.references) if f.references else "",
            f.created_at.isoformat() if f.created_at else "",
        ])
    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

_PDF_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 11px; color: #1a1a1a; line-height: 1.5; }
h1 { font-size: 22px; margin-bottom: 4px; color: #1a1a2e; }
h2 { font-size: 16px; margin-top: 24px; margin-bottom: 8px; color: #1a1a2e; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; }
h3 { font-size: 13px; margin-top: 16px; margin-bottom: 4px; }
.meta { color: #6b7280; font-size: 10px; margin-bottom: 16px; }
.summary-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
.summary-table th, .summary-table td { border: 1px solid #e2e8f0; padding: 6px 10px; text-align: left; font-size: 11px; }
.summary-table th { background: #f8fafc; font-weight: 600; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; color: white; font-size: 10px; font-weight: 600; }
.finding { page-break-inside: avoid; margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; }
.finding-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.finding-title { font-size: 14px; font-weight: 600; margin: 0; }
.section-label { font-size: 10px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 10px; margin-bottom: 4px; }
.content { font-size: 11px; }
.content p { margin: 0 0 6px 0; }
.content code { background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 10px; }
.content pre { background: #f1f5f9; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 10px; }
.ref-list { margin: 0; padding-left: 16px; font-size: 10px; }
.ref-list li { margin-bottom: 2px; }
.cover-info { margin-bottom: 20px; }
.cover-info dt { font-weight: 600; color: #6b7280; font-size: 10px; float: left; width: 120px; clear: left; }
.cover-info dd { margin-left: 130px; margin-bottom: 4px; }
"""


def generate_pdf(session: ReviewSession, findings: list[Finding]) -> bytes:
    findings = _sort_findings(findings)

    # Build summary counts
    risk_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for f in findings:
        risk_counts[f.risk_level] = risk_counts.get(f.risk_level, 0) + 1
        status_counts[f.remediation_status] = status_counts.get(f.remediation_status, 0) + 1

    reviewer_name = session.reviewer.full_name if session.reviewer else "N/A"
    asset_name = session.asset.asset_name if session.asset else "N/A"

    # Summary table rows
    summary_rows = ""
    for level in ["critical", "high", "medium", "low", "informational"]:
        count = risk_counts.get(level, 0)
        if count > 0:
            color = RISK_COLORS[level]
            summary_rows += f'<tr><td><span class="badge" style="background:{color};">{level.upper()}</span></td><td>{count}</td></tr>'

    status_rows = ""
    for st, label in STATUS_LABELS.items():
        count = status_counts.get(st, 0)
        if count > 0:
            status_rows += f"<tr><td>{label}</td><td>{count}</td></tr>"

    # Finding cards
    finding_cards = ""
    for i, f in enumerate(findings, 1):
        color = RISK_COLORS.get(f.risk_level, "#6b7280")
        status_label = STATUS_LABELS.get(f.remediation_status, f.remediation_status)

        desc_html = _render_md(f.description)
        impact_html = _render_md(f.impact)
        rec_html = _render_md(f.recommendation)

        refs_html = ""
        if f.references:
            refs_items = "".join(
                f"<li>{r}</li>" for r in f.references
            )
            refs_html = f'<div class="section-label">References</div><ul class="ref-list">{refs_items}</ul>'

        impact_section = f'<div class="section-label">Impact</div><div class="content">{impact_html}</div>' if impact_html else ""
        rec_section = f'<div class="section-label">Recommendation</div><div class="content">{rec_html}</div>' if rec_html else ""

        finding_cards += f"""
        <div class="finding">
            <div class="finding-header">
                <p class="finding-title">{i}. {f.title}</p>
                <span class="badge" style="background:{color};">{f.risk_level.upper()}</span>
            </div>
            <div style="font-size:10px;color:#6b7280;margin-bottom:8px;">
                Status: {status_label}
            </div>
            <div class="section-label">Description</div>
            <div class="content">{desc_html}</div>
            {impact_section}
            {rec_section}
            {refs_html}
        </div>
        """

    notes_section = ""
    if session.notes:
        notes_html = _render_md(session.notes)
        notes_section = f'<h2>Session Notes</h2><div class="content">{notes_html}</div>'

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{_PDF_CSS}</style></head>
<body>
    <h1>Security Code Review Report</h1>
    <p class="meta">Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>

    <dl class="cover-info">
        <dt>Review Name</dt><dd>{session.review_name}</dd>
        <dt>Review Date</dt><dd>{session.review_date}</dd>
        <dt>Reviewer</dt><dd>{reviewer_name}</dd>
        <dt>Asset</dt><dd>{asset_name}</dd>
        <dt>Status</dt><dd>{session.status.replace('_', ' ').title()}</dd>
    </dl>

    <h2>Executive Summary</h2>
    <p>This report contains <strong>{len(findings)}</strong> finding(s) from the security code review.</p>

    <table class="summary-table">
        <thead><tr><th>Risk Level</th><th>Count</th></tr></thead>
        <tbody>{summary_rows if summary_rows else '<tr><td colspan="2">No findings</td></tr>'}</tbody>
    </table>

    <table class="summary-table">
        <thead><tr><th>Remediation Status</th><th>Count</th></tr></thead>
        <tbody>{status_rows if status_rows else '<tr><td colspan="2">No findings</td></tr>'}</tbody>
    </table>

    {notes_section}

    <h2>Detailed Findings</h2>
    {finding_cards if finding_cards else '<p>No findings recorded for this session.</p>'}
</body>
</html>"""

    return HTML(string=html_content).write_pdf()
