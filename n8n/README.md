# Workflow do n8n — Meta Ad Agent

`meta-ad-agent.workflow.json` é um workflow pronto para importar no n8n. Ele usa a
credencial **Facebook Graph API** que você já tem guardada no n8n — nenhum token
fica no arquivo.

## O que ele faz

A partir de um post já publicado no Instagram, cria em sequência:

1. **Campanha** (objetivo configurável, padrão `OUTCOME_ENGAGEMENT`)
2. **Conjunto de anúncios** (orçamento diário + segmentação: países e faixa de idade)
3. **Criativo** reaproveitando o post existente (`source_instagram_media_id`)
4. **Anúncio** dentro do conjunto

Tudo nasce **PAUSADO** — nada vai ao ar sem você ativar no Gerenciador de Anúncios.

## Como importar e usar

1. No n8n: **Workflows → Import from File** e selecione `meta-ad-agent.workflow.json`.
2. Em cada node **HTTP** (Criar Campanha/Conjunto/Criativo/Anúncio), abra
   *Credential to connect with* e selecione a sua credencial **Facebook Graph API**
   (o template traz o placeholder `REPLACE_WITH_YOUR_CREDENTIAL`).
3. (Opcional) Ajuste a versão da API no node **Parametros** (`apiVersion`, padrão `v21.0`).
4. Abra o formulário (botão do **Form Trigger**) e preencha:
   - ID da conta de anúncios (somente números)
   - ID do Instagram (IG User ID)
   - ID do post do Instagram a promover
   - Objetivo, nomes, orçamento (em centavos), países e faixa de idade
5. Execute. O node **Resumo** devolve `campaign_id`, `adset_id`, `creative_id` e `ad_id`.

## Permissões do token

A credencial precisa de: `ads_management`, `instagram_basic`,
`pages_read_engagement`, `pages_show_list`, `business_management`.

## Observações

- O orçamento é em **centavos** da moeda da conta (ex.: `5000` = R$ 50,00).
- A segmentação padrão é Brasil, idade 18–65 — edite no formulário.
- Para apenas adicionar o anúncio a uma campanha/conjunto que já existem,
  desconecte os nodes **Criar Campanha** / **Criar Conjunto** e aponte
  `campaign_id` / `adset_id` para os IDs existentes.
