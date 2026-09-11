# Material

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Material/` (`untFrmManutencaoMaterial`,
  `untDtmManutencaoMaterial`, `untFrmConsultaMaterial`,
  `untFrmRelatorioMaterial`)
- Banco: tabela `material`.

## Campos reais (confirmados via `untFrmManutencaoMaterial.dfm` e o
`CREATE TABLE`/dados do dump de produção `sgf_abrigo`, 2026-09-10)

`id_material` (int, PK, `AUTO_INCREMENT`), `descricao` (varchar(60),
obrigatório), `codigo_identificacao` (varchar(60), opcional — código de
patrimônio), `disponivel_emprestimo` (varchar(3) 'Sim'/'Não', obrigatório —
modelado como `boolean`), `situacao` (varchar(60), obrigatório — **campo de
texto livre** no legado, `TcxDBTextEdit`, não um combo/radio de valores
fixos como `estadia.situacao`; dado real observado: `'Disponível'`,
`'Baixado'`, mas sem lista fechada confirmada na UI — mantido como
`String`, não enum), `local` (varchar(20), obrigatório — texto livre, ex.:
`'Casa'`), `observacao` (text, opcional — no dado real usado como
descrição detalhada de origem/uso do item, texto longo com quebras de
linha), `ativo` (varchar(3) 'Sim'/'Não', **opcional no legado** —
`DEFAULT NULL`, mesmo padrão de `estadia.ativo`; modelado como `bool |
None`), `motivo_baixa` (text, opcional — preenchido quando
`situacao='Baixado'`, ex.: `'Queimou a placa.'`).

~1.710 registros reais. CRUD completo (mesmo padrão de `pessoas`/
`voluntarios`): busca por descrição/código, filtro
`apenas_disponiveis_emprestimo` (pré-requisito da feature `emprestimos`,
próximo item do backlog — só materiais com `disponivel_emprestimo=true`
devem aparecer no combo de seleção de item emprestado).

## Status
Mapeado e implementado (CRUD completo). Dados reais entram via ETL
(`docs/migracao-postgres.md`), não pela migração Alembic.
