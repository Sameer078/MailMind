from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from bs4 import BeautifulSoup
import re


SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def clean_email_body(html_body: str) -> str:
    soup = BeautifulSoup(html_body, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    cleaned = re.sub(r'[\u200b\u200c\u200d\uFEFF]', '', text)
    return cleaned

def get_gmail_service():
    if not os.path.exists('token.json'):
        flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save token for reuse
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('gmail', 'v1', credentials=creds)

def fetch_unread_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['UNREAD'], maxResults=1).execute()
    messages = results.get('messages', [])

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        mailer = next((h['value'] for h in headers if h['name'] == 'X-Mailer'), '')
        reciever = next((h['value'] for h in headers if h['name'] == 'To'), '')
        body = ""

        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in msg_data['payload']:
            body = base64.urlsafe_b64decode(msg_data['payload']['body'].get('data', '')).decode('utf-8')
        service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        emails.append({
            "mail_id" : msg['id'],
            "from": sender,
            "subject": subject,
            "timestamp": date,
            "mailer": mailer,
            "reciever": reciever,
            "body": clean_email_body(body)
        })
    return emails