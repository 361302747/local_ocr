"""Verify local backend requests succeed despite unusable environment proxies."""
import asyncio
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lmstudio_client import LMStudioClient


class ProxyBypassTests(unittest.TestCase):
    def test_recognition_and_health_bypass_proxy_in_both_modes(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def respond(self, payload):
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                received.append(self.path)
                self.respond({"data": [{"id": "glm-ocr"}]})

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                received.append(self.path)
                self.respond({"choices": [{"message": {"content": "recognized"}}],
                              "response": "recognized"})

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        proxy_env = {name: "http://127.0.0.1:1" for name in (
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")}
        proxy_env.update(NO_PROXY="", no_proxy="")

        async def verify():
            for mode, path in (("openai", "/v1/chat/completions"), ("ollama", "/api/generate")):
                client = LMStudioClient(api_url=origin + path, timeout=2)
                client.api_mode = mode
                self.assertTrue(await client.health_check())
                result = await client.recognize_image("test-image")
                self.assertTrue(result["success"], result)
                self.assertEqual(result["text"], "recognized")

        try:
            with patch.dict(os.environ, proxy_env):
                asyncio.run(asyncio.wait_for(verify(), timeout=10))
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(received, ["/v1/models", "/v1/chat/completions", "/api/tags", "/api/generate"])


if __name__ == "__main__":
    unittest.main()
