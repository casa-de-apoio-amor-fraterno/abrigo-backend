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
como em `pessoa`.

## CRUD completo (2026-09-13)

Apesar de não haver tela de cadastro própria no legado, o time decidiu
implementar CRUD completo (`POST`/`PUT`/`DELETE`) — mesmo padrão de
`quartos` (`inativar` marca `ativo = false`, não deleta a linha, pra não
quebrar `Estadia.id_hospital`/`Pessoa.id_hospital` que referenciam o
registro). Motivador: `Estadia.id_hospital` (ver `estadia.legacy.md`) passou
a ser editável pela equipe, e não fazia sentido não poder cadastrar um
hospital novo sem mexer direto no banco.

## Status
Mapeado e implementado (CRUD completo). Dados reais entram via ETL
(`docs/migracao-postgres.md`), não pela migração Alembic.
