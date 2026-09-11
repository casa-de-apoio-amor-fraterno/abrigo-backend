# Estado

Origem (Delphi — abrigo-legacy):
- Sem tela de manutenção própria no legado — tabela de apoio (combo de UF
  usado no cadastro de pessoa), populada uma vez, sem CRUD na UI.
- Banco: tabela `estado`.

## Campos reais (confirmados no `CREATE TABLE` do dump de produção
`sgf_abrigo`, 2026-09-10)

`id_estado` (int, PK, **não é `AUTO_INCREMENT`** — usa o código IBGE da UF,
não sequencial), `nome` (varchar(60), obrigatório), `uf` (varchar(2),
obrigatório). Sem `ativo` — não existe nessa tabela no legado.

27 registros fixos (as 27 UFs brasileiras). Nenhum CRUD de escrita
implementado — só leitura (`GET /api/estados`, `GET /api/estados/{id}`),
já que não há tela de cadastro no legado e o valor de negócio é só servir de
combo/referência pra `Pessoa.id_estado` e `Municipio.id_estado`.

## Status
Mapeado e implementado (somente leitura). Seed dos 27 registros ainda
pendente — entra via ETL (`docs/migracao-postgres.md`), não pela migração
Alembic.
