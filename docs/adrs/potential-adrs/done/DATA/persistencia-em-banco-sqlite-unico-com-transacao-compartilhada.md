# Potential ADR: Persistência em banco SQLite único com transação compartilhada

**Module**: DATA  
**Category**: Architecture / Technology  
**Priority**: Must Document (Score: 125/150)  
**Date Identified**: 2026-10-15  
**Estado da evidência**: escolha aprovada em documentação; armazenamento operacional ainda não implementado. Este candidato não é um ADR formal nem comprova as garantias.

## What Was Identified

A persistência planejada usa um único SQLite para sessões, eventos, confirmações e domínio. Todas as gravações decorrentes de uma ação compartilham conexão e transação: efeito, conclusão, estado e eventos correspondentes. A revisão aprovada em 15/10/2026 prioriza simplicidade e atomicidade; a integração ADK deve participar da unidade de trabalho sem commits independentes.

Os quatro JSONs são fontes iniciais imutáveis, não o armazenamento mutável da API. A aplicação importará o domínio em uma transação quando o banco estiver vazio e preservará o estado quando já populado. O reset explícito repõe o domínio e limpa sessões, eventos e confirmações na mesma transação, revertendo ambas as partes em caso de falha. Carga e restauração foram consolidadas como parte do ciclo de vida dessa persistência.

Como consequência estrutural no domínio RESERVA, a exclusividade de reserva ativa por área/data deve ser imposta por restrição no SQLite no instante da gravação transacional, e não apenas por consulta prévia. Cancelamentos devem preservar histórico e impedir reutilização dos códigos iniciais, novos ou cancelados. O conflito concorrente deve virar recusa normal, mantendo `200` nas duas aprovações. São requisitos documentados para o desenho de persistência; schema e tratamento de conflitos ainda não existem.

Os JSONs foram introduzidos em `be87e1d`, em 17/09/2026, antes da decisão local de armazenamento. As decisões de 15/10/2026 e o PRD não estão rastreados; não existe commit que comprove adoção de SQLite, schemas, migrações ou rotinas de carga/reset. A execução única passa a usar commit conjunto ou rollback integral; a participação da persistência ADK nessa transação continua sujeita a definição e prova de integração.

## Why This Might Deserve an ADR

- **Impacto:** a escolha define armazenamento, fronteiras transacionais e ciclo de vida dos dados usados por API, AGENT, SESSION, RESERVA, VISITA e DATA.
- **Trade-offs:** dispensa operação de servidor de banco, mas concentra concorrência de escrita no mesmo arquivo e exige que ADK e tools compartilhem a transação.
- **Complexidade:** distinguir banco vazio, reinício normal e reset evita perda de dados ou importação parcial; um arquivo único com commits independentes também não atende à decisão de atomicidade.
- **Conhecimento da equipe:** operações devem alterar o banco e preservar as fontes; desenvolvedores precisam entender onde as restrições e transações serão impostas.
- **Implicações futuras:** o desenho condiciona comandos operacionais, testes de falha, caminho do arquivo e evolução de schema, ainda a implementar.
- **Contexto temporal:** estabilidade é intenção da arquitetura aprovada; não há meses de uso ou histórico de migração demonstrados.

### Filtragem e pontuação

Step 0: banco de dados como infraestrutura fundamental de persistência, base **75**. SQLite é embarcado, portanto não foi identificado como serviço externo independente ou container. A classificação reconhece o papel estrutural do armazenamento primário. Transação compartilhada, carga e reset não recebem bases adicionais.

Os 3 E's são atendidos prospectivamente: a escolha estrutura a persistência e a integração, sua justificativa precisa ser entendida e foi aprovada como base duradoura da entrega. Não se confunde intenção de estabilidade com tempo de adoção comprovado.

| Dimensão | Pontos | Justificativa |
| --- | --- | --- |
| Base estrutural | 75 | Banco primário e fronteiras de persistência |
| Escopo e impacto | 20 | Infraestrutura central, envolvendo seis módulos planejados |
| Custo de mudança | 10 | Piso metodológico para infraestrutura estrutural; faixa de 1–2 semanas após implementação é hipótese, não esforço medido |
| Conhecimento da equipe | 20 | Persistência e ciclo de vida afetam a maior parte dos fluxos |
| **Total** | **125/150** | **must-document** |

## Evidence Found in Codebase

### Key Files

