# Potential ADRs Index

Data da análise: 2026-10-15.

Fase 2 executada para os oito módulos do [mapeamento](mapping.md), usando o [PRD](../PRD.md), as [decisões aprovadas](../decisoes.md), o enunciado e os dados locais. Os candidatos registram decisões documentais, sem implementação ou testes de runtime comprovados. Não são ADRs formais.

## Analysis Progress

### Analyzed Modules

| Módulo | Data | Alta prioridade | Média prioridade | Resultado |
| --- | --- | ---: | ---: | --- |
| API | 2026-10-15 | 1 | 0 | Framework, validação e contrato HTTP consolidados |
| AGENT | 2026-10-15 | 2 | 0 | Orquestração ADK e integração Gemini |
| SESSION | 2026-10-15 | 2 | 0 | Isolamento e confirmação persistida |
| RESERVA | 2026-10-15 | 0 | 0 | Integridade consolidada em DATA; confirmação e isolamento em SESSION |
| VISITA | 2026-10-15 | 0 | 0 | Fluxos de negócio descartados; infraestrutura coberta por SESSION, DATA e AGENT |
| DATA | 2026-10-15 | 1 | 0 | Persistência, fontes imutáveis e ciclo de vida |
| REG | 2026-10-15 | 1 | 0 | Recuperação de conhecimento com contexto seletivo |
| SUPPORT | 2026-10-15 | 0 | 0 | Configuração, documentação e validação sem candidato estrutural independente |

### Pending Analysis

Nenhum módulo pendente nesta rodada documental. Evidências de implementação deverão ser incorporadas quando houver código, schemas, dependências e testes.

## High Priority ADRs (must-document/)

| Módulo | Título | Categoria | Pontuação | Arquivo |
| --- | --- | --- | ---: | --- |
| API | API HTTP/JSON assíncrona com FastAPI e Pydantic | Arquitetura / tecnologia | 125/150 | [Candidato](potential-adrs/done/API/api-http-json-assincrona-com-fastapi-e-pydantic.md) |
| AGENT | Orquestração ADK com principal e especialistas por transferência | Arquitetura / plataforma IA | 125/150 | [Candidato](potential-adrs/done/AGENT/orquestracao-adk-com-principal-e-especialistas-por-transferencia.md) |
| AGENT | Integração Gemini compartilhada entre os agentes | Tecnologia / integração IA | 110/150 | [Candidato](potential-adrs/done/AGENT/integracao-gemini-compartilhada-entre-os-agentes.md) |
| SESSION | Isolamento por apartamento na fronteira das tools | Segurança / autorização | 120/150 | [Candidato](potential-adrs/done/SESSION/isolamento-por-apartamento-na-fronteira-das-tools.md) |
| SESSION | Confirmações persistidas e retomada do ADK | Arquitetura / runtime IA | 125/150 | [Candidato](potential-adrs/done/SESSION/confirmacoes-persistidas-e-retomada-do-adk.md) |
| DATA | Persistência em banco SQLite único com transação compartilhada | Arquitetura / persistência | 125/150 | [Candidato](potential-adrs/done/DATA/persistencia-em-banco-sqlite-unico-com-transacao-compartilhada.md) |
| REG | Recuperação local do regulamento com contexto seletivo | Arquitetura / contexto IA | 105/150 | [Candidato](potential-adrs/done/REG/recuperacao-local-do-regulamento-com-contexto-seletivo.md) |

## Medium Priority ADRs (consider/)

Nenhum candidato atingiu a faixa de 75–99 pontos. Não foram criados arquivos ou diretórios vazios para representar módulos sem candidatos.

## Consolidações e descartes

