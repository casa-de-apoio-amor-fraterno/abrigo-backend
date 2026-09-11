# Hospital

Origem (Delphi — abrigo-legacy):
- Sem tela de manutenção própria identificada no legado — tabela de apoio
  (combo de origem/encaminhamento usado no cadastro de pessoa).
- Banco: tabela `hospital`.

## Campos reais (confirmados no `CREATE TABLE` e nos dados do dump de
produção `sgf_abrigo`, 2026-09-10)

`id_hospital` (int, PK, `AUTO_INCREMENT`), `nome` (varchar(60),
obrigatório), `ativo` (varchar(3) 'Sim'/'Não', obrigatório — modelado como
`boolean` no schema novo, mesmo padrão de `pessoa`/`usuario`).

13 registros reais. Apesar do nome da tabela, os dados reais mostram que é
usada como categoria genérica de origem/encaminhamento — não só hospitais
(ex.: "Empréstimo Solidário", "Doação de fralda", "SUS de Porto União").
Mantido fiel ao dado legado, sem tentar "corrigir" os nomes.

`GET /api/hospitais` lista só ativos por padrão (`apenas_ativos=true`),
como em `pessoa`. CRUD só de leitura por ora — não há evidência de tela de
cadastro no legado.

## Status
Mapeado e implementado (somente leitura). Dados reais entram via ETL
(`docs/migracao-postgres.md`), não pela migração Alembic.
