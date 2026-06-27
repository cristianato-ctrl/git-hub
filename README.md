# Meta Ad Agent

Agente em Python que **promove posts já publicados do Instagram como anúncios**
no Meta Ads. Em vez de subir uma nova mídia, ele reaproveita a publicação que já
existe — com a legenda, curtidas e comentários originais — colocando-a como
anúncio dentro do conjunto de anúncios (ad set) que você escolher. É o recurso
"Usar publicação existente" da Meta Marketing API.

## O que ele faz

- Lista os posts já publicados na sua conta profissional do Instagram.
- Lista campanhas e conjuntos de anúncios da sua conta de anúncios.
- Cria um anúncio a partir de um post existente, dentro do conjunto escolhido.
- Cria do zero campanha + conjunto (com orçamento e segmentação) + anúncio.
  Por segurança tudo nasce **PAUSADO** (você revisa e ativa depois).

## Duas formas de usar

- **CLI em Python** (este repositório) — credenciais via `.env`. Veja abaixo.
- **Workflow do n8n** — se você guarda as credenciais no n8n, use o template
  pronto em [`n8n/`](n8n/README.md) e importe `n8n/meta-ad-agent.workflow.json`.
  Ele usa a credencial *Facebook Graph API* do n8n; nenhum token fica no código.

## Como funciona (por baixo dos panos)

1. Cria um *ad creative* que referencia o post via
   `instagram_user_id` + `source_instagram_media_id` (posts do Instagram) ou
   `object_story_id` (posts de Página do Facebook).
2. Cria o *ad* no conjunto de anúncios apontando para esse creative.

## Pré-requisitos

- Python 3.10+
- Uma conta de anúncios do Meta, uma conta profissional do Instagram ligada a
  uma Página do Facebook, e um **token de acesso** com as permissões:
  `ads_management`, `instagram_basic`, `pages_read_engagement`,
  `pages_show_list`, `business_management`.

## Instalação

```bash
pip install -r requirements.txt
cp .env.example .env   # depois edite o .env com suas credenciais
```

## Configuração

Preencha o `.env` (veja `.env.example`):

| Variável               | Obrigatória | Descrição                                            |
| ---------------------- | ----------- | ---------------------------------------------------- |
| `META_ACCESS_TOKEN`    | sim         | Token de acesso (System User token recomendado).     |
| `META_AD_ACCOUNT_ID`   | sim         | ID da conta de anúncios (com ou sem prefixo `act_`). |
| `META_IG_USER_ID`      | sim*        | ID da conta profissional do Instagram.               |
| `META_PAGE_ID`         | não         | ID da Página do Facebook (posts de Página).          |
| `META_API_VERSION`     | não         | Versão da Graph API (padrão `v21.0`).                |

\* Obrigatória para tudo que envolve posts do Instagram.

### Como descobrir os IDs

- **Ad Account ID**: Gerenciador de Anúncios → canto superior, formato `act_...`.
- **Instagram User ID**: `GET /me/accounts` → na Página, campo
  `instagram_business_account`.
- **Page ID**: na própria Página, em "Sobre" / Transparência, ou via
  `GET /me/accounts`.

## Uso

```bash
# Listar posts já publicados no Instagram
python -m meta_ad_agent posts

# Listar campanhas e conjuntos de anúncios
python -m meta_ad_agent campaigns
python -m meta_ad_agent adsets --campaign 123456789

# Promover um post como anúncio passando os IDs
python -m meta_ad_agent promote \
  --post 17841400000000000 \
  --adset 23847000000000000 \
  --name "Anúncio - Promo de Junho"

# Modo interativo: escolhe post e conjunto por menu numerado
python -m meta_ad_agent promote

# Lançar do zero: campanha + conjunto (orçamento/segmentação) + anúncio
python -m meta_ad_agent launch \
  --post 17841400000000000 \
  --campaign-name "Campanha - Junho" \
  --adset-name "Conjunto - SP 25-45" \
  --daily-budget 5000 \
  --countries BR --age-min 25 --age-max 45

# Criar já ATIVO (padrão é PAUSADO) e pular a confirmação
python -m meta_ad_agent promote --post ... --adset ... --activate --yes
```

## Testes

```bash
python -m unittest discover -s tests
```

Os testes cobrem a lógica que não depende de rede (configuração, parsing de
posts). As chamadas à Graph API não são testadas automaticamente porque exigem
credenciais reais.

## Estrutura

```
meta_ad_agent/
  config.py   # leitura de credenciais (.env / variáveis de ambiente)
  client.py   # cliente fino da Graph API (GET/POST + paginação + erros)
  posts.py    # listagem de posts do Instagram
  ads.py      # campanhas, conjuntos e criação de anúncios a partir de posts
  cli.py      # interface de linha de comando
tests/        # testes unitários
n8n/          # workflow do n8n pronto para importar (+ guia)
```

## Avisos

- O `.env` está no `.gitignore`. **Nunca** faça commit de tokens.
- Anúncios criados ficam PAUSADOS por padrão — nada vai ao ar sem você ativar.
- Respeite os limites e políticas de anúncios do Meta.
