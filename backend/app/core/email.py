import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)

_INVITE_HTML = """<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;padding:20px">
  <h2 style="color:#1e293b">You've been invited to {tenant_name}</h2>
  <p>Hi {to_name},</p>
  <p>You've been invited to join the <strong>{tenant_name}</strong> fleet management
     platform as a <strong>{role}</strong>.</p>
  <p>Click the button below to accept your invitation and set your password.
     This link expires in <strong>48 hours</strong>.</p>
  <div style="margin:28px 0;text-align:center">
    <a href="{invite_link}"
       style="background:#1e293b;color:#fff;padding:12px 28px;border-radius:6px;
              text-decoration:none;font-size:15px;font-weight:600">
      Accept Invitation
    </a>
  </div>
  <p style="font-size:13px;color:#64748b">
    If the button doesn't work, copy this link into your browser:<br>
    <a href="{invite_link}" style="color:#3b82f6">{invite_link}</a>
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0">
  <p style="font-size:12px;color:#94a3b8">
    If you didn't expect this invitation, you can safely ignore this email.
  </p>
</body>
</html>"""

_INVITE_TEXT = (
    "You've been invited to {tenant_name}\n\n"
    "Hi {to_name},\n\n"
    "You've been invited to join the {tenant_name} fleet management platform "
    "as a {role}.\n\n"
    "Accept your invitation here (expires in 48 hours):\n{invite_link}\n\n"
    "If you didn't expect this invitation, you can safely ignore this email.\n"
)

_OTP_HTML = """<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;padding:20px">
  <h2 style="color:#1e293b">Verify your email address</h2>
  <p>Hi {to_name},</p>
  <p>Use the code below to verify your email address.
     It expires in <strong>15 minutes</strong>.</p>
  <div style="margin:28px 0;text-align:center">
    <span style="font-size:36px;font-weight:700;letter-spacing:12px;color:#1e293b">
      {otp_code}
    </span>
  </div>
  <p style="font-size:13px;color:#64748b">Never share this code with anyone.</p>
</body>
</html>"""

_OTP_TEXT = (
    "Your verification code is: {otp_code}\n\n"
    "This code expires in 15 minutes. Do not share it with anyone.\n"
)


def _build_message(to_email: str, subject: str, html: str, text: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def _smtp_send(msg: MIMEMultipart) -> None:
    if settings.SMTP_PORT == 465:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT, context=ctx
        ) as srv:
            srv.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            srv.send_message(msg)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as srv:
            srv.ehlo()
            srv.starttls(context=ssl.create_default_context())
            srv.ehlo()
            srv.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            srv.send_message(msg)


def send_invitation(
    to_email: str,
    to_name: str,
    invite_link: str,
    tenant_name: str,
    role: str = "staff member",
) -> None:
    """Send a staff invitation email. Logs and returns on failure — does not raise."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured — invitation email skipped for %s", to_email
        )
        return
    try:
        html = _INVITE_HTML.format(
            to_name=to_name,
            invite_link=invite_link,
            tenant_name=tenant_name,
            role=role,
        )
        text = _INVITE_TEXT.format(
            to_name=to_name,
            invite_link=invite_link,
            tenant_name=tenant_name,
            role=role,
        )
        msg = _build_message(
            to_email,
            f"You're invited to join {tenant_name}",
            html,
            text,
        )
        _smtp_send(msg)
        logger.info("Invitation email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send invitation email to %s: %s", to_email, exc)


def send_verification(to_email: str, to_name: str, otp_code: str) -> None:
    """Send an OTP verification email. Logs and returns on failure — does not raise."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured — OTP email skipped for %s", to_email)
        return
    try:
        html = _OTP_HTML.format(to_name=to_name, otp_code=otp_code)
        text = _OTP_TEXT.format(otp_code=otp_code)
        msg = _build_message(to_email, "Your verification code", html, text)
        _smtp_send(msg)
        logger.info("OTP email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send OTP email to %s: %s", to_email, exc)
