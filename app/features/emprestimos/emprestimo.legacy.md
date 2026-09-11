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

## `emprestimo_historico` (adicionada 2026-09-11)

Trilha de auditoria — **não existe no dump de produção original**
(`sgf_abrigo`, 2026-09-09), foi criada no legado *depois* do dump, via
`abrigo-legacy/Scripts/Atualização Setembro 2026/Criar tabela
emprestimo_historico.sql` (autor: Samuel Parastchuk, 2026-09-09). Registra
automaticamente cada criação de empréstimo, alteração de observação, ou
inclusão/edição de item — nunca escrita diretamente pelo cliente da API.

Campos: `id_emprestimo_historico` (PK), `id_emprestimo`/`id_usuario` (FK),
`tipo` (varchar(20), texto livre — valores observados na lógica original:
`'Inclusão'`, `'Alteração'`, `'Item incluído'`, `'Item alterado'`;
`'Item removido'` existe no legado mas nunca ocorre no backend novo porque
não há endpoint de exclusão de item), `observacao` (text, obrigatório —
descrição gerada automaticamente, não digitada pelo usuário),
`data_cadastro` (datetime, obrigatório).

Lógica replicada de `untDtmManutencaoEmprestimo.pas`
(`RegistrarHistorico`, `qryDadosBeforePost`, `SalvarDetalhe`) em
`service.py` (`_registrar_historico`, `_descricao_item`):
- Criar empréstimo → `tipo='Inclusão'`, `observacao='Cadastro do registro.'`
- Editar empréstimo, só se `observacao` mudou → `tipo='Alteração'`. Se o
  texto novo começa com o texto antigo (caso comum: usuário vai
  completando a observação), guarda só o trecho acrescentado; senão guarda
  `'Observação alterada de "X" para "Y"'`.
- Incluir/editar item → `tipo='Item incluído'`/`'Item alterado'`,
  `observacao` no formato `"{descrição do material} (situação: X, data
  empréstimo: dd/mm/yyyy, data devolução: dd/mm/yyyy ou -)"`.

`EmprestimoItemCreate`/`Update` ganharam campo `id_usuario` (mesmo padrão
de `Estadia.id_usuario` — client-supplied, não vem de `usuario_atual`) só
pra alimentar o histórico; não é persistido na linha do item.

**Gap conhecido, não implementado:** o legado também atualiza
`Material.situacao` automaticamente a cada item incluído/editado/removido
(`AtualizarSituacaoMaterial`) — o backend novo não replica esse
side-effect ainda. Ficou fora de escopo desta mudança (só histórico foi
pedido); considerar ao revisar o fluxo completo de Material↔Empréstimo.

Migração `0010_emprestimo_historico`. 7 testes novos cobrindo
inclusão/alteração/item, incluindo os dois casos de diff de observação
(acréscimo vs. substituição total) e o caso "sem mudança não registra".

## Status
Mapeado e implementado (CRUD completo + sub-recurso de itens + histórico
de auditoria). Dados reais (exceto histórico, que não existia no dump)
entram via ETL (`docs/migracao-postgres.md`), não pela migração Alembic.
