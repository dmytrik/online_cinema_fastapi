import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings

def send_activation_email(to_email: str, activation_token: str) \
        -> None:
    try:
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD

        subject = "Activate Your Account"
        body = (f"Please click the link to activate your account: "
                f"{settings.ACTIVATION_URL}/{activation_token}")

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with (smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
              as server):
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")


def send_password_reset_email(to_email: str, reset_token: str) \
        -> None:
    try:
        sender_email = settings.EMAIL_HOST_USER
        sender_password = settings.EMAIL_HOST_PASSWORD

        subject = "Password Reset Request"
        body = (f"Please click the link to reset your password: "
                f"{settings.PASSWORD_RESET_URL}/{reset_token}")

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with (smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
              as server):
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")
