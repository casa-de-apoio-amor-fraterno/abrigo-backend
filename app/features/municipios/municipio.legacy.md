# Município

Origem (Delphi — abrigo-legacy):
- Sem tela de manutenção própria no legado — tabela de apoio IBGE (combo de
  cidade usado no cadastro de pessoa, dependente da UF selecionada).
- Banco: tabela `municipio`.

## Campos reais (confirmados no `CREATE TABLE` do dump de produção
`sgf_abrigo`, 2026-09-10)

`id_municipio` (int, PK, **não é `AUTO_INCREMENT`** — código IBGE de 7
dígitos), `nome` (varchar(61), obrigatório), `id_estado` (int, obrigatório —
**já tinha FK real no legado** para `estado.id_estado`, mantida como
`ForeignKey` de verdade no model novo). Sem `ativo`.

~5.570 registros fixos (tabela IBGE completa). Nomes mantidos fiéis ao dado
de origem mesmo com grafia irregular (ex.: "Alta Floresta DOeste", "Machadinho
D Oeste") — não normalizar ao migrar (mesma diretriz de `pessoa.legacy.md`).

`GET /api/municipios` aceita filtro `id_estado` (obrigatório na prática, já
que listar ~5.570 linhas de uma vez não serve pra um combo de UI) e `busca`
por nome. CRUD só de leitura — sem tela de cadastro no legado.

## Status
Mapeado e implementado (somente leitura). Dados reais entram via ETL
(`docs/migracao-postgres.md`), não pela migração Alembic.