- **API:** porta, códigos HTTP, datas, caminhos e schemas isolados são configuração ou partes do contrato; foram incorporados ao candidato da camada HTTP.
- **AGENT:** versão exata do ADK e transferência integram a escolha da plataforma; nome do modelo e variável de ambiente integram a estratégia Gemini. Não receberam ADRs separados. A futura redação pode consolidar provedor e orquestração se não houver justificativas independentes.
- **SESSION:** eventos, bloqueio de mensagens durante pendência, respostas `409` e aprovação exclusiva pela rota integram a estratégia de confirmação. O isolamento é uma fronteira estrutural de autorização, sem pressupor autenticação real.
- **RESERVA:** a regra de uma reserva por área/data não constitui por si uma escolha arquitetural. A opção por restrição transacional na gravação e preservação histórica dos códigos, analisada isoladamente sem base Step 0, soma 40/150 (15 escopo + 10 custo + 15 conhecimento). Foi incorporada como consequência do candidato DATA, evitando um documento abaixo do limiar. Taxas e cancelamento próprio são regras de negócio.
- **VISITA:** nome/data e registro de autorização são modelagem e fluxo de negócio, descartados antes da pontuação. A fronteira de acesso, confirmação e efeito único está coberta pelos candidatos de SESSION; armazenamento e execução por tools estão em DATA e AGENT.
- **DATA:** banco único, transação compartilhada, carga inicial, reset atômico e fontes imutáveis compõem o ciclo de vida da persistência. Não se escolheu ORM, WAL, migração, fila, outbox ou algoritmo de recuperação não aprovado nas fontes.
- **REG:** horários, capítulos e artigos são dados de negócio. Segmentação está incorporada à estratégia de recuperação; biblioteca, ranking ou algoritmo ainda indefinidos não geraram candidatos.
- **SUPPORT:** configuração de segredos, documentação e comandos isolados não receberam candidatos próprios; Python/uv e pin de dependências estão no contexto da plataforma. A exigência de testes é uma obrigação de validação, sem escolha de framework de testes ou estratégia técnica adicional aprovada.

## Relações e pendências

- **AGENT → SESSION:** transferência de atendimento deve preservar o especialista que pediu confirmação; a retomada persistida precisa ser comprovada com ADK `2.12.0`.
- **SESSION ↔ DATA:** o banco único e a transação compartilhada por ação foram aprovados. Efeito, conclusão, estado e eventos são confirmados ou revertidos juntos. Foi aprovado um serviço de sessões próprio para integrar ADK e tools nessa unidade de trabalho; sua implementação e comprovação permanecem pendentes.
- **RESERVA → DATA:** exclusividade no instante da gravação, histórico e códigos únicos devem ser comprovados por schema, transações e testes concorrentes.
- **REG ↔ AGENT/SESSION:** recuperação deve limitar o retorno da tool antes de o conteúdo entrar no modelo e nos eventos completos.
- **Gemini:** acesso, cota e comportamento do modelo escolhido permanecem sujeitos a verificação no projeto utilizado.
- Na identificação, ainda não havia ADRs formais. A geração posterior está registrada no [índice das ADRs](generated/README.md); não foram identificadas sucessões. As sobreposições documentais desta rodada foram consolidadas conforme acima.

## Método e limites

Aplicados Step 0, filtros de granularidade/modelagem/fluxo, os três critérios estruturais e a pontuação do `adr-analyzer`. Bases não foram somadas quando uma escolha se enquadra em mais de uma categoria. As dimensões de custo e estabilidade são estimativas prospectivas, não esforço medido ou histórico operacional. A prioridade indica relevância documental, não urgência de implementação.

O Git disponível contém apenas `be87e1d`, de 17/09/2026, com enunciado e dados iniciais. PRD e decisões estavam não rastreados durante a análise; suas datas não comprovam adoção em código. Não houve consulta externa, execução Gemini, instalação ou teste de aplicação nesta fase.

## Summary

- Alta prioridade: **7 candidatos**.
- Média prioridade: **0 candidatos**.
- Total: **7 candidatos**, sem numeração formal.
- Módulos analisados: **8 de 8**.
- Fase 3: os sete candidatos foram convertidos em ADRs MADR e arquivados em `potential-adrs/done/`. Consulte o [índice das ADRs geradas](generated/README.md). A numeração permanece provisória (`XXX`), conforme o comando; lacunas e validações pendentes estão preservadas nos documentos.

Revisão de persistência em 15/10/2026: os candidatos arquivados e as ADRs foram alinhados ao SQLite único e à atomicidade por ação; a escolha anterior de arquivos separados foi substituída antes da implementação. A pontuação documental não constitui medição de esforço ou resultado de runtime.

Escolhas complementares: serviço de sessões próprio, manutenção do modelo com validação de acesso/cota e ausência de repetição automática de inferência. Essas decisões encerram a seleção de opções; não encerram os testes exigidos.
