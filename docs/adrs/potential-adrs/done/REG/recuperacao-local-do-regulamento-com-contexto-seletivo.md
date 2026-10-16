# Potencial ADR: Recuperação local do regulamento com contexto seletivo

**Módulo:** REG  
**Categoria:** Arquitetura / infraestrutura de IA — recuperação e gestão de contexto  
**Prioridade:** Must Document — **105/150**  
**Data de identificação:** 2026-10-15

## O que foi identificado

Decisão documental aprovada: consultar o Markdown local por assunto, segmentando capítulos e artigos, sem embeddings ou banco vetorial. Apenas os trechos pertinentes devem retornar pela tool ao especialista e integrar os eventos persistidos. O principal não recebe o regulamento nas instruções. O objeto deste candidato é a arquitetura de recuperação de contexto; os horários, artigos e demais regras do condomínio não são decisões arquiteturais.

O arquivo-fonte possui 491 linhas e 14 capítulos. Seu conteúdo e o requisito de consulta localizada foram introduzidos em `be87e1d`, de 17/09/2026. A escolha de busca local sem embeddings aparece nas decisões datadas de 15/10/2026, ainda não versionadas neste snapshot. Não há segmentador, mecanismo de busca, tool ou teste implementado. O algoritmo de seleção não foi definido e não é escolhido por esta análise.

## Por que pode merecer uma ADR

- **Impacto:** define como informação entra no modelo e permanece no histórico, cruzando REG, AGENT e SESSION.
- **Trade-offs:** aproveitar a estrutura do documento evita dependências adicionais; cobertura de sinônimos e ambiguidade depende da qualidade da seleção local.
- **Complexidade:** respostas corretas precisam coexistir com ausência de capítulos irrelevantes nos eventos completos; resumir a resposta final não remove contexto já persistido.
- **Conhecimento da equipe:** autores das tools e da integração precisam conhecer a fronteira entre documento-fonte, retorno da recuperação e contexto enviado ao modelo.
- **Implicações futuras:** adicionar embeddings ou outra fonte de recuperação altera dependências e exige revisar a pertinência dos trechos e a garantia de contexto localizado.
- **Contexto temporal:** estratégia planejada para a implementação; não há histórico de operação que comprove estabilidade ou desempenho.

### Filtro e pontuação

Passa pelos 3 E: estrutural (pipeline de recuperação e contexto), evidente (por que evitar contexto integral e infraestrutura vetorial), estável (estratégia de consulta prevista para o produto). Enquadramento Step 0 de infraestrutura específica de IA, base **70**, por sustentar diretamente a garantia obrigatória de gestão de contexto. Não é base de banco/ORM: nenhum serviço vetorial existe ou foi aprovado.

| Parcela | Pontos | Justificativa |
| --- | ---: | --- |
| Base Step 0 | 70 | Recuperação de conhecimento e gestão de contexto críticas à garantia 4 do produto de IA |
| Escopo e impacto | 15 | REG, AGENT e SESSION |
| Custo de mudança | 5 | Estimativa inferior a uma semana para trocar a estratégia neste estágio sem runtime; não é esforço medido |
| Conhecimento da equipe | 15 | Importante para ferramentas de consulta, contexto e inspeção dos eventos |
| **Total** | **105** | **Must Document** |

A base decorre da estratégia completa de recuperação de conhecimento. Capítulos, horários e respostas específicas não recebem essa base nem candidatos próprios. Sem o caráter de infraestrutura de IA, uma simples rotina de busca localizada não atingiria o limiar.

## Evidências encontradas no repositório

As respostas sobre regras devem usar `dados/regulamento.md`, sem colocar o regulamento nas instruções do principal. Nenhum evento da sessão pode conter trechos de capítulos de assuntos alheios à pergunta: texto integral no histórico amplia o contexto de todas as chamadas seguintes. Na avaliação, a pergunta sobre o funcionamento da piscina aos domingos deve trazer o horário de fechamento da fonte; os eventos devem conter as chamadas de tools anteriores, sem capítulos irrelevantes.

