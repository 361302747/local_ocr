"""Mount the automation project's existing signal protocol on the OCR host."""

from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sqlite3

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool


router = APIRouter()
MAX_REQUEST_BYTES = 16 * 1024 * 1024


def open_signal_database():
    root = Path(os.environ.get("GHOST_CATCHER_PROJECT_ROOT")
                or Path(__file__).resolve().parent.parent / "ghost_catcher").resolve()
    candidates = (root / "utils/signal_service.py", root / "utils/signal_service.pyc")
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        return None
    path = Path(os.environ.get("GHOST_CATCHER_SIGNAL_DATABASE")
                or root / "runtime/signal_service/state.sqlite3").resolve()
    if str(path).startswith("\\\\"):
        raise ValueError("Assistant signal database must be on the host's local disk")
    if os.name == "nt":
        import ctypes
        if ctypes.windll.kernel32.GetDriveTypeW(path.anchor) == 4:
            raise ValueError("Assistant signal database cannot use a mapped network drive")
    spec = spec_from_file_location("_ghost_catcher_signal_protocol", source)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SignalDatabase(path)


@router.post("/v1/signals")
async def signal_request(request: Request):
    broker = getattr(request.app.state, "assistant_signal_database", None)
    if broker is None:
        raise HTTPException(503, "Assistant signal service is not configured")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_REQUEST_BYTES:
            raise HTTPException(413, "Signal request too large")
        body.extend(chunk)
    try:
        payload = json.loads(body)
        operation = payload["operation"]
        arguments = payload.get("arguments", {})
        request_id = payload.get("request_id", "")
        if not isinstance(operation, str) or not isinstance(arguments, dict) or not isinstance(request_id, str):
            raise ValueError("Invalid signal request")
        result = await run_in_threadpool(broker.dispatch, operation, arguments, request_id)
    except (KeyError, TypeError, ValueError, sqlite3.Error):
        raise HTTPException(409, "Signal operation rejected") from None
    return {"result": result}
