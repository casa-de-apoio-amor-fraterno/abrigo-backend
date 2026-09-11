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
migração Alembic. Frontend: só serviço de apoio por ora, tela de
consulta/cadastro ainda não implementada (já existe rota placeholder no
`app.routes.ts`).
