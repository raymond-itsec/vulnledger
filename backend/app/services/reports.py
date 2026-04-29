"""Report generation service -- PDF (WeasyPrint), CSV, and JSON exports."""

import csv
import io
import json
from datetime import datetime

from weasyprint import HTML
from weasyprint import default_url_fetcher

from app.config import settings
from app.models.finding import Finding
from app.models.review_session import ReviewSession
from app.services.html_safety import escape_html, sanitize_hex_color, sanitize_markdown_to_html
from app.services.taxonomy import TaxonomyBundle

MAX_REPORT_OUTPUT_SIZE = settings.report_max_output_size_mb * 1024 * 1024


def _blocking_url_fetcher(url: str, *args, **kwargs):
    # Refuse every scheme except data: URIs. Prevents SSRF / external leaks
    # from user-controlled markdown that could produce <img src="..."> nodes.
    if url.startswith("data:"):
        return default_url_fetcher(url, *args, **kwargs)
    raise ValueError(f"External resources are not allowed in PDF reports: {url!r}")


class ReportLimitError(ValueError):
    pass


_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def _sort_findings(findings: list[Finding], taxonomy: TaxonomyBundle) -> list[Finding]:
    risk_order = taxonomy.order_map("risk_level")
    return sorted(findings, key=lambda finding: risk_order.get(finding.risk_level, 99))


def _render_md(text: str | None) -> str:
    return sanitize_markdown_to_html(text)


def _safe_csv_cell(value: object | None) -> str:
    text = "" if value is None else str(value)
    if text.startswith(_CSV_FORMULA_PREFIXES):
        return f"'{text}"
    return text


def _estimate_report_input_size(session: ReviewSession, findings: list[Finding]) -> int:
    total_chars = len(session.review_name) + len(session.notes or "")
    for finding in findings:
        total_chars += len(finding.title)
        total_chars += len(finding.description)
        total_chars += len(finding.impact or "")
        total_chars += len(finding.recommendation or "")
        if finding.references:
            total_chars += sum(len(reference) for reference in finding.references)
    return total_chars


def validate_report_limits(session: ReviewSession, findings: list[Finding]) -> None:
    if len(findings) > settings.report_max_findings:
        raise ReportLimitError(
            f"Report export exceeds the maximum of {settings.report_max_findings} findings."
        )

    total_chars = _estimate_report_input_size(session, findings)
    if total_chars > settings.report_max_input_chars:
        raise ReportLimitError(
            "Report export exceeds the maximum allowed rendered input size."
        )


def validate_report_output_size(data: bytes) -> None:
    if len(data) > MAX_REPORT_OUTPUT_SIZE:
        raise ReportLimitError(
            f"Report export exceeds the maximum output size of {settings.report_max_output_size_mb} MB."
        )


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def generate_json(
    session: ReviewSession, findings: list[Finding], taxonomy: TaxonomyBundle
) -> bytes:
    validate_report_limits(session, findings)
    findings = _sort_findings(findings, taxonomy)
    data = {
        "report_generated_at": datetime.utcnow().isoformat(),
        "taxonomy_version": taxonomy.version.version_number,
        "session": {
            "session_id": str(session.session_id),
            "review_name": session.review_name,
            "review_date": str(session.review_date),
            "reviewer": session.reviewer.full_name if session.reviewer else None,
            "status": session.status,
            "status_label": taxonomy.label("session_status", session.status),
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
            "risk_level_label": taxonomy.label("risk_level", f.risk_level),
            "remediation_status": f.remediation_status,
            "remediation_status_label": taxonomy.label(
                "remediation_status", f.remediation_status
            ),
            "description": f.description,
            "impact": f.impact,
            "recommendation": f.recommendation,
            "references": f.references or [],
            "created_at": f.created_at.isoformat() if f.created_at else None,
        })

    encoded = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    validate_report_output_size(encoded)
    return encoded


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def generate_csv(
    session: ReviewSession, findings: list[Finding], taxonomy: TaxonomyBundle
) -> bytes:
    validate_report_limits(session, findings)
    findings = _sort_findings(findings, taxonomy)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Finding ID", "Title", "Risk Level", "Risk Label", "Remediation Status", "Remediation Label",
        "Description", "Impact", "Recommendation", "References", "Created At",
    ])
    for f in findings:
        writer.writerow([
            _safe_csv_cell(f.finding_id),
            _safe_csv_cell(f.title),
            _safe_csv_cell(f.risk_level),
            _safe_csv_cell(taxonomy.label("risk_level", f.risk_level)),
            _safe_csv_cell(f.remediation_status),
            _safe_csv_cell(taxonomy.label("remediation_status", f.remediation_status)),
            _safe_csv_cell(f.description),
            _safe_csv_cell(f.impact or ""),
            _safe_csv_cell(f.recommendation or ""),
            _safe_csv_cell("; ".join(f.references) if f.references else ""),
            _safe_csv_cell(f.created_at.isoformat() if f.created_at else ""),
        ])
    encoded = buf.getvalue().encode("utf-8")
    validate_report_output_size(encoded)
    return encoded


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


