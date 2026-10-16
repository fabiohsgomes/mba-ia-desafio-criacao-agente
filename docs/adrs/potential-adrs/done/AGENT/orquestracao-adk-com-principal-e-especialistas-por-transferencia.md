# Potencial ADR: Orquestração ADK com principal e especialistas por transferência

**Módulo:** AGENT  
**Categoria:** Tecnologia / arquitetura — framework principal (Step 0, categoria 2)  
**Prioridade:** Must Document — **125/150**  
**Data de identificação:** 2026-10-15

## O que foi identificado

Decisão documental aprovada: usar Google ADK com Runner/App, um principal e três especialistas de reservas, visitantes e regulamento, acionados por transferência entre subagentes. A separação determina a distribuição de tools e contexto e a identidade do agente que precisa receber uma retomada. Não há código de runtime, dependência instalada ou teste que comprove essa arquitetura neste snapshot.

O requisito de ADK e principal/especialistas aparece no README introduzido pelo commit `be87e1d`, de 17/09/2026, `chore: enunciado e dados do desafio`. A topologia exata e o pin `2.12.0` constam nas decisões datadas de 15/10/2026, ainda não rastreadas pelo Git. Essa é a data documental, não a data de adoção em código.

## Por que pode merecer uma ADR

- **Impacto:** estrutura o atendimento, integração HTTP, estado conversacional e acesso às tools dos três domínios.
- **Trade-offs:** responsabilidades explícitas exigem preservar a execução e encaminhar a confirmação ao especialista correto, inclusive após reinício.
- **Complexidade:** a própria fonte alerta que topologia, serviço de sessão e retomada podem interagir; não existe combinação comprovada aqui.
- **Conhecimento da equipe:** quem escreve tools, rotas ou persistência precisa compreender transferência e retomada.
- **Implicações futuras:** troca do framework ou da forma de delegação exige rever os contratos de execução e de eventos.
- **Contexto temporal:** escolha destinada à implementação duradoura; o histórico não demonstra meses de estabilidade operacional.

### Filtro e pontuação

Passa pelos 3 E: estrutural (runtime e delegação), evidente (por que transferir e a quem retomar), estável (arquitetura planejada). Step 0 garante base de framework; não se aplicam red flags a essa categoria.

| Parcela | Pontos | Justificativa |
| --- | ---: | --- |
| Base Step 0 | 75 | Framework principal da aplicação conversacional |
| Escopo e impacto | 20 | Infraestrutura central para API, SESSION e três domínios |
| Custo de mudança | 10 | Estimativa conservadora de 1–2 semanas para substituir integração planejada; não é esforço medido |
| Conhecimento da equipe | 20 | Relevante para a maioria das features conversacionais |
| **Total** | **125** | **Must Document** |

## Evidências encontradas no repositório

### Arquivos principais

- [decisoes.md](../../../../decisoes.md#L28), linhas 28–52: versão, topologia, justificativa e dependência de retomada.
- [PRD.md](../../../../PRD.md#L118), linhas 118–140: fluxo pelo Runner e interação com pendências.
- [PRD.md](../../../../PRD.md#L414), linhas 414–416 e 449–457: Runner/App, transferência e trade-off.
- [README.md](../../../../../README.md#L54), linhas 54–56 e 282–284: requisito base e alerta do enunciado sobre retomada; o relato de testes no enunciado não comprova a implementação deste projeto.

### Evidência documental — sem código executável

Trechos literais de `docs/decisoes.md`:

```text
39: Usar um agente principal e três especialistas:
48: O principal acionará os especialistas por transferência de atendimento usando subagentes do ADK.
52: Consequência: a retomada de confirmação deve chegar ao especialista que a solicitou. A topologia escolhida precisa ser validada com sessão persistida e após reinício da API.
```

### Análise de impacto e histórico

- Consultados `git log --follow --diff-filter=A`, log recente dos três documentos e busca por ADK/Gemini/agente/transferência.
- O único commit disponível introduz o enunciado em 17/09/2026; não há evolução de implementação nem commit específico de escolha da topologia.
- São três documentos compartilhados como evidência; zero arquivos de implementação AGENT.
- Módulos afetados: AGENT, API, SESSION, RESERVA, VISITA e REG.

### Alternativas observáveis

O README permite pelo menos dois especialistas e deixa livre o modo de acionamento; as decisões restringem a escolha a três e transferência. Não foi encontrado registro de comparação entre padrões concretos de delegação. Não presumir alternativas rejeitadas.

## Perguntas para a ADR formal

- Como a separação de tools/contexto motivou os três especialistas?
- Por que transferência atende ao objetivo e quais alternativas foram efetivamente avaliadas?
- Que configuração de Runner/App preservará o solicitante ao retomar, sem inventar uma solução antes da prova prática?
- Quais testes com sessão persistida e reinício comprovarão a escolha em ADK `2.12.0`?

## Potenciais ADRs relacionados

- [Integração Gemini compartilhada](./integracao-gemini-compartilhada-entre-os-agentes.md).
- SESSION: relacionar o candidato sobre confirmação persistida e execução única, mantendo o algoritmo de persistência fora deste candidato de topologia.
- REG: relacionar a estratégia de recuperação do regulamento quando consolidada no índice.

## Notas adicionais

Não havia `docs/adrs/generated/` ao iniciar esta análise; não foram encontrados ADRs formais para deduplicação. A configuração da versão ADK pertence a esta decisão maior, não constitui candidato separado. Este arquivo identifica uma decisão, sem numerar ou gerar ADR formal. Compatibilidade, disponibilidade e comportamento de APIs externas não foram verificados nesta análise documental.
