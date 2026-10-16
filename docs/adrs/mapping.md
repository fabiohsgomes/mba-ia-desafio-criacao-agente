# Codebase Architecture Mapping

## Project Overview

- **Projeto:** assistente virtual do Residencial Aurora.
- **Objetivo:** API conversacional para reservas de áreas comuns, cancelamentos próprios, autorizações de visitantes e consulta localizada do regulamento.
- **Data do mapeamento:** 15/10/2026.
- **Fase:** 1 — mapeamento para orientar análise posterior de decisões arquiteturais.
- **Diretório analisado:** raiz deste repositório; contexto principal em [PRD](../PRD.md) e [decisões aprovadas](../decisoes.md).
- **Estado observado:** documentação, dados iniciais e skills de apoio. Ainda não existe implementação da aplicação, API, agentes, tools, bancos, comandos operacionais ou testes.

O inventário atual contém **33 arquivos não ignorados**, incluindo ocultos e este mapa, excluindo `.git` e arquivos ignorados: 3 documentos do produto, 5 fontes de dados, 6 arquivos de skills locais, 2 arquivos de configuração, 7 candidatos arquivados, 7 ADRs, 2 índices e este mapa. Há **7 arquivos rastreados pelo Git**; `.agents/`, `.env.example` e `docs/` permanecem não rastreados. As contagens dos módulos excluem o próprio mapa, totalizando 32 arquivos de entrada.

Não foram encontrados `pyproject.toml`, `uv.lock`, fontes Python, schemas SQL, arquivos SQLite, configuração de containers, pipelines ou suíte de testes. As contagens abaixo descrevem o acervo observado; não estimam quantidade futura de arquivos nem esforço de implementação.

### Histórico disponível

O histórico local contém um único commit: `be87e1d`, de **17/09/2026 às 16:13:43 -03:00**, com mensagem `chore: enunciado e dados do desafio`, introduzindo README e os cinco arquivos de dados. O `.gitignore` também está rastreado. PRD e decisões não têm histórico versionado neste snapshot; a data de 15/10/2026 vem dos próprios documentos. Não há commits de implementação dos quais inferir adoção ou evolução de padrões de runtime.

## Technology Stack

| Camada | Presente no repositório | Escolha documentada para implementação |
| --- | --- | --- |
| Linguagem e dependências | Nenhum projeto Python ou lockfile | Python ≥ 3.12, uv, `pyproject.toml` e `uv.lock` versionados |
| API e validação | Contrato HTTP JSON no README/PRD | FastAPI e Pydantic, execução local em `http://localhost:8000` |
| Orquestração de agentes | Responsabilidades descritas em documentos | Google ADK fixado em `2.12.0`, Runner/App, principal e três especialistas por transferência |
| Modelo externo | Nenhuma integração executável | `gemini-3.8-flash` compartilhado, configurável por `GEMINI_MODEL`, com chave do Google AI Studio |
| Estado conversacional | Nenhum banco ou schema | Serviço de sessões próprio do ADK sobre SQLite único compartilhado com o domínio |
| Domínio | Quatro JSONs de estado inicial | Mesmo SQLite das sessões; transação compartilhada por ação e restrições de integridade |
| Conhecimento | Markdown local com 14 capítulos | Busca local por assunto e segmentação em capítulos/artigos, sem embeddings ou banco vetorial |
| Configuração | `.gitignore` e `.env.example` | Chaves fora do Git e variáveis documentadas, sem valores no exemplo |
| Qualidade e operação | Requisitos de teste e de comandos | Testes automatizados, fluxo real do avaliador, comandos de subida e restauração; bibliotecas de teste ainda não definidas |

As versões e tecnologias da última coluna são **decisões das fontes locais, não dependências instaladas ou compatibilidade comprovada**. Este mapeamento não verificou catálogo, disponibilidade, cotas ou funcionamento do Gemini/ADK. Acesso ao modelo e retomada persistida nessa combinação continuam pendentes conforme as fontes. Não há ORM, fila, cache, infraestrutura de nuvem ou serviço externo de banco definido ou observado.

## Context Notes

**Source Files:**

