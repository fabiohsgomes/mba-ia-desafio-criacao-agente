# Decisões do assistente do Residencial Aurora

Data: 15/10/2026.

Status: decisões aprovadas para orientar a implementação. Este documento não representa funcionalidades já implementadas ou testes já executados.

## Contexto e limites

Este documento registra as decisões de arquitetura, operação e validação do assistente do Residencial Aurora, respeitando o contrato da API, as regras de negócio e as cinco garantias obrigatórias do projeto.

A prioridade é simplicidade operacional com garantias robustas implementadas em código. A entrega continua sendo uma API local, sem interface visual, autenticação real, pagamento, estorno ou deploy. Não serão acrescentadas regras de antecedência, datas passadas, horários ou capacidade às operações. Os arquivos de `dados/` devem permanecer inalterados.

## Decisões aprovadas

### 1. API e armazenamento

- Usar FastAPI + Pydantic para a API e a validação dos dados, com SQLite para armazenamento, sem banco em container ou outro serviço externo de armazenamento.
- Usar um único banco SQLite para sessões, eventos, confirmações e dados de domínio, como apartamentos, áreas, reservas e visitantes.
- Persistir todas as gravações decorrentes de uma ação na mesma transação local: efeito no domínio, estado da sessão, eventos correspondentes e conclusão da confirmação, quando houver. As camadas devem compartilhar a mesma conexão e o mesmo controle transacional nessa unidade de trabalho, sem commits independentes do serviço de sessão ou das tools. Um arquivo compartilhado com transações distintas não atende à decisão.
- Ao subir a API, verificar se as tabelas de domínio estão vazias. Nesse caso, importar os dados dos arquivos JSON de `dados/` para as tabelas de domínio do banco único antes de aceitar requisições.
- Executar a carga inicial em uma transação, sem deixar uma importação parcial. Se o domínio já estiver populado, preservar seu estado, sem reimportar os JSONs no reinício.
- Manter os arquivos JSON imutáveis: as operações da API devem ler e gravar os dados de domínio no banco, sem modificar os arquivos de origem.

Justificativa: reduzir dependências operacionais, facilitar a reprodução do ambiente e eliminar a janela de falha entre o efeito de domínio e a conclusão da confirmação por meio de uma transação única por ação.

Consequência: reiniciar a API não pode reinicializar os dados nem apagar conversas. O contrato HTTP e seus formatos devem ser preservados.

### 2. Versão do Google ADK

- Fixar a dependência em `google-adk==2.12.0`.
- Manter Python 3.12 ou superior e gerenciamento por uv, com `pyproject.toml` e `uv.lock` versionados.

Justificativa: a versão 2.12.0 foi escolhida explicitamente nesta conversa e atende à exigência da série 2, igual ou superior à 2.2.0.

Consequência: a confirmação persistida precisa ser validada nessa versão. Resultados obtidos em outras versões não comprovam compatibilidade com a versão escolhida.

### 3. Agentes e responsabilidades

Usar um agente principal e três especialistas:

| Agente | Responsabilidade |
|---|---|
| Principal | Receber o morador e encaminhar a solicitação ao especialista adequado. |
| Reservas | Consultar disponibilidade, listar as próprias reservas, reservar e cancelar por meio de tools. |
| Visitantes | Consultar as próprias autorizações e solicitar autorização de entrada por meio de tools. |
| Regulamento | Consultar trechos pertinentes do regulamento e responder dúvidas com base neles. |

O principal acionará os especialistas por transferência de atendimento usando subagentes do ADK.

Justificativa: separar responsabilidades por domínio e tornar explícito quais tools e informações cada especialista utiliza.

Consequência: a retomada de confirmação deve chegar ao especialista que a solicitou. A topologia escolhida precisa ser validada com sessão persistida e após reinício da API.

### 4. Modelo Gemini

