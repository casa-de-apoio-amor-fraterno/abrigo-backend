# Quarto

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Quarto/` (`untFrmManutencaoQuarto`, `untDtmManutencaoQuarto`,
  `untFrmConsultaQuarto`, `untDtmConsultaQuarto`)
- Banco: tabela `quarto`.

## Campos reais (confirmados via `untFrmManutencaoQuarto.dfm` e o
`CREATE TABLE`/dados do dump de produção `sgf_abrigo`, 2026-09-10)

`id_quarto` (int, PK, `AUTO_INCREMENT`), `descricao` (varchar(60),
opcional), `numero` (varchar(60), obrigatório), `leito` (varchar(60) no
legado, `Integer` no schema novo — ver achado abaixo), `ativo` (varchar(3)
'Sim'/'Não', obrigatório — modelado como `boolean`, mesmo padrão de
`pessoa`/`usuario`/`hospital`).

**`numero` tem valor não numérico** (`'Sala de Convivência'`) apesar do
nome — mantido como `String`, fiel ao dado real (ver
`[[feedback-verificar-antes-de-supor]]`), não seguir o rótulo do
formulário Delphi.

**`leito` normalizado pra `Integer` (achado/fix 2026-09-12).** O rótulo da
UI é "Número de leitos" mas o dado real de produção era `varchar` sujo —
valores como `'2 leitos'`, `'00003'`, `'04'`. Inicialmente modelado como
`String` fiel ao dado bruto; depois de confirmado que **todo** valor real
contém dígitos e representa de fato uma contagem (não texto livre como
`numero`), a migração `0016_quarto_leito_integer` normaliza extraindo só
os dígitos de cada valor (`regexp_replace(leito, '[^0-9]', '', 'g')`) e
convertendo pra `Integer` — `'2 leitos'` → `2`, `'00003'` → `3`, `'04'` →
`4`. `numero` fica de fora dessa normalização (tem valor legitimamente não
numérico).

25 registros reais. CRUD completo (o legado tem tela de manutenção própria,
diferente de `estado`/`hospital`/`municipio`): `GET`/`POST`/`PUT` e
`DELETE` (inativação lógica via `ativo=false`, mesmo padrão de `pessoa`).
`GET /api/quartos` lista só ativos por padrão.

## Dependências a analisar antes de migrar por completo
- É FK de `estadia` (`id_quarto`) — pré-requisito da feature `estadias`
  (próximo item do backlog).

## Status
Mapeado e implementado (CRUD completo). Dados reais entram via ETL
(`docs/migracao-postgres.md`), não pela migração Alembic.