- [README.md](../../README.md): enunciado, cinco garantias, contrato HTTP e fluxo de avaliação em 15 passos; ainda não é o README operacional final.
- [docs/PRD.md](../PRD.md): requisitos RF-001 a RF-010, arquitetura proposta, critérios de aceitação e riscos.
- [docs/decisoes.md](../decisoes.md): decisões aprovadas e validações ainda necessárias, explicitamente anteriores à implementação.
- [dados/](../../dados/): fontes iniciais de domínio e regulamento, inspecionadas para delimitar responsabilidades.

**Key Insights:**

- Arquitetura planejada: uma aplicação backend local com camada HTTP, orquestração multiagente, tools de domínio, persistência conversacional e de domínio no mesmo banco e recuperação local de conhecimento. Não há evidência de microserviços ou implantação distribuída.
- Domínios identificados: reservas, visitantes e regulamento; apartamento é o limite de autorização das operações conversacionais.
- O modelo conduz a conversa, enquanto autorização, confirmação, unicidade e isolamento devem ser impostos em código e armazenamento.
- O enunciado permite escolhas que os documentos posteriores especificam: FastAPI/SQLite, três especialistas, bloqueio de novas execuções durante pendência, `404` para apartamento inexistente e reset que também limpa sessões.
- Testes automatizados estão fora do mínimo do enunciado, mas foram incluídos expressamente nas decisões e no PRD; isso é ampliação aprovada, não evidência de testes existentes.
- Os limites funcionais não são diretórios implementados. Os IDs a seguir são fronteiras lógicas para análise posterior; nenhum caminho de código futuro é presumido.

## System Modules

### Module Index

| ID | Nome | Estado | Acervo próprio observado |
| --- | --- | --- | --- |
| API | Contrato HTTP e inspeção | Planejado | 0 arquivos de implementação |
| AGENT | Orquestração e integração com modelo | Planejado | 0 arquivos de implementação |
| SESSION | Sessões, eventos e confirmações | Planejado | 0 arquivos de implementação |
| RESERVA | Reservas e disponibilidade | Planejado; fontes presentes | 2 JSONs de referência |
| VISITA | Autorizações de visitantes | Planejado; fonte presente | 1 JSON de referência |
| DATA | Persistência de domínio e ciclo de vida | Planejado; fonte cadastral presente | 1 JSON de referência |
| REG | Consulta do regulamento | Planejado; fonte presente | 1 Markdown de referência |
| SUPPORT | Especificação, configuração e apoio ao desenvolvimento | Presente como acervo | 27 arquivos |

A atribuição de acervo evita dupla contagem: os cinco arquivos de `dados/` pertencem a RESERVA, VISITA, DATA e REG, embora sejam consumidos por outros módulos. SUPPORT reúne os demais 27 arquivos, incluindo candidatos arquivados, ADRs e índices gerados. API, AGENT e SESSION têm fontes documentais compartilhadas em SUPPORT, sem arquivos próprios de runtime. Todos os módulos têm escopo observado pequeno; complexidade futura não é inferida desse tamanho.

### API: Contrato HTTP e inspeção

- **Purpose:** receber clientes HTTP, validar entradas e expor conversa, confirmação, eventos e consultas diretas de avaliação.
- **Location:** implementação ausente; contrato em `README.md` e `docs/PRD.md`.
- **Key Components:** `POST /sessoes`; `POST /sessoes/{session_id}/mensagens`; `POST /sessoes/{session_id}/confirmacoes`; `GET /sessoes/{session_id}/eventos`; `GET /apartamentos/{numero}/reservas`; `GET /apartamentos/{numero}/visitantes`.
- **Technologies:** FastAPI/Pydantic planejados; JSON e datas `AAAA-MM-DD` no contrato.
- **Dependencies:** SESSION, AGENT e consultas diretas a DATA/RESERVA/VISITA. As rotas de verificação não passam pelo modelo.
- **Patterns:** validação na fronteira HTTP e execução assíncrona previstas; `404` para sessão/apartamento inexistente e `409` para confirmação inválida.
- **Key Files:** [PRD RF-001, RF-002, RF-007 e RF-009](../PRD.md), [decisões 1, 7 e 8](../decisoes.md).
- **Scope:** pequeno no acervo — 0 arquivos de implementação; 6 operações HTTP especificadas.

### AGENT: Orquestração e integração com modelo

