"""Email notification service using Mailjet."""

import logging
from mailjet_rest import Client as MailjetClient

from app.config import settings

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
                "Subject": subject,
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
    base = settings.app_base_url
    subject = f"Finding status changed: {finding_title}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
        <h2 style="color:#1a1a2e;">Finding Status Updated</h2>
        <p>The remediation status for a finding has been changed:</p>
        <table style="border-collapse:collapse;width:100%;margin:16px 0;">
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Finding</td><td style="padding:8px;">{finding_title}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Session</td><td style="padding:8px;">{session_name}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Previous Status</td><td style="padding:8px;">{old_status_label}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">New Status</td><td style="padding:8px;font-weight:600;color:#2563eb;">{new_status_label}</td></tr>
        </table>
        <p><a href="{base}/findings/{finding_id}" style="display:inline-block;padding:10px 20px;background:#3b82f6;color:white;text-decoration:none;border-radius:6px;">View Finding</a></p>
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
    base = settings.app_base_url
    subject = f"New {risk_level_label} finding: {finding_title}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
        <h2 style="color:#1a1a2e;">New Finding Created</h2>
        <p>A new finding has been added to review session <strong>{session_name}</strong>:</p>
        <table style="border-collapse:collapse;width:100%;margin:16px 0;">
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Title</td><td style="padding:8px;">{finding_title}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Risk Level</td><td style="padding:8px;"><span style="background:{risk_color};color:white;padding:2px 8px;border-radius:4px;font-size:12px;">{risk_level_label}</span></td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6b7280;">Session</td><td style="padding:8px;">{session_name}</td></tr>
        </table>
        <p><a href="{base}/findings/{finding_id}" style="display:inline-block;padding:10px 20px;background:#3b82f6;color:white;text-decoration:none;border-radius:6px;">View Finding</a></p>
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
    base = settings.app_base_url
    subject = f"Report ready: {session_name}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
        <h2 style="color:#1a1a2e;">Report Available</h2>
        <p>A report has been generated for session <strong>{session_name}</strong>.</p>
        <p>You can download the report in PDF, CSV, or JSON format from the session page:</p>
        <p><a href="{base}/sessions/{session_id}" style="display:inline-block;padding:10px 20px;background:#3b82f6;color:white;text-decoration:none;border-radius:6px;">View Session</a></p>
        <p style="color:#9ca3af;font-size:12px;margin-top:24px;">Security Findings Manager</p>
    </div>
    """
    return send_email(to_email, to_name, subject, html)
