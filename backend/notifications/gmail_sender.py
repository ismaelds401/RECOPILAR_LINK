"""Minimal Gmail SMTP adapter using a Google app password."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr


class GmailSender:
    def __init__(
        self,
        *,
        sender_email: str,
        app_password: str,
        host: str = "smtp.gmail.com",
        port: int = 465,
        timeout: int = 30,
    ) -> None:
        self.sender_email = sender_email
        self.app_password = app_password
        self.host = host
        self.port = port
        self.timeout = timeout

    def send(
        self, *, recipient: str, subject: str, plain_body: str, html_body: str
    ) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr(("TechEvents Perú", self.sender_email))
        message["To"] = recipient
        message.set_content(plain_body)
        message.add_alternative(html_body, subtype="html")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            self.host, self.port, timeout=self.timeout, context=context
        ) as smtp:
            smtp.login(self.sender_email, self.app_password)
            smtp.send_message(message)

