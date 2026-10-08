"""Vercel function for importing and rating a Path of Building export."""

from http.server import BaseHTTPRequestHandler
import json

from pob import BuildInputError, build_profile, decode_build
from rules import REGEX_LIMIT, classify, make_regex


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 350_000:
                raise BuildInputError("Input is empty or too large.")
            data = json.loads(self.rfile.read(length))
            source = data.get("source", "")
            if not isinstance(source, str):
                raise BuildInputError("Paste a pobb.in link or a PoB export code.")
            profile = build_profile(decode_build(source))
            mods = classify(profile)
            self._json(200, {
                "profile": profile,
                "mods": mods,
                "presets": {preset: make_regex(mods, preset) for preset in ("safe", "balanced", "greedy")},
                "regex_limit": REGEX_LIMIT,
            })
        except (BuildInputError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": "Analysis failed unexpectedly. Please try again."})
            self.log_error("Analysis failed: %s", exc)
