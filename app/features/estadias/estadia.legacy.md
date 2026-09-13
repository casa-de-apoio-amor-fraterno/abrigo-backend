# Estadia

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Estadia/` (`untFrmManutencaoEstadia`,
  `untDtmManutencaoEstadia`, `untFrmRelatorioEstadia`,
  `untFrmConsultaEstadiaFoto`)
- Banco: tabelas `estadia` e `estadia_acompanhante`.

## Campos reais — `estadia` (confirmados via `untFrmManutencaoEstadia.dfm`
e o `CREATE TABLE`/dados do dump de produção `sgf_abrigo`, 2026-09-10)

`id_estadia` (int, PK), `id_pessoa`/`id_quarto`/`id_usuario` (int, FK reais
já no legado), `data_entrada` (**datetime**, obrigatório — diferente de
`pessoa.data_nascimento`/`data_cadastro`, que são `date`), `data_saida`
(datetime, opcional), `tempo_estadia` (varchar(60), texto livre — ex.:
`'06 dias '`, `'4 dias'`, grafia inconsistente, não é um valor calculado de
forma confiável a partir de `data_entrada`/`data_saida`; mantido como
string livre, não recalculado), `tipo_pessoa` (varchar(60), default
`'Paciente'` — ver decisão abaixo), `situacao` (varchar(60), obrigatório,
3 valores fixos no combo Delphi: `'Em acompanhamento'`, `'Aguardando
retorno'`, `'Finalizada'` — modelado como enum de verdade), `observacao`
(text, opcional), `ativo` (varchar(3) 'Sim'/'Não', **opcional no legado**
— `DEFAULT NULL`, diferente de `pessoa`/`usuario` onde é obrigatório;
modelado como `bool | None`).

## Campos reais — `estadia_acompanhante`

`id_estadia_acompanhante` (int, PK), `id_estadia`/`id_pessoa` (int, FK
reais já no legado), `data_entrada` (datetime, obrigatório), `data_saida`
(datetime, opcional), `grau_parentesco` (varchar(100), opcional — texto
livre, ex.: `'irmã '`).

## Decisão de design: `tipo_pessoa` × `estadia_acompanhante` (achado 3 de
`docs/atividades.md`, resolvido em 2026-09-10)

Suposição inicial (registrada em `docs/atividades.md`) era que os dois
conceitos se sobrepunham e um deveria ser eliminado. **Verificação contra a
tela real do legado (`untFrmManutencaoEstadia.dfm`) mostrou que isso está
errado**: a tela de manutenção de estadia usa os dois campos
**simultaneamente** — `dbetipo_pessoa` (combo `Acompanhante`/`Paciente`,
ligado a `tipo_pessoa`) e uma grade separada `viewAcompanhante`
(`grau_parentesco`, ligada a `estadia_acompanhante`) — não são a mesma
tela/funcionalidade.

**São conceitos diferentes:**
- `Estadia.tipo_pessoa` — papel da pessoa que **ocupa aquele leito**
  (aquela linha de `estadia`, ligada a um `id_quarto`). Uma estadia sempre
  representa uma ocupação de leito por uma pessoa; `tipo_pessoa` diz se
  essa pessoa está ali como paciente ou como acompanhante que também tem
  leito próprio (situação real observada nos dados, ex.: id_estadia 1 e 2
  no dump, ambos com leito próprio e `tipo_pessoa='Acompanhante'`).
- `EstadiaAcompanhante` — pessoas que acompanham a estadia de um paciente
  **sem necessariamente ter leito próprio**, com sua própria janela de
  entrada/saída e grau de parentesco (ex.: alguém que fica de dia mas não
  dorme no abrigo).

**Decisão: manter os dois.** `Estadia.tipo_pessoa` vira um enum de verdade
(`TipoPessoaEstadia`: `PACIENTE`/`ACOMPANHANTE`, conforme já anotado em
`pessoa.legacy.md`), e `EstadiaAcompanhante` é modelada como tabela própria
relacionada (`app/features/estadias/models.py`), não descartada.

## `acompanhamento` × `estadia_acompanhante` (achado 1 de
`docs/atividades.md`)

Mantida a decisão sugerida em `docs/atividades.md`: `acompanhamento`
(tabela antiga, 41 linhas, sem FK real — só índice) **não vira tabela
própria** no schema novo. Seus dados (`id_paciente`/`id_acompanhante`)
devem ser reconciliados com `estadia_acompanhante` na ETL (cruzando com a
`estadia` correspondente de cada paciente), não recriados como model.

