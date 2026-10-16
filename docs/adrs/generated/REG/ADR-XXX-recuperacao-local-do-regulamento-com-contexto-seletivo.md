# ADR-XXX: Recuperação local do regulamento com contexto seletivo

**Status:** Aceita  
**Data:** 15-10-2026  
**ADRs relacionadas:** [Orquestração ADK com principal e especialistas por transferência](../AGENT/ADR-XXX-orquestracao-adk-com-principal-e-especialistas-por-transferencia.md); [Confirmações persistidas e retomada do ADK](../SESSION/ADR-XXX-confirmacoes-persistidas-e-retomada-do-adk.md)

## 1. Contexto e problema

O assistente do Residencial Aurora responde dúvidas a partir de um
regulamento local em Markdown, organizado em capítulos e artigos.
O enunciado exige consulta por assunto e proíbe que eventos da sessão
contenham trechos de capítulos sobre assuntos alheios à pergunta.
Também determina que o principal não receba o regulamento nas instruções.
A resposta precisa ser fundamentada sem transportar contexto irrelevante
para as mensagens posteriores e para outros atendimentos da sessão.

O documento-fonte possui 491 linhas e 14 capítulos. Essa estrutura explícita
fundamenta a escolha aprovada de busca local por assunto, segmentada por
capítulos e artigos, sem embeddings ou banco vetorial.
A justificativa é começar com recuperação simples, evitando dependências
adicionais e contexto desnecessário. O objeto desta decisão é a forma de
recuperar conhecimento; os horários e demais regras do condomínio são dados,
e não novas restrições operacionais acrescentadas às tools.

A fonte e o requisito de contexto localizado foram introduzidos em
17/09/2026, conforme o levantamento anterior. A estratégia de busca local
foi aprovada documentalmente em 15/10/2026, data deste registro.
O status Aceita expressa aprovação da arquitetura, sem afirmar que exista
segmentador, busca ou teste implementado. O algoritmo de seleção continua
indefinido, e não há medição de qualidade, latência ou economia de tokens.

## 2. Fatores da decisão

- Responder com fundamento no regulamento fornecido pelo desafio.

- Impedir que capítulos irrelevantes entrem no contexto e nos eventos persistidos.

- Aproveitar a organização explícita do Markdown em capítulos e artigos.

- Evitar dependências adicionais de embeddings e armazenamento vetorial.

- Manter a consulta de conhecimento separada das regras operacionais fora de escopo.

## 3. Opções consideradas

1. **Recuperação local seletiva:** busca por assunto no Markdown,
   respeitando capítulos e artigos e retornando apenas conteúdo pertinente.
   Esta é a estratégia aprovada para o especialista de regulamento.

2. **Recuperação com embeddings e banco vetorial:** alternativa tecnológica
   explicitamente excluída pelas decisões aprovadas.
   Não há evidência de experimento, produto específico ou comparação
   de qualidade que tenha antecedido essa exclusão.

O carregamento integral do regulamento é uma abordagem proibida pelo
requisito, e não uma opção admissível para a solução deste desafio.

## 4. Resultado da decisão

Foi escolhida a recuperação local por assunto, com segmentação baseada
nos capítulos e artigos do Markdown e retorno seletivo ao especialista.
O documento estruturado permite adotar essa base simples sem introduzir
embeddings ou banco vetorial. A escolha delimita a fonte e o conteúdo
que pode alcançar o modelo, sem escolher biblioteca, ranking ou algoritmo.
Não se afirma que a busca local tenha qualidade superior a outra estratégia.

O principal permanece sem o regulamento em suas instruções.
A restrição de pertinência aplica-se ao conteúdo recuperado e aos eventos,
não apenas à redação da resposta final. Perguntas ambíguas ou sem trecho
pertinente devem resultar em esclarecimento ou indicação de limitação,
sem regra inventada. A presença de restrições no regulamento não as torna
automaticamente validações das operações de reservas ou visitantes.

## 5. Vantagens e desvantagens das opções

### Recuperação local seletiva

- **Vantagem prevista:** utiliza a fonte estruturada já disponível,
  preservando vínculo direto entre pergunta e conteúdo regulamentar.

- **Vantagem prevista:** evita as dependências adicionais de embeddings
  e banco vetorial, conforme a justificativa aprovada.

- **Limitação:** sinônimos e ambiguidade dependem da qualidade da seleção
  local; a fonte não registra evidência de cobertura suficiente.

- **Limitação:** segmentação estrutural, por si só, não comprova que
  os trechos retornados serão pertinentes em todas as perguntas.

### Embeddings e banco vetorial

- **Limitação arquitetural:** introduziriam dependências que a decisão
  aprovada explicitamente evita nesta entrega.

- **Ausência de evidência:** não há vantagem de qualidade, custo ou
  desempenho demonstrada para essa alternativa no material disponível.

- **Ausência de comparação:** a exclusão foi documentada como escolha
  de simplicidade, sem resultado de avaliação de solução vetorial.

## 6. Consequências

A recuperação passa a constituir uma fronteira de gestão de contexto
entre REG, AGENT e SESSION. O especialista recebe conteúdo selecionado,
e os eventos preservam o que efetivamente participou da conversa.
Reduzir ou resumir apenas a resposta final não corrige a entrada prévia
de capítulos irrelevantes no histórico; a restrição alcança a própria consulta.

A qualidade da seleção local precisa atender tanto à resposta correta
quanto à pertinência dos trechos persistidos. O PRD exige que perguntas
sobre a piscina sejam respondidas conforme a fonte e que os eventos
não incluam capítulos de outros assuntos. Ausência ou ilegibilidade
do arquivo impede afirmar que a consulta foi realizada.

A escolha não registra economia monetária ou redução medida de tokens.
Também não comprova o atendimento da garantia: busca e testes ainda
não estão implementados nas evidências disponíveis. A adoção de outra
infraestrutura de recuperação alteraria a decisão aprovada, suas
dependências e o tratamento de contexto, sem eliminar a exigência
de consultar apenas conteúdo pertinente ao assunto.

## 7. Referências

- [docs/decisoes.md:64](../../../decisoes.md#L64)
- [docs/PRD.md:277](../../../PRD.md#L277)
- [README.md:80](../../../../README.md#L80)
- [dados/regulamento.md:149](../../../../dados/regulamento.md#L149)
