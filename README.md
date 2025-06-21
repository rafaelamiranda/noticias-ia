# Notícias IA

Este projeto coleta automaticamente as principais notícias sobre inteligência artificial publicadas nas últimas 24 horas e gera um feed RSS em `index.xml`.

## Como funciona

1. O script `generate_rss.py` busca as notícias no Google News em português do Brasil.
2. Apenas itens publicados nas últimas 24 horas são mantidos.
3. As descrições são resumidas para até 90 caracteres, conforme as diretrizes de uso de notícias recentes.
4. O resultado é salvo no arquivo `index.xml` no formato RSS 2.0.

## Atualizações automáticas

Um fluxo de trabalho do GitHub Actions agendado executa o script todos os dias às 05h (UTC-3), equivalente a 08h UTC, e publica o arquivo atualizado no Cloudflare Pages.

Para acionar manualmente o workflow ou alterar configurações de deploy, edite `.github/workflows/main.yml`.