## `ativo` como `bool | None`

Diferente de `pessoa`/`usuario`/`hospital`/`quarto` (onde `ativo` é
obrigatório), em `estadia` o dado real do dump mostra `ativo` como coluna
opcional (`DEFAULT NULL`). Mantido `bool | None` no model novo — não forçar
um valor default por suposição.

## Endpoints implementados
- `GET/POST /api/estadias`, `GET/PUT /api/estadias/{id}` — CRUD principal.
- `POST /api/estadias/{id}/encerrar` — atalho pra marcar `situacao =
  Finalizada` e `ativo = false` (fluxo real do legado: uma estadia é
  encerrada, não deletada).
- `GET/POST /api/estadias/{id}/acompanhantes` — sub-recurso
  `EstadiaAcompanhante`.

## Status
Mapeado e implementado (CRUD completo + sub-recurso de acompanhantes).
Dados reais entram via ETL (`docs/migracao-postgres.md`), não pela
migração Alembic. Frontend: CRUD completo (cadastro + consulta),
incluindo sub-recurso de acompanhantes.

## `tempo_estadia` depreciado em favor de `tempo_estadia_valor` +
`tempo_estadia_unidade` (migração 0017, 2026-09-12)

Pedido do time: separar o texto livre `tempo_estadia` em dois campos
estruturados — quantidade (`tempo_estadia_valor`, inteiro) e unidade
(`tempo_estadia_unidade`, enum `dias`/`noites`/`horas`) — e depreciar o
campo antigo, mantendo-o só para auditoria/histórico.

**Por que não dava pra só recalcular a partir de `data_entrada`/
`data_saida`**: o campo era texto livre sem validação na tela Delphi
(`edttempo_estadia`), e o dado real do dump de produção mostra que ele
também foi usado pra registrar observações da saída, não só duração —
achado confirmado analisando a amostra real de valores distintos do
dump (`sgf_abrigo`, tabela `estadia`, ~4432 linhas): exemplos como
`'não pernoitou'`, `'TROCA DE QUARTO'`, `'café da manhã'`, `'QUARTO
ERRADO'`, além de erros de digitação (`'2 diias'`, `'1 NIOITE'`) e
grafia por extenso (`'dois dias'`).

**Estratégia de migração (best-effort, não perde dado)**:
- Regex reconhece o padrão `"N dia(s)/noite(s)/hora(s)"`
  (case-insensitive, zero à esquerda e espaços tolerados) e popula os
  dois campos novos.
- Número sozinho sem unidade (ex.: `'1'`, `'2'` — ~600 ocorrências no
  dump) é tratado como dias, por ser a unidade largamente predominante
  no restante dos dados reais (decisão do time, não inferência).
- Quando o texto não casa com nenhum padrão reconhecível, os campos
  novos ficam `NULL` e **o texto original permanece intacto** em
  `tempo_estadia` — nunca sobrescrito nem descartado, pra quem precisar
  auditar manualmente depois.
- Resultado real (migração 0017 rodada contra o dump completo): ~3550
  de ~3685 registros com texto (96%) migrados automaticamente; os ~135
  restantes são exatamente os casos "sujos" (observação, erro de
  digitação, grafia irregular) — ficaram de fora de propósito.
- A mesma lógica (`parse_tempo_estadia`,
  `app/scripts/etl/transformacoes.py`) roda tanto na migração Alembic
  (backfill via SQL) quanto na ETL de carga inicial, pra manter os dois
  caminhos de entrada de dado consistentes.

**Frontend**: o input de texto livre "Tempo estadia" foi removido da
tela de cadastro/edição (decisão do time — não faz sentido manter um
campo depreciado editável), substituído por um input numérico +
`mat-select` de unidade. O valor legado (quando existir e não tiver
sido migrado) não aparece mais na tela — só via API, pra quem precisar
consultar o histórico bruto.

## `id_hospital` movido de `Pessoa` pra `Estadia` (migração 0020, 2026-09-13)

Mesmo raciocínio já usado pra `tipo_pessoa` (ver `pessoa.legacy.md`):
`pessoa.id_hospital` era tratado como atributo permanente da pessoa, mas o
hospital é contextual a UM atendimento — a mesma pessoa pode passar por
hospitais diferentes em estadias diferentes, e o campo fixo em `Pessoa`
sobrescrevia o valor a cada nova estadia, sem histórico.

**Levantamento no dump real antes de decidir** (`abrigo_teste`,
2026-09-13, 5.329 pessoas / 4.422 estadias):
- 5.310 pessoas (99,6%) têm `id_hospital` preenchido; 5.001 (93,9%) têm
  `observacao` preenchida.
