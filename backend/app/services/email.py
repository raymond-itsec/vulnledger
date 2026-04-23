"""Email notification service using Mailjet."""

import logging
from mailjet_rest import Client as MailjetClient

from app.config import settings
from app.services.html_safety import escape_html, sanitize_header_text, sanitize_hex_color

logger = logging.getLogger(__name__)


def _get_client() -> MailjetClient | None:
    if not settings.mailjet_api_key or not settings.mailjet_api_secret:
        return None
    return MailjetClient(
        auth=(settings.mailjet_api_key, settings.mailjet_api_secret),
        version="v3.1",
    )


def send_email(to_email: str, to_name: str, subject: str, html_body: str) -> bool:
    client = _get_client()
    if not client:
        logger.warning("Mailjet not configured -- email not sent: %s", subject)
        return False

    data = {
        "Messages": [
            {
                "From": {
                    "Email": settings.mailjet_from_email,
                    "Name": settings.mailjet_from_name,
                },
                "To": [{"Email": to_email, "Name": to_name}],
                "Subject": sanitize_header_text(subject),
                "HTMLPart": html_body,
            }
        ]
    }
    try:
        result = client.send.create(data=data)
        if result.status_code == 200:
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        else:
            logger.error("Mailjet error %s: %s", result.status_code, result.json())
            return False
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


# ---------------------------------------------------------------------------
# Pre-built notification templates
# ---------------------------------------------------------------------------

def notify_finding_status_changed(
    to_email: str,
    to_name: str,
    finding_title: str,
    old_status_label: str,
    new_status_label: str,
    session_name: str,
    finding_id: str,
) -> bool:
    base = settings.app_base_url.rstrip("/")
    safe_finding_title = escape_html(finding_title)
    safe_session_name = escape_html(session_name)
    safe_old_status_label = escape_html(old_status_label)
    safe_new_status_label = escape_html(new_status_label)
    safe_href = escape_html(f"{base}/findings/{finding_id}")
    subject = f"Finding status changed: {sanitize_header_text(finding_title)}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
        <h2 style="color:#1a1a2e;">Finding Status Updated</h2>
        <p>The remediation status for a finding has been changed:</p>
        <table style="border-collapse:collapse;width:100%;margin:16px 0;">
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Finding</td><td style="padding:8px;">{safe_finding_title}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Session</td><td style="padding:8px;">{safe_session_name}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Previous Status</td><td style="padding:8px;">{safe_old_status_label}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">New Status</td><td style="padding:8px;font-weight:600;color:#2563eb;">{safe_new_status_label}</td></tr>
        </table>
        <p><a href="{safe_href}" style="display:inline-block;padding:10px 20px;background:#3b82f6;color:white;text-decoration:none;border-radius:6px;">View Finding</a></p>
        <p style="color:#9ca3af;font-size:12px;margin-top:24px;">Security Findings Manager</p>
    </div>
    """
    return send_email(to_email, to_name, subject, html)


def notify_new_finding(
    to_email: str,
    to_name: str,
    finding_title: str,
    risk_level_label: str,
    risk_color: str,
    session_name: str,
    finding_id: str,
) -> bool:
    base = settings.app_base_url.rstrip("/")
    safe_finding_title = escape_html(finding_title)
    safe_risk_level_label = escape_html(risk_level_label)
    safe_risk_color = sanitize_hex_color(risk_color)
    safe_session_name = escape_html(session_name)
    safe_href = escape_html(f"{base}/findings/{finding_id}")
    subject = (
        f"New {sanitize_header_text(risk_level_label)} finding: "
        f"{sanitize_header_text(finding_title)}"
    )
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
        <h2 style="color:#1a1a2e;">New Finding Created</h2>
        <p>A new finding has been added to review session <strong>{safe_session_name}</strong>:</p>
        <table style="border-collapse:collapse;width:100%;margin:16px 0;">
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Title</td><td style="padding:8px;">{safe_finding_title}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Risk Level</td><td style="padding:8px;"><span style="background:{safe_risk_color};color:white;padding:2px 8px;border-radius:4px;font-size:12px;">{safe_risk_level_label}</span></td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Session</td><td style="padding:8px;">{safe_session_name}</td></tr>
        </table>
        <p><a href="{safe_href}" style="display:inline-block;padding:10px 20px;background:#3b82f6;color:white;text-decoration:none;border-radius:6px;">View Finding</a></p>
        <p style="color:#9ca3af;font-size:12px;margin-top:24px;">Security Findings Manager</p>
    </div>
    """
    return send_email(to_email, to_name, subject, html)


def notify_report_ready(
    to_email: str,
    to_name: str,
    session_name: str,
    session_id: str,
) -> bool:
    base = settings.app_base_url.rstrip("/")
    safe_session_name = escape_html(session_name)
    safe_href = escape_html(f"{base}/sessions/{session_id}")
    subject = f"Report ready: {sanitize_header_text(session_name)}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
        <h2 style="color:#1a1a2e;">Report Available</h2>
        <p>A report has been generated for session <strong>{safe_session_name}</strong>.</p>
        <p>You can download the report in PDF, CSV, or JSON format from the session page:</p>
        <p><a href="{safe_href}" style="display:inline-block;padding:10px 20px;background:#3b82f6;color:white;text-decoration:none;border-radius:6px;">View Session</a></p>
        <p style="color:#9ca3af;font-size:12px;margin-top:24px;">Security Findings Manager</p>
    </div>
    """
    return send_email(to_email, to_name, subject, html)
