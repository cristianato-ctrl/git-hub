"""Carrega configuração a partir de variáveis de ambiente (ou de um arquivo .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: str | os.PathLike[str] = ".env") -> None:
    """Carrega pares CHAVE=VALOR de um .env para os.environ, sem dependências externas.

    Não sobrescreve variáveis que já existem no ambiente.
    """
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# Versão padrão da Graph API. Pode ser sobrescrita por META_API_VERSION.
DEFAULT_API_VERSION = "v21.0"


@dataclass
class Config:
    """Configuração necessária para falar com a Meta Marketing API."""

    access_token: str
    ad_account_id: str          # ex.: act_1234567890  (com ou sem o prefixo "act_")
    ig_user_id: str = ""        # ID da conta profissional do Instagram (Instagram User ID)
    page_id: str = ""           # ID da Página do Facebook ligada à conta
    api_version: str = DEFAULT_API_VERSION

    @property
    def normalized_ad_account(self) -> str:
        """Garante o prefixo act_ exigido pela Marketing API."""
        acct = self.ad_account_id.strip()
        return acct if acct.startswith("act_") else f"act_{acct}"

    @classmethod
    def from_env(cls, dotenv_path: str | os.PathLike[str] = ".env") -> "Config":
        _load_dotenv(dotenv_path)

        token = os.environ.get("META_ACCESS_TOKEN", "").strip()
        ad_account = os.environ.get("META_AD_ACCOUNT_ID", "").strip()

        missing = []
        if not token:
            missing.append("META_ACCESS_TOKEN")
        if not ad_account:
            missing.append("META_AD_ACCOUNT_ID")
        if missing:
            raise SystemExit(
                "Configuração ausente: "
                + ", ".join(missing)
                + ".\nDefina essas variáveis no ambiente ou em um arquivo .env "
                "(veja .env.example)."
            )

        return cls(
            access_token=token,
            ad_account_id=ad_account,
            ig_user_id=os.environ.get("META_IG_USER_ID", "").strip(),
            page_id=os.environ.get("META_PAGE_ID", "").strip(),
            api_version=os.environ.get("META_API_VERSION", DEFAULT_API_VERSION).strip()
            or DEFAULT_API_VERSION,
        )