- `id_hospital` está sobrecarregado no legado: `'Empréstimo Solidário'`
  (2.133 registros) e `'Doação de fralda'` (22) não são hospitais de
  verdade, são categoria de motivo do atendimento reaproveitando a mesma
  FK — achado que não estava óbvio antes de olhar a distribuição real.
- **2.541 dessas pessoas (quase metade) não têm nenhuma `Estadia`**: 2.065
  só têm empréstimo, 279 são acompanhantes (`EstadiaAcompanhante`) sem
  leito próprio, 197 sem vínculo nenhum. Mover o campo inteiramente pra
  `Estadia` deixaria esses registros órfãos.

**Decisão do time:** `Estadia.id_hospital` (novo, nullable) vira a fonte de
verdade quando existe estadia. `Pessoa.id_hospital`/`observacao`
**permanecem** no schema como fallback — não removidos — justamente pra não
perder o dado dessas ~2.541 pessoas sem estadia.

**Backfill** (migração 0020, SQL puro — mesmo padrão de 0018): para cada
pessoa com hospital/observação preenchidos, propaga pra sua estadia mais
recente (`data_entrada` desc — heurística, não dá pra saber retroativamente
qual estadia era a certa). `observacao` é **concatenada**
(`pessoa.observacao || '\n\n' || estadia.observacao`), nunca sobrescrita,
quando a estadia alvo já tem texto próprio (1.844 casos no dump real).
Pessoas com múltiplas estadias (~832 no dump) só recebem o backfill na mais
recente — as estadias antigas da mesma pessoa não ganham hospital/
observação adicional (assumir que o dado da pessoa valia pra TODAS as
estadias seria pior que não aplicar às antigas).

**Frontend**: `Estadia` ganhou o campo "Hospital" na aba "Dados" (ao lado
de "Observação", já existente). A aba "Atendimento" do cadastro de pessoa
continua existindo — não é mais o lugar recomendado pra registrar
hospital/observação de quem tem estadia, mas seguiu ativa pro caso de
pessoas sem estadia (empréstimo-only).

## `EstadiaHistorico` — roadmap de eventos da estadia (2026-09-13)

Mesma lacuna que motivou `EmprestimoHistorico` (ver
`emprestimos/models.py`): sem uma trilha própria, a única forma de saber o
que aconteceu durante uma estadia era o campo `observacao` livre — qualquer
edição sobrescreve o texto anterior sem deixar rastro. Sem equivalente no
legado, feature nova.

`EstadiaHistorico` (`id`, `id_estadia`, `id_usuario`, `tipo`, `observacao`,
`data_cadastro`) é gravado automaticamente pelo backend
(`service._registrar_historico`), nunca por escrita direta do cliente:

- **"Inclusão"** — ao criar a estadia (`service.criar`).
- **"Alteração"** — ao editar (`service.atualizar`), só quando algum campo
  relevante (`id_quarto`, `id_hospital`, `tipo_pessoa`, `situacao`,
  `data_entrada`, `data_saida`, `tempo_estadia_valor`/`unidade`,
  `observacao`) realmente mudou de valor — `service._descricao_alteracao`
  compara antes de sobrescrever e monta um diff tipo `"Situação: Em
  acompanhamento -> Finalizada"`. Um PUT idempotente (nada muda) não gera
  entrada vazia no histórico.
- **"Encerramento"** — ao chamar `POST /{id}/encerrar`, só se `id_usuario`
  foi informado no corpo (`EstadiaEncerrarRequest.id_usuario`, opcional —
  ver nota abaixo).

**Por que `id_usuario` é opcional em `EstadiaEncerrarRequest`:** esse
endpoint já tinha chamadores em produção (frontend) sem esse campo antes
desta feature existir. Tornar obrigatório quebraria quem ainda não foi
atualizado pra mandá-lo — em vez disso, o encerramento simplesmente não
fica no histórico quando `id_usuario` não vem, e o resto do fluxo
(finalizar a estadia) funciona normalmente. Não cobre ainda inclusão/
remoção de `EstadiaAcompanhante` (sem `id_usuario` no schema atual) — fica
como próximo passo natural se a equipe quiser esse evento no roadmap
também.

`GET /api/estadias/{id}/historico` retorna a lista ordenada por
`data_cadastro` decrescente (mais recente primeiro), mesmo padrão de
`GET /api/emprestimos/{id}/historico`.
