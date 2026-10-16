# ADRs geradas

Data da geração: 15/10/2026.

Os sete candidatos do [índice de identificação](../potential-adrs-index.md) foram convertidos em registros MADR em português. O status **Aceita** registra as decisões aprovadas em [decisoes.md](../../decisoes.md), sem afirmar implementação ou testes concluídos.

A numeração **ADR-XXX** é provisória, conforme o comando `adr-generate`; cada arquivo tem título e caminho próprios. A atribuição de números únicos permanece pendente. Os candidatos originais foram preservados em `../potential-adrs/done/` após a geração.

| Módulo | ADR | Lacunas explícitas |
| --- | --- | ---: |
| API | [API HTTP/JSON assíncrona com FastAPI e Pydantic](API/ADR-XXX-api-http-json-assincrona-com-fastapi-e-pydantic.md) | 0 |
| AGENT | [Orquestração ADK com principal e especialistas por transferência](AGENT/ADR-XXX-orquestracao-adk-com-principal-e-especialistas-por-transferencia.md) | 0 |
| AGENT | [Integração Gemini compartilhada entre os agentes](AGENT/ADR-XXX-integracao-gemini-compartilhada-entre-os-agentes.md) | 0 |
| SESSION | [Confirmações persistidas e retomada do ADK](SESSION/ADR-XXX-confirmacoes-persistidas-e-retomada-do-adk.md) | 0 |
| SESSION | [Isolamento por apartamento na fronteira das tools](SESSION/ADR-XXX-isolamento-por-apartamento-na-fronteira-das-tools.md) | 0 |
| DATA | [Persistência em banco SQLite único com transação compartilhada](DATA/ADR-XXX-persistencia-em-banco-sqlite-unico-com-transacao-compartilhada.md) | 0 |
| REG | [Recuperação local do regulamento com contexto seletivo](REG/ADR-XXX-recuperacao-local-do-regulamento-com-contexto-seletivo.md) | 0 |

O responsável confirmou que não houve comparação de alternativas: as escolhas atendem ao documento de requisitos e às decisões locais aprovadas. As lacunas comparativas foram encerradas com esse esclarecimento.

Não há marcadores de decisão pendente nem ADRs em `needs-input/`. Foram aprovados serviço de sessões próprio, manutenção do modelo atual com validação de acesso/cota e nenhuma repetição automática do Gemini. Todas as ADRs continuam sujeitas à implementação e aos testes previstos.

A revisão aprovada usa um banco SQLite e transação compartilhada por ação, integrada por um serviço de sessões próprio. Permanecem pendentes as provas de atomicidade e retomada no ADK, acesso/cota do Gemini e ausência de repetição automática na aplicação e no SDK. Essas são verificações de implementação, não decisões de escolha em aberto.

As relações entre ADRs estão nos cabeçalhos por links de título, para evitar ambiguidade enquanto todos usam o identificador provisório.
