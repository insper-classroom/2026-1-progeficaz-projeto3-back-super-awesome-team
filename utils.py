import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


def enviar_email(subject, body, to_email):
    CLIENT_ID = "placeholder"
    CLIENT_SECRET = "placeholder"
    REFRESH_TOKEN = "placeholder"

    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )

    creds.refresh(Request())

    service = build('gmail', 'v1', credentials=creds)

    message = MIMEText(body)
    message['to'] = to_email
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()