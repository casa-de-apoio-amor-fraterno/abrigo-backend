# Voluntário

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Voluntario/` (tela de manutenção/cadastro).
- Banco: tabela `voluntario`.

## Campos reais (confirmados no `CREATE TABLE` e nos dados do dump de
produção `sgf_abrigo`, 2026-09-10)

`id_voluntario` (int, PK, `AUTO_INCREMENT`), `nome` (varchar(60),
obrigatório), `telefone` (varchar(60), obrigatório — normalizado em
`voluntario_contato` no schema novo, ver seção Contatos abaixo e
`app/features/pessoas/pessoa.legacy.md`), `setor` (varchar(60),
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

## Contatos (2026-09-11)

Mesma normalização de `Pessoa` — ver `app/features/pessoas/pessoa.legacy.md`
(seção Contatos) pro raciocínio completo. `voluntario.telefone` também era
texto livre sem estrutura; `VoluntarioContato` (`voluntario_contato`,
migração `0012_pessoa_voluntario_contato`) substitui o campo solto.
`Voluntario.telefone_principal` (property) expõe o telefone marcado como
`principal` (ou o primeiro cadastrado) pra listagem, sem quebrar
`VoluntarioResumoResponse`. Coluna antiga removida em
`0013_remove_telefone_pessoa_voluntario`.

Diferente de `pessoa` (campo opcional), `voluntario.telefone` era
`NOT NULL` no legado — a criação de um voluntário não exige mais nenhum
contato de cara (relaxado no schema novo: sem contato nenhum,
`telefone_principal` só retorna `None`); contatos são adicionados depois,
como sub-recurso (`POST /api/voluntarios/{id}/contatos`).

## Status
Mapeado e implementado (CRUD completo). Dados reais entram via ETL
(`docs/migracao-postgres.md`), não pela migração Alembic.
