"""Leitura de posts já publicados no Instagram (orgânicos, com legenda)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .client import MetaClient

# Campos úteis de cada mídia do Instagram.
_MEDIA_FIELDS = "id,caption,media_type,media_product_type,permalink,timestamp,thumbnail_url,media_url"


@dataclass
class InstagramPost:
    id: str
    caption: str
    media_type: str          # IMAGE, VIDEO, CAROUSEL_ALBUM
    permalink: str
    timestamp: str
    thumbnail_url: str = ""
    media_url: str = ""

    @property
    def short_caption(self) -> str:
        cap = (self.caption or "").replace("\n", " ").strip()
        return (cap[:70] + "…") if len(cap) > 70 else cap

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "InstagramPost":
        return cls(
            id=item.get("id", ""),
            caption=item.get("caption", "") or "",
            media_type=item.get("media_type", "") or "",
            permalink=item.get("permalink", "") or "",
            timestamp=item.get("timestamp", "") or "",
            thumbnail_url=item.get("thumbnail_url", "") or "",
            media_url=item.get("media_url", "") or "",
        )


def list_instagram_posts(
    client: MetaClient, ig_user_id: str, *, limit: int = 25
) -> list[InstagramPost]:
    """Lista as mídias publicadas na conta profissional do Instagram (mais recentes primeiro)."""
    if not ig_user_id:
        raise SystemExit(
            "META_IG_USER_ID não definido. Informe o ID da conta profissional do Instagram "
            "para listar os posts existentes."
        )
    items = client.paginate(
        f"{ig_user_id}/media",
        params={"fields": _MEDIA_FIELDS, "limit": min(limit, 100)},
        max_items=limit,
    )
    return [InstagramPost.from_api(it) for it in items]


def get_instagram_post(client: MetaClient, media_id: str) -> InstagramPost:
    """Busca uma única mídia do Instagram pelo seu ID."""
    data = client.get(media_id, params={"fields": _MEDIA_FIELDS})
    return InstagramPost.from_api(data)
