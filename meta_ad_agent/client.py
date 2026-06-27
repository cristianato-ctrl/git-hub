"""Cliente fino para a Meta Graph / Marketing API usando apenas requests."""

from __future__ import annotations

from typing import Any, Iterator

import requests

from .config import Config

GRAPH_BASE = "https://graph.facebook.com"


class MetaApiError(RuntimeError):
    """Erro retornado pela Graph API, com a mensagem amigável já extraída."""

    def __init__(self, status: int, payload: dict[str, Any]):
        self.status = status
        self.payload = payload
        err = payload.get("error", {}) if isinstance(payload, dict) else {}
        message = err.get("error_user_msg") or err.get("message") or str(payload)
        code = err.get("code")
        subcode = err.get("error_subcode")
        detail = f" (code={code}, subcode={subcode})" if code else ""
        super().__init__(f"Meta API {status}: {message}{detail}")


class MetaClient:
    """Wrapper mínimo: GET/POST com tratamento de erro e paginação."""

    def __init__(self, config: Config, *, timeout: int = 30):
        self.config = config
        self.timeout = timeout
        self._base = f"{GRAPH_BASE}/{config.api_version}"
        self._session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self._base}/{path.lstrip('/')}"

    def _check(self, resp: requests.Response) -> dict[str, Any]:
        try:
            data = resp.json()
        except ValueError:
            resp.raise_for_status()
            return {}
        if not resp.ok or (isinstance(data, dict) and "error" in data):
            raise MetaApiError(resp.status_code, data)
        return data

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = dict(params or {})
        params.setdefault("access_token", self.config.access_token)
        resp = self._session.get(self._url(path), params=params, timeout=self.timeout)
        return self._check(resp)

    def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        data = dict(data or {})
        data.setdefault("access_token", self.config.access_token)
        resp = self._session.post(self._url(path), data=data, timeout=self.timeout)
        return self._check(resp)

    def paginate(
        self, path: str, params: dict[str, Any] | None = None, *, max_items: int | None = None
    ) -> Iterator[dict[str, Any]]:
        """Itera por todos os itens de um endpoint paginado (segue paging.next)."""
        params = dict(params or {})
        params.setdefault("access_token", self.config.access_token)
        url = self._url(path)
        count = 0
        while url:
            resp = self._session.get(url, params=params, timeout=self.timeout)
            data = self._check(resp)
            for item in data.get("data", []):
                yield item
                count += 1
                if max_items is not None and count >= max_items:
                    return
            url = data.get("paging", {}).get("next")
            params = {}  # a URL "next" já traz todos os parâmetros embutidos
