# Potential ADR: Confirmações persistidas e retomada do ADK

**Module**: SESSION  
**Category**: Architecture  
**Priority**: Must Document (Score: 125/150)  
**Date Identified**: 2026-10-15

## What Was Identified

A estratégia aprovada persiste confirmações vinculadas à sessão e à execução do ADK, com contexto suficiente para retomar o especialista solicitante após reinício. A aprovação ocorre exclusivamente pela rota de confirmações e a mesma aprovação deve produzir no máximo um efeito. Eventos completos e ordenados também são persistidos para continuar a sessão.

Essa infraestrutura de execução com intervenção humana é parte crítica do runtime de IA. O candidato reúne persistência, retomada e controle de execução; não pretende transformar cada condição de aprovação em ADR independente. A escolha do SQLite único e da transação compartilhada pertence ao módulo DATA e a topologia dos especialistas pertence ao módulo AGENT.

O requisito original foi registrado em 2026-09-17, no commit `be87e1d`. O documento de decisões de 2026-10-15 explicita o vínculo persistido e a atomicidade por ação, mas ainda está não rastreado no Git. Nenhum histórico comprova que essa retomada funciona em ADK 2.12.0.

## Why This Might Deserve an ADR

- **Impact**: SESSION, AGENT, RESERVA, VISITA e DATA devem cooperar para que HTTP `200` corresponda a uma retomada efetiva, inclusive após reinício.
- **Trade-offs**: o arquivo único concentra escritores; ADK e tools devem compartilhar conexão/transação por ação, com validação da integração.
- **Complexity**: o Runner deve retomar o especialista correto; falha antes do commit deve reverter efeito, conclusão, estado e eventos; após commit, o reenvio não pode repetir a ação.
- **Team Knowledge**: quem desenvolve tools de escrita ou integra o runtime precisa compreender a fronteira entre pendência, aprovação e efeito.
- **Future Implications**: mudanças de versão do ADK, serviço de sessão ou topologia exigem nova validação da retomada.
- **Temporal Context**: decisão documental duradoura, com validação ainda pendente; não há estabilidade operacional medida.

### Filtering and Scoring

Step 0: infraestrutura crítica de IA, base **70**, porque define a execução suspensível e persistente do runtime ADK com aprovação externa. Não é base concedida pela simples existência de uma regra de negócio e não recebe mínimo automático das categorias universais 1–4.

| Dimensão | Pontos | Justificativa |
| --- | ---: | --- |
| Base Step 0 | 70 | Infraestrutura de execução do assistente com intervenção humana |
| Scope + Impact | 20 | Cinco módulos envolvidos |
| Cost to Change | 15 | Estimativa de análise na faixa de 2–8 semanas para substituir estratégia de retomada e revalidar falhas; não é prazo medido |
| Team Knowledge | 20 | Essencial às operações de escrita e integração do runtime |
| **Total** | **125** | **must-document** |

Passa os 3 E's: define integração estrutural, o motivo precisa ser compreendido e a estratégia deve sobreviver a reinícios e evolução do produto. As dimensões são estimativas qualitativas, revisáveis com a implementação.

## Evidence Found in Codebase

A retomada só funciona quando a resposta à confirmação chega ao agente que a solicitou, escolhido pelo Runner. Topologia, bloqueios de transferência, configuração de retomada do App e serviço de sessões podem alterar esse encaminhamento. O alerta original relatava diferenças nas versões `2.2.0` e `2.9.1`, inclusive entre execução em memória e persistida; não constitui validação de `2.12.0`. Um retorno HTTP sem erro pode ocorrer sem executar a ação. Por isso, aprovação e efeito devem ser verificados com sessões persistidas e após reiniciar a API, além da inspeção no ambiente de desenvolvimento do ADK.

### Key Files

- [Decisões: confirmações persistidas](../../../../decisoes.md#confirmações-persistidas), linhas 119–131: vínculo com execução, retomada, efeito único e eventos.
- [Decisões: mensagem durante pendência](../../../../decisoes.md#7-nova-mensagem-durante-confirmação-pendente), linhas 82–88: impedir outra execução até resolver a pendência.
- [PRD RF-007](../../../../PRD.md#rf-007-responder-confirmação-e-retomar-execução), linhas 249–271: transação compartilhada aprovada e integração ADK a comprovar.

### Code Evidence

Não há implementação. Trecho documental literal de `docs/decisoes.md:121`:

```text
Efeito de domínio, conclusão da confirmação e estado/eventos correspondentes devem ser gravados na mesma transação.
```

Trecho literal de `docs/PRD.md:265`:

```text
A integração ADK deve compartilhar a transação, sem commits independentes.
```

### Impact Analysis

- Escopo inicial do projeto: um commit relevante, 2026-09-17, sem implementação do runtime.
- PRD e decisões: documentos locais de 2026-10-15 sem commits; não há histórico de correções ou migrações.
- Cinco módulos previstos; arquivos de código e schema ainda não definidos.
- ADK 2.12.0, subagentes por transferência e SQLite precisam ser testados juntos, inclusive com confirmação pendente antes do reinício.

### Alternatives (if observable)

As decisões excluem aprovação pelo texto da conversa e proíbem iniciar outra execução com confirmação pendente. A revisão posterior aprova banco único e transação compartilhada. Não houve comparação de alternativas; a implementação da unidade de trabalho ADK ainda precisa ser comprovada.

## Questions to Address in ADR (if created)

- Quais identificadores e dados persistidos permitem ao Runner alcançar o especialista solicitante após reinício?
- Como garantir rollback conjunto entre escritas e reconhecer uma confirmação concluída após queda posterior ao commit?
- Como demonstrar aprovação, negativa, ID de outra sessão, ID inexistente e reenvio sequencial com `409`?
- Como demonstrar participação do ADK e das tools na mesma conexão e transação, sem commits independentes?
- Qual prova de integração confirma o comportamento na versão ADK escolhida?

## Related Potential ADRs

- [Isolamento por apartamento](isolamento-por-apartamento-na-fronteira-das-tools.md): a pendência pertence ao escopo confiável da sessão.
- O banco único e a transação compartilhada devem ser referenciados no candidato DATA quando consolidado no índice; não é uma segunda decisão deste candidato.

## Additional Notes

Não existem ADRs formais em `docs/adrs/generated/` para comparação. Este é candidato à documentação da estratégia já aprovada; a transação compartilhada foi aprovada e a integração concreta ADK permanece por comprovar. Não se escolhem outbox ou transação distribuída. O serviço de sessões próprio foi aprovado explicitamente. Reenvio sequencial é exigido; comportamento para duas respostas simultâneas à mesma confirmação continua fora do escopo. A classe do serviço de sessão, o schema e a participação na transação compartilhada não foram comprovados.

Escolha complementar aprovada: serviço de sessões próprio integrado à mesma conexão/transação das tools; implementação e provas de retomada ainda pendentes.
