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
registrou), `situacao` (varchar(60), obrigatório — ver achado abaixo,
2026-09-11: não é texto livre digitado pelo usuário, é calculado a partir
dos itens; dado real observado: `'Pendente'`, `'Devolvido'`),
`numero_contrato` (varchar(60), opcional), `observacao` (text, opcional —
no dado real usado pra registrar responsável pelo empréstimo com RG/CPF
quando a pessoa cadastrada não é quem retirou o item), `ativo` (varchar(3)
'Sim'/'Não', obrigatório, default `'Sim'` — modelado como `boolean`).

**`situacao` (cabeçalho) é calculada, não digitada (achado 2026-09-11).**
O campo no legado (`untFrmManutencaoEmprestimo.dfm`, `cxDBTextEdit3`) é um
`TcxDBTextEdit` com `Enabled = False` — só exibição. O valor real vem de
`AtualizarSituacaoEmprestimo` (`untFrmManutencaoEmprestimo.pas`), chamada
toda vez que um item é salvo (`btnSalvarItemClick`): varre todos os itens
do empréstimo e aplica, nesta ordem de prioridade, as mesmas 3 constantes
de `CasaApoio.Material.Constants.pas` usadas no combo do item — qualquer
item `'Renovado'` vence; senão qualquer item `'Pendente'` vence; só vira
`'Devolvido'` se **todos** os itens estiverem `'Devolvido'`; sem itens,
default `'Pendente'` (mesmo valor setado na criação do registro,
`btnNovoClick`). Backend novo replica em `service._recalcular_situacao`,
chamada após `criar`/`adicionar_item`/`atualizar_item`/`devolver`; o
schema de entrada (`EmprestimoCreate`/`EmprestimoUpdate`) não aceita mais
`situacao` do cliente — só `EmprestimoResponse`/`EmprestimoResumoResponse`
expõem o valor computado. Frontend: campo "Situação" do cabeçalho virou
somente leitura no formulário.

## Campos reais — `emprestimo_item`

`id_emprestimo_item` (int, PK), `id_emprestimo`/`id_material` (int, FK
reais já no legado), `data_emprestimo` (date, opcional), `data_devolucao`
(date, opcional), `situacao` (varchar(60), opcional — texto livre, valores
observados: `'Pendente'`, `'Renovado'`, `'Devolvido'` — 3 estados reais no
Delphi (`CasaApoio.Material.Constants.pas`), não só 2 como o comentário
original do model dizia), `renovacao` (varchar(60), opcional — **texto
livre, não é data nem boolean**; dado real tem valores como `'até
22/03/2019 até 22/05/2019 Devolvido 02/07/2019'` — histórico de renovações
registrado manualmente em texto corrido, mantido fiel ao dado real).

**`data_devolucao` é prevista, não efetiva (achado 2026-09-11).** No
legado (`untFrmManutencaoEmprestimo`), o campo é digitado manualmente no
mesmo formulário e no mesmo momento que `data_emprestimo`, ao lado do
combo de `situacao` — não existe nenhum fluxo que a atualize quando o item
é devolvido de fato. Confirmado com dado real (`abrigo_teste`): havia 87
itens com `situacao='Pendente'` (ainda emprestados) e `data_devolucao` já
no passado, o que só é possível se o campo for uma previsão que venceu, não
um registro do que já aconteceu. Adicionada `data_devolucao_efetiva`
(coluna nova, sem equivalente no legado, migração `0014`), gravada
automaticamente pelo backend (`service.py`,
`_aplicar_devolucao_efetiva`) com a data de hoje na primeira vez que
`situacao` vira `'Devolvido'`, e limpa se a situação for corrigida depois
pra outra coisa. Para os ~3.265 itens já `'Devolvido'` migrados do legado,
a migração faz backfill usando a própria `data_devolucao` como
aproximação (não há como saber a data real retroativamente) — deixa claro
no comentário da migração que é só uma estimativa. Frontend: label do
campo original virou "Data prevista de devolução"; "Data efetiva da
devolução" aparece como campo só leitura na edição do item, e ambas
aparecem separadas na listagem e no histórico de alteração.

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
