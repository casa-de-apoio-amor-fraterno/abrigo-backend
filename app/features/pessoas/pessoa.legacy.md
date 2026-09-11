# Pessoa

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Pessoa/` (`untFrmManutencaoPessoa`, `untDtmManutencaoPessoa`,
  `untFrmConsultaPessoa`, `untDtmConsultaPessoa`)
- Telas relacionadas: avaliação social (`untFrmManutencaoAvaliacaoSocial`),
  composição familiar (`untFrmManutencaoComposicaoFamiliar`), relatório
  (`untFrmRelatorioPessoa`)
- Banco: tabela `pessoa`

## Campos reais (confirmados via `untFrmManutencaoPessoa.dfm` e o
`CREATE TABLE` do dump de produção `sgf_abrigo`, 2026-09-09)

`id_pessoa` (int, PK), `id_estado`/`id_municipio`/`id_hospital` (int, FK),
`nome` (varchar(60), obrigatório), `data_nascimento` (date, obrigatório),
`rg` (varchar(15)), `cpf` (varchar(11)), `profissao` (varchar(60)),
`cartao_sus` (varchar(60)), `endereco` (varchar(60)), `ponto_referencia`
(varchar(60)), `telefone` (varchar(60)), `ativo` (varchar(3) 'Sim'/'Não',
obrigatório — modelado como `boolean` no schema novo), `observacao` (text),
`tipo` (varchar(12), obrigatório — ver decisão abaixo, não migrado),
`acompanhamento_social` (text), `data_cadastro` (date, obrigatório).

**Correção em relação a uma suposição anterior:** eu havia descartado a
coluna `ativo` por ela não aparecer no formulário de manutenção
(`untFrmManutencaoPessoa.dfm`) — o dump real de produção mostra que ela
existe e é obrigatória. O model novo tem `ativo: bool`, e `GET /api/pessoas`
só lista pessoas ativas por padrão.

## Decisão de design: removendo o campo `tipo`

O legado tem um campo `pessoa.tipo` (radio group com três opções fixas:
**Paciente / Acompanhante / Emprestimo** — `untFrmManutencaoPessoa.dfm`,
`edtTipoPessoa`), tratado como um atributo **permanente** da pessoa.

**Isso não faz sentido no domínio real:** o papel de uma pessoa (paciente,
acompanhante, ou tomadora de um empréstimo) é contextual a um evento
específico — uma estadia ou um empréstimo — não uma característica fixa da
pessoa. A mesma pessoa pode ser paciente numa estadia e acompanhante de
outra pessoa em outra ocasião.

**Evidência de que o próprio legado sentiu esse problema:** a tabela
`estadia` ganhou depois sua própria coluna `tipo_pessoa` (migração de
2026-09-03, `Scripts/Atualização Março 2026/Add coluna tipo pessoa na
tabela estadia.sql`), duplicando o conceito — e pior, migrando dados
existentes com um heurística frágil (`UPDATE estadia SET tipo_pessoa =
'Acompanhante' WHERE observacao LIKE '%acompanha%'`), o que é evidência de
que amarrar o papel à pessoa, e não ao evento, gerou dado inconsistente.

**Decisão:** `app/features/pessoas/models.py` **não tem** campo `tipo`.
Quando a feature `estadias` for implementada, `tipo_pessoa` (paciente /
acompanhante) vive em `Estadia`, como enum de verdade (não `VARCHAR` livre).
"Emprestimo" não deveria ser um tipo de pessoa: qualquer pessoa pode estar
associada a um empréstimo ativo via a FK em `Emprestimo.id_pessoa` — não
precisa de nenhum campo em `Pessoa` para isso.

Ao migrar os dados existentes: o valor de `pessoa.tipo` só é relevante para
saber que emparelhamento paciente/acompanhante existia (tabela de
acompanhamento com `id_paciente`/`id_acompanhante`) — isso deve ser
reconciliado com `estadia.tipo_pessoa` na migração de dados, não recriado
como coluna no schema novo.

## Tipo:
Cadastro (+ sub-rotinas de avaliação social e composição familiar, que devem
ficar restritas ao perfil de assistente social conforme anotado em
`abrigo-legacy/CasaApoio.txt`)

## Dependências a analisar antes de migrar por completo:
- Vínculo com `Estadia` (que herda o papel contextual, ver acima)
- Vínculo com `Emprestimo` (pessoa como tomadora de item emprestado)
- `id_hospital`/`id_municipio`/`id_estado` são FKs pra tabelas que ainda não
  foram mapeadas no backend novo — hoje ficam como inteiros soltos
- Regras de acesso: avaliação social e composição familiar só para
  assistente social (regra de negócio ainda não implementada no legado)

## `data_cadastro` opcional (achado ao testar o ETL, 2026-09-10)

O `CREATE TABLE` legado tem `data_cadastro date NOT NULL DEFAULT
'0000-00-00'` — parecia seguro modelar como `date` obrigatório. Ao restaurar
o dump real de produção pra testar `app/scripts/etl_migracao.py` de ponta a
ponta, o ETL falhou: **444 de 5.326 pessoas (~8,3%) têm
`data_cadastro = '0000-00-00'` de verdade** (o `DEFAULT` nunca foi
substituído por um valor real nesses cadastros). `data_zerada_para_none`
mapeia isso pra `NULL` (não existe no Postgres), mas o model exigia
`NOT NULL`. Corrigido: `Pessoa.data_cadastro` agora é `date | None`
(`alembic/versions/0009_pessoa_data_cadastro_nullable.py`). `data_nascimento`
segue `NOT NULL` — 0 registros zerados nessa coluna no dado real.

## Foto (feature nova, 2026-09-11)

O legado capturava a foto da pessoa pela webcam na tela de manutenção
(`untFrmManutencaoPessoa.pas`, componente DevExpress `TdxCameraControl`) e
salvava como arquivo `.bmp` **em disco**, fora do banco — caminho
`<pasta do executável>\pessoas\<id_pessoa>.bmp`, sem nenhuma coluna
correspondente na tabela `pessoa` (confirmado no `CREATE TABLE` do dump —
não existe `foto`/`caminho_imagem`). Havia também uma segunda tela,
`untFrmConsultaEstadiaFoto.pas` ("Consulta com Foto" de Estadia), que lia
os mesmos arquivos `.bmp` do disco só pra exibição num grid — não migrada
ainda (ver gap conhecido em `abrigo-frontend/docs/atividades.md`).

**Sem dado real pra migrar:** os arquivos ficavam na máquina onde o Delphi
rodava, fora do dump de produção e do controle de versão — greenfield, não
migração.

**Decisão (2026-09-11, confirmada com o usuário):** foto vira **BLOB no
Postgres** (`Pessoa.foto: bytes | None`, `LargeBinary`), não arquivo em
disco nem storage externo — mais simples de operar (cai no mesmo backup do
banco, sem pasta separada pra gerenciar) e adequado ao volume (uma foto
pequena por pessoa, ~5.300 pessoas). `foto_content_type` guarda o mime type
enviado pelo navegador (`image/jpeg`/`image/png`/`image/webp` — únicos
aceitos, `service.TIPOS_FOTO_PERMITIDOS`), limite de 5MB por imagem
(`service.TAMANHO_MAXIMO_FOTO_BYTES`).

A foto **não entra** em `PessoaResponse`/`PessoaResumoResponse` como bytes
(pesado demais pra listagem) — só um `tem_foto: bool` computado
(`Pessoa.tem_foto`, property no model). Os bytes reais ficam atrás de
endpoints próprios: `GET /api/pessoas/{id}/foto` (retorna a imagem crua,
404 se não tiver), `PUT /api/pessoas/{id}/foto` (multipart/form-data,
substitui a foto existente) e `DELETE /api/pessoas/{id}/foto` (remove).
Migração `alembic/versions/0011_pessoa_foto.py`.

## Status:
- Mapeado com campos reais. Endpoint de consulta (`GET /api/pessoas`) com
  busca por nome/CPF implementado. Cadastro/edição implementados no backend;
  tela de cadastro no frontend ainda não (só a consulta). ETL testado de
  ponta a ponta contra o dump real de produção (ver
  `docs/migracao-postgres.md`).