- Usar `gemini-3.8-flash` nos quatro agentes.
- Permitir configurar o identificador compartilhado pela variável `GEMINI_MODEL`.
- Usar chave do Google AI Studio, mantida fora do Git. O `.env.example` deve listar as variáveis necessárias sem valores.

Justificativa: um único modelo simplifica a configuração e a análise de comportamento dos agentes.

Consequência: disponibilidade e cota no projeto do usuário ainda precisam ser verificadas. A presença do modelo no catálogo oficial não comprova acesso nesse projeto.

### 5. Consulta ao regulamento

- Usar busca local por assunto, sem embeddings ou banco vetorial.
- Segmentar o Markdown por capítulos e artigos e retornar somente os trechos pertinentes à pergunta.
- Não incluir o regulamento completo nas instruções do principal ou nos eventos da sessão.

Justificativa: o documento local tem estrutura explícita e permite começar com uma recuperação simples, evitando dependências adicionais e contexto desnecessário.

Consequência: a seleção de trechos precisa ser validada para não introduzir capítulos de outros assuntos nos eventos. As restrições operacionais fora de escopo não serão acrescentadas às tools apenas por constarem no regulamento.

### 6. Restauração do ambiente

- O comando de restauração deve limpar sessões, eventos e confirmações, incluindo as pendentes, na mesma transação que repõe os dados de domínio.
- Os dados de domínio devem ser restaurados ao estado inicial a partir dos JSONs de `dados/`, incluindo apartamentos, áreas, reservas e visitantes. Reposição e limpeza conversacional devem ser atômicas: confirmar tudo junto ou reverter tudo em caso de falha.
- A restauração não deve alterar os arquivos originais em `dados/`.

Justificativa: produzir um ambiente limpo e reproduzível para cada execução do fluxo de avaliação, sem pendências baseadas no estado anterior.

### 7. Nova mensagem durante confirmação pendente

- Responder `200` no formato normal da rota de mensagens, com orientação para resolver a pendência e a lista de confirmações pendentes da sessão.
- Não iniciar outra execução enquanto houver confirmação pendente.
- Aprovação ou negativa deve ocorrer exclusivamente pela rota de confirmações.

Justificativa: reduzir a complexidade de retomada e impedir que mensagens de conversa sejam interpretadas como autorização.

### 8. Apartamento inexistente

Retornar `404` para apartamento ausente de `dados/apartamentos.json`, tanto na criação de sessão quanto nas rotas de verificação.

Justificativa: adotar um comportamento consistente para um recurso que não existe.

### 9. Validação

- Criar testes automatizados das garantias.
- Validar também o fluxo real com Gemini, seguindo os 15 passos do avaliador.

Justificativa: confirmar que as regras continuam válidas independentemente das decisões do modelo, inclusive em reinícios e disputas simultâneas.

## Padrões técnicos aprovados

### Isolamento por apartamento

O apartamento é definido uma única vez na criação da sessão. As tools devem obtê-lo exclusivamente da sessão, sem permitir que o modelo escolha o apartamento de uma operação. Consultas e alterações devem ser limitadas ao apartamento dessa sessão.

A consulta de disponibilidade pode examinar a agenda global, mas deve retornar apenas livre ou ocupado, sem identificar o titular ou o código da reserva de outro apartamento. Essa proteção também se aplica aos retornos de tools gravados nos eventos.

### Exclusividade de reservas e preservação dos códigos

A exclusividade de reserva ativa por área e data deve ser imposta por restrição nas tabelas de domínio do SQLite, no instante da gravação, dentro de uma transação. Uma verificação prévia de disponibilidade pode melhorar a resposta, mas não substitui a restrição.

O cancelamento deve preservar o histórico. Os códigos gerados pelo sistema devem ter unicidade garantida inclusive em relação às reservas iniciais e às canceladas.

Na disputa entre duas aprovações, apenas uma reserva deve ser criada. A execução perdedora deve produzir uma recusa normal, sem expor dados de terceiros e sem erro de servidor; ambas as rotas de aprovação devem responder `200`.

### Confirmações persistidas

