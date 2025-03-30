import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email-related environment variables
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

def send_email(subject, body, to_email):
    """Send an email using the Gmail SMTP server."""
    from_email = EMAIL_FROM
    password = EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        logging.info("Email sent successfully")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