- **Purpose:** encaminhar intenções e executar tools pelo runtime ADK.
- **Location:** implementação ausente; topologia definida em `docs/decisoes.md`, seção 3.
- **Key Components:** principal, especialista de reservas, especialista de visitantes, especialista de regulamento e integração Runner/App.
- **Technologies:** ADK `2.12.0` e Gemini configurável, conforme decisão local.
- **Dependencies:** SESSION para estado e retomada; RESERVA, VISITA e REG para ferramentas; Gemini como integração externa.
- **Patterns:** transferência de atendimento entre subagentes; responsabilidade por domínio; acesso a dados via tools. Compatibilidade dessa topologia com confirmação persistida ainda precisa de prova prática.
- **Key Files:** [PRD RF-002 e Arquitetura e abordagem](../PRD.md), [decisões 2–4](../decisoes.md).
- **Scope:** pequeno no acervo — 0 arquivos de implementação; 4 agentes planejados.

### SESSION: Sessões, eventos e confirmações

- **Purpose:** manter identidade contextual, histórico completo e pendências retomáveis após reinício.
- **Location:** implementação ausente; nome/caminho do arquivo SQLite não definido.
- **Key Components:** vínculo imutável sessão/apartamento, eventos ordenados, pendências vinculadas à execução e ao especialista, aprovação/negativa e retomada.
- **Technologies:** serviço próprio de sessões do ADK no SQLite compartilhado com o domínio; integração na mesma unidade de trabalho, a validar.
- **Dependencies:** AGENT para execução; DATA/RESERVA/VISITA para efeitos; API para aprovação exclusiva pela rota dedicada.
- **Patterns:** persistência de estado; confirmação de execução; gravação atômica do efeito, conclusão da confirmação, estado e eventos correspondentes, com rollback antes do commit. A integração ADK na mesma transação ainda precisa ser comprovada.
- **Key Files:** [PRD RF-001, RF-002, RF-007 e RF-009](../PRD.md), [decisões: Confirmações persistidas e Persistência dos eventos](../decisoes.md).
- **Scope:** pequeno no acervo — 0 arquivos de implementação; 3 tipos de estado persistente previstos: sessões, eventos e confirmações.

### RESERVA: Reservas e disponibilidade

- **Purpose:** consultar disponibilidade/listagens próprias, criar reservas e cancelar as próprias sem reutilizar códigos.
- **Location:** fontes em `dados/areas.json` e `dados/reservas.json`; tools e persistência operacional ausentes.
- **Key Components:** catálogo de áreas/taxas, agenda, reserva ativa, cancelamento com histórico, geração de código e tratamento de disputa concorrente.
- **Technologies:** JSON presente; tools Python e restrições/transações SQLite planejadas.
- **Dependencies:** DATA para cadastro e armazenamento; SESSION para apartamento e confirmação quando houver taxa; AGENT para atendimento.
- **Patterns:** isolamento por sessão, confirmação condicionada à taxa, exclusividade de área/data no instante da gravação e unicidade histórica de código. Disponibilidade global retorna apenas livre/ocupado.
- **Key Files:** [areas.json](../../dados/areas.json), [reservas.json](../../dados/reservas.json), [PRD RF-003 a RF-005](../PRD.md), [padrões técnicos aprovados](../decisoes.md).
- **Scope:** pequeno no acervo — 2 arquivos JSON, 3 áreas e 3 reservas iniciais; 0 arquivos de implementação.

### VISITA: Autorizações de visitantes

- **Purpose:** consultar autorizações próprias e registrar nome/data após aprovação válida.
- **Location:** fonte em `dados/visitantes.json`; tools e persistência operacional ausentes.
- **Key Components:** listagem por apartamento, proposta de autorização e gravação única do acesso aprovado.
- **Technologies:** JSON presente; tools Python e SQLite planejados.
- **Dependencies:** DATA, SESSION e AGENT. Uma declaração de aprovação no texto da conversa não autoriza o efeito.
- **Patterns:** autorização condicionada à confirmação, isolamento por apartamento e execução única com efeito e conclusão persistidos na mesma transação.
- **Key Files:** [visitantes.json](../../dados/visitantes.json), [PRD RF-003, RF-006 e RF-007](../PRD.md).
- **Scope:** pequeno no acervo — 1 arquivo JSON, 2 autorizações iniciais; 0 arquivos de implementação.

### DATA: Persistência de domínio e ciclo de vida

