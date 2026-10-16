# ADR-XXX: API HTTP/JSON assíncrona com FastAPI e Pydantic

**Status:** Aceita  
**Data:** 15-10-2026  
**ADRs relacionadas:** [Orquestração ADK com principal e especialistas por transferência](../AGENT/ADR-XXX-orquestracao-adk-com-principal-e-especialistas-por-transferencia.md); [Persistência em banco SQLite único com transação compartilhada](../DATA/ADR-XXX-persistencia-em-banco-sqlite-unico-com-transacao-compartilhada.md)

## 1. Contexto e problema

O assistente do Residencial Aurora será entregue como uma API local para
conversas sobre reservas, visitantes e regulamento. O enunciado exige um
contrato HTTP/JSON específico, consumido pelo avaliador, e permite escolher
o framework web. Também exige execução personalizada do Google ADK,
persistência de eventos e consulta direta aos efeitos das operações.
A fronteira HTTP precisa combinar esse atendimento conversacional com
respostas verificáveis, preservando as cinco garantias do projeto.

As decisões aprovadas em 15/10/2026 estabelecem FastAPI e Pydantic para
API e validação. O PRD acrescenta o padrão assíncrono compatível com o
runtime ADK e distingue conversas de consultas diretas ao domínio.
Essa separação permite verificar efeitos persistidos sem transformar
o texto do modelo em evidência de que uma operação ocorreu.
O objetivo documentado é manter a entrega local simples e reproduzível.

O contrato do desafio aparece no commit introdutório de 17/09/2026,
conforme o levantamento anterior; essa data não é a aprovação de FastAPI.
O status Aceita registra a escolha de arquitetura de 15/10/2026.
Não registra implementação, compatibilidade comprovada ou testes concluídos.
Os documentos disponíveis ainda não apontam código executável da aplicação
nem resultados comparativos; o responsável confirmou que não houve comparação.

## 2. Fatores da decisão

- Preservar o contrato HTTP/JSON exigido pelo avaliador em todos os fluxos.

- Compatibilizar a aplicação web com a execução assíncrona do Google ADK.

- Validar os dados na fronteira HTTP sem delegar as regras críticas ao modelo.

- Expor efeitos e eventos persistidos independentemente da redação das respostas.

- Manter simplicidade e reprodução do ambiente local como prioridades da entrega.

## 3. Opções consideradas

1. **FastAPI e Pydantic com API HTTP/JSON assíncrona:** opção aprovada
   para a camada web, a validação e a integração com o runtime ADK.
   O protocolo e o contrato são restrições do desafio;
   a escolha do framework utiliza a liberdade concedida pelo enunciado.

Não houve comparação com outros frameworks. A escolha foi feita para atender
ao enunciado, usando a liberdade de framework que ele permite e as decisões
locais aprovadas. FastAPI/Pydantic não são apresentados como tecnologias
obrigatórias do desafio.

## 4. Resultado da decisão

Foi escolhida uma API HTTP/JSON assíncrona com FastAPI e Pydantic,
preservando o contrato obrigatório e a integração com o Google ADK.
Framework, validação e protocolo são registrados juntos por constituírem
a fronteira entre o cliente, a execução conversacional e os dados.
A justificativa aprovada situa essa escolha na prioridade de simplicidade
operacional e reprodução da entrega local; não estabelece superioridade
comparativa de desempenho, segurança ou produtividade sobre alternativas.

A camada HTTP recebe solicitações e disponibiliza resultados e eventos,
enquanto as tools e o armazenamento impõem as regras críticas.
As consultas de verificação leem diretamente o domínio e não passam
pelo modelo. Confirmações permanecem uma fronteira explícita de autorização,
sem que mensagens de conversa sejam tomadas como aprovação.
Essa decisão não acrescenta interface visual, autenticação real,
pagamento ou deploy ao escopo aprovado.

## 5. Vantagens e desvantagens das opções

### FastAPI e Pydantic com HTTP/JSON assíncrono

- **Vantagem prevista:** concentra a camada web e a validação nas
  tecnologias explicitamente aprovadas para a entrega.

- **Vantagem prevista:** mantém uma fronteira compatível com o contrato
  exigido e com a abordagem assíncrona do runtime conversacional.

- **Desvantagem:** a escolha vincula a camada web e seus modelos de
  validação ao framework, exigindo adaptação se essa base for substituída.

- **Limitação:** integração assíncrona e validação de entrada não asseguram
  isolamento, persistência ou execução única sem as demais camadas.

Não se aplica uma comparação de vantagens e desvantagens de alternativas,
pois nenhuma foi avaliada. Os pontos acima descrevem consequências da
escolha aprovada, sem resultados comparativos.

## 6. Consequências

O contrato passa a orientar a fronteira de comunicação e seus critérios
de aceite. Alterações que afetem o cliente ou a avaliação dependem da
preservação das obrigações do enunciado, mesmo quando o framework
permitir outra representação. Consultas diretas permanecem distintas da
geração de respostas, tornando os efeitos do atendimento verificáveis.

A aplicação precisa integrar o ciclo de execução do ADK com a resposta
HTTP sem anunciar sucesso de domínio apenas porque houve resposta do
modelo. Persistência, confirmação e integridade continuam obrigações
das respectivas fronteiras arquiteturais; a camada web não as substitui.
As rotas de avaliação pertencem ao cenário local e não comprovam
a existência de uma camada administrativa protegida.

A aceitação desta escolha não encerra sua comprovação prática.
O PRD exige testes do contrato e das garantias, além do fluxo real com
Gemini. Falhas externas não podem ser apresentadas como operações
concluídas sem efeito persistido. A política aprovada não repete automaticamente chamadas ao Gemini,
inclusive no SDK, nem reinicia o Runner ou reaplica tools. Resultados
de integração e latência ainda não comprovam funcionamento nesta entrega.

## 7. Referências

- [docs/decisoes.md:15](../../../decisoes.md#L15)
- [docs/PRD.md:410](../../../PRD.md#L410)
- [README.md:96](../../../../README.md#L96)
