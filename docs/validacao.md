# Validação da implementação Aurora

Data: 16/10/2026. Escopo: PRD, FDD e as sete ADRs aceitas. Os dados de origem permanecem imutáveis. Este registro complementa os documentos de desenho, que preservam a descrição anterior à implementação.

## Ambiente

| Componente | Versão validada |
| --- | --- |
| Python / SQLite | 3.13.5 / 3.46.1 |
| uv | 0.12.13 |
| google-adk | 2.12.0 |
| google-genai | 2.31.0 |
| FastAPI / Pydantic | 0.141.1 / 2.14.1 |
| Uvicorn / HTTPX | 0.54.0 / 0.28.1 |
| pytest / pytest-asyncio | 9.1.1 / 1.4.0 |
| Gemini | `gemini-3.8-flash`, acesso real confirmado com a chave local |

As versões resolvidas estão em `uv.lock`. Não há afirmação de compatibilidade testada com Python 3.12 ou outros releases do ADK.

## TDD e resultados locais

As falhas iniciais observadas incluíram:

| Incremento | Red observado | Resultado verificado após implementação/correção |
| --- | --- | --- |
| Serviço de sessões | `NotImplementedError` ao criar sessão | Sessão preservada ao reconstruir o adaptador |
| Portão ADK | Zero pendências em vez de uma | Transferência, proposta sem efeito e retomada na mesma invocação/especialista |
| Contrato e jornadas | `404` em criação de sessão, esperado `201` | Criação, consultas, mensagens, confirmação e erros do contrato |
| Regulamento | Busca sem resultado; artigo 22 ausente dos eventos | Horários completos recuperados, sem artigos/capítulos alheios |
| Tools em lote | `502` para proposta paga junto com reserva gratuita | Efeito gratuito persistido e proposta paga preservada sem execução |
| Timeout | `502` em vez de `504` | Cancelamento do transporte, uma tentativa e ausência de efeitos tardios |
| Entrada vazia | Apartamento só com espaços retornava `404` | Corpo inválido retorna `422` sem inferência |
| Apresentação após falha | Resultado serializado não atendia à asserção de resposta legível | Texto determinístico informa a reserva realizada e a continuação não concluída |

Resultado da suíte padrão: **37 testes aprovados, 1 skipped** (teste externo executado separadamente), em 3,79 segundos. O ADK emitiu três avisos de recursos experimentais. Os testes CLI comprovaram reset sem chave e falha sanitizada para configuração inválida. `uv run aurora probe` também concluiu uma inferência real com sucesso.

A suíte local verifica isolamento de leitura/escrita e de deltas de estado; negativa e aprovação; reenvio e ID alheio; pendências múltiplas; concorrência; integridade SQL; falhas injetadas após efeito, conclusão, estado, eventos e antes do commit; reset atômico; catálogo parcial; erro de importação; falha de geração após commit; e logs sem conteúdo conversacional.

O teste de queda após commit encerra um subprocesso com `os._exit` antes da inferência que apresentaria o resultado. Na reconstrução da API, a reserva e seu evento permanecem, e reenviar a confirmação retorna `409`. A instrumentação da fronteira transacional verifica que efeito, conclusão, estado e eventos ocorrem em uma unidade, e que nenhuma inferência observa transação de escrita aberta ou resultado provisório.

## Correspondência com o FDD

| Critérios | Evidência executável |
| --- | --- |
| AT-01, AT-02 | `pyproject.toml`, `uv.lock`, CLI, README e `tests/test_api.py` |
| AT-03, AT-04 | Isolamento, cancelamento alheio e delta de identidade em `tests/test_api.py`; cenário real nos passos 3, 4 e 10 |
| AT-05, AT-06 | Confirmação obrigatória, negativa, reenvio, reserva gratuita e cancelamento próprio em `tests/test_api.py` |
| AT-07, AT-08 | Aprovações simultâneas em `tests/test_api.py`; restrições SQL e códigos cancelados em `tests/test_storage.py` |
| AT-09, AT-10, AT-13 | Falhas por etapa, queda do subprocesso e instrumentação transacional em `tests/test_api.py` |
| AT-11, AT-12 | `tests/test_session_gate.py`, recriação da API em `tests/test_api.py`, reinícios de processo com Gemini em `tests/test_live.py` |
| AT-14, AT-15 | `tests/test_storage.py`, hash das fontes no teste real e `git diff --exit-code HEAD -- dados/` |
| AT-16 | `tests/test_regulation.py` e passo 12 de `tests/test_live.py` |
| AT-17, AT-18 | Transporte do SDK recebendo 429/503 e timeout em `tests/test_transport.py`; lock SQLite em `tests/test_api.py` |
| AT-19, AT-20 | Geração após commit e logs sanitizados em `tests/test_api.py`; contagem/duração de inferência no adaptador Gemini |
| AT-21 | Serialização da mesma sessão e concorrência de sessões distintas em `tests/test_api.py` |
| AT-22 | `tests/test_live.py`, execução opt-in com Gemini real e servidor HTTP |

## Execução real

Comando executado: `AURORA_RUN_LIVE=1 uv run pytest tests/test_live.py -q -s --tb=short`.

Resultado: **1 teste aprovado em 163,03 segundos**. Os passos **1 a 15 foram aprovados**, incluindo isolamento nas respostas/eventos, negativa e aprovação, reenvio com `409`, visitante sem aprovação textual, piscina aos domingos, continuidade depois de reinício e duas aprovações concorrentes com uma única reserva.

Depois dos 15 passos, a mesma execução comprovou três retomadas adicionais após reinício real do processo: reserva aprovada, visitante aprovado e visitante negado. Os testes conferiram a presença do resultado da tool no especialista e na invocação originais.

O teste usa banco temporário próprio, HTTP e reinícios da API sem reset. Não exporta conversas nem credenciais para este documento ou para os logs operacionais. A execução é adicional à suíte padrão, em que ele aparece como skipped por depender de acesso externo.

As verificações `uv sync --locked`, `uv lock --check`, `git diff --check` e `git diff --exit-code HEAD -- dados/` passaram. A chave local não foi alterada nem adicionada ao controle de versão.

## Limites da evidência

Os testes cobrem cenários e invariantes especificados; não constituem prova de qualidade de interpretação para toda redação possível do morador. A cota e o acesso ao Gemini podem mudar. Não há validação de múltiplos processos ou escala de produção. Aliases locais do regulamento pedem esclarecimento quando não há seleção inequívoca. Recursos experimentais de confirmação/retomada do ADK são usados na versão fixada e exercitados pelos testes.
