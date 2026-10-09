"""Run the local PoE 1 map-regex app with Python's standard library."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from backend.pob import BuildInputError
from backend.analysis_service import analyze_request


STATIC = Path(__file__).resolve().parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._json(200, {"ok": True})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 350_000:
                raise BuildInputError("Input is empty or too large.")
            data = json.loads(self.rfile.read(length))
            self._json(200, analyze_request(data))
        except (BuildInputError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": "Analysis failed unexpectedly. Check the terminal for details."})
            self.log_error("Analysis failed: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local build-aware PoE 1 map regex app")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
