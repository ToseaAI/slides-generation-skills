from __future__ import annotations

import argparse
import json
import mimetypes
import os
import socket
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://tosea.ai"
DEFAULT_TIMEOUT_SECONDS = 180
MCP_PREFIX = "/api/mcp/v1"
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
SKILL_CLIENT_NAME = os.getenv("TOSEA_CLIENT_NAME", "tosea-slides-skill")
SKILL_CLIENT_VERSION = os.getenv("TOSEA_CLIENT_VERSION", "0.1.0")
SKILL_CLIENT_SESSION_ID = os.getenv("TOSEA_CLIENT_SESSION_ID") or str(uuid.uuid4())
SKILL_INVOCATION_ID = os.getenv("TOSEA_INVOCATION_ID") or str(uuid.uuid4())


@dataclass
class ApiError(Exception):
    message: str
    status_code: int | None = None
    detail: Any = None
    response_body: str | None = None
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "message": self.message,
            "status_code": self.status_code,
            "path": self.path,
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        if self.response_body:
            payload["response_body"] = self.response_body
        return payload


def normalize_base_url(value: str | None = None) -> str:
    base_url = (value or os.getenv("TOSEA_API_BASE_URL") or DEFAULT_BASE_URL).strip()
    base_url = base_url.rstrip("/")
    for suffix in ("/api/mcp/v1", "/api/v1", "/api"):
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)]
            break
    return base_url


def build_api_url(path: str, base_url: str | None = None) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{normalize_base_url(base_url)}{MCP_PREFIX}{normalized_path}"


def resolve_api_key(cli_value: str | None = None, *, required: bool = True) -> str | None:
    api_key = cli_value or os.getenv("TOSEA_API_KEY")
    if required and not api_key:
        raise ApiError(
            "Missing API key. Set TOSEA_API_KEY or pass --api-key.",
            detail={"error": "missing_api_key"},
        )
    return api_key


def new_idempotency_key(prefix: str | None = None) -> str:
    if not prefix:
        return str(uuid.uuid4())
    normalized = prefix.strip().lower().replace("_", "-").replace(" ", "-")
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch == "-").strip("-")
    normalized = normalized[:24]
    if not normalized:
        return str(uuid.uuid4())
    return f"{normalized}-{uuid.uuid4()}"


def _windows_unicode_path_guidance(raw_path: str) -> dict[str, Any]:
    return {
        "error": "invalid_windows_path",
        "raw_path": raw_path,
        "hint": (
            "The local path appears to have been mangled before Python received it. "
            "On Windows/OpenClaw, prefer a UTF-8 manifest file via --manifest or copy "
            "the source file to an ASCII-only staging path such as C:\\tosea-inputs\\source.pdf."
        ),
        "recommended_manifest_shape": {
            "files": [
                r"C:\tosea-inputs\source.pdf",
                r"C:\tosea-inputs\source.docx",
            ]
        },
    }


def _raise_local_path_error(raw_path: str, exc: Exception) -> ApiError:
    winerror = getattr(exc, "winerror", None)
    if os.name == "nt" and (winerror == 123 or "?" in raw_path or "\ufffd" in raw_path):
        return ApiError(
            message="Invalid Windows file path. The shell or host likely mangled a non-ASCII path.",
            detail=_windows_unicode_path_guidance(raw_path),
            path="local_file_path",
        )
    return ApiError(
        message=f"Failed to access local file path: {raw_path}",
        detail={
            "error": "local_file_access_failed",
            "raw_path": raw_path,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        },
        path="local_file_path",
    )


def coerce_local_file_path(file_path: str | Path) -> Path:
    raw_path = str(file_path).strip().strip('"')
    if not raw_path:
        raise ApiError(
            message="Empty local file path",
            detail={"error": "empty_local_file_path"},
            path="local_file_path",
        )
    if os.name == "nt" and ("?" in raw_path or "\ufffd" in raw_path):
        raise ApiError(
            message="Invalid Windows file path. The shell or host likely mangled a non-ASCII path.",
            detail=_windows_unicode_path_guidance(raw_path),
            path="local_file_path",
        )
    try:
        path = Path(raw_path).expanduser().resolve(strict=False)
    except OSError as exc:
        raise _raise_local_path_error(raw_path, exc) from exc

    try:
        if not path.exists():
            raise ApiError(
                message=f"Local file not found: {path}",
                detail={
                    "error": "local_file_not_found",
                    "raw_path": raw_path,
                    "resolved_path": str(path),
                },
                path="local_file_path",
            )
    except ApiError:
        raise
    except OSError as exc:
        raise _raise_local_path_error(raw_path, exc) from exc

    if not path.is_file():
        raise ApiError(
            message=f"Local path is not a file: {path}",
            detail={
                "error": "local_path_not_file",
                "raw_path": raw_path,
                "resolved_path": str(path),
            },
            path="local_file_path",
        )
    return path


