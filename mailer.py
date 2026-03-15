"""
Email sender — sends the digest via Gmail SMTP (free).
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta


def _markdown_to_html(md: str) -> str:
    """Minimal Markdown→HTML for email rendering."""
    import re
    html = md
    # Headers
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    # Links  [text](url)
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)
    # List items
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    # Wrap consecutive <li> in <ul>
    html = re.sub(r"((?:<li>.*?</li>\n?)+)", r"<ul>\1</ul>", html)
    # Line breaks
    html = html.replace("\n\n", "<br><br>")
    return html


def send_digest(digest_md: str) -> None:
    """Send the digest email via Gmail SMTP."""
    smtp_email = os.environ["SMTP_EMAIL"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT_EMAIL", smtp_email)

    london_tz = timezone(timedelta(hours=0))  # UTC≈London (DST handled by cron)
    today = datetime.now(london_tz).strftime("%Y-%m-%d")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📋 每日信息简报 — {today}"
    msg["From"] = smtp_email
    msg["To"] = recipient

    # Plain text fallback
    msg.attach(MIMEText(digest_md, "plain", "utf-8"))

    # HTML version
    html_body = f"""
    <html>
    <head>
    <style>
        body {{ font-family: -apple-system, 'Segoe UI', sans-serif; line-height: 1.7;
               max-width: 700px; margin: 0 auto; padding: 20px; color: #333; }}
        h2 {{ color: #1a1a1a; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }}
        h3 {{ color: #444; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        li {{ margin-bottom: 10px; }}
        ul {{ padding-left: 20px; }}
    </style>
    </head>
    <body>
    {_markdown_to_html(digest_md)}
    <hr>
    <p style="color:#999;font-size:12px;">
        由 AI Digest 自动生成 · 信息仅供参考 · {today}
    </p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, [recipient], msg.as_string())

    print(f"✅ Digest sent to {recipient}")
