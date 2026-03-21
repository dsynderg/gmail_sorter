import os
from pathlib import Path
from typing import Iterable, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from connection_test import load_credentials, parse_loopback_uri, pretty_http_error

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def build_gmail_service():
    client_file = Path(os.getenv("GOOGLE_CLIENT_FILE", "client_id.json")).expanduser()
    token_file = Path(os.getenv("GOOGLE_TOKEN_PATH", "token.json")).expanduser()
    _, _, normalized_redirect_uri = parse_loopback_uri(
        os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/")
    )

    credentials = load_credentials(client_file, token_file, normalized_redirect_uri)
    return build("gmail", "v1", credentials=credentials)


def list_message_ids(user_id: str = "me", query: Optional[str] = None, max_results: int = 10):
    service = build_gmail_service()
    request = service.users().messages().list(userId=user_id, q=query, maxResults=max_results)
    response = request.execute()
    return [item["id"] for item in response.get("messages", [])]


def get_message(user_id: str, message_id: str, format: str = "full"):
    service = build_gmail_service()
    return service.users().messages().get(userId=user_id, id=message_id, format=format).execute()


def list_labels(user_id: str = "me"):
    service = build_gmail_service()
    response = service.users().labels().list(userId=user_id).execute()
    return response.get("labels", [])


def list_history(
    user_id: str = "me",
    start_history_id: Optional[str] = None,
    history_types: Optional[Iterable[str]] = None,
    max_results: int = 100,
):
    service = build_gmail_service()
    if start_history_id is None:
        profile = service.users().getProfile(userId=user_id).execute()
        start_history_id = profile.get("historyId")

    if not start_history_id:
        raise ValueError("start_history_id is required and could not be inferred from profile")

    response = (
        service.users()
        .history()
        .list(
            userId=user_id,
            startHistoryId=start_history_id,
            historyTypes=list(history_types) if history_types else None,
            maxResults=max_results,
        )
        .execute()
    )
    return response


__all__ = [
    "build_gmail_service",
    "list_message_ids",
    "get_message",
    "list_labels",
    "list_history",
    "pretty_http_error",
    "HttpError",
]
