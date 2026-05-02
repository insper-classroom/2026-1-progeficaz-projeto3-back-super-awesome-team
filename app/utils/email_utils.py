import base64
import os
from email.mime.text import MIMEText

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

load_dotenv()

CLIENT_ID = str(os.getenv("CLIENT_ID"))
CLIENT_SECRET = str(os.getenv("CLIENT_SECRET"))
REFRESH_TOKEN = str(os.getenv("REFRESH_TOKEN"))
APP_URL = str(os.getenv("APP_URL", "https://adapte.com/start"))

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))

with open(os.path.join(_TEMPLATES_DIR, "adapte_logo.png"), "rb") as _f:
    _LOGO_URL = "data:image/png;base64," + base64.b64encode(_f.read()).decode()

with open(os.path.join(_TEMPLATES_DIR, "white_short_logo.png"), "rb") as _f:
    _LOGO_WHITE_URL = "data:image/png;base64," + base64.b64encode(_f.read()).decode()

with open(os.path.join(_TEMPLATES_DIR, "black_short_logo.png"), "rb") as _f:
    _LOGO_BLACK_URL = "data:image/png;base64," + base64.b64encode(_f.read()).decode()

with open(os.path.join(_TEMPLATES_DIR, "confirm_icon.png"), "rb") as _f:
    _CONFIRM_ICON_URL = "data:image/png;base64," + base64.b64encode(_f.read()).decode()


def send_welcome_email(name, to_email):
    subject = "Bem-vindo ao Adapte Finance!"
    body = _jinja_env.get_template("welcomeemail.html").render(
        name=name, app_url=APP_URL, logo_url=_LOGO_URL
    )
    return send_email(subject, body, to_email)


def send_email(subject, body, to_email):
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )

    creds.refresh(Request())

    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body, "html")
    message["to"] = to_email
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_confirm_email(name, to_email, confirm_url):
    subject = "Confirme seu email – Adapte Finance"
    body = _jinja_env.get_template("confirmemail.html").render(
        name=name,
        confirm_url=confirm_url,
        logo_url=_LOGO_URL,
        confirm_icon_url=_CONFIRM_ICON_URL,
    )
    return send_email(subject, body, to_email)


def send_reset_code_email(name, to_email, code):
    subject = "Seu código de recuperação de senha – Adapte Finance"
    body = _jinja_env.get_template("resetcodeemail.html").render(
        name=name, code=code, logo_url=_LOGO_BLACK_URL
    )
    return send_email(subject, body, to_email)
