"""Google Drive connector (SPEC-003 §2.3). Requires extra: pip install aiboarding[gdrive]."""

from __future__ import annotations

import io
import logging
from collections.abc import Iterable
from pathlib import Path

from aiboarding.connectors.base import Connector
from aiboarding.models import SourceDocument

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

EXPORTABLE = {
    "application/vnd.google-apps.document": "text/plain",
}
DOWNLOADABLE = {"application/pdf", "text/plain", "text/markdown"}


class GDriveConnector(Connector):
    name = "gdrive"

    def __init__(self, credentials_path: str, folder_ids: list[str]):
        self.credentials_path = credentials_path
        self.folder_ids = folder_ids

    def is_configured(self) -> bool:
        if not (self.credentials_path and Path(self.credentials_path).exists() and self.folder_ids):
            return False
        try:
            import googleapiclient  # noqa: F401

            return True
        except ImportError:
            logger.warning("google-api-python-client not installed; run: pip install 'aiboarding[gdrive]'")
            return False

    def _service(self):
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)

    def fetch(self) -> Iterable[SourceDocument]:
        from googleapiclient.http import MediaIoBaseDownload

        service = self._service()
        for folder_id in self.folder_ids:
            page_token = None
            while True:
                results = (
                    service.files()
                    .list(
                        q=f"'{folder_id}' in parents and trashed=false",
                        fields="nextPageToken, files(id, name, mimeType, webViewLink)",
                        pageToken=page_token,
                    )
                    .execute()
                )
                for f in results.get("files", []):
                    content = self._extract(service, f, MediaIoBaseDownload)
                    if not content or not content.strip():
                        continue
                    yield SourceDocument.create(
                        source="gdrive",
                        title=f["name"],
                        uri=f.get("webViewLink", f"https://drive.google.com/file/d/{f['id']}"),
                        content=content,
                        mime=f["mimeType"],
                        file_id=f["id"],
                    )
                page_token = results.get("nextPageToken")
                if not page_token:
                    break

    def _extract(self, service, f: dict, downloader_cls) -> str:
        mime = f["mimeType"]
        try:
            if mime in EXPORTABLE:
                data = service.files().export(fileId=f["id"], mimeType=EXPORTABLE[mime]).execute()
                return data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
            if mime in DOWNLOADABLE:
                request = service.files().get_media(fileId=f["id"])
                buf = io.BytesIO()
                downloader = downloader_cls(buf, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                raw = buf.getvalue()
                if mime == "application/pdf":
                    from pypdf import PdfReader

                    reader = PdfReader(io.BytesIO(raw))
                    return "\n\n".join((p.extract_text() or "") for p in reader.pages)
                return raw.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Drive file %s failed: %s", f.get("name"), exc)
        return ""
