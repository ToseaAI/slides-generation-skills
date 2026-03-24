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
    content_type: str | None = None,
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "tosea-slides-skill/0.1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    if content_type:
        headers["Content-Type"] = content_type
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
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        content_type = "application/json"
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
            content_type=content_type,
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
