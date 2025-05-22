import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.settings.sharing',
    'https://www.googleapis.com/auth/gmail.compose'
]


def get_gmail_api_service():
    """
    Authenticate and return a Gmail API service client.

    This function handles authentication using OAuth 2.0. It checks for a saved
    token file (token.json) and refreshes or recreates it if necessary using the 
    credentials in credentials.json. It returns an authorized Gmail service object 
    for making API calls.

    Returns:
        googleapiclient.discovery.Resource: An authorized Gmail API service client.

    Side Effects:
        - Reads and writes token.json in the same directory as the script.
        - Opens a local browser window for OAuth login if credentials are missing/invalid.
    """
    creds = None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(base_dir, "token.json")
    creds_path = os.path.join(base_dir, "credentials.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES
            )
            creds = flow.run_local_server(port=60141)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
    
    return build("gmail", "v1", credentials=creds)