def load_source_manifest(manifest_path: str | None) -> tuple[list[str], list[str]]:
    if manifest_path is None:
        return [], []

    manifest = coerce_local_file_path(manifest_path)
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ApiError(
            message="Manifest file must be UTF-8 encoded JSON.",
            detail={
                "error": "manifest_not_utf8",
                "manifest_path": str(manifest),
            },
            path="source_manifest",
        ) from exc
    except json.JSONDecodeError as exc:
        raise ApiError(
            message=f"Manifest file contains invalid JSON: {exc.msg}",
            detail={
                "error": "invalid_manifest_json",
                "manifest_path": str(manifest),
                "line": exc.lineno,
                "column": exc.colno,
            },
            path="source_manifest",
        ) from exc

    if isinstance(payload, list):
        files = payload
        file_ids: list[str] = []
    elif isinstance(payload, dict):
        files = payload.get("files") or payload.get("paths") or []
        file_ids = payload.get("file_ids") or []
    else:
        raise ApiError(
            message="Manifest JSON must be either a list of file paths or an object with files/file_ids.",
            detail={
                "error": "invalid_manifest_shape",
                "manifest_path": str(manifest),
            },
            path="source_manifest",
        )

    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        raise ApiError(
            message="Manifest field 'files' must be a list of strings.",
            detail={
                "error": "invalid_manifest_files",
                "manifest_path": str(manifest),
            },
            path="source_manifest",
        )
    if not isinstance(file_ids, list) or not all(isinstance(item, str) for item in file_ids):
        raise ApiError(
            message="Manifest field 'file_ids' must be a list of strings.",
            detail={
                "error": "invalid_manifest_file_ids",
                "manifest_path": str(manifest),
            },
            path="source_manifest",
        )
    return files, file_ids


def parse_json_argument(raw: str | None, *, default: Any = None) -> Any:
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ApiError(
            f"Invalid JSON argument: {exc.msg}",
            detail={"error": "invalid_json_argument", "raw": raw},
        ) from exc


def parse_int_list(raw: str | None) -> list[int] | None:
    if raw is None or not raw.strip():
        return None
    items = []
    for chunk in raw.split(","):
        piece = chunk.strip()
        if not piece:
            continue
        try:
            items.append(int(piece))
        except ValueError as exc:
            raise ApiError(
                f"Invalid integer list item: {piece}",
                detail={"error": "invalid_int_list", "raw": raw},
            ) from exc
    return items or None


def read_text_file(path: str | None) -> str | None:
    if path is None:
        return None
    return Path(path).read_text(encoding="utf-8")


