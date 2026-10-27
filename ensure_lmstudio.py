"""Prepare the local LM Studio backend before starting the OCR service."""

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener


logger = logging.getLogger(__name__)


def find_lms():
    executable = shutil.which("lms")
    if executable:
        return executable
    fallback = Path.home() / ".lmstudio" / "bin" / "lms.exe"
    if fallback.is_file():
        return str(fallback)
    raise RuntimeError("LM Studio CLI not found. Install LM Studio and its lms CLI first.")


def run_lms(executable, *arguments, timeout=30, as_json=False):
    logger.info("Running lms %s", " ".join(arguments))
    try:
        result = subprocess.run(
            [executable, *arguments],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"lms {' '.join(arguments)} timed out after {timeout}s") from exc
    if result.returncode:
        raise RuntimeError(
            f"lms {' '.join(arguments)} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    if as_json:
        return json.loads(result.stdout)
    return None


def ensure_backend():
    base_url = os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234").rstrip("/")
    model = os.environ.get("LMSTUDIO_MODEL", "glm-ocr")
    model_key = os.environ.get("LMSTUDIO_MODEL_KEY", model)
    load_timeout = int(os.environ.get("LMSTUDIO_LOAD_TIMEOUT", "180"))
    if load_timeout <= 0:
        raise ValueError("LMSTUDIO_LOAD_TIMEOUT must be positive")
    endpoint = urlsplit(base_url)
    if endpoint.scheme != "http" or endpoint.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Automatic LM Studio startup requires a local HTTP endpoint")
    if endpoint.path or endpoint.query or endpoint.fragment or endpoint.username or endpoint.password:
        raise ValueError("LMSTUDIO_BASE_URL must contain only the local server origin")
    port = endpoint.port or 80
    executable = find_lms()

    # Reuse the desktop runtime when it is running; otherwise start llmster.
    status = run_lms(executable, "daemon", "status", "--json", as_json=True)
    if status.get("status") != "running":
        run_lms(executable, "daemon", "up", timeout=60)

    loaded = run_lms(executable, "ps", "--json", as_json=True)
    if not any(item.get("identifier") == model for item in loaded):
        available = run_lms(executable, "ls", "--json", as_json=True)
        if not any(item.get("modelKey") == model_key for item in available):
            raise RuntimeError(f"Model {model_key!r} is not downloaded. Download it in LM Studio first.")
        run_lms(
            executable, "load", model_key, "--identifier", model, "-y",
            timeout=load_timeout,
        )
        loaded = run_lms(executable, "ps", "--json", as_json=True)
        if not any(item.get("identifier") == model for item in loaded):
            raise RuntimeError(f"Model {model!r} is still not loaded after lms load")
    else:
        logger.info("Reusing loaded model %s", model)

    # Do not use a system HTTP proxy for a loopback health check.
    opener = build_opener(ProxyHandler({}))

    def api_ready():
        try:
            with opener.open(f"{base_url}/v1/models", timeout=3) as response:
                payload = json.load(response)
            return any(item.get("id") == model for item in payload.get("data", []))
        except (URLError, TimeoutError, ValueError, OSError):
            return False

    if not api_ready():
        run_lms(executable, "server", "start", "--port", str(port))
    deadline = time.monotonic() + 15
    while not api_ready():
        if time.monotonic() >= deadline:
            raise RuntimeError(f"LM Studio API did not expose model {model!r} at {base_url}")
        time.sleep(0.5)
    logger.info("LM Studio ready: %s (model=%s)", base_url, model)


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    try:
        # Match the OCR service's .env configuration in portable distributions.
        from config import settings

        api = urlsplit(settings.lmstudio_api_url)
        if settings.vlm_api_mode.lower() != "openai" or api.hostname not in {"localhost", "127.0.0.1", "::1"}:
            logger.info("External backend configured; automatic local startup skipped")
            return 0
        os.environ.setdefault("LMSTUDIO_MODEL", settings.lmstudio_model)
        os.environ.setdefault("LMSTUDIO_BASE_URL", f"{api.scheme}://{api.netloc}")
        ensure_backend()
    except (RuntimeError, ValueError, OSError) as exc:
        logger.error("LM Studio startup failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
