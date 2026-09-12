# Material

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Material/` (`untFrmManutencaoMaterial`,
  `untDtmManutencaoMaterial`, `untFrmConsultaMaterial`,
  `untFrmRelatorioMaterial`)
- Banco: tabela `material`.

## Campos reais (confirmados via `untFrmManutencaoMaterial.dfm` e o
`CREATE TABLE`/dados do dump de produção `sgf_abrigo`, 2026-09-10)

`id_material` (int, PK, `AUTO_INCREMENT`), `descricao` (varchar(60),
obrigatório), `codigo_identificacao` (varchar(60), opcional — código de
patrimônio), `disponivel_emprestimo` (varchar(3) 'Sim'/'Não', obrigatório —
modelado como `boolean`), `situacao` (varchar(60), obrigatório — **campo de
texto livre** no legado, `TcxDBTextEdit`, não um combo/radio de valores
fixos como `estadia.situacao`; dado real observado: `'Disponível'`,
`'Baixado'`, mas sem lista fechada confirmada na UI — mantido como
`String`, não enum), `local` (varchar(20), obrigatório — texto livre, ex.:
`'Casa'`), `observacao` (text, opcional — no dado real usado como
descrição detalhada de origem/uso do item, texto longo com quebras de
linha), `ativo` (varchar(3) 'Sim'/'Não', **opcional no legado** —
`DEFAULT NULL`, mesmo padrão de `estadia.ativo`; modelado como `bool |
None`), `motivo_baixa` (text, opcional — preenchido quando
`situacao='Baixado'`, ex.: `'Queimou a placa.'`).

~1.710 registros reais. CRUD completo (mesmo padrão de `pessoas`/
`voluntarios`): busca por descrição/código, filtro
`apenas_disponiveis_emprestimo` (pré-requisito da feature `emprestimos`,
próximo item do backlog — só materiais com `disponivel_emprestimo=true`
devem aparecer no combo de seleção de item emprestado).

## Foto (feature nova, 2026-09-12 — sem equivalente no legado)

Sem dado real pra migrar (não existia campo de imagem em `material` no
legado). Mesmo padrão de `Pessoa.foto` (`pessoa.legacy.md`): BLOB opcional
no próprio Postgres, sem storage externo. Duas diferenças:

- **Upload de arquivo do PC, não captura por webcam** — decisão do time
  (materiais são objetos físicos já fotografados por outro meio, não faz
  sentido exigir câmera ao vivo como em pessoas). Frontend usa
  `app-upload-foto` (`shared/ui/upload-foto`), não `app-captura-foto`.
- **Gera miniatura no servidor** (`foto_thumb`, coluna própria, via
  Pillow — `Image.thumbnail((200, 200))`) — a listagem de materiais
  mostra muitos itens de uma vez, então evita trafegar a imagem inteira
  só pra exibir um ícone pequeno. `Pessoa.foto` não tem esse problema
  (exibida em detalhe, não em lista) e não gera thumb.

Endpoints: `GET/PUT/DELETE /materiais/{id}/foto` (mesmo contrato de
`pessoas`) + `GET /materiais/{id}/foto/thumb`. Mesma validação
(JPEG/PNG/WebP, limite 5MB) e mesmo erro de domínio (`FotoInvalida`), com
uma camada a mais: se o conteúdo passa na whitelist de content-type mas
não é uma imagem decodificável de verdade (arquivo corrompido ou
content-type forjado), o Pillow falha ao gerar a miniatura e isso também
vira `FotoInvalida` (400), não erro 500.

## Status
Mapeado e implementado (CRUD completo + foto/thumb). Dados reais entram
via ETL (`docs/migracao-postgres.md`), não pela migração Alembic.
