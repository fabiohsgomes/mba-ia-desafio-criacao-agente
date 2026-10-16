# ADR-XXX: Confirmações persistidas e retomada do ADK

**Status:** Aceita
**Data:** 15-10-2026  
**ADRs relacionadas:** [Orquestração ADK com principal e especialistas por transferência](../AGENT/ADR-XXX-orquestracao-adk-com-principal-e-especialistas-por-transferencia.md); [Persistência em banco SQLite único com transação compartilhada](../DATA/ADR-XXX-persistencia-em-banco-sqlite-unico-com-transacao-compartilhada.md)

## Contexto e problema

O assistente do Residencial Aurora executará operações que geram cobrança
ou liberam acesso ao condomínio.
Esses efeitos dependem de aprovação explícita fornecida ao sistema,
independentemente do texto da conversa ou da decisão do modelo.
A conversa, seus eventos e as confirmações pendentes devem sobreviver
ao reinício da API, permitindo continuar o atendimento na mesma sessão.
Uma resposta de sucesso sem retomada efetiva não atende a essa garantia.

A arquitetura aprovada usa Google ADK 2.12.0 e especialistas por transferência.
Uma confirmação deve manter o vínculo com a sessão e com a execução que
a originou para que a retomada alcance o especialista solicitante.
O estado conversacional e os efeitos de domínio ficam no mesmo SQLite.
Todas as gravações da ação compartilham conexão e transação: efeito,
conclusão da confirmação, estado da sessão e eventos correspondentes.
Falha antes do commit reverte tudo; após commit, o resultado permanece.

O enunciado original registra o requisito desde 17-09-2026;
as decisões aprovadas em 15-10-2026 explicitam a estratégia persistente.
O status Aceita registra essa aprovação documental.
Não representa implementação concluída, teste executado ou compatibilidade
comprovada entre ADK, transferência de especialistas e persistência SQLite.
Foi aprovado um serviço de sessões próprio integrado à transação.
Sua implementação e compatibilidade com ADK 2.12.0 ainda precisam de prova.

## Direcionadores da decisão

- Impedir efeitos de cobrança ou acesso antes de aprovação válida no sistema.
- Preservar o vínculo entre confirmação, sessão, execução e especialista solicitante.
- Continuar o atendimento e conservar eventos completos após reinício.
- Garantir efeito único com rollback integral ou commit conjunto de todas as escritas.
- Rejeitar respostas para confirmações inexistentes, de outra sessão ou já respondidas.
- Manter o controle das operações em código, sem depender de autorização textual ao modelo.

## Opções consideradas

1. Persistir confirmações vinculadas à execução do ADK e retomar o
   especialista solicitante mediante aprovação externa à conversa.

A documentação aprovada define essa estratégia, mas não registra
uma comparação entre mecanismos concretos de persistência e recuperação.
A aprovação pelo texto da conversa está explicitamente excluída;
ela não é apresentada como alternativa compatível com os requisitos.
Apenas a opção documentada consta como opção considerada.

O responsável confirmou que não houve comparação de alternativas. A
estratégia foi escolhida para atender às garantias do enunciado e às
decisões locais aprovadas. A decisão revisada define a atomicidade por transação compartilhada;
a implementação do serviço próprio e sua comprovação permanecem pendentes.

## Resultado da decisão

Adota-se a persistência das confirmações com seu contexto de execução
para retomar o especialista correto somente após resposta válida do sistema.
O controle de pendências, a aprovação e a negativa ficam fora da interpretação
livre do modelo.
Enquanto uma confirmação estiver pendente, outra mensagem não inicia uma
nova execução; o atendimento informa a necessidade de resolver a pendência.
Eventos completos e ordenados compõem o estado persistido da sessão.

A estratégia foi escolhida para impedir autorização implícita,
preservar continuidade e manter execução única em operações sensíveis.
Efeito, conclusão, estado e eventos devem ser confirmados juntos.
A resposta é enviada após commit; uma queda anterior reverte todas as escritas.
Uma queda posterior preserva o resultado completo, impedindo repetição.
Chamadas Gemini e espera pela aprovação ficam fora da transação de escrita.
Compartilhar o arquivo com commits independentes não atende à decisão.

## Prós e contras das opções

**Persistência vinculada à execução e retomada do especialista solicitante**

- **Pró:** preserva o contexto necessário à continuidade após reinício.
- **Pró:** mantém a aprovação como autorização verificável pelo sistema.
- **Contra:** exige integração comprovada entre persistência, ADK e transferência.
- **Contra:** compartilhar a transação exige integração da persistência ADK
  com as tools e concentra a disputa de escrita no mesmo arquivo.

Essas consequências decorrem das escolhas documentadas.
Não há comparação experimental com outras opções ou comprovação
de comportamento do runtime neste projeto.
A existência de uma confirmação persistida, isoladamente, não prova
que o especialista correto será retomado ou que o efeito não será repetido.

## Consequências

SESSION, AGENT, RESERVA, VISITA e DATA passam a compartilhar uma fronteira
de execução que distingue proposta, autorização e efeito.
Uma negativa não altera o domínio, e uma aprovação válida permite tentar
a operação sem prometer que a disponibilidade de uma reserva permaneceu livre.
Identificadores não pendentes na sessão não autorizam nenhum efeito.
O reenvio sequencial de resposta não pode repetir a ação.
O comportamento de duas respostas simultâneas à mesma confirmação
permanece fora do escopo definido no projeto.

A integração deve demonstrar retomada com confirmação pendente após reinício,
preservação dos eventos, rollback antes do commit e ausência de repetição após commit.
Também precisa manter o isolamento da sessão e executar a ação no
especialista que originou a pendência.
A escolha aprovada é implementar um serviço de sessões próprio que
preserve o vínculo com o especialista e participe da conexão/transação
das tools. Comprovar esse comportamento em ADK 2.12.0, inclusive após
reinício, é obrigação de implementação e validação, sem decisão adicional
entre serviços nativos e serviço próprio.
Até essa comprovação, as garantias permanecem requisitos da implementação.
A revisão aprova a transação compartilhada e o serviço próprio,
sem declarar a integração implementada.

## Referências

- [docs/decisoes.md:119](../../../decisoes.md#confirmações-persistidas): estratégia aprovada de confirmação e execução única.
- [docs/PRD.md:249](../../../PRD.md#rf-007-responder-confirmação-e-retomar-execução): retomada e participação na transação compartilhada.
- [README.md:282](../../../../README.md#dicas-finais): risco documentado de sucesso sem retomada efetiva.
