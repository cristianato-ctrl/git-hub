"""Interface de linha de comando do Meta Ad Agent.

Exemplos
--------
  # Listar os posts já publicados no Instagram
  python -m meta_ad_agent posts

  # Listar campanhas e conjuntos de anúncios
  python -m meta_ad_agent campaigns
  python -m meta_ad_agent adsets --campaign 123456

  # Promover um post existente como anúncio (nasce PAUSADO por segurança)
  python -m meta_ad_agent promote --post 178414... --adset 234567... --name "Anúncio - Promo X"

  # Modo interativo (escolhe post e conjunto por menu)
  python -m meta_ad_agent promote
"""

from __future__ import annotations

import argparse
import sys

from . import ads, posts
from .client import MetaApiError, MetaClient
from .config import Config


def _client() -> tuple[MetaClient, Config]:
    config = Config.from_env()
    return MetaClient(config), config


def _print_posts(items: list[posts.InstagramPost]) -> None:
    if not items:
        print("Nenhum post encontrado.")
        return
    for idx, p in enumerate(items, 1):
        print(f"[{idx}] {p.id}  {p.media_type:14}  {p.timestamp[:10]}  {p.short_caption}")


def cmd_posts(args: argparse.Namespace) -> int:
    client, config = _client()
    items = posts.list_instagram_posts(client, config.ig_user_id, limit=args.limit)
    _print_posts(items)
    return 0


def cmd_campaigns(args: argparse.Namespace) -> int:
    client, config = _client()
    items = ads.list_campaigns(client, config, limit=args.limit)
    if not items:
        print("Nenhuma campanha encontrada.")
        return 0
    for c in items:
        print(f"{c.id}  {c.status:10}  {c.objective:20}  {c.name}")
    return 0


def cmd_adsets(args: argparse.Namespace) -> int:
    client, config = _client()
    items = ads.list_adsets(client, config, campaign_id=args.campaign, limit=args.limit)
    if not items:
        print("Nenhum conjunto de anúncios encontrado.")
        return 0
    for a in items:
        print(f"{a.id}  {a.status:10}  {a.name}")
    return 0


def _pick(prompt: str, options: list[tuple[str, str]]) -> str:
    """Mostra um menu numerado e devolve o ID escolhido. options = [(id, label)]."""
    for idx, (_id, label) in enumerate(options, 1):
        print(f"  [{idx}] {label}")
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][0]
        print("Opção inválida, tente de novo.")


def cmd_promote(args: argparse.Namespace) -> int:
    client, config = _client()

    post_id = args.post
    if not post_id:
        items = posts.list_instagram_posts(client, config.ig_user_id, limit=args.limit)
        if not items:
            print("Nenhum post do Instagram para promover.")
            return 1
        print("Escolha o post do Instagram:")
        post_id = _pick(
            "Post nº: ",
            [(p.id, f"{p.short_caption or p.media_type} — {p.timestamp[:10]}") for p in items],
        )

    adset_id = args.adset
    if not adset_id:
        adsets = ads.list_adsets(client, config, campaign_id=args.campaign)
        if not adsets:
            print("Nenhum conjunto de anúncios disponível.")
            return 1
        print("Escolha o conjunto de anúncios:")
        adset_id = _pick(
            "Conjunto nº: ",
            [(a.id, f"{a.name} [{a.status}]") for a in adsets],
        )

    name = args.name or f"Anúncio do post {post_id}"
    status = "ACTIVE" if args.activate else "PAUSED"

    if not args.yes:
        print()
        print(f"  Post Instagram : {post_id}")
        print(f"  Conjunto       : {adset_id}")
        print(f"  Nome do anúncio: {name}")
        print(f"  Status inicial : {status}")
        if input("Confirmar criação do anúncio? [s/N] ").strip().lower() not in {"s", "sim", "y"}:
            print("Cancelado.")
            return 1

    result = ads.promote_instagram_post(
        client,
        config,
        instagram_media_id=post_id,
        adset_id=adset_id,
        ad_name=name,
        status=status,
    )
    print("\nAnúncio criado com sucesso:")
    print(f"  creative_id = {result.creative_id}")
    print(f"  ad_id       = {result.ad_id}")
    print(f"  status      = {status}")
    if status == "PAUSED":
        print("  (O anúncio está PAUSADO. Ative-o no Gerenciador de Anúncios quando quiser.)")
    return 0


