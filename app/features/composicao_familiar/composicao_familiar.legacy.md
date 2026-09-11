# Composição Familiar

Origem (Delphi — abrigo-legacy):
- Unit: `untFrmManutencaoComposicaoFamiliar` (sub-rotina de `Pessoa`, ver
  `pessoa.legacy.md`).
- Banco: tabela `composicao_familiar`.

## Campos reais (confirmados no `CREATE TABLE`/dados do dump de produção
`sgf_abrigo`, 2026-09-10)

`id_composicao_familiar` (int, PK), `id_pessoa` (int, FK real já no
legado), `nome` (varchar(60), obrigatório — nome do membro da família, não
da pessoa cadastrada em `pessoa`), `idade` (varchar(60), opcional — **texto
livre, não inteiro**; dado real pode ter valores não numéricos, ex. "5
meses", mantido como `String`), `grau_parentesco` (varchar(60),
obrigatório, texto livre — ex.: `'casada'` aparece em dado real no lugar
que seria esperado "Filha"/"Esposa", inconsistência do preenchimento
original mantida fiel ao dado), `estado_civil` (varchar(60), opcional),
`renda` (varchar(60), opcional, texto livre), `ocupacao` (varchar(60),
opcional).

~3.612 registros reais (um paciente pode ter vários membros de família
cadastrados). Diferente de `avaliacao_social` (1 registro por avaliação,
histórico por `data_movimento`), aqui há `DELETE` real — um membro pode ser
removido da composição familiar sem deixar rastro (mesmo comportamento do
legado, que não tinha soft-delete nessa sub-rotina).

## Controle de acesso

Mesma regra nova de `avaliacao_social` — router inteiro protegido por
`dependencies=[Depends(exigir_perfil("assistente_social"))]`
(`app/features/auth/dependencies.py`). Ver `avaliacao_social.legacy.md`
para o raciocínio completo (legado não tinha controle de acesso por
perfil).

Endpoints aninhados sob pessoa: `GET/POST /api/pessoas/{pessoa_id}
/composicao-familiar`, `PUT/DELETE .../composicao-familiar/{id}`.

## Status
Mapeado e implementado (CRUD completo com acesso restrito). Dados reais
entram via ETL (`docs/migracao-postgres.md`), não pela migração Alembic.
