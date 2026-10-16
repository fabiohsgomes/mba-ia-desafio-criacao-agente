# Potencial ADR: Integração Gemini compartilhada entre os agentes

**Módulo:** AGENT  
**Categoria:** Tecnologia — infraestrutura de IA crítica ao produto (Step 0)  
**Prioridade:** Must Document — **110/150**  
**Data de identificação:** 2026-10-15

## O que foi identificado

Decisão documental aprovada: integrar os quatro agentes ao Gemini mediante chave do Google AI Studio e compartilhar o identificador de modelo configurável. O objeto arquitetural é a dependência externa de inferência e sua estratégia comum entre agentes; o valor `gemini-3.8-flash` e o nome `GEMINI_MODEL` são detalhes dessa estratégia, sem candidatura separada.

O requisito original exige Gemini e chave do Google AI Studio desde o commit `be87e1d`, de 17/09/2026. O compartilhamento entre os quatro agentes foi registrado nas decisões datadas de 15/10/2026, não rastreadas no snapshot. Não existe integração executável, nem evidência de acesso, cota ou teste do modelo escolhido neste projeto.

## Por que pode merecer uma ADR

- **Impacto:** todas as conversas dependem do provedor externo; rotas diretas de verificação permanecem independentes do modelo.
- **Trade-offs:** compartilhar o modelo simplifica configuração e análise de comportamento, mantendo dependência comum de disponibilidade e cota.
- **Complexidade:** falhas externas não podem ser apresentadas como efeitos já realizados; a política aprovada proíbe repetição automática na aplicação e no SDK, sem reiniciar Runner ou reaplicar tools.
- **Conhecimento da equipe:** implementação conversacional e operação local exigem compreender credenciais, limites e evidência de efeitos persistidos.
- **Implicações futuras:** substituir a integração requer rever cliente/runtime e validar comportamento das tools; trocar apenas o identificador é mudança de configuração.
- **Contexto temporal:** estratégia planejada para a vida do produto; não há histórico operacional que comprove estabilidade.

### Filtro e pontuação

Passa pelos 3 E: estrutural (integração de IA central), evidente (razão do compartilhamento e dependências), estável (provedor e estratégia comuns). Step 0 de infraestrutura de IA crítica, base 70; a aplicação da base recai sobre a integração, não sobre uma string de configuração.

| Parcela | Pontos | Justificativa |
| --- | ---: | --- |
| Base Step 0 | 70 | Infraestrutura de IA essencial ao atendimento |
| Escopo e impacto | 20 | Dependência central da orquestração e de todos os especialistas |
| Custo de mudança | 5 | Estimativa inferior a uma semana neste estágio sem runtime; não é migração medida |
| Conhecimento da equipe | 15 | Importante para integração, operação e validação conversacional |
| **Total** | **110** | **Must Document** |

## Evidências encontradas no repositório

O requisito original exige modelos Gemini com chave do Google AI Studio e permite escolher o modelo de cada agente. A seleção deve considerar a documentação oficial e os limites ativos do projeto, que podem mudar; o fluxo de avaliação demanda algumas dezenas de chamadas. A chave deve ficar fora do Git, em `.env`, e `.env.example` deve conter somente os nomes das variáveis, sem valores. O compartilhamento do modelo entre os quatro agentes é uma decisão local, sem acesso ou cota comprovados por este documento.

### Arquivos principais

- [decisoes.md](../../../../decisoes.md#L54), linhas 54–62 e 137–138: compartilhamento, justificativa e verificação pendente.
- [PRD.md](../../../../PRD.md#L140), linha 140: ausência de política aprovada sem repetição automática diante de falha externa.
- [PRD.md](../../../../PRD.md#L459), linhas 459–462 e 497–499: estratégia comum e validação de acesso pendente.

### Evidência documental — sem código executável

Trechos literais de `docs/decisoes.md`:

```text
56: - Usar `gemini-3.8-flash` nos quatro agentes.
57: - Permitir configurar o identificador compartilhado pela variável `GEMINI_MODEL`.
60: Justificativa: um único modelo simplifica a configuração e a análise de comportamento dos agentes.
62: Consequência: disponibilidade e cota no projeto do usuário ainda precisam ser verificadas. A presença do modelo no catálogo oficial não comprova acesso nesse projeto.
```

### Análise de impacto e histórico

- Consultados logs de introdução e recentes dos documentos e busca por palavras-chave no histórico. Só há o commit inicial do documento de requisitos; não há migração de provedor ou validação de inferência versionada.
- A data de aprovação documental é 15/10/2026; não é data de implantação.
- Evidências em três documentos compartilhados e zero arquivos de integração executável.
- Afeta AGENT e atendimento de RESERVA, VISITA e REG, com consequências para API e SESSION quando a execução externa falha.

### Alternativas observáveis

O requisito original deixa livre o modelo de cada agente; o documento posterior adota um modelo compartilhado. Não houve comparação entre provedores ou modelos; não há fallback automático aprovado. Não inventar seleção por custo ou qualidade sem evidência.

## Perguntas para a ADR formal

- Qual problema de configuração e análise motivou compartilhar um modelo entre domínios?
- Que evidências demonstram acesso e cota no projeto utilizado?
- Como os efeitos persistidos serão distinguidos de respostas do modelo diante de falha externa?
- Como comprovar a política aprovada de nenhuma repetição automática e preservar resultados já confirmados quando a inferência falhar?

## Potenciais ADRs relacionados

- [Orquestração ADK e transferência](./orquestracao-adk-com-principal-e-especialistas-por-transferencia.md).
- SESSION: relacionar confirmação persistida e recuperação de efeitos, se identificado no índice consolidado.

## Notas adicionais

Não havia `docs/adrs/generated/` ao iniciar a análise; não foram encontrados ADRs formais para comparação. A candidatura deve ser descartada como duplicata se a futura ADR de orquestração absorver explicitamente a integração com provedor; nesse caso, consolidar os dois contextos. O identificador exato do modelo, `GEMINI_MODEL`, a chave e o pin ADK não merecem documentos individuais. Disponibilidade atual do catálogo e compatibilidade não foram investigadas: este candidato registra somente as fontes locais e suas pendências.

Escolhas complementares aprovadas: manter o modelo atual, validar acesso/cota com chamada real e fluxo completo e não repetir automaticamente inferência, inclusive no SDK. Não reiniciar Runner nem repetir tools após falha. As verificações de acesso ainda não foram executadas.
