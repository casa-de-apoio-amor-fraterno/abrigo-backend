# Empréstimo

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Emprestimo/` (`untFrmManutencaoEmprestimo`,
  `untDtmManutencaoEmprestimo`, `untFrmConsultaEmprestimo`,
  `untDtmConsultaEmprestimo`)
- Banco: tabelas `emprestimo` e `emprestimo_item`.

## Campos reais — `emprestimo` (confirmados no `CREATE TABLE`/dados do
dump de produção `sgf_abrigo`, 2026-09-10)

`id_emprestimo` (int, PK), `id_pessoa`/`id_usuario` (int, FK reais já no
legado — a pessoa que toma o(s) item(ns) emprestado(s) e o usuário que
registrou), `situacao` (varchar(60), obrigatório — texto livre
(`TStringField`, sem combo fechado, mesmo padrão de `material.situacao`);
dado real observado: `'Pendente'`, `'Devolvido'`), `numero_contrato`
(varchar(60), opcional), `observacao` (text, opcional — no dado real usado
pra registrar responsável pelo empréstimo com RG/CPF quando a pessoa
cadastrada não é quem retirou o item), `ativo` (varchar(3) 'Sim'/'Não',
obrigatório, default `'Sim'` — modelado como `boolean`).

## Campos reais — `emprestimo_item`

`id_emprestimo_item` (int, PK), `id_emprestimo`/`id_material` (int, FK
reais já no legado), `data_emprestimo` (date, opcional), `data_devolucao`
(date, opcional), `situacao` (varchar(60), opcional — texto livre, ex.:
`'Devolvido'`), `renovacao` (varchar(60), opcional — **texto livre, não é
data nem boolean**; dado real tem valores como `'até 22/03/2019 até
22/05/2019 Devolvido 02/07/2019'` — histórico de renovações registrado
manualmente em texto corrido, mantido fiel ao dado real).

Um empréstimo pode ter vários itens (`emprestimo_item`), cada um associado
a um `material` diferente — por isso `EmprestimoItem` é modelada como
sub-recurso de `Emprestimo` (mesmo padrão de `EstadiaAcompanhante` em
`estadias`), não como feature própria de topo.

~2.583 empréstimos / ~3.591 itens reais. CRUD completo pro empréstimo
(busca por pessoa/situação, inativação lógica); sub-recurso de itens com
`GET`/`POST`/`PUT` (sem exclusão — no legado um item de empréstimo não é
removido, só tem sua situação atualizada pra "Devolvido").

## Status
Mapeado e implementado (CRUD completo + sub-recurso de itens). Dados reais
entram via ETL (`docs/migracao-postgres.md`), não pela migração Alembic.
