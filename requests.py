"""Minimal requests-compatible shim for offline/test environments."""
from __future__ import annotations

import json as _json
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Response:
    status_code: int
    text: str
    _json_data: Any = None

    def json(self) -> Any:
        if self._json_data is not None:
            return self._json_data
        try:
            return _json.loads(self.text)
        except Exception:
            return {}


def _request(method: str, url: str, *, data: Any = None, json: Any = None, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Response:
    req_headers = dict(headers or {})
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        delim = "&" if urllib.parse.urlparse(url).query else "?"
        url = f"{url}{delim}{query}"

    payload = None
    json_payload = None
    if json is not None:
        payload = _json.dumps(json).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
        json_payload = json
    elif isinstance(data, dict):
        payload = urllib.parse.urlencode(data).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, (bytes, bytearray)):
        payload = bytes(data)

    req = urllib.request.Request(url=url, data=payload, headers=req_headers, method=method.upper())
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            status = getattr(resp, "status", 200)
    except urllib.error.HTTPError as err:
        text = err.read().decode("utf-8", errors="replace")
        status = err.code
    return Response(status_code=status, text=text, _json_data=json_payload if json_payload and status < 400 else None)


def get(url: str, **kwargs: Any) -> Response:
    return _request("GET", url, **kwargs)


def post(url: str, **kwargs: Any) -> Response:
    return _request("POST", url, **kwargs)


def put(url: str, **kwargs: Any) -> Response:
    return _request("PUT", url, **kwargs)