### Arquivos principais

- [decisoes.md](../../../../decisoes.md#L64), linhas 64–72: escolha explícita, justificativa e limite de escopo.
- [PRD.md](../../../../PRD.md#L277), linhas 277–298: recuperação por tool, pertinência, ambiguidade e indisponibilidade da fonte.
- [PRD.md](../../../../PRD.md#L464), linhas 464–467: trade-off da busca local e cobertura de sinônimos.
- [PRD.md](../../../../PRD.md#L569), linhas 569–576: risco de contexto irrelevante e validação por eventos.
- [dados/regulamento.md](../../../../../dados/regulamento.md#L149), linhas 149–159: exemplo de estrutura por capítulo/artigo e trecho pertinente ao caso de piscina aos domingos; a regra de horário é dado de domínio, não candidato a ADR.

### Evidência documental — sem código executável

Trechos literais de `docs/decisoes.md`:

```text
66: - Usar busca local por assunto, sem embeddings ou banco vetorial.
67: - Segmentar o Markdown por capítulos e artigos e retornar somente os trechos pertinentes à pergunta.
68: - Não incluir o regulamento completo nas instruções do principal ou nos eventos da sessão.
70: Justificativa: o documento local tem estrutura explícita e permite começar com uma recuperação simples, evitando dependências adicionais e contexto desnecessário.
```

### Análise de impacto e histórico

- Consultados `git log --follow --diff-filter=A`, log recente do regulamento e documentos, e busca por regulamento/busca/contexto/embeddings nas mensagens.
- O único commit disponível, de 17/09/2026, introduz a fonte e o documento de requisitos; não há evolução do mecanismo de busca ou resultado de testes versionado.
- Decisão posterior datada documentalmente de 15/10/2026, sem commit que comprove sua adoção.
- Evidência em um arquivo de conhecimento próprio (491 linhas, 14 capítulos) e três documentos compartilhados; zero arquivos executáveis REG.
- Afeta REG, AGENT e SESSION. Não se infere economia medida de tokens, latência ou custo monetário.

### Alternativas observáveis

As fontes contrapõem recuperação localizada ao carregamento do regulamento integral, proibido pelo requisito. Embeddings e banco vetorial são explicitamente excluídos pela decisão. Não há comparação implementada, benchmark ou registro de avaliação de algoritmos específicos de ranqueamento.

## Perguntas para a ADR formal

- Como a estrutura de capítulos/artigos sustenta a escolha de busca local?
- Como delimitar o menor trecho suficiente quando uma pergunta exige artigos relacionados?
- Que comportamento tratará sinônimos, ambiguidade e ausência de resultado sem inventar regras?
- Que testes inspecionarão eventos completos para provar que capítulos irrelevantes não entraram no contexto?
- Que mudança de volume ou qualidade justificaria revisar a estratégia, sem presumir limites quantitativos ainda não aprovados?

## Potenciais ADRs relacionados

- [Orquestração ADK e especialistas](../AGENT/orquestracao-adk-com-principal-e-especialistas-por-transferencia.md): define quem consulta; este candidato define o que a recuperação devolve.
- SESSION: relacionar a persistência completa dos eventos no índice consolidado, sem duplicar a estratégia de armazenamento.

## Notas adicionais

`docs/adrs/generated/` não existe neste snapshot; não há ADR formal a deduplicar. Horário de fechamento da piscina, estrutura das entidades e demais regras do regulamento foram descartados como dados/regras de negócio. Quantidade de capítulos, caminhos e detalhe isolado de segmentação foram incorporados como evidência desta decisão maior. Não foram criados candidatos para índice invertido, busca lexical, biblioteca, embeddings, cache ou ranking: tais mecanismos não estão definidos nas fontes. Este arquivo identifica uma decisão documental e não gera ADR formal nem comprova implementação.
