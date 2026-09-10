# Pessoa

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Pessoa/` (`untFrmManutencaoPessoa`, `untDtmManutencaoPessoa`,
  `untFrmConsultaPessoa`, `untDtmConsultaPessoa`)
- Telas relacionadas: avaliação social (`untFrmManutencaoAvaliacaoSocial`),
  composição familiar (`untFrmManutencaoComposicaoFamiliar`), relatório
  (`untFrmRelatorioPessoa`)
- Banco: tabela `pessoa`

## Campos reais (confirmados via `untFrmManutencaoPessoa.dfm`)

`id_pessoa`, `nome`, `data_nascimento`, `rg`, `cpf`, `profissao`,
`cartao_sus`, `endereco`, `ponto_referencia`, `telefone`, `id_estado`,
`id_municipio`, `id_hospital`, `data_cadastro`, `acompanhamento_social`,
`observacao`, `tipo` (ver decisão abaixo). Não existe coluna `ativo` —
não há soft-delete de pessoa no legado.

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

## Status:
- Mapeado com campos reais. Endpoint de consulta (`GET /api/pessoas`) com
  busca por nome/CPF implementado. Cadastro/edição implementados no backend;
  tela de cadastro no frontend ainda não (só a consulta).