As confirmações devem ser persistidas no banco único e vinculadas à sessão e à execução do ADK que as originou, mantendo as informações necessárias para retomar o especialista solicitante. Efeito de domínio, conclusão da confirmação e estado/eventos correspondentes devem ser gravados na mesma transação. Falha antes do commit reverte todas essas gravações; após commit, a conclusão persistida impede reaplicar o efeito. A resposta HTTP deve ocorrer depois do commit. A integração com o ADK deve participar dessa unidade de trabalho, sem confirmação de gravações em transações independentes.

Reservas com taxa e autorizações de visitantes só podem produzir o efeito após aprovação pela rota de confirmações. O código deve impedir qualquer execução direta baseada em texto do morador. A negativa não executa a ação proposta.

A rota deve aceitar somente um identificador pendente na sessão informada. Identificadores inexistentes, de outra sessão ou já respondidos recebem `409`, sem executar a ação. Aprovar deve executar a ação uma única vez.

Reservas sem taxa e cancelamentos de reservas do próprio apartamento não devem gerar confirmação.

### Persistência dos eventos

Os eventos completos, incluindo chamadas de tools, devem sobreviver ao reinício e continuar disponíveis em ordem pela rota de eventos. A mesma sessão deve aceitar novas mensagens após o reinício.

## Validações ainda necessárias

Estas são verificações de implementação, não decisões de produto em aberto:

- Confirmar acesso e cota de `gemini-3.8-flash` no projeto do Google AI Studio utilizado.
- Comprovar a integração entre ADK 2.12.0, transferência entre especialistas e persistência em SQLite, especialmente a retomada de confirmação após reiniciar a API com a ação ainda pendente.
- Testar aprovação, negativa, identificador inexistente, identificador de outra sessão e reenvio de confirmação já respondida.
- Testar isolamento nas respostas e nos eventos, incluindo tentativas de trocar o apartamento pela conversa.
- Testar persistência de reservas, cancelamentos, visitantes e eventos após reinício.
- Testar a carga automática dos JSONs quando as tabelas de domínio estiverem vazias, a preservação de um banco já populado e a ausência de alterações nos arquivos de origem.
- Testar o reset atômico do banco único: sessões, eventos e confirmações apagados e dados de domínio restaurados integralmente a partir dos JSONs.
- Testar rollback integral com falha entre as escritas do efeito, da confirmação e dos eventos antes do commit; testar queda após commit e antes da resposta, preservando conclusão e efeito único no reinício e reenvio sequencial.
- Testar duas aprovações simultâneas de sessões diferentes para a mesma área e data, garantindo uma única reserva ativa e duas respostas HTTP `200`.
- Testar consulta ao regulamento com resposta correta e sem trechos de capítulos irrelevantes nos eventos.
- Executar o fluxo completo do avaliador, incluindo restauração e conferência de que os dados originais permanecem inalterados.

Se a validação demonstrar incompatibilidade com uma escolha aprovada, registrar o impedimento e revisar a decisão explicitamente, sem apresentar a alternativa como se já tivesse sido aprovada nesta conversa.

## Referências

Referências oficiais consultadas em 15/10/2026:

