# Avaliação Social

Origem (Delphi — abrigo-legacy):
- Unit: `untFrmManutencaoAvaliacaoSocial` (sub-rotina de `Pessoa`, ver
  `pessoa.legacy.md`).
- Banco: tabela `avaliacao_social`.

## Campos reais (confirmados no `CREATE TABLE`/dados do dump de produção
`sgf_abrigo`, 2026-09-10)

`id_avaliacao_social` (int, PK), `id_pessoa` (int, FK real já no legado),
`fumante`/`energia_eletrica`/`agua_encanada`/
`necessita_medicamento_uso_continuo`/`medicamento_disponibilizado_sus`
(varchar(3) 'Sim'/'Não', opcionais — modelados como `bool | None`, mesmo
padrão de `pessoa`/`usuario`), `residencia` (varchar(10), ex.: `'Alugada'`,
`'Própria'`), `tipo_construcao` (varchar(10), ex.: `'Madeira'`,
`'Alvenaria'`, `'Outros'`), `renda_mensal_familiar` (varchar(60), texto
livre — valores monetários com formatação inconsistente, ex.:
`'1.300,00'`, `'2500,00'`, não convertido pra número),
`quantas_pessoas_contribuem_formacao_renda` (varchar(60), texto livre, ex.:
`'01'`), `alguem_recebe_beneficio_previdenciario_governo` (varchar(60),
texto livre, ex.: `'200,00 Bolsa Família'`, `'não '`), `diagnostico` /
`tratamento_realizado` (text, opcionais), `casos_cancer_familia` (**text**,
não `varchar(3)` como os outros campos Sim/Não desta tabela — mantido
`String`, não convertido pra boolean, mesmo a amostra real só tendo
`'Sim'`/`'Não'`: o tipo da coluna permite texto livre),
`custo_mensal_medicamento` (varchar(60), texto livre),
`alimentacao_especifica`/`equipamento_para_locomocao` (text, opcionais),
`data_movimento` (datetime, opcional — data do preenchimento da
avaliação).

~1.312 registros reais.

## Controle de acesso (regra nova)

O legado **não tinha controle de acesso por perfil** —
`untFrmLogin.pas` só validava usuário/senha, qualquer usuário logado
acessava qualquer tela, incluindo avaliação social (dados sensíveis: renda
familiar, diagnóstico médico, benefícios sociais). `CasaApoio.txt`
(abrigo-legacy) já anotava que essa sub-rotina deveria ficar restrita à
assistente social, mas isso nunca foi implementado.

**Implementado no sistema novo:** `app/features/auth/dependencies.py`
ganhou `usuario_atual` (decodifica o JWT emitido em `POST /api/auth/login`
e carrega o `Usuario`) e `exigir_perfil(*perfis)` (dependência FastAPI que
retorna 403 se `Usuario.perfil` não estiver na lista). O router de
`avaliacao_social` inteiro usa `dependencies=[Depends(exigir_perfil(
"assistente_social"))]` — todo endpoint exige um usuário autenticado com
`perfil == "assistente_social"`.

Endpoints aninhados sob pessoa: `GET/POST /api/pessoas/{pessoa_id}
/avaliacoes-sociais`, `PUT .../avaliacoes-sociais/{id}`.

## Status
Mapeado e implementado (CRUD com acesso restrito). Dados reais entram via
ETL (`docs/migracao-postgres.md`), não pela migração Alembic.
