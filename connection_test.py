import json
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SEPARATOR = "-" * 70


def print_section(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"{title}")
    print(SEPARATOR)


def print_item(label: str, value) -> None:
    print(f"{label:<24}: {value}")


def parse_loopback_uri(raw_uri: str):
    parsed = urlparse((raw_uri or "").strip())
    if parsed.scheme != "http":
        raise ValueError("GOOGLE_REDIRECT_URI must use http for local OAuth flow")

    host = parsed.hostname
    if host not in {"localhost", "127.0.0.1"}:
        raise ValueError("GOOGLE_REDIRECT_URI host must be localhost or 127.0.0.1")

    port = parsed.port or 8080
    return host, port, f"http://{host}:{port}/"


def build_client_config_from_file(client_file: Path, redirect_uri: str) -> dict:
    if not client_file.exists():
        raise FileNotFoundError(f"Missing OAuth client file: {client_file}")

    data = json.loads(client_file.read_text(encoding="utf-8"))
    client_block = data.get("installed") or data.get("web")
    if not client_block:
        raise ValueError("client_id.json must contain either an 'installed' or 'web' section")

    return {
        "installed": {
            "client_id": client_block["client_id"],
            "client_secret": client_block["client_secret"],
            "auth_uri": client_block.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": client_block.get("token_uri", "https://oauth2.googleapis.com/token"),
            "redirect_uris": [redirect_uri],
        }
    }


def load_credentials(client_file: Path, token_file: Path, redirect_uri: str):
    credentials = None
    if token_file.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except ValueError:
            credentials = None

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if credentials and credentials.valid:
        return credentials

    client_config = build_client_config_from_file(client_file, redirect_uri)
    flow = InstalledAppFlow.from_client_config(
        client_config,
        SCOPES,
        redirect_uri=redirect_uri,
    )
    try:
        credentials = flow.run_local_server(host=urlparse(redirect_uri).hostname, port=urlparse(redirect_uri).port, redirect_uri_trailing_slash=True)
    except OSError:
        # If the configured port is in use, use any available loopback port.
        credentials = flow.run_local_server(host=urlparse(redirect_uri).hostname, port=0, redirect_uri_trailing_slash=True)

    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def pretty_http_error(error: HttpError) -> str:
    status = getattr(error.resp, "status", "unknown")
    body = ""
    if getattr(error, "content", None):
        try:
            body = json.loads(error.content.decode("utf-8")).get("error", {})
        except Exception:
            body = error.content.decode("utf-8", errors="ignore")
    return f"status={status}, details={body}"


def test_gmail_with_client_json() -> None:
    client_file = Path(os.getenv("GOOGLE_CLIENT_FILE", "client_id.json")).expanduser()
    token_file = Path(os.getenv("GOOGLE_TOKEN_PATH", "token.json")).expanduser()
    host, port, normalized_redirect_uri = parse_loopback_uri(
        os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/")
    )
    _ = (host, port)
    user_id = os.getenv("GMAIL_USER_EMAIL", "me")

    credentials = load_credentials(client_file, token_file, normalized_redirect_uri)
    service = build("gmail", "v1", credentials=credentials)

    print_section("Gmail Connection Test")
    print_item("Auth Source", client_file)
    print_item("Token File", token_file)
    print_item("User ID", user_id)
    print_item("Scopes", ", ".join(SCOPES))

    try:
        profile = service.users().getProfile(userId=user_id).execute()
        print_section("Result")
        print("✅ PASS: Gmail API connection established")
        print_item("Authorized Gmail", profile.get("emailAddress"))
        print_item("Total Messages", profile.get("messagesTotal"))
    except HttpError as error:
        print_section("Result")
        print("❌ FAIL: Gmail API connection failed")
        print_item("Error", pretty_http_error(error))


if __name__ == "__main__":
    test_gmail_with_client_json()
