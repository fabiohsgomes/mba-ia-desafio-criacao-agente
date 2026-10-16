# ADR-XXX: Integração Gemini compartilhada entre os agentes

**Status:** Aceita  
**Data:** 15-10-2026  
**ADRs relacionadas:** [Orquestração ADK com principal e especialistas por transferência](ADR-XXX-orquestracao-adk-com-principal-e-especialistas-por-transferencia.md); [Confirmações persistidas e retomada do ADK](../SESSION/ADR-XXX-confirmacoes-persistidas-e-retomada-do-adk.md)

## Contexto e definição do problema

O atendimento conversacional do Residencial Aurora utiliza Google ADK
com um principal e três especialistas para reservas, visitantes e
regulamento.
O documento de requisitos exige modelos Gemini e acesso pelo Google AI Studio,
deixando livre a escolha do modelo de cada agente.
A implementação precisa definir uma estratégia de inferência comum
ao atendimento e distinguir disponibilidade externa de efeitos
realmente persistidos nas operações do condomínio.

A escolha documental é compartilhar um único modelo entre os quatro
agentes, com identificador configurável.
A justificativa registrada é simplificar a configuração e a análise
do comportamento dos agentes.
Essa escolha concentra a dependência do atendimento no acesso ao
modelo aprovado, sem tornar consultas diretas de verificação
dependentes da inferência.
O acesso, a cota e o funcionamento da integração não foram comprovados.

O requisito de Gemini consta do documento de requisitos introduzido em 17/09/2026,
conforme o histórico já registrado na identificação do candidato.
A estratégia compartilhada foi aprovada documentalmente em 15/10/2026,
data desta decisão.
O status Aceita descreve a aprovação arquitetural, sem declarar que
a integração, seus testes ou a validação de acesso já foram concluídos.
Não há implementação executável como evidência neste snapshot.

O requisito original exige modelos Gemini com chave do Google AI Studio e permite
escolher o modelo de cada agente. A seleção deve considerar a documentação oficial e os
limites ativos do projeto, que podem mudar; o fluxo de avaliação demanda algumas dezenas
de chamadas. A chave deve ficar fora do Git, em `.env`, e `.env.example` deve conter
somente os nomes das variáveis, sem valores. O compartilhamento do modelo entre os
quatro agentes é uma decisão local, sem acesso ou cota comprovados por este documento.

## Motivadores da decisão

- Cumprir o requisito de utilizar Gemini no atendimento conversacional.
- Simplificar a configuração dos quatro agentes com um modelo comum.
- Simplificar a análise do comportamento dos agentes pela escolha comum.
- Manter o identificador do modelo configurável na integração aprovada.
- Preservar a distinção entre resposta do modelo e efeito persistido.

## Opções consideradas

1. Compartilhar um modelo Gemini entre o principal e os três especialistas.
2. Escolher o modelo Gemini individualmente para cada agente.

A primeira opção é a decisão aprovada.
A segunda é uma possibilidade explicitamente permitida pelo documento de requisitos,
sem evidência de que tenha sido submetida a avaliação comparativa.
Sua inclusão registra a alternativa documental disponível, sem afirmar
que houve experimentos ou uma rejeição fundamentada em métricas.

O responsável confirmou que não houve comparação entre modelo comum e
modelos por agente. A escolha atende ao requisito de Gemini e adota o
compartilhamento por simplicidade, conforme a decisão local aprovada.
O documento de requisitos não obriga que os agentes usem o mesmo modelo.

## Resultado da decisão

Adotar Gemini como integração externa de inferência para os quatro
agentes, compartilhando um único identificador de modelo configurável.
O modelo aprovado nas fontes é gemini-3.8-flash.
A razão documentada para o compartilhamento é simplificar tanto a
configuração quanto a análise de comportamento do atendimento.
O identificador integra esta decisão maior de dependência externa;
seu registro não comprova disponibilidade ou acesso no ambiente usado.

A validação depende de acesso e cota no projeto do Google AI Studio.
As fontes não registram comparação de qualidade, latência ou preço
que sustente outras vantagens da escolha.
A política aprovada é não repetir automaticamente chamadas que falhem,
inclusive no SDK, e não realizar fallback automático de modelo.
Uma operação só pode ser apresentada como concluída quando houver
o efeito persistido correspondente.

## Vantagens e desvantagens das opções

### Modelo Gemini compartilhado

- **Vantagem:** simplifica a configuração entre o principal e especialistas,
  conforme a justificativa aprovada.
- **Vantagem:** simplifica a análise do comportamento dos agentes,
  conforme a justificativa aprovada.
- **Desvantagem:** o atendimento mantém dependência comum de acesso,
  disponibilidade e cota para o modelo escolhido.
- **Limitação da evidência:** não há resultado executável que comprove
  acesso ou vantagem comparativa no projeto utilizado.

### Modelo Gemini escolhido por agente

A liberdade de escolha individual está documentada no documento de requisitos.
As fontes não apresentam vantagens, desvantagens ou resultados de
avaliação dessa alternativa.
Não são atribuídos ganhos de qualidade ou custos de manutenção sem
registro que sustente essas conclusões.
A ausência de comparação foi confirmada e está registrada na seção de opções consideradas.

## Consequências

A configuração de inferência passa a seguir uma escolha comum aos
quatro agentes, enquanto os especialistas mantêm responsabilidades
distintas por domínio.
A dependência de Gemini permanece externa ao armazenamento do domínio
e à inspeção direta dos efeitos.
O funcionamento do atendimento requer acesso e cota no projeto usado;
essa condição ainda não é evidência disponível no repositório.
Manter o modelo aprovado e verificar acesso/cota por uma chamada real e
pelo fluxo completo do avaliador. Essas verificações continuam pendentes,
sem evidência de funcionamento alegada nesta decisão.

Falhas de inferência não podem ser confundidas com conclusão da ação.
Cada chamada planejada tem uma tentativa, sem retries automáticos na
aplicação ou no SDK. Chamadas distintas necessárias à conversa continuam
permitidas. A falha não reinicia o Runner nem reaplica tools. Um resultado
já confirmado no banco deve ser preservado e informado sem nova inferência;
antes do commit, a unidade de trabalho respeita rollback. Falhas transitórias
podem interromper o atendimento; esse é o trade-off aceito.
Se o acesso ou a compatibilidade inviabilizar a escolha aprovada,
as fontes exigem registrar o impedimento e revisar explicitamente
a decisão antes de apresentar uma alternativa como aprovada.

## Referências

- [docs/decisoes.md:54](../../../decisoes.md#L54): modelo comum,
  justificativa e validação de acesso e cota pendente.
- [docs/PRD.md:140](../../../PRD.md#L140): falhas externas e política
  aprovada de ausência de repetição automática.