- [docs/decisoes.md](../../../../decisoes.md#L15), linhas 15–26: SQLite único, conexão/transação compartilhadas por ação, carga inicial e fontes imutáveis.
- [docs/decisoes.md](../../../../decisoes.md#L74), linhas 74–80: reset do domínio e limpeza das sessões.
- [docs/decisoes.md](../../../../decisoes.md#L111), linhas 111–117: restrição transacional de reserva ativa, códigos históricos e recusa normal no conflito concorrente.
- [docs/PRD.md](../../../../PRD.md#L180), linhas 180–188, e [cancelamento próprio](../../../../PRD.md#L207), linha 207: gravação sob restrição e preservação de histórico; [requisitos de integridade](../../../../PRD.md#L385), linhas 385–386: exclusividade e códigos não reutilizados.
- [docs/decisoes.md](../../../../decisoes.md#L119), linhas 119–125: execução única por commit conjunto e rollback integral, com integração ADK a comprovar.
- [docs/PRD.md](../../../../PRD.md#L329), linhas 329–349: inicialização, preservação no reinício, reset e falhas transacionais.
- [docs/PRD.md](../../../../PRD.md#L439), linhas 439–447: justificativas e trade-offs da persistência e das fontes imutáveis.
- [apartamentos.json](../../../../../dados/apartamentos.json#L1), [areas.json](../../../../../dados/areas.json#L1), [reservas.json](../../../../../dados/reservas.json#L1) e [visitantes.json](../../../../../dados/visitantes.json#L1): quatro fontes efetivamente presentes, sem schema ou banco de runtime.
- [mapping.md](../../../mapping.md): fronteira DATA e inventário da implementação ausente.

### Documentary Evidence

Trechos locais; não são implementação de banco ou de transação:

```text
docs/decisoes.md:18
Usar um único banco SQLite

docs/decisoes.md:22
Manter os arquivos JSON imutáveis

docs/PRD.md:349
Falha na restauração: reverter a limpeza conversacional e a reposição do domínio juntas.
```

### Impact Analysis

- **Fontes introduzidas:** `be87e1d`, 17/09/2026 às 16:13:43 -03:00, `chore: enunciado e dados do desafio`.
- **Escolha de SQLite:** documento de decisões datado de 15/10/2026; data de implementação desconhecida.
- **Histórico consultado:** mudanças recentes em `dados/`, PRD e decisões; busca de commits por `SQLite`, `banco` e `restauração` não trouxe resultados.
- **Evolução observável:** um commit introdutório dos dados; nenhuma migração ou implementação versionada. PRD e decisões não têm commits neste snapshot.
- **Acervo relevante existente:** quatro JSONs, com 6 apartamentos, 3 áreas, 3 reservas e 2 autorizações; documentos especificam o destino operacional desses dados.
- **Validação pendente:** carga transacional, preservação no reinício, rollback de importação, reset atômico do banco único, fontes inalteradas, exclusividade de reserva na gravação, códigos nunca reutilizados e integração com execução única de SESSION.

### Alternatives (if observable)

O enunciado deixa armazenamento livre, incluindo possibilidade de serviço externo. As decisões excluem banco em container/serviço externo e escolhem SQLite por simplicidade e reprodução local. O responsável confirmou que não houve comparação de produtos. A revisão para banco único decorre da necessidade de atomicidade; não houve benchmark ou migração implementada. Os JSONs presentes são fontes de carga; não há evidência de tentativa anterior de usá-los como armazenamento operacional.

## Questions to Address in ADR (if created)

- Como comprovar que todas as escritas da ação compartilham a conexão e o commit do SQLite único?
- Como definir o caminho do banco, a detecção de domínio vazio e a evolução de schema sem sobrescrever estado existente?
- Como demonstrar rollback conjunto do reset diante de falha entre limpeza conversacional e reposição do domínio?
- Como demonstrar que carga/reposição não deixam domínio parcial e que as fontes permanecem intactas?
- Como DATA e a persistência ADK compartilham a unidade de trabalho, impedindo commits independentes e comprovando rollback antes do commit e execução única após commit?

## Related Potential ADRs

- [API HTTP/JSON assíncrona com FastAPI e Pydantic](../API/api-http-json-assincrona-com-fastapi-e-pydantic.md): API consome o armazenamento e publica efeitos para avaliação; escolha do framework permanece naquele candidato.
- SESSION é responsável pela confirmação e execução única; RESERVA pela exclusividade e histórico de códigos. Essas relações vêm do [mapa](../../../mapping.md); não se afirmam arquivos de candidatos não examinados.
- `docs/adrs/generated/` não foi encontrado; não há ADR formal disponível para comparação de duplicidade ou sucessão.

## Additional Notes

- Carga inicial e restauração foram consolidadas neste candidato, evitando ADR separado para cada comando ou etapa do fluxo.
- Entidades, nome do arquivo SQLite ainda indefinido e valores de configuração não foram tratados como candidatos independentes.
- Confirmações, isolamento por apartamento e execução única por transação compartilhada não foram duplicados como escolhas de DATA. Unicidade de reserva e preservação dos códigos aparecem como consequências da infraestrutura SQLite; seus fluxos funcionais pertencem a RESERVA.
- Não se assume ORM, WAL, retry, fila, outbox, migrações específicas : nenhum desses mecanismos foi aprovado ou implementado nas fontes observadas.

Revisão documental em 15/10/2026: este candidato arquivado foi alinhado à decisão atual de banco único; a proposta anterior foi substituída antes da implementação.
