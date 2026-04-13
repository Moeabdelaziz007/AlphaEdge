"""Minimal aiohttp shim for async HTTP calls in offline tests."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request


class ClientError(Exception):
    pass


class ClientTimeout:
    def __init__(self, total: int = 10):
        self.total = total


class _Response:
    def __init__(self, status: int, body: str):
        self.status = status
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        try:
            return json.loads(self._body)
        except Exception:
            return {"status": "unknown", "message": self._body[:200]}

    async def text(self):
        return self._body


class ClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def _request(self, method: str, url: str, json_body=None, headers=None, timeout=None):
        headers = headers or {}
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=getattr(timeout, "total", 10)) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return _Response(getattr(resp, "status", 200), body)
        except Exception as exc:
            return _Response(503, str(exc))

    def post(self, url: str, json=None, headers=None, timeout=None):
        return self._request("POST", url, json_body=json, headers=headers, timeout=timeout)

    def get(self, url: str, headers=None, timeout=None):
        return self._request("GET", url, headers=headers, timeout=timeout)
