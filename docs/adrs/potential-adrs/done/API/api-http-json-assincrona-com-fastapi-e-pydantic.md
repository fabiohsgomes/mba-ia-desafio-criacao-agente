# Potential ADR: API HTTP/JSON assíncrona com FastAPI e Pydantic

**Module**: API  
**Category**: Architecture / Technology  
**Priority**: Must Document (Score: 125/150)  
**Date Identified**: 2026-10-15  
**Estado da evidência**: decisão documental aprovada; implementação ausente. Este arquivo identifica um candidato, não constitui um ADR formal nem comprova funcionamento.

## What Was Identified

A API será implementada com FastAPI e Pydantic, em padrão assíncrono compatível com Runner/App do Google ADK, expondo o contrato HTTP/JSON do enunciado. A camada HTTP recebe conversas e confirmações e oferece consultas diretas de eventos e efeitos de domínio para avaliação, sem depender de resposta gerada pelo modelo nessas consultas.

Framework, validação e protocolo foram consolidados neste candidato por formarem a mesma fronteira de integração. O contrato é uma restrição do desafio; FastAPI/Pydantic são escolhas aprovadas nos documentos locais. O histórico mostra a introdução do enunciado em `be87e1d`, de 17/09/2026, mas não registra a decisão posterior de framework: PRD e decisões, datados de 15/10/2026, permanecem não rastreados. Não há dependências Python, rotas ou testes implementados.

## Why This Might Deserve an ADR

- **Impacto:** a fronteira HTTP conecta API, SESSION, AGENT, DATA, RESERVA e VISITA, além do cliente/avaliador externo; alterações de contrato afetam a avaliação inteira.
- **Trade-offs:** o contrato fixo limita mudanças de rotas, campos e status; a execução assíncrona precisa preservar eventos e confirmação sem anunciar efeitos inexistentes.
- **Complexidade:** a API deve distinguir diálogo com runtime ADK de consultas diretas ao banco e de retomada de execução pendente.
- **Conhecimento da equipe:** quem implementar fluxos e validações deve compreender essa fronteira e o que permanece nas tools/armazenamento.
- **Implicações futuras:** o desenho orienta schemas, handlers e testes de contrato. Nenhum mecanismo de autenticação real ou proteção administrativa deve ser declarado como entregue neste escopo local.
- **Contexto temporal:** escolha prevista para sustentar a entrega; não há tempo de uso operacional ou estabilidade histórica comprovados.

### Filtragem e pontuação

Step 0: categoria 2 (framework principal) e categoria 4 (protocolo/arquitetura de API), consolidadas com **uma única base de 75**, sem soma de bases. A escolha é estrutural, precisa ter sua justificativa entendida e é prevista para durar além de uma alteração pontual; isso satisfaz os 3 E's como análise prospectiva, não como adoção demonstrada.

| Dimensão | Pontos | Justificativa |
| --- | --- | --- |
| Base estrutural | 75 | Framework e contrato de API |
| Escopo e impacto | 20 | Fronteira de seis módulos planejados |
| Custo de mudança | 10 | Piso da categoria universal; estimativa metodológica de 1–2 semanas após implementação, sem medição histórica |
| Conhecimento da equipe | 20 | Contrato e validação relevantes para a maior parte dos fluxos |
| **Total** | **125/150** | **must-document** |

## Evidence Found in Codebase

### Key Files

- [docs/decisoes.md](../../../../decisoes.md#L15), linhas 15–26: FastAPI/Pydantic aprovados e obrigação de preservar contrato HTTP.
- [README.md](../../../../../README.md#L96), linhas 96–104: execução assíncrona, contrato JSON e consultas de verificação independentes do modelo; linhas 106–169 apresentam as seis operações HTTP.
- [docs/PRD.md](../../../../PRD.md#L303), linhas 303–323: eventos completos e listagens diretas de reservas/visitantes.
- [docs/PRD.md](../../../../PRD.md#L410), linhas 410–417: runtime, framework e padrão assíncrono planejados.
- [mapping.md](../../../mapping.md#L71): fronteira lógica do módulo API; nenhum arquivo de implementação identificado.

### Documentary Evidence

Trechos locais curtos; não são código executável:

```text
docs/decisoes.md:17
Usar FastAPI + Pydantic para a API e a validação dos dados

docs/PRD.md:416
API em padrão assíncrono compatível com o runtime do ADK

README.md:104
Todas as rotas recebem e devolvem JSON.
```

### Impact Analysis

- **Introdução do contrato:** commit `be87e1d`, 17/09/2026 às 16:13:43 -03:00, `chore: enunciado e dados do desafio`.
- **Decisão de framework:** registrada no documento de decisões de 15/10/2026; data de adoção em código não disponível.
- **Histórico consultado:** introdução e mudanças recentes de README, PRD e decisões; busca de mensagens por `API`, `FastAPI` e `contrato` não trouxe commits adicionais.
- **Modificações observáveis:** um commit referente ao README; nenhum histórico versionado de PRD/decisões, nenhuma implementação da escolha.
- **Alcance previsto:** 3 documentos de requisitos/contexto e 6 módulos lógicos envolvidos; contagens não representam arquivos de runtime existentes.
- **Validação pendente:** instalação reproduzível, schemas e rotas reais, contrato HTTP, integração assíncrona ADK e efeitos observados diretamente no armazenamento.

### Alternatives (if observable)

O README permite framework web livre e menciona FastAPI como usado no curso. As decisões aprovam FastAPI/Pydantic; nenhuma comparação com outro framework nomeado ou experimento está registrada. Não se inferem alternativas descartadas ou vantagens de desempenho não medidas.

## Questions to Address in ADR (if created)

- Por que FastAPI/Pydantic foi escolhido frente à liberdade de framework do enunciado? Quais critérios específicos de validação e integração pesaram?
- Como os handlers assíncronos delimitam a execução do ADK, a retomada e a consulta direta ao domínio?
- Como mapear falhas externas e erros de validação sem modificar os campos/status obrigatórios ou afirmar efeitos não persistidos?
- Como comprovar o contrato com testes e manter as regras críticas nas tools e no armazenamento?

## Related Potential ADRs

Nenhum relacionamento com outro candidato é afirmado nesta análise exclusiva de API. SESSION, AGENT e DATA são fronteiras relacionadas no [mapa](../../../mapping.md), a verificar nas respectivas análises. Não foi encontrado diretório de ADRs formais em `docs/adrs/generated/` para comparação ou detecção de duplicatas.

## Additional Notes

- Porta `8000`, caminhos isolados, formato de data, status `404`/`409` e schemas específicos foram consolidados como detalhes do contrato, sem candidatos separados.
- Aprovação/negativa e bloqueio de mensagens são fluxos de SESSION; unicidade e concorrência pertencem a DATA/RESERVA. Não foram duplicados neste módulo.
- A inspeção direta para avaliação integra o contrato; não fundamenta sozinha uma arquitetura CQRS, serviço administrativo ou infraestrutura de observabilidade.
- Não há testes executáveis ou resultados de runtime a anexar. A prioridade é documental e não comprova que a implementação cumprirá as garantias.
