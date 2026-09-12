import structlog
import httpx
from apps.api.config import settings

logger = structlog.get_logger()


class EmailService:
    """
    Transactional email delivery service supporting SendGrid and local development preview.
    """

    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.email_from_address or "noreply@aicalling.com"
        self.from_name = settings.email_from_name or "AI Voice Platform"

    async def send_email(
        self, to_email: str, subject: str, html_content: str, text_content: str = ""
    ) -> bool:
        """Dispatches an email via SendGrid API or logs locally in dev mode."""
        if not self.api_key or self.api_key.startswith("SG.your-"):
            # Development / Mock Mode: Log email preview safely without crashing
            logger.info(
                "email_mock_delivered",
                to=to_email,
                subject=subject,
                from_email=self.from_email,
                preview=text_content[:120] if text_content else html_content[:120],
            )
            return True

        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_content or subject},
                {"type": "text/html", "value": html_content},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code in (200, 201, 202):
                    logger.info("email_sent_successfully", to=to_email, subject=subject)
                    return True
                logger.error("email_send_failed", status=response.status_code, body=response.text)
                return False
        except Exception as e:
            logger.error("email_send_exception", error=str(e), to=to_email)
            return False

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, reset_url: str = ""
    ) -> bool:
        """Sends a secure password reset link to the user."""
        target_url = reset_url or f"http://localhost:3000/reset-password?token={reset_token}"
        subject = "Reset Your Password - AI Voice Platform"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; rounded: 12px;">
            <h2 style="color: #4f46e5;">Reset Your Password</h2>
            <p>You requested a password reset for your account. Click the button below to choose a new password:</p>
            <p style="margin: 24px 0;">
                <a href="{target_url}" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p style="color: #64748b; font-size: 14px;">This link will expire in 15 minutes. If you did not request this, you can safely ignore this email.</p>
        </div>
        """
        text = f"You requested a password reset. Open the following link to choose a new password: {target_url}\nThis link expires in 15 minutes."
        return await self.send_email(to_email, subject, html, text)

    async def send_welcome_email(self, to_email: str, first_name: str = "") -> bool:
        """Sends a welcome email to newly registered business owners."""
        subject = "Welcome to AI Voice Platform!"
        greeting = f"Hi {first_name}," if first_name else "Hello,"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
            <h2 style="color: #4f46e5;">Welcome to AI Voice Calling!</h2>
            <p>{greeting}</p>
            <p>Your workspace is ready. You have 300 free minutes to configure your first AI voice agent and connect your phone number.</p>
            <p style="margin: 24px 0;">
                <a href="http://localhost:3000/dashboard" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Go to Your Dashboard
                </a>
            </p>
        </div>
        """
        text = f"{greeting}\nWelcome to AI Voice Platform! Your workspace is ready. Log in to start building your voice agents."
        return await self.send_email(to_email, subject, html, text)
