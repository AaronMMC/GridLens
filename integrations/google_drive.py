from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
import os
import io

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDS_FILE = "credentials/google_oauth_client.json"
TOKEN_FILE = "credentials/google_token.json"


def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if not os.path.exists(CREDS_FILE):
            raise FileNotFoundError(
                f"Google OAuth client credentials not found at {CREDS_FILE}. "
                "Create a Google Cloud project, enable the Drive API, and download "
                "the OAuth client JSON to this location."
            )
        flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def list_recent_files(service, max_results=30) -> list[dict]:
    results = service.files().list(
        q="mimeType='image/jpeg' or mimeType='image/png' or mimeType='application/pdf'",
        pageSize=max_results,
        orderBy="modifiedTime desc",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get("files", [])


def download_file(service, file_id: str, dest_path: str) -> None:
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()