# Diretrizes do Repositório

## Estrutura do Projeto e Organização dos Módulos

Este repositório implementa o assistente do Residencial Aurora: API FastAPI, equipe de agentes Google ADK com Gemini e persistência SQLite. A entrega é local, exclusivamente backend, com um processo/worker e sem autenticação real.

- `docs/PRD.md`, `docs/decisoes.md`, `docs/FDD.md`: requisitos, decisões aprovadas e desenho da implementação.
- `README.md`: instalação, operação, contrato HTTP e limites atuais; `docs/validacao.md`: evidências de testes, falhas iniciais e execução real. Consulte ambos ao comparar o desenho com o código implementado.
- `docs/adrs/generated/`: decisões de arquitetura aceitas; `potential-adrs/` preserva o histórico de análise.
- `dados/`: arquivos JSON iniciais e regulamento do condomínio, todos imutáveis. Nunca os modifique.
- `src/aurora/api/`: contrato HTTP e tratamento sanitizado de erros; `agents/`: principal, três especialistas e adaptador Gemini; `tools/`: interfaces das ferramentas; `services/`: conversa, execução, validação e autorização; `storage/`: SQL, ações e sessões ADK; `regulation/`: recuperação local de artigos.
- `src/aurora/cli.py`, `config.py` e `observability.py`: CLI, configuração e logs operacionais. `tests/` contém testes determinísticos e a avaliação real opt-in; `api.http` contém exemplos para REST Client.
- `var/aurora.sqlite3`: banco operacional padrão, ignorado pelo Git. Nos testes, use bancos temporários.

## Comandos de Instalação, Teste e Desenvolvimento

- `uv sync --locked`: instala as dependências conforme `uv.lock`. Os metadados atuais exigem Python 3.13+, embora os documentos de projeto permitam 3.12+.
- `uv lock --check`: verifica se o lock está atualizado em relação aos metadados.
- `uv run aurora serve`: inicia a API em `127.0.0.1:8000`, com um worker; aceita `--host` e `--port`.
- `uv run aurora reset`: restaura os dados iniciais e apaga sessões, eventos, confirmações e execuções atomicamente. Execute somente com a API parada e confira o banco de destino; não exige chave Gemini.
- `uv run aurora probe`: realiza uma inferência real no modelo configurado, sem retries; exige chave e consome cota.
- `uv run pytest -q`: executa a suíte padrão, sem inferência externa; o teste real fica skipped sem opt-in.
- `AURORA_RUN_LIVE=1 uv run pytest tests/test_live.py -q -s --tb=short`: executa os 15 passos com Gemini real e retomadas após reinício, usando banco temporário e servidor HTTP próprios; exige chave e consome cota.
- `git diff --check`: verifica erros de espaçamento nas alterações rastreadas.
- `git diff --exit-code HEAD -- dados/`: verifica se os arquivos iniciais rastreados permanecem inalterados.

Para configurar o ambiente, copie `.env.example` para `.env` somente se o arquivo ainda não existir e preencha `GOOGLE_API_KEY` sem expor seu conteúdo. `GEMINI_MODEL`, `GEMINI_TIMEOUT_SECONDS`, `SQLITE_BUSY_TIMEOUT_SECONDS` e `AURORA_DB_PATH` são opcionais; os padrões ficam em `src/aurora/config.py`. Caminhos relativos do banco são resolvidos a partir da raiz do projeto. Atualize `pyproject.toml` e `uv.lock` juntos ao alterar dependências.

## Estilo de Código e Convenções de Nomenclatura

Use indentação de quatro espaços em Python, anotações de tipo nas interfaces dos serviços, `snake_case` para funções/módulos e `PascalCase` para classes. Preserve os campos da API em português e a terminologia definida no PRD e no FDD. Mantenha SQL nos módulos de armazenamento e regras de autorização nos serviços/tools. Não há formatador ou linter configurado; documente ferramentas adicionadas.

## Arquitetura e Segurança

- Mantenha `google-adk==2.12.0` fixado e o principal com três especialistas por transferência, compartilhando a configuração Gemini. Ao alterar a integração, valide primeiro confirmação/retomada com o serviço de sessões próprio (`tests/test_session_gate.py`); esses recursos do ADK são experimentais.
- Tools mutáveis preparam intenções; `SQLiteSessionService.append_event` aplica os efeitos e persiste resultado, confirmação, estado, eventos e checkpoint em uma transação compartilhada (`BEGIN IMMEDIATE`). Preserve essa fronteira: não introduza commits independentes em tools/serviços nem execute Gemini durante transações de escrita.
- Obtenha o apartamento exclusivamente da sessão persistida. Alegações na conversa, argumentos do modelo e deltas de estado não alteram a identidade; tools não recebem apartamento. Consultas de disponibilidade não devem revelar o titular da reserva.
- Reservas com taxa e autorizações de visitantes exigem confirmação pela rota HTTP, vinculada à sessão, invocação, tool e argumentos persistidos. Texto do morador não autoriza ações. Reenvio, ID alheio ou confirmação já respondida retornam `409`. Novo pedido explícito após negativa deve gerar outra proposta e outro ID; preserve a rejeição do ID anterior.
- Preserve a unicidade SQL de reserva ativa por área/data e a não reutilização de códigos cancelados. A disputa de agenda é recusa de negócio. Não acrescente regras de pagamento, estorno, antecedência, datas passadas, horários ou capacidade às operações sem alteração aprovada dos requisitos.
- Serialize mensagens/confirmações da mesma sessão e permita concorrência entre sessões distintas. Uma escrita cancelada deve terminar antes de liberar o lock da sessão. Mantenha uma conexão no mesmo thread por unidade transacional; múltiplos workers exigem revisão da coordenação.
- Mantenha uma tentativa de transporte por inferência, timeout limitado e ausência de troca automática de modelo. Após efeito persistido, falha de geração retorna resultado determinístico sem repetir a ação/inferência.
- Recupere somente artigos pertinentes do regulamento; não carregue o documento completo nas instruções dos agentes. Na ausência de evidência inequívoca, peça esclarecimento.
- Preserve bancos válidos na inicialização e rejeite esquema incompatível ou catálogo parcial, sem reset silencioso. `dados/` é somente leitura, inclusive durante reset.
- Mantenha credenciais no `.env`, ignorado pelo Git. Logs JSON operacionais usam correlação por `request_id`, sem conversas, prompts, respostas Gemini, dados pessoais, chaves ou parâmetros SQL. Eventos completos pertencem ao SQLite e à rota de eventos; não os copie para logs ou relatórios.

## Fluxo de Desenvolvimento

Para novas funcionalidades e correções de comportamento, utilize **Fail-first** e o ciclo **TDD (Red → Green → Refactor)**:

1. **Red:** escreva primeiro um teste para o comportamento esperado ou a reprodução do defeito. Execute-o e confirme que falha pelo motivo esperado, não por erro de configuração.
2. **Green:** implemente apenas o necessário para fazer o teste passar e execute os testes afetados.
3. **Refactor:** melhore a estrutura sem alterar o comportamento, mantendo os testes verdes. Execute a suíte pertinente antes de concluir.

Trabalhe em incrementos pequenos. Os testes devem verificar requisitos e resultados observáveis, sem apenas reproduzir a implementação. Registre na entrega os testes executados e a falha inicial observada. Alterações exclusivamente documentais não exigem testes de comportamento.

## Diretrizes de Testes

Os testes devem focar no **negócio do produto**, usando cenários derivados do PRD e dos critérios de aceite: reserva com taxa exige aprovação, morador só altera suas próprias reservas e duas solicitações concorrentes não criam dupla reserva. Priorize regras de negócio, jornadas do morador e resultados observáveis. Evite acoplar as verificações a métodos privados, estrutura de classes ou sequência interna de chamadas; testes técnicos devem comprovar as garantias que sustentam esses comportamentos.

Use pytest e pytest-asyncio, já configurados em `pyproject.toml` com modo assíncrono automático, descoberta em `tests/` e arquivos `test_*.py`. Não há percentual mínimo de cobertura definido nem linter/formatador configurado.

- `test_api.py`: jornadas HTTP, isolamento, confirmação, novo pedido após negativa, concorrência, rollback, falha após commit, locks e logs.
- `test_session_gate.py` e `test_storage.py`: confirmação/retomada ADK, persistência, integridade SQL, importação e restauração atômica.
- `test_regulation.py`, `test_transport.py` e `test_cli.py`: recuperação seletiva, tentativa única/timeout do transporte e comandos/configuração.
- `test_live.py`: os 15 passos do avaliador com Gemini real e retomadas após reinício de processo.

A suíte padrão usa inferência programada, mantendo Runner ADK, transferências, tools, API e SQLite reais; os testes de transporte usam respostas HTTP controladas. Para alterações de comportamento, execute os testes afetados e a suíte pertinente antes de concluir. A aceitação integral exige os critérios do FDD e os 15 passos com Gemini real; inferência programada não comprova interpretação do modelo. Para alterações em prompts, roteamento ou confirmação/retomada, inclua a avaliação real na validação e registre eventuais impedimentos.

Atualize `docs/validacao.md` quando houver novas evidências relevantes, distinguindo testes determinísticos de execução real e informando falhas, skips e limitações. Evidência anterior não substitui a validação de comportamento alterado; não declare testes históricos como executados na entrega atual. Alterações exclusivamente documentais exigem verificação de coerência e os checks de diff, sem necessidade de inferência real.

## Diretrizes de Commits e Pull Requests

O histórico usa mensagens com prefixo de tipo, como `chore:`; siga esse estilo, por exemplo `feat: implementa confirmação de reserva`. Mantenha commits focados. PRs devem descrever comportamento, requisitos/ADRs afetados, validações realizadas e limitações restantes. Vincule issues quando aplicável e atualize os documentos afetados. Inclua exemplos de API sem dados sensíveis para alterações de contrato; capturas de tela são desnecessárias neste projeto exclusivamente backend.