- [Google ADK 2.12.0 no PyPI](https://pypi.org/project/google-adk/2.12.0/): publicação da versão escolhida.
- [Catálogo de modelos Gemini](https://ai.google.dev/gemini-api/docs/models): identificador do modelo escolhido; disponibilidade por projeto requer verificação própria.
- [Confirmação de ações no ADK](https://adk.dev/tools-custom/confirmation/): fluxo de confirmação e limitações documentadas de persistência, a validar na combinação adotada.


## Esclarecimento sobre justificativas e alternativas

Em 15/10/2026, o responsável esclareceu que não houve comparação de alternativas. As escolhas foram feitas para atender aos requisitos do projeto: API Python com Google ADK e Gemini, principal e especialistas, confirmação de cobrança e acesso, isolamento por apartamento, persistência após reinício, consulta seletiva do regulamento e exclusividade de reserva por área/data, com os critérios de simplicidade e separação de responsabilidades já registrados neste documento. Não se exige avaliação comparativa retrospectiva para completar as ADRs.

O documento de requisitos exige, entre outros pontos, Google ADK, Gemini, principal e especialistas e as cinco garantias. FastAPI/Pydantic, um banco SQLite, três especialistas por transferência e um modelo compartilhado concretizam esses requisitos dentro das escolhas permitidas; são decisões de arquitetura aprovadas. Permanecem válidas as pendências de definição técnica e validação, incluindo comprovação do serviço de sessões próprio na transação compartilhada, retomada persistida e acesso/cota do Gemini. A política aprovada é não repetir automaticamente chamadas ao modelo.


## Revisão aprovada: banco único e atomicidade por ação

Em 15/10/2026, o responsável substituiu a decisão anterior de dois arquivos SQLite por um banco único e uma transação compartilhada por ação. A simplificação e a atomicidade substituem a separação de locks como prioridade. As tabelas conversacionais e de domínio continuam com responsabilidades lógicas distintas.

A transação abrange todas as gravações locais decorrentes da ação, inclusive efeitos, conclusão da confirmação, estado e eventos correspondentes. Chamadas ao Gemini e espera pela aprovação acontecem fora da transação de escrita; não se mantém uma transação aberta durante uma conversa inteira. Cada unidade de persistência deve ser atômica. Negativa e recusa por indisponibilidade também persistem seu resultado e encerramento de forma consistente, sem efeito de domínio.

A integração de persistência do ADK deve permitir compartilhar a unidade de trabalho com as tools. Se o serviço utilizado executar commits próprios, precisará ser adaptado para cumprir esta decisão; apontá-lo para o mesmo arquivo não basta. A solução concreta e sua comprovação permanecem parte da validação da integração, sem compatibilidade presumida. A contenção entre escritores passa a ocorrer no mesmo arquivo e deve ser tratada sem quebrar a disputa concorrente exigida pelo documento de requisitos.


## Escolhas aprovadas para integração e validação

Em 15/10/2026, o responsável escolheu as opções 1-A, 2-A e 3-A apresentadas na discussão das lacunas:

- **Serviço de sessões próprio:** implementar a persistência exigida pelo ADK em um serviço próprio, integrado à mesma unidade de trabalho das tools. Sessões, eventos, confirmações e efeitos de domínio usam o SQLite único e compartilham conexão/transação por ação. O serviço deve conservar os vínculos necessários para retomar o especialista solicitante após reinício. A escolha está aprovada; implementação e compatibilidade com ADK 2.12.0 precisam ser comprovadas.
- **Manter o modelo aprovado:** continuar com `gemini-3.8-flash`, compartilhado pelos quatro agentes e configurável por `GEMINI_MODEL`. Verificar acesso e cota no projeto utilizado com uma chamada real e depois com o fluxo completo do avaliador. Não há evidência de sucesso dessas verificações ainda. Se falharem, registrar o impedimento e revisar a decisão explicitamente; não substituir o modelo automaticamente.
- **Sem repetição automática do Gemini:** cada chamada planejada de inferência tem uma única tentativa. A aplicação e a configuração do SDK devem impedir retries automáticos. Uma conversa pode exigir várias chamadas distintas para encaminhamento ou tools; a proibição trata de repetir uma chamada que falhou. Não reiniciar automaticamente o Runner, não reaplicar tools e não usar fallback automático de modelo. Falhas devem ser informadas sem alegar sucesso inexistente. Se o efeito já tiver sido confirmado por commit, preservar e informar o resultado persistido sem nova execução ou nova tentativa de inferência. Falha antes de commit respeita o rollback da unidade de trabalho.

Não há decisão pendente entre as opções apresentadas. Continuam necessárias as provas de integração transacional, retomada, acesso/cota e comportamento sem repetição, além dos demais testes já previstos.