def cmd_launch(args: argparse.Namespace) -> int:
    client, config = _client()

    post_id = args.post
    if not post_id:
        items = posts.list_instagram_posts(client, config.ig_user_id, limit=args.limit)
        if not items:
            print("Nenhum post do Instagram para promover.")
            return 1
        print("Escolha o post do Instagram:")
        post_id = _pick(
            "Post nº: ",
            [(p.id, f"{p.short_caption or p.media_type} — {p.timestamp[:10]}") for p in items],
        )

    countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    targeting = ads.build_targeting(
        countries=countries, age_min=args.age_min, age_max=args.age_max
    )
    status = "ACTIVE" if args.activate else "PAUSED"

    if not args.yes:
        print()
        print(f"  Post Instagram : {post_id}")
        print(f"  Campanha       : {args.campaign_name}  (objetivo {args.objective})")
        print(f"  Conjunto       : {args.adset_name}")
        print(f"  Orçamento/dia  : {args.daily_budget} centavos")
        print(f"  Segmentação    : {countries}, idade {args.age_min}-{args.age_max}")
        print(f"  Status inicial : {status}")
        if input("Confirmar criação? [s/N] ").strip().lower() not in {"s", "sim", "y"}:
            print("Cancelado.")
            return 1

    result = ads.launch_post_campaign(
        client,
        config,
        instagram_media_id=post_id,
        campaign_name=args.campaign_name,
        adset_name=args.adset_name,
        ad_name=args.name or f"Anúncio do post {post_id}",
        daily_budget_cents=args.daily_budget,
        objective=args.objective,
        targeting=targeting,
        optimization_goal=args.optimization_goal,
        status=status,
    )
    print("\nCampanha criada com sucesso:")
    print(f"  campaign_id = {result.campaign_id}")
    print(f"  adset_id    = {result.adset_id}")
    print(f"  creative_id = {result.creative_id}")
    print(f"  ad_id       = {result.ad_id}")
    print(f"  status      = {status}")
    if status == "PAUSED":
        print("  (Tudo PAUSADO. Ative no Gerenciador de Anúncios quando quiser.)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="meta_ad_agent",
        description="Agente que promove posts já publicados do Instagram como anúncios no Meta Ads.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_posts = sub.add_parser("posts", help="Lista posts já publicados no Instagram")
    p_posts.add_argument("--limit", type=int, default=25)
    p_posts.set_defaults(func=cmd_posts)

    p_camp = sub.add_parser("campaigns", help="Lista campanhas da conta de anúncios")
    p_camp.add_argument("--limit", type=int, default=50)
    p_camp.set_defaults(func=cmd_campaigns)

    p_as = sub.add_parser("adsets", help="Lista conjuntos de anúncios")
    p_as.add_argument("--campaign", help="Filtra por ID da campanha")
    p_as.add_argument("--limit", type=int, default=100)
    p_as.set_defaults(func=cmd_adsets)

    p_prom = sub.add_parser("promote", help="Cria um anúncio a partir de um post existente")
    p_prom.add_argument("--post", help="ID da mídia do Instagram (se omitido, abre menu)")
    p_prom.add_argument("--adset", help="ID do conjunto de anúncios (se omitido, abre menu)")
    p_prom.add_argument("--campaign", help="Filtra conjuntos por campanha no menu")
    p_prom.add_argument("--name", help="Nome do anúncio")
    p_prom.add_argument("--limit", type=int, default=25)
    p_prom.add_argument(
        "--activate", action="store_true", help="Cria o anúncio ATIVO (padrão: PAUSADO)"
    )
    p_prom.add_argument("--yes", "-y", action="store_true", help="Pula a confirmação")
    p_prom.set_defaults(func=cmd_promote)

    p_la = sub.add_parser(
        "launch", help="Cria campanha + conjunto + anúncio do zero a partir de um post"
    )
    p_la.add_argument("--post", help="ID da mídia do Instagram (se omitido, abre menu)")
    p_la.add_argument("--campaign-name", default="Campanha - Post Instagram")
    p_la.add_argument("--adset-name", default="Conjunto - Post Instagram")
    p_la.add_argument("--name", help="Nome do anúncio")
    p_la.add_argument(
        "--objective", default="OUTCOME_ENGAGEMENT", help="Objetivo da campanha"
    )
    p_la.add_argument(
        "--optimization-goal", default="POST_ENGAGEMENT", help="Meta de otimização do conjunto"
    )
    p_la.add_argument(
        "--daily-budget", type=int, default=5000,
        help="Orçamento diário em centavos (padrão 5000 = R$ 50,00)",
    )
    p_la.add_argument("--countries", default="BR", help="Países (separados por vírgula)")
    p_la.add_argument("--age-min", type=int, default=18)
    p_la.add_argument("--age-max", type=int, default=65)
    p_la.add_argument("--limit", type=int, default=25)
    p_la.add_argument(
        "--activate", action="store_true", help="Cria tudo ATIVO (padrão: PAUSADO)"
    )
    p_la.add_argument("--yes", "-y", action="store_true", help="Pula a confirmação")
    p_la.set_defaults(func=cmd_launch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MetaApiError as exc:
        print(f"Erro da API do Meta: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
