"""Criação de anúncios a partir de posts existentes do Instagram / Facebook.

Fluxo "Usar publicação existente" da Meta Marketing API:

1. Cria-se um *ad creative* que referencia a publicação que já existe, em vez de
   subir uma nova mídia.
   - Para um post do Instagram orgânico usa-se ``instagram_user_id`` +
     ``source_instagram_media_id``.
   - Para um post de Página do Facebook usa-se ``object_story_id`` no formato
     ``{page_id}_{post_id}``.
2. Cria-se o *ad* dentro do conjunto de anúncios (ad set) apontando para esse creative.
   Por segurança o anúncio nasce PAUSADO (status=PAUSED) até você revisar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .client import MetaClient
from .config import Config


@dataclass
class Campaign:
    id: str
    name: str
    status: str
    objective: str = ""


@dataclass
class AdSet:
    id: str
    name: str
    status: str
    campaign_id: str = ""


def list_campaigns(client: MetaClient, config: Config, *, limit: int = 50) -> list[Campaign]:
    items = client.paginate(
        f"{config.normalized_ad_account}/campaigns",
        params={"fields": "id,name,status,objective", "limit": min(limit, 100)},
        max_items=limit,
    )
    return [
        Campaign(
            id=i.get("id", ""),
            name=i.get("name", ""),
            status=i.get("status", ""),
            objective=i.get("objective", ""),
        )
        for i in items
    ]


def list_adsets(
    client: MetaClient, config: Config, *, campaign_id: str | None = None, limit: int = 100
) -> list[AdSet]:
    if campaign_id:
        path = f"{campaign_id}/adsets"
    else:
        path = f"{config.normalized_ad_account}/adsets"
    items = client.paginate(
        path,
        params={"fields": "id,name,status,campaign_id", "limit": min(limit, 100)},
        max_items=limit,
    )
    return [
        AdSet(
            id=i.get("id", ""),
            name=i.get("name", ""),
            status=i.get("status", ""),
            campaign_id=i.get("campaign_id", ""),
        )
        for i in items
    ]


def create_creative_from_instagram_post(
    client: MetaClient,
    config: Config,
    *,
    instagram_media_id: str,
    name: str,
) -> str:
    """Cria um ad creative que reaproveita um post existente do Instagram.

    Retorna o ID do creative criado.
    """
    if not config.ig_user_id:
        raise SystemExit(
            "META_IG_USER_ID é obrigatório para criar anúncios a partir de posts do Instagram."
        )
    payload: dict[str, Any] = {
        "name": name,
        "object_type": "SHARE",
        "instagram_user_id": config.ig_user_id,
        "source_instagram_media_id": instagram_media_id,
    }
    data = client.post(f"{config.normalized_ad_account}/adcreatives", payload)
    return data["id"]


def create_creative_from_facebook_post(
    client: MetaClient,
    config: Config,
    *,
    object_story_id: str,
    name: str,
) -> str:
    """Cria um ad creative reaproveitando um post de Página do Facebook (object_story_id)."""
    payload = {"name": name, "object_story_id": object_story_id}
    data = client.post(f"{config.normalized_ad_account}/adcreatives", payload)
    return data["id"]


def create_ad(
    client: MetaClient,
    config: Config,
    *,
    adset_id: str,
    creative_id: str,
    name: str,
    status: str = "PAUSED",
) -> str:
    """Cria o anúncio no conjunto de anúncios apontando para o creative. Retorna o ad ID."""
    payload = {
        "name": name,
        "adset_id": adset_id,
        "creative": f'{{"creative_id":"{creative_id}"}}',
        "status": status,
    }
    data = client.post(f"{config.normalized_ad_account}/ads", payload)
    return data["id"]


@dataclass
class PostAdResult:
    creative_id: str
    ad_id: str
    adset_id: str


def promote_instagram_post(
    client: MetaClient,
    config: Config,
    *,
    instagram_media_id: str,
    adset_id: str,
    ad_name: str,
    status: str = "PAUSED",
) -> PostAdResult:
    """Atalho: cria o creative a partir do post e o anúncio no conjunto, em um passo."""
    creative_id = create_creative_from_instagram_post(
        client, config, instagram_media_id=instagram_media_id, name=f"{ad_name} (creative)"
    )
    ad_id = create_ad(
        client, config, adset_id=adset_id, creative_id=creative_id, name=ad_name, status=status
    )
    return PostAdResult(creative_id=creative_id, ad_id=ad_id, adset_id=adset_id)