def maybe_base64_from_path(path: str | None) -> str | None:
    if path is None:
        return None
    import base64

    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def emit_json(payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    sys.stdout.flush()


def emit_error(error: Exception, *, idempotency_key: str | None = None) -> int:
    if isinstance(error, ApiError):
        payload: dict[str, Any] = {"ok": False, "error": error.to_dict()}
        message = error.message
    else:
        payload = {"ok": False, "error": {"message": str(error), "type": type(error).__name__}}
        message = str(error)
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    emit_json(payload)
    print(message, file=sys.stderr)
    return 1


def run_cli(main_func) -> int:
    try:
        payload = main_func()
    except Exception as exc:  # pragma: no cover - thin CLI wrapper
        return emit_error(exc)
    if payload is not None:
        emit_json(payload)
    return 0


def _parse_response_body(body_text: str) -> Any:
    if not body_text:
        return None
    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        return None


def _build_headers(
    *,
    api_key: str | None,
    idempotency_key: str | None,
    operation_name: str | None = None,
    content_type: str | None = None,
    presentation_id: str | None = None,
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "tosea-slides-skill/0.1.0",
        "X-Tosea-Client-Channel": "skill",
        "X-Tosea-Client-Name": SKILL_CLIENT_NAME,
        "X-Tosea-Client-Version": SKILL_CLIENT_VERSION,
        "X-Tosea-Client-Session-ID": SKILL_CLIENT_SESSION_ID,
        "X-Tosea-Invocation-ID": SKILL_INVOCATION_ID,
        "X-Tosea-Operation-Name": operation_name or "skill_request",
    }
    client_trace_id = os.getenv("TOSEA_CLIENT_TRACE_ID")
    if client_trace_id:
        headers["X-Tosea-Client-Trace-ID"] = client_trace_id
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    if content_type:
        headers["Content-Type"] = content_type
    if presentation_id:
        headers["X-Presentation-ID"] = presentation_id
    return headers


def _encode_multipart(
    *,
    form_fields: dict[str, str] | None,
    file_fields: list[tuple[str, Path]] | None,
) -> tuple[bytes, str]:
    boundary = f"----tosea-skill-{uuid.uuid4().hex}"
    body = bytearray()

    def write_bytes(chunk: bytes) -> None:
        body.extend(chunk)

    for name, value in (form_fields or {}).items():
        write_bytes(f"--{boundary}\r\n".encode("utf-8"))
        write_bytes(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
        )
        write_bytes(str(value).encode("utf-8"))
        write_bytes(b"\r\n")

    for name, path in file_fields or []:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        write_bytes(f"--{boundary}\r\n".encode("utf-8"))
        write_bytes(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{path.name}"\r\n'
            ).encode("utf-8")
        )
        write_bytes(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        write_bytes(path.read_bytes())
        write_bytes(b"\r\n")

    write_bytes(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def request_json(
    method: str,
    path: str,
    *,
    api_key: str | None = None,
    query: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    form_fields: dict[str, str] | None = None,
    file_fields: list[tuple[str, Path]] | None = None,
    idempotency_key: str | None = None,
    operation_name: str | None = None,
    base_url: str | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    url = build_api_url(path, base_url=base_url)
    if query:
        clean_query = {
            key: value
            for key, value in query.items()
            if value is not None and value != ""
        }
        if clean_query:
            url = f"{url}?{urlencode(clean_query)}"

    data: bytes | None = None
    content_type: str | None = None
    presentation_id: str | None = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        content_type = "application/json"
        raw_presentation_id = json_body.get("presentation_id")
        if isinstance(raw_presentation_id, str) and raw_presentation_id.strip():
            presentation_id = raw_presentation_id.strip()
    elif form_fields is not None or file_fields is not None:
        data, content_type = _encode_multipart(
            form_fields=form_fields,
            file_fields=file_fields,
        )

    request = Request(
        url,
        data=data,
        headers=_build_headers(
            api_key=api_key,
            idempotency_key=idempotency_key,
            operation_name=operation_name or _derive_operation_name(method, path),
            content_type=content_type,
            presentation_id=presentation_id,
        ),
        method=method.upper(),
    )

    try:
        with urlopen(
            request,
            timeout=timeout_seconds or int(os.getenv("TOSEA_API_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
        ) as response:
            raw_body = response.read().decode("utf-8", errors="replace")
            parsed = _parse_response_body(raw_body)
            if isinstance(parsed, dict):
                return parsed
            return {
                "success": True,
                "message": "Non-JSON response received",
                "data": {"raw_text": raw_body},
            }
    except HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        parsed = _parse_response_body(raw_body)
        detail = parsed.get("detail") if isinstance(parsed, dict) else parsed
        message = f"HTTP {exc.code}"
        if isinstance(detail, dict):
            message = (
                detail.get("message")
                or detail.get("error")
                or detail.get("detail")
                or message
            )
        elif isinstance(detail, str):
            message = detail
        elif raw_body:
            message = raw_body
        raise ApiError(
            message=message,
            status_code=exc.code,
            detail=detail,
            response_body=raw_body,
            path=path,
        ) from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise ApiError(
            message=f"Transport error: {exc}",
            detail={"error": "transport_error", "retryable": True},
            path=path,
        ) from exc


def request_download(url: str, destination: str | Path) -> Path:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=int(os.getenv("TOSEA_API_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))) as response:
        destination_path.write_bytes(response.read())
    return destination_path


def guess_mime_type(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0]
    if mime_type:
        return mime_type
    return "application/octet-stream"


def upload_file_to_signed_url(*, signed_url: str, file_path: Path) -> None:
    request = Request(
        signed_url,
        data=file_path.read_bytes(),
        headers={
            "Content-Type": guess_mime_type(file_path),
            "User-Agent": "tosea-slides-skill/0.1.0",
        },
        method="PUT",
    )
    try:
        with urlopen(
            request,
            timeout=int(os.getenv("TOSEA_API_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
        ) as response:
            response.read()
    except HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        raise ApiError(
            message=f"Upload failed: HTTP {exc.code}",
            status_code=exc.code,
            response_body=raw_body,
            detail={"error": "upload_failed", "file": str(file_path)},
            path="signed_url_upload",
        ) from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise ApiError(
            message=f"Transport error during upload: {exc}",
            detail={"error": "transport_error", "retryable": True},
            path="signed_url_upload",
        ) from exc


def _derive_operation_name(method: str, path: str) -> str:
    normalized = path.strip().strip("/").replace("-", "_").replace("/", "_")
    normalized = normalized or "root"
    return f"{method.lower()}_{normalized}"


def request_upload_credentials(
    *,
    api_key: str,
    file_path: Path,
    base_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return request_json(
        "POST",
        "/files/upload-credentials",
        api_key=api_key,
        base_url=base_url,
        json_body={
            "filename": file_path.name,
            "file_type": file_path.suffix.lstrip(".").lower(),
            "file_size": file_path.stat().st_size,
            "metadata": metadata,
        },
    )


def confirm_uploaded_file(
    *,
    api_key: str,
    file_id: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    return request_json(
        "POST",
        "/files/confirm",
        api_key=api_key,
        base_url=base_url,
        json_body={"file_id": file_id},
    )


def upload_path_and_get_file_id(
    *,
    api_key: str,
    file_path: str | Path,
    base_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = coerce_local_file_path(file_path)
    credentials_response = request_upload_credentials(
        api_key=api_key,
        file_path=path,
        base_url=base_url,
        metadata=metadata,
    )
    credentials = credentials_response.get("data") or {}
    file_id = credentials.get("file_id")
    if not file_id:
        raise ApiError(
            message="Upload credentials response missing file_id",
            detail=credentials_response,
            path="/files/upload-credentials",
        )
    if not credentials.get("duplicate"):
        signed_url = credentials.get("signed_url")
        if not signed_url:
            raise ApiError(
                message="Upload credentials response missing signed_url",
                detail=credentials_response,
                path="/files/upload-credentials",
            )
        upload_file_to_signed_url(signed_url=signed_url, file_path=path)
    confirm_response = confirm_uploaded_file(
        api_key=api_key,
        file_id=file_id,
        base_url=base_url,
    )
    return {
        "path": str(path),
        "file_id": file_id,
        "duplicate": bool(credentials.get("duplicate")),
        "credentials": credentials_response,
        "confirm": confirm_response,
    }


def resolve_source_file_ids(
    *,
    api_key: str,
    base_url: str | None = None,
    local_files: list[str] | None = None,
    existing_file_ids: list[str] | None = None,
    manifest_path: str | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    manifest_files, manifest_file_ids = load_source_manifest(manifest_path)
    resolved_ids = list(existing_file_ids or []) + list(manifest_file_ids or [])
    upload_results: list[dict[str, Any]] = []
    for value in [*(local_files or []), *manifest_files]:
        result = upload_path_and_get_file_id(
            api_key=api_key,
            file_path=value,
            base_url=base_url,
        )
        resolved_ids.append(result["file_id"])
        upload_results.append(result)
    if not resolved_ids:
        raise ApiError(
            message="At least one --file or --file-id is required",
            detail={"error": "missing_source_files"},
        )
    return resolved_ids, upload_results


def extract_terminal_status(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    job = data.get("job")
    if isinstance(job, dict) and job.get("status"):
        return str(job["status"])
    presentation = data.get("presentation")
    if isinstance(presentation, dict) and presentation.get("status"):
        return str(presentation["status"])
    status_value = data.get("status")
    if status_value:
        return str(status_value)
    return "unknown"


def wait_for_job(
    *,
    presentation_id: str,
    api_key: str,
    base_url: str | None = None,
    interval_seconds: int = 3,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] | None = None
    while time.monotonic() <= deadline:
        last_payload = request_json(
            "GET",
            f"/jobs/{presentation_id}",
            api_key=api_key,
            base_url=base_url,
        )
        if extract_terminal_status(last_payload) in TERMINAL_STATUSES:
            return last_payload
        time.sleep(interval_seconds)
    raise ApiError(
        message="Timed out waiting for job completion",
        detail={
            "error": "job_timeout",
            "presentation_id": presentation_id,
            "last_status": extract_terminal_status(last_payload or {}),
            "retryable": True,
        },
        path=f"/jobs/{presentation_id}",
    )


def add_common_auth_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-key", default=None, help="Override TOSEA_API_KEY for this call.")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override TOSEA_API_BASE_URL for this call.",
    )


def mutation_envelope(
    *,
    path: str,
    idempotency_key: str | None,
    response: dict[str, Any],
    request_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "path": path,
        "response": response,
    }
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    if request_payload:
        payload["request"] = request_payload
    return payload
