# ADR-XXX: Orquestração ADK com principal e especialistas por transferência

**Status:** Aceita  
**Data:** 15-10-2026  
**ADRs relacionadas:** [Confirmações persistidas e retomada do ADK](../SESSION/ADR-XXX-confirmacoes-persistidas-e-retomada-do-adk.md); [Integração Gemini compartilhada entre os agentes](ADR-XXX-integracao-gemini-compartilhada-entre-os-agentes.md)

## Contexto e definição do problema

O assistente do Residencial Aurora atenderá moradores sobre reservas,
visitantes e regulamento por uma API local.
O documento de requisitos exige Google ADK, um agente principal e pelo menos dois
especialistas, deixando livres a divisão de responsabilidades e a forma
de acionamento.
As consultas e alterações do domínio devem ocorrer por tools, com regras
críticas impostas em código e armazenamento.
A arquitetura precisa organizar esse atendimento sem deixar autorização
ou isolamento dependentes das decisões do modelo.

O trabalho pode parar aguardando uma confirmação do morador.
A aprovação precisa alcançar o especialista que originou a pendência,
inclusive quando a API reiniciar antes da resposta.
O documento de requisitos alerta que a retomada depende da combinação entre topologia,
persistência e runtime do ADK.
Assim, separar os domínios também estabelece uma dependência entre a
identidade do especialista e a continuidade da execução conversacional.

O documento de requisitos já estava presente no commit inicial de 17/09/2026.
A escolha específica desta topologia foi aprovada documentalmente em
15/10/2026, data adotada nesta ADR.
O status Aceita registra essa aprovação, enquanto implementação e
validação técnica permanecem pendentes.
Não há evidência de funcionamento da combinação escolhida no snapshot
que fundamentou a identificação.

O requisito original exige Google ADK série 2, em versão exata igual ou superior a
`2.2.0`, um agente principal e pelo menos dois especialistas, com modo de acionamento
livre. Reservas e visitantes devem ser lidos e gravados por tools. A retomada da
confirmação precisa alcançar o agente solicitante: o Runner escolhe esse agente, e
topologia, bloqueios de transferência, configuração de retomada do App e serviço de
sessões podem influenciar o resultado. Aprovação com sucesso HTTP não comprova execução;
é necessário verificar o efeito com sessão persistida e após reinício. O alerta original
descrevia testes em `2.2.0` e `2.9.1`, sem comprovar a combinação `2.12.0` deste
projeto.

## Motivadores da decisão

- Cumprir a exigência de Google ADK com principal e especialistas.
- Separar responsabilidades conforme os domínios de atendimento.
- Tornar explícitas as tools e informações utilizadas por especialista.
- Preservar o especialista solicitante na retomada de confirmações.
- Manter as garantias críticas em código, independentemente do modelo.
- Validar a continuidade do atendimento com estado persistente.

## Opções consideradas

1. Google ADK com principal e três especialistas por transferência.

Essa é a única opção com aprovação específica nas fontes.
O documento de requisitos admite outras quantidades de especialistas e formas de
acionamento, mas essa liberdade não comprova avaliação de alternativas.
Não há registro de comparação entre padrões concretos de delegação.

O responsável confirmou que não houve comparação de topologias ou formas
de delegação. A escolha atende ao documento de requisitos e concretiza a divisão por
domínio aprovada, dentro da liberdade de acionamento que o projeto permite.

## Resultado da decisão

Adotar Google ADK como runtime de orquestração, com um agente principal
responsável por receber o morador e encaminhar a solicitação.
Os três especialistas atendem reservas, visitantes e regulamento.
O acionamento ocorre por transferência entre subagentes do ADK.
A justificativa aprovada é separar responsabilidades por domínio e
explicitar quais tools e informações cada especialista utiliza.

A execução conversacional utiliza o runtime do ADK integrado à API.
A versão aprovada é ADK 2.12.0, parte desta escolha de plataforma.
A retomada deve preservar o especialista que solicitou a confirmação,
com sessões persistidas e continuidade após reinício.
A decisão não presume que a versão ou a topologia já demonstrem essa
compatibilidade; a prova prática é uma obrigação ainda pendente.

## Vantagens e desvantagens das opções

### Principal e três especialistas por transferência

- **Vantagem:** a distribuição por domínio torna explícito o atendimento
  de reservas, visitantes e regulamento.
- **Vantagem:** a divisão permite delimitar as tools e informações
  utilizadas por cada especialista, conforme a justificativa aprovada.
- **Desvantagem:** a retomada precisa preservar o especialista que
  originou a pendência, mesmo após reinício da API.
- **Desvantagem:** a combinação de topologia, persistência e versão do
  runtime exige validação específica antes de comprovar a garantia.

Não são atribuídas vantagens ou desvantagens a opções sem avaliação
registrada nas fontes.
A ausência de comparação está registrada na seção de opções consideradas.
Também não há evidência comparativa de latência, custo ou qualidade
que permita atribuir superioridade mensurada à topologia escolhida.

## Consequências

A separação por domínio passa a orientar a fronteira entre atendimento,
tools e contexto dos especialistas.
Mudanças nessa organização afetam o encaminhamento conversacional e
a continuidade de execuções que aguardam confirmação.
O controle de apartamento, a autorização dos efeitos e a integridade
dos dados continuam sendo responsabilidades do código e armazenamento;
a existência de especialistas não comprova essas garantias.

A persistência precisa conservar o vínculo entre a execução e o
especialista solicitante para cumprir o comportamento aprovado.
Essa dependência conecta a orquestração à decisão de sessões e
confirmações persistidas, sem definir nesta ADR o mecanismo de
persistência que integra estado, eventos, confirmação e efeito na mesma transação.
A compatibilidade com ADK 2.12.0, sessão persistida e reinício ainda
depende de validação real.

A aprovação documental não autoriza apresentar uma ação como entregue
quando sua execução e seus efeitos não foram comprovados.
Caso a validação revele incompatibilidade com a escolha aprovada,
as fontes exigem registrar o impedimento e revisar explicitamente
a decisão, preservando a distinção entre arquitetura aceita e
comportamento implementado.

## Referências

- [docs/decisoes.md:28](../../../decisoes.md#L28): versão aprovada,
  topologia, justificativa e exigência de retomada do solicitante.
- [docs/PRD.md:414](../../../PRD.md#L414): arquitetura conversacional,
  responsabilidades e trade-off da transferência entre especialistas.