- **Purpose:** manter cadastros e fornecer armazenamento íntegro ao domínio, carga inicial e restauração.
- **Location:** fonte cadastral em `dados/apartamentos.json`; schema, banco e comandos ausentes. Nome/caminho do banco único não definido.
- **Key Components:** apartamentos e áreas; armazenamento de reservas/histórico e visitantes; carga transacional de banco vazio; preservação de banco populado; reposição de domínio e coordenação com limpeza de SESSION no reset.
- **Technologies:** JSON presente; SQLite único com conexão e transação compartilhadas por ação planejado. ORM e estratégia de migração não definidos.
- **Dependencies:** fontes RESERVA/VISITA para carga e restauração, SESSION para reset completo, API para inicialização antes de aceitar requisições.
- **Patterns:** fontes iniciais imutáveis, persistência operacional no banco único, integridade no banco e unidade de trabalho por ação. Limpeza de sessões e reposição de domínio são parte da mesma transação de reset.
- **Key Files:** [apartamentos.json](../../dados/apartamentos.json), [PRD RF-010](../PRD.md), [decisões 1 e 6 e padrões técnicos](../decisoes.md).
- **Scope:** pequeno no acervo — 1 JSON próprio, 6 apartamentos; consome outros 3 JSONs já contabilizados. 0 arquivos de implementação.

### REG: Consulta do regulamento

- **Purpose:** responder dúvidas a partir de trechos pertinentes sem propagar capítulos irrelevantes no histórico.
- **Location:** `dados/regulamento.md`; busca, segmentador e tool ausentes.
- **Key Components:** capítulos/artigos, seleção por assunto, retorno localizado e especialista de regulamento.
- **Technologies:** Markdown presente; busca local sem embeddings ou banco vetorial planejada.
- **Dependencies:** AGENT para atendimento e SESSION para persistência dos eventos resultantes.
- **Patterns:** recuperação seletiva de contexto; principal sem regulamento nas instruções. Regras operacionais fora de escopo não passam a bloquear tools por constarem no texto.
- **Key Files:** [regulamento.md](../../dados/regulamento.md), [PRD RF-008](../PRD.md), [decisão 5](../decisoes.md).
- **Scope:** pequeno no acervo — 1 arquivo, 491 linhas, 14 capítulos; 0 arquivos de implementação.

### SUPPORT: Especificação, configuração e apoio ao desenvolvimento

- **Purpose:** registrar requisitos/decisões e oferecer instruções de entrevistas para gerar documentos de produto e desenho técnico.
- **Location:** `README.md`, `docs/PRD.md`, `docs/decisoes.md`, `docs/adrs/`, `.gitignore`, `.env.example` e `.agents/skills/`.
- **Key Components:** 3 documentos de produto; 7 candidatos arquivados, 7 ADRs e 2 índices; 2 configurações; 2 skills locais, cada qual com `SKILL.md`, referência e configuração `agents/openai.yaml`.
- **Technologies:** Markdown e YAML, sem runtime da aplicação.
- **Dependencies:** demais módulos usam esse contexto como especificação; as skills não são os agentes Google ADK do produto.
- **Patterns:** documentação orientadora e separação de segredos/configuração. A existência de `.env.example` não implica que esteja versionado: ele está não rastreado neste snapshot.
- **Key Files:** [README](../../README.md), [PRD](../PRD.md), [decisões](../decisoes.md), [skill PRD](../../.agents/skills/prd-feature-interview/SKILL.md), [skill FDD](../../.agents/skills/fdd-feature-interview/SKILL.md), [.gitignore](../../.gitignore), [.env.example](../../.env.example).
- **Scope:** pequeno no acervo — 27 arquivos de entrada, excluindo este mapa; este documento gerado fica em `docs/adrs/mapping.md` e não é componente de runtime.

## Cross-Cutting Concerns

