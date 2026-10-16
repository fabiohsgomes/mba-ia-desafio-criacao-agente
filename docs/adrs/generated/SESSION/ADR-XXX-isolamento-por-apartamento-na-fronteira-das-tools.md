# ADR-XXX: Isolamento por apartamento na fronteira das tools

**Status:** Aceita
**Data:** 15-10-2026  
**ADRs relacionadas:** [Confirmações persistidas e retomada do ADK](ADR-XXX-confirmacoes-persistidas-e-retomada-do-adk.md); [Persistência em banco SQLite único com transação compartilhada](../DATA/ADR-XXX-persistencia-em-banco-sqlite-unico-com-transacao-compartilhada.md)

## Contexto e problema

O assistente manipulará reservas e autorizações de visitantes de moradores.
Cada sessão pertence a um apartamento definido uma única vez na sua criação.
No cenário local do projeto, esse apartamento representa o morador autenticado;
a implementação de autenticação real está fora do escopo.
Mensagens posteriores podem alegar outra identidade ou solicitar dados alheios.
O modelo não deve poder ampliar o escopo de acesso a partir dessas mensagens.

As tools são a fronteira entre a conversa e os dados do condomínio.
Se devolverem informações indevidas, estas poderão aparecer tanto na resposta
quanto nos eventos completos persistidos da sessão.
Filtrar somente a redação final do assistente deixaria essa exposição possível.
Ao mesmo tempo, consultar disponibilidade exige examinar a agenda global,
sem revelar quem reservou uma data nem o código da reserva correspondente.

O requisito de isolamento consta do enunciado desde 17-09-2026.
As decisões de 15-10-2026 explicitam a origem confiável do apartamento
e o controle dos resultados antes de sua inclusão nos eventos.
Este registro formaliza uma decisão documental aprovada.
O status Aceita não representa código concluído, teste executado ou
evidência de proteção já demonstrada no runtime do assistente.

## Direcionadores da decisão

- Manter o apartamento da sessão como origem confiável do escopo das operações.
- Impedir que prompt injection amplie acesso ou permita alterações de terceiros.
- Aplicar o mesmo isolamento a leitura, escrita e resultados persistidos nos eventos.
- Permitir disponibilidade global sem revelar titular ou código de reserva alheia.
- Preservar a independência entre decisões do modelo e permissões de acesso aos dados.

## Opções consideradas

1. Impor o isolamento em código na fronteira das tools, usando o apartamento
   definido na sessão e limitando consultas, alterações e resultados.
2. Depender apenas das instruções do prompt para que o modelo respeite
   o apartamento e não exponha ou altere dados de terceiros.

A segunda opção é um contraponto explicitamente rejeitado pelo enunciado.
Ela não foi adotada nem apresentada como experimento executado.
Não há comparação documentada entre bibliotecas ou serviços de autorização.
A decisão trata da origem confiável e do local de imposição da restrição,
sem selecionar tecnologia adicional para autenticar moradores.

## Resultado da decisão

Escolhe-se impor o isolamento em código na fronteira das tools.
O apartamento usado pelas operações deve vir exclusivamente da sessão,
e o conteúdo da conversa não pode alterar esse vínculo.
Consultas e alterações permanecem limitadas ao apartamento correspondente,
com resultados já autorizados antes de chegarem ao modelo e aos eventos.
Essa abordagem foi aprovada porque a garantia deve independer do que
o morador escreve e das escolhas do modelo durante o atendimento.

A consulta global de disponibilidade retorna somente livre ou ocupado.
Ela não revela dados que identifiquem o titular nem o código de outra reserva.
Essa projeção restrita é parte da fronteira de acesso,
inclusive quando o resultado é registrado nos eventos completos.
Instruções de comportamento podem orientar a conversa,
mas não substituem a imposição do escopo nas operações.

## Prós e contras das opções

**Isolamento em código na fronteira das tools**

- **Pró:** mantém a origem do escopo fora das escolhas livres do modelo.
- **Pró:** protege simultaneamente respostas, resultados de tools e eventos.
- **Contra:** exige que todas as operações preservem o contexto confiável da sessão.
- **Contra:** exige limitar resultados globais antes de devolvê-los ao atendimento.

**Isolamento dependente apenas do prompt**

- **Contra:** não estabelece uma fronteira de acesso independente da interpretação do modelo.
- **Contra:** não atende à exigência explícita de proteção contra troca de apartamento pela conversa.
- **Contra:** não garante proteção dos dados registrados nos retornos das tools.

Não se atribuem benefícios mensurados à alternativa rejeitada.
As limitações acima decorrem do contrato do projeto;
não representam resultados de uma comparação experimental.

## Consequências

API, SESSION, AGENT, RESERVA e VISITA devem preservar a mesma fronteira:
o modelo solicita operações dentro do contexto recebido,
e o código determina quais dados podem ser consultados ou modificados.
Reservas, visitantes e cancelamentos não podem assumir apartamento
extraído livremente de uma mensagem como autorização suficiente.
A consulta global de disponibilidade permanece permitida,
com devolução restrita à informação necessária para responder ao morador.

Os eventos completos devem conservar somente resultados compatíveis
com o acesso autorizado desde a produção desses resultados.
A comprovação requer cenários de consulta, alteração e alegação de outra
identidade sem exposição de dados alheios em respostas ou eventos.
Essas verificações ainda pertencem à implementação e não foram executadas.
A arquitetura continua sem autenticação real,
conforme o limite estabelecido para a entrega local do projeto.

## Referências

- [docs/decisoes.md:105](../../../decisoes.md#isolamento-por-apartamento): fronteira de acesso aprovada.
- [docs/PRD.md:146](../../../PRD.md#rf-003-consultar-reservas-visitantes-e-disponibilidade-com-isolamento): consultas e resultados restritos à sessão.
- [README.md:68](../../../../README.md#3-garantia-2-cada-sessão-pertence-a-um-apartamento): requisito original e rejeição de proteção dependente do prompt.
