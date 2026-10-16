# ADR-XXX: Persistência em banco SQLite único com transação compartilhada

**Status:** Aceita  
**Data:** 15-10-2026  
**ADRs relacionadas:** [Confirmações persistidas e retomada do ADK](../SESSION/ADR-XXX-confirmacoes-persistidas-e-retomada-do-adk.md); [Isolamento por apartamento](../SESSION/ADR-XXX-isolamento-por-apartamento-na-fronteira-das-tools.md)

## 1. Contexto e problema

O assistente precisa preservar conversas e efeitos de domínio após reinício,
reproduzir o estado inicial e executar ações aprovadas uma única vez.
Os JSONs fornecidos pelo desafio são fontes imutáveis, enquanto o estado
operacional deve ser persistido. O enunciado permite escolher o armazenamento.

Em 15/10/2026, o responsável revisou a escolha anterior de dois arquivos
SQLite para um banco único com transação compartilhada por ação.
A revisão prioriza simplicidade e atomicidade entre estado conversacional
e domínio, eliminando a necessidade de coordenar commits em bancos distintos.
Responsabilidades de sessão e domínio continuam logicamente separadas.

O status Aceita registra a decisão documental revisada.
Não comprova implementação, testes ou integração transacional do ADK.
O commit introdutório dos dados, de 17/09/2026, não representa a adoção
da arquitetura atual.

## 2. Fatores da decisão

- Simplificar a persistência e a reprodução do ambiente local.
- Persistir todas as gravações de uma ação atomicamente.
- Impedir efeito confirmado sem a conclusão persistida correspondente.
- Manter fontes imutáveis, restrições de integridade e histórico de códigos.
- Preservar sessões, eventos e efeitos após reinício.
- Tornar a restauração integral atômica no mesmo banco.

## 3. Opções consideradas

1. **Banco SQLite único com transação compartilhada:** escolha atual aprovada.
2. **Dois arquivos SQLite com transações independentes:** escolha anterior,
   substituída nesta revisão pela complexidade de recuperação entre commits.

Não houve avaliação comparativa ou benchmark de produtos.
A revisão decorre da análise da janela de falha entre efeito e confirmação
e da preferência explícita do responsável pela solução de banco único.
SQLite permanece uma escolha local permitida pelo enunciado.

## 4. Resultado da decisão

Adotar um banco SQLite para sessões, eventos, confirmações e domínio.
Todas as gravações locais decorrentes de uma ação compartilham conexão
e transação: efeito de domínio, conclusão da confirmação, estado da sessão
e eventos correspondentes. A resposta só é enviada após o commit.
Compartilhar apenas o arquivo com transações independentes não atende à decisão.

Cada unidade de persistência é atômica. Chamadas ao modelo e espera por
aprovação ficam fora da transação de escrita; não se abre uma transação
para toda a conversa. A integração ADK deve participar da unidade de trabalho,
sem commits próprios que dividam o resultado da ação.
A limpeza conversacional e a reposição de domínio no reset também são atômicas.

## 5. Vantagens e desvantagens das opções

### Banco único e transação compartilhada

- **Vantagem:** confirma ou reverte todas as gravações da ação em conjunto.
- **Vantagem:** simplifica armazenamento, restauração e diagnóstico local.
- **Desvantagem:** escritores conversacionais e de domínio disputam o mesmo arquivo.
- **Desvantagem:** a persistência ADK precisa compartilhar a unidade de trabalho,
  exigindo adaptação se o serviço utilizado controlar commits independentemente.

### Dois arquivos com transações independentes

- **Vantagem:** separava a disputa de locks de arquivo entre sessões e domínio.
- **Desvantagem:** permitia persistir efeito sem concluir a confirmação.
- **Desvantagem:** exigia reconhecimento e recuperação de efeitos entre commits.
- **Limitação:** nenhuma medição comprovou benefício de contenção que justificasse
  essa complexidade no cenário local do projeto.

## 6. Consequências

Falha entre escritas antes do commit reverte integralmente a ação.
Se houver queda após commit e antes da resposta, efeito, conclusão, estado
e eventos já estarão persistidos; o reenvio sequencial deve reconhecer
confirmação respondida e não reaplicar o efeito.
A exclusividade da reserva e a unicidade histórica dos códigos continuam
impostas pelo banco no instante da gravação, inclusive sob concorrência.

Carga inicial ocorre apenas quando o domínio está vazio e não sobrescreve
estado existente no reinício. A restauração limpa sessões, eventos e
confirmações e repõe o domínio em uma transação; falha preserva o estado
anterior inteiro. Os arquivos de origem permanecem inalterados.

A implementação precisa comprovar a participação da persistência ADK na
mesma transação das tools, com falhas antes e depois do commit, retomada
após reinício e disputa concorrente. O serviço de sessão não é considerado
compatível apenas por apontar para o mesmo arquivo SQLite.
A solução concreta dessa integração permanece na validação de SESSION.
Nenhuma migração de dados existentes é alegada, pois não há runtime implementado.

## 7. Referências

- [docs/decisoes.md:15](../../../decisoes.md#L15)
- [docs/PRD.md:249](../../../PRD.md#L249)
- [README.md:25](../../../../README.md#L25)