| Preocupação | Módulos | Fronteira e evidência esperada na implementação |
| --- | --- | --- |
| Isolamento e prompt injection | API, SESSION, AGENT, RESERVA, VISITA | Apartamento obtido da sessão; consultas/alterações limitadas antes de produzir resultados de tools e eventos; disponibilidade sem titular/código de terceiros |
| Confirmação e execução única | SESSION, AGENT, RESERVA, VISITA, DATA | Aprovação exclusiva pela rota; pendência vinculada à execução; `409` para ID inválido/reutilizado; efeito, confirmação, estado e eventos na mesma transação, sem duplicação após commit |
| Integridade e concorrência | RESERVA, DATA, API | Restrição no banco para reserva ativa por área/data, preservação de códigos cancelados e recusa normal com `200` na aprovação perdedora |
| Persistência e observabilidade | SESSION, DATA, API | Eventos completos/ordenados e efeitos preservados no reinício; novas mensagens na mesma sessão; nenhuma proteção baseada só em ocultar dados na leitura de eventos |
| Contexto e custo do modelo | REG, AGENT, SESSION | Recuperação de apenas trechos pertinentes; principal sem regulamento completo; inspeção dos eventos de consulta |
| Inicialização e restauração | DATA, SESSION, API, SUPPORT | Não confundir subida com reset; carga antes do atendimento; fontes preservadas; reset limpa conversas e repõe domínio na mesma transação |
| Configuração e infraestrutura | SUPPORT, AGENT, DATA, SESSION | Sem banco externo/container; chave fora do Git; dependências exatas e comandos ainda a criar; arquivo SQLite com nome ainda indefinido |
| Validação | Todos | Testes determinísticos e adversariais, reinício, rollback integral e queda após commit, concorrência e 15 passos reais com Gemini; não há testes executáveis neste snapshot |

Autenticação real, interface visual, pagamento/estorno e deploy permanecem fora do escopo. As rotas diretas de verificação pertencem ao cenário local do avaliador; não há camada administrativa implementada ou exigida para esta entrega.

## Guidelines for Phase 2

1. Usar os IDs acima para escolher um ou dois módulos por análise. AGENT + SESSION concentram a dependência de validação da retomada; DATA + RESERVA concentram integridade e concorrência; REG pode ser analisado separadamente.
2. Enquanto não houver implementação, identificar a evidência como **decisão documental aprovada** ou **requisito**, sem atribuir adoção a arquivos de código inexistentes. Este mapa não cria candidatos ou ADRs formais; os artefatos das fases seguintes já estão disponíveis nos índices em `docs/adrs/`.
3. Após implementação, atualizar localizações, contagens, dependências e histórico Git; conferir schema/restrições, integração ADK, rotas, comandos e testes antes de afirmar garantias comprovadas.
4. Implementar e comprovar o serviço de sessões próprio integrado à transação compartilhada; detalhar representação persistente das confirmações/execuções e estratégia concreta de busca. Não escolher tecnologias ou algoritmos adicionais implicitamente durante a análise.
5. Conferir acesso/cota do modelo e compatibilidade real do ADK escolhido, sem tratar as referências dos documentos como validação do ambiente atual. Incompatibilidades devem ser registradas e as decisões revisadas explicitamente.
6. Evitar transformar entidades, regras de negócio ou detalhes isolados de configuração em decisões arquiteturais. Usar contexto e histórico para explicar escolhas estruturais e consolidar preocupações que cruzam módulos.

## Revisão da persistência

Em 15/10/2026, a decisão foi revisada para um único banco e atomicidade por ação, substituindo a separação anterior em arquivos. Efeito, conclusão da confirmação, estado e eventos correspondentes devem compartilhar conexão e transação. Chamadas externas e espera pela aprovação ficam fora da transação de escrita. A integração será feita por serviço de sessões próprio, sem commits independentes; sua compatibilidade ainda não foi demonstrada. Escritores passam a disputar o mesmo arquivo.

## Verification Notes

- Inventário de arquivos comuns/ocultos e rastreamento Git conferidos; nenhum `AGENTS.md` aplicável foi encontrado nos ancestrais ou no projeto.
- README, PRD, decisões, estruturas dos JSONs e capítulos do regulamento inspecionados; contagens de dados verificadas no acervo local.
- Histórico Git consultado; não há evidência versionada de implementação a analisar.
- Arquivos de dados sem diferenças locais em relação ao `HEAD`; não foi feita comparação remota com o repositório base.
- Verificação documental apenas: nenhuma chamada Gemini, instalação de dependências, execução de API ou teste funcional foi realizada nesta fase.

Escolhas complementares aprovadas: manter o modelo Gemini atual e validar acesso/cota por chamada real e fluxo completo; nenhuma repetição automática de inferência na aplicação ou SDK, sem fallback ou reinício automático do Runner. As decisões estão fechadas, mas não comprovam implementação ou resultados de testes.
