# Voluntário

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Voluntario/` (tela de manutenção/cadastro).
- Banco: tabela `voluntario`.

## Campos reais (confirmados no `CREATE TABLE` e nos dados do dump de
produção `sgf_abrigo`, 2026-09-10)

`id_voluntario` (int, PK, `AUTO_INCREMENT`), `nome` (varchar(60),
obrigatório), `telefone` (varchar(60), obrigatório), `setor` (varchar(60),
opcional — área que o voluntário atua, ex.: "Móveis", "Roupas"),
`data_nascimento` (date, opcional — diferente de `pessoa`, aqui é
opcional), `estado_civil` (varchar(60), opcional), `cpf` (varchar(60),
opcional — diferente de `pessoa.cpf` que é `varchar(11)`, aqui tem 60
chars, mas o dado real observado é só dígitos), `endereco` (varchar(60),
opcional), `formacao` (varchar(60), opcional), `observacao` (text,
opcional — no legado usado pra registrar dias/horários de disponibilidade
em texto livre, ex.: "Terça-feira e quinta-feira."), `ativo` (varchar(3)
'Sim'/'Não', obrigatório — modelado como `boolean`, mesmo padrão de
`pessoa`/`usuario`).

40 registros reais. CRUD completo (mesmo padrão de `pessoas`): `GET`
(lista com busca por nome/CPF + detalhe), `POST`, `PUT`, `DELETE`
(inativação lógica). `GET /api/voluntarios` lista só ativos por padrão.

## Status
Mapeado e implementado (CRUD completo). Dados reais entram via ETL
(`docs/migracao-postgres.md`), não pela migração Alembic.
