# Diretrizes do Repositório

## Estrutura do Projeto e Organização dos Módulos

Este repositório contém requisitos, documentos de arquitetura, dados iniciais e metadados de dependências; o código da aplicação e os testes ainda não foram implementados.

- `docs/PRD.md`, `docs/decisoes.md`, `docs/FDD.md`: requisitos, decisões aprovadas e desenho da implementação.
- `docs/adrs/generated/`: decisões de arquitetura aceitas; `potential-adrs/` preserva o histórico de análise.
- `dados/`: arquivos JSON iniciais e regulamento do condomínio, todos imutáveis. Nunca os modifique.
- Estrutura planejada: `src/aurora/` com `api/`, `agents/`, `tools/`, `services/`, `storage/` e `regulation/`; coloque os testes em `tests/`.

## Comandos de Instalação, Teste e Desenvolvimento

- `uv sync --locked`: instala as dependências conforme `uv.lock`. Os metadados atuais exigem Python 3.13+, embora os documentos de projeto permitam 3.12+.
- `git diff --check`: verifica erros de espaçamento nas alterações rastreadas.
- `git diff --exit-code HEAD -- dados/`: verifica se os arquivos iniciais rastreados permanecem inalterados.

Ainda não há ponto de entrada da aplicação nem executor de testes configurado. O FDD propõe `uv run aurora serve`, `uv run aurora reset` e pytest; implemente e documente essas opções antes de apresentá-las como comandos disponíveis. Atualize `pyproject.toml` e `uv.lock` juntos ao alterar dependências.

## Estilo de Código e Convenções de Nomenclatura

Use indentação de quatro espaços em Python, anotações de tipo nas interfaces dos serviços, `snake_case` para funções/módulos e `PascalCase` para classes. Preserve os campos da API em português e a terminologia definida no PRD e no FDD. Mantenha SQL nos módulos de armazenamento e regras de autorização nos serviços/tools. Não há formatador ou linter configurado; documente ferramentas adicionadas.

## Arquitetura e Segurança

Mantenha `google-adk==2.12.0` fixado. Valide primeiro a confirmação/retomada do ADK com o serviço de sessões próprio. Use um banco SQLite e uma transação compartilhada para efeito, confirmação, estado e eventos de cada ação. Execute chamadas Gemini fora das transações de escrita. Obtenha o escopo do apartamento exclusivamente das sessões persistidas. Desative repetições automáticas de inferência e troca automática de modelo em caso de falha. Mantenha credenciais no `.env`, ignorado pelo Git; nunca registre conversas ou dados pessoais nos logs.

## Fluxo de Desenvolvimento

Para novas funcionalidades e correções de comportamento, utilize **Fail-first** e o ciclo **TDD (Red → Green → Refactor)**:

1. **Red:** escreva primeiro um teste para o comportamento esperado ou a reprodução do defeito. Execute-o e confirme que falha pelo motivo esperado, não por erro de configuração.
2. **Green:** implemente apenas o necessário para fazer o teste passar e execute os testes afetados.
3. **Refactor:** melhore a estrutura sem alterar o comportamento, mantendo os testes verdes. Execute a suíte pertinente antes de concluir.

Trabalhe em incrementos pequenos. Os testes devem verificar requisitos e resultados observáveis, sem apenas reproduzir a implementação. Registre na entrega os testes executados e a falha inicial observada. Alterações exclusivamente documentais não exigem testes de comportamento.

## Diretrizes de Testes

Os testes devem focar no **negócio do produto**, usando cenários derivados do PRD e dos critérios de aceite: reserva com taxa exige aprovação, morador só altera suas próprias reservas e duas solicitações concorrentes não criam dupla reserva. Priorize regras de negócio, jornadas do morador e resultados observáveis. Evite acoplar as verificações a métodos privados, estrutura de classes ou sequência interna de chamadas; testes técnicos devem comprovar as garantias que sustentam esses comportamentos.

Adote pytest, conforme planejado, com arquivos `test_*.py`. Cubra isolamento, reenvio de confirmação, reservas concorrentes, reinício/retomada, rollback, restauração atômica e recuperação seletiva do regulamento. Não há percentual mínimo de cobertura definido. A conclusão exige os critérios de aceite do FDD e os 15 passos do avaliador com Gemini real; testes apenas com mocks são insuficientes.

## Diretrizes de Commits e Pull Requests

O histórico usa mensagens com prefixo de tipo, como `chore:`; siga esse estilo, por exemplo `feat: implementa confirmação de reserva`. Mantenha commits focados. PRs devem descrever comportamento, requisitos/ADRs afetados, validações realizadas e limitações restantes. Vincule issues quando aplicável e atualize os documentos afetados. Inclua exemplos de API sem dados sensíveis para alterações de contrato; capturas de tela são desnecessárias neste projeto exclusivamente backend.