def generate_pdf(
    session: ReviewSession, findings: list[Finding], taxonomy: TaxonomyBundle
) -> bytes:
    validate_report_limits(session, findings)
    findings = _sort_findings(findings, taxonomy)

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
    for entry in taxonomy.active_entries("risk_level"):
        count = risk_counts.get(entry.value, 0)
        if count > 0:
            color = sanitize_hex_color(entry.color)
            safe_label = escape_html(entry.label)
            summary_rows += (
                f'<tr><td><span class="badge" style="background:{color};">'
                f"{safe_label}</span></td><td>{count}</td></tr>"
            )

    status_rows = ""
    for entry in taxonomy.active_entries("remediation_status"):
        count = status_counts.get(entry.value, 0)
        if count > 0:
            status_rows += f"<tr><td>{escape_html(entry.label)}</td><td>{count}</td></tr>"

    # Finding cards
    finding_cards = ""
    for i, f in enumerate(findings, 1):
        color = sanitize_hex_color(taxonomy.color("risk_level", f.risk_level, "#6b7280"))
        risk_label = escape_html(taxonomy.label("risk_level", f.risk_level))
        status_label = escape_html(taxonomy.label("remediation_status", f.remediation_status))

        desc_html = _render_md(f.description)
        impact_html = _render_md(f.impact)
        rec_html = _render_md(f.recommendation)

        refs_html = ""
        if f.references:
            refs_items = "".join(
                f"<li>{escape_html(r)}</li>" for r in f.references
            )
            refs_html = f'<div class="section-label">References</div><ul class="ref-list">{refs_items}</ul>'

        impact_section = f'<div class="section-label">Impact</div><div class="content">{impact_html}</div>' if impact_html else ""
        rec_section = f'<div class="section-label">Recommendation</div><div class="content">{rec_html}</div>' if rec_html else ""

        finding_cards += f"""
        <div class="finding">
            <div class="finding-header">
                <p class="finding-title">{i}. {escape_html(f.title)}</p>
                <span class="badge" style="background:{color};">{risk_label}</span>
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

    safe_review_name = escape_html(session.review_name)
    safe_review_date = escape_html(session.review_date)
    safe_reviewer_name = escape_html(reviewer_name)
    safe_asset_name = escape_html(asset_name)
    safe_session_status = escape_html(taxonomy.label("session_status", session.status))
    safe_taxonomy_version = escape_html(taxonomy.version.version_number)

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{_PDF_CSS}</style></head>
<body>
    <h1>Security Code Review Report</h1>
    <p class="meta">Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>

    <dl class="cover-info">
        <dt>Review Name</dt><dd>{safe_review_name}</dd>
        <dt>Review Date</dt><dd>{safe_review_date}</dd>
        <dt>Reviewer</dt><dd>{safe_reviewer_name}</dd>
        <dt>Asset</dt><dd>{safe_asset_name}</dd>
        <dt>Status</dt><dd>{safe_session_status}</dd>
        <dt>Taxonomy Version</dt><dd>v{safe_taxonomy_version}</dd>
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

    pdf = HTML(string=html_content, url_fetcher=_blocking_url_fetcher).write_pdf()
    validate_report_output_size(pdf)
    return pdf
