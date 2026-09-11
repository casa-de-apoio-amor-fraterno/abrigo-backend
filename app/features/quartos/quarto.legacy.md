# Quarto

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Quarto/` (`untFrmManutencaoQuarto`, `untDtmManutencaoQuarto`,
  `untFrmConsultaQuarto`, `untDtmConsultaQuarto`)
- Banco: tabela `quarto`.

## Campos reais (confirmados via `untFrmManutencaoQuarto.dfm` e o
`CREATE TABLE`/dados do dump de produção `sgf_abrigo`, 2026-09-10)

`id_quarto` (int, PK, `AUTO_INCREMENT`), `descricao` (varchar(60),
opcional), `numero` (varchar(60), obrigatório), `leito` (varchar(60),
obrigatório), `ativo` (varchar(3) 'Sim'/'Não', obrigatório — modelado como
`boolean`, mesmo padrão de `pessoa`/`usuario`/`hospital`).

**Atenção:** apesar do rótulo da UI ser "Número de leitos" para o campo
`leito`, o dado real de produção **não é numérico** — valores como
`'2 leitos'`, `'00003'`, `'1'`. `numero` também tem valor não numérico
(`'Sala de Convivência'`). Ambos modelados como `String`, não `Integer`,
fiéis ao dado real (ver `[[feedback-verificar-antes-de-supor]]`) — não
seguir o rótulo do formulário Delphi.

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
