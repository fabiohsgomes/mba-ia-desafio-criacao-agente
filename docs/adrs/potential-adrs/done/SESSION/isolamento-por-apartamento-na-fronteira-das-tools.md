# Potential ADR: Isolamento por apartamento na fronteira das tools

**Module**: SESSION  
**Category**: Security  
**Priority**: Must Document (Score: 120/150)  
**Date Identified**: 2026-10-15

## What Was Identified

A decisão aprovada estabelece o apartamento imutável da sessão como origem confiável do escopo das operações. As tools obtêm esse vínculo sem delegá-lo ao modelo e filtram consultas, alterações e resultados antes de estes alcançarem a conversa e os eventos. A disponibilidade pode considerar a agenda global, mas devolve somente livre/ocupado.

Trata-se da fronteira estrutural de autorização do assistente, não da definição de uma entidade ou de uma regra de reserva. Não adiciona autenticação real: no cenário local, o apartamento informado na criação representa a identidade autenticada. A implementação dessa fronteira ainda não existe.

O requisito original foi registrado no commit de 2026-09-17. A estratégia foi explicitada no documento de decisões datado de 2026-10-15; esse documento está não rastreado no Git, portanto não há data de adoção versionada ou evolução de código a inferir.

## Why This Might Deserve an ADR

- **Impact**: cruza API, SESSION, AGENT, RESERVA e VISITA; evita que prompt injection amplie privilégios ou revele dados nos eventos.
- **Trade-offs**: queries globais de disponibilidade continuam possíveis, com projeção restrita dos resultados; a aplicação deve manter o contexto confiável em cada tool.
- **Complexity**: a proteção precisa ocorrer antes da resposta da tool, pois ocultar apenas a resposta final deixaria dados nos eventos.
- **Team Knowledge**: qualquer nova operação sobre dados de moradores deve preservar essa origem do apartamento.
- **Future Implications**: uma autenticação futura deverá alimentar o mesmo contexto confiável; seu mecanismo não está aprovado nesta fase.
- **Temporal Context**: intenção estrutural duradoura documentada; não há meses de operação demonstrados.

### Filtering and Scoring

Step 0: infraestrutura de autorização crítica ao domínio, base **70**. O enquadramento decorre da fronteira confiável entre identidade da sessão, modelo e acesso aos dados, e não de um provedor de autenticação inexistente. Não se aplica a garantia automática das categorias universais 1–4.

| Dimensão | Pontos | Justificativa |
| --- | ---: | --- |
| Base Step 0 | 70 | Autorização estrutural de todas as tools de moradores |
| Scope + Impact | 20 | Cinco módulos afetados |
| Cost to Change | 10 | Estimativa de análise na faixa de 1–2 semanas para trocar a fronteira e rever tools/queries; não é medição de implementação |
| Team Knowledge | 20 | Fundamental para a maior parte das operações de moradores |
| **Total** | **120** | **must-document** |

Passa os 3 E's: estrutura a integração, exige compreensão explícita e foi definida como garantia estável. As dimensões são estimativas qualitativas, sujeitas a revisão quando houver código.

## Evidence Found in Codebase

O apartamento é definido uma única vez na criação da sessão e representa o morador autenticado. Mensagens posteriores não podem alterar esse vínculo, modificar reservas ou visitantes de outro apartamento nem trazer dados deles à conversa ou aos eventos. A proteção deve estar no código: as tools usam o apartamento da sessão e não um valor escolhido pelo modelo sem validação. A consulta global de disponibilidade pode informar apenas livre ou ocupado, sem titular nem código de reserva.

### Key Files

- [Decisões aprovadas](../../../../decisoes.md#isolamento-por-apartamento), linhas 105–109: origem do escopo e sanitização antes dos eventos.
- [PRD](../../../../PRD.md#rf-003-consultar-reservas-visitantes-e-disponibilidade-com-isolamento), linhas 146–166: fluxo de consulta restrito ao contexto.
- [Mapeamento](../../../mapping.md#cross-cutting-concerns), linhas 161–166: fronteira transversal entre cinco módulos.

### Code Evidence

Não há código de runtime. Trecho documental literal de `docs/decisoes.md:107`:

```text
As tools devem obtê-lo exclusivamente da sessão, sem permitir que o modelo escolha o apartamento de uma operação.
```

### Impact Analysis

- Requisito introduzido em 2026-09-17, com um commit do escopo inicial do projeto; nenhum commit de implementação.
- Decisões e PRD locais datados de 2026-10-15, ainda não rastreados; `git log` desses caminhos não retorna commits.
- Escopo previsto: cinco módulos; a quantidade de arquivos futuros não está definida.
- Histórico não demonstra incidentes, migração ou custo real da solução.

### Alternatives (if observable)

O requisito original rejeita depender somente do prompt ou aceitar apartamento escolhido pelo modelo sem validação. Não há comparação documentada entre bibliotecas de autorização.

## Questions to Address in ADR (if created)

- Como transmitir o contexto confiável a cada tool e impedir sua alteração pelo modelo?
- Como garantir que todos os resultados sejam filtrados antes de persistir eventos completos?
- Como provar isolamento em consultas, cancelamentos e pedidos que alegam outro apartamento?
- Quais interfaces futuras podem reutilizar a fronteira sem introduzir autenticação fora do escopo atual?

## Related Potential ADRs

- [Confirmações persistidas e retomada](confirmacoes-persistidas-e-retomada-do-adk.md): validação da confirmação também depende do vínculo confiável com a sessão.

## Additional Notes

Não existem ADRs formais em `docs/adrs/generated/` para comparação. Este candidato registra decisão documental aprovada e pendente de comprovação. A inexistência de autenticação real não autoriza tratar o conteúdo da conversa como identidade.
