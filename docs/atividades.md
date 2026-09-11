# Atividades — Migração Abrigo

Levantamento feito a partir de três fontes cruzadas: o dump real de
produção (`sgf_abrigo 20260909 1501.sql`, MySQL 5.5), o código-fonte do
legado Delphi (`abrigo-legacy/fonte/`) e o que já existe implementado em
`abrigo-backend`/`abrigo-frontend`. Ver `[[feedback-verificar-antes-de-supor]]`
— este documento é o resultado de cruzar as três fontes, não só ler o
código do legado.

## Inventário de tabelas (produção real)

18 tabelas no total. "Volume" é o `AUTO_INCREMENT` atual (limite superior
aproximado de linhas já inseridas, não a contagem exata).

| Tabela | Volume aprox. | FKs (para) | Status no backend novo |
| --- | --- | --- | --- |
| `pessoa` | ~5.327 | `estado`, `municipio`, `hospital` | ✅ Implementado (`app/features/pessoas/`) |
| `usuario` | 8 | — | ✅ Implementado (`app/features/usuarios/` + `auth/`) |
| `estado` | 27 (fixo, lista de UFs) | — | ✅ Implementado (`app/features/estados/`) |
| `municipio` | ~5.570 (fixo, IBGE) | `estado` | ✅ Implementado (`app/features/municipios/`) |
| `hospital` | 14 | — | ✅ Implementado (`app/features/hospitais/`) |
| `quarto` | 25 | — | ✅ Implementado (`app/features/quartos/`) |
| `voluntario` | 40 | — | ✅ Implementado (`app/features/voluntarios/`) |
| `disponibilidade` | **0 linhas** | `voluntario` | ❌ Não implementado — feature parece não usada |
| `estadia` | ~4.434 | `pessoa`, `quarto`, `usuario` | ✅ Implementado (`app/features/estadias/`) |
| `estadia_acompanhante` | ~648 | `estadia`, `pessoa` | ✅ Implementado (mesma feature — ver decisão abaixo) |
| `acompanhamento` | 41 | `pessoa` (id_paciente/id_acompanhante — **sem FK de verdade**, só índice) | ❌ Não vira tabela própria — dados reconciliados na ETL (ver decisão abaixo) |
| `avaliacao_social` | ~1.312 | `pessoa` | ✅ Implementado (`app/features/avaliacao_social/`, acesso restrito) |
| `composicao_familiar` | ~3.612 | `pessoa` | ✅ Implementado (`app/features/composicao_familiar/`, acesso restrito) |
| `material` | ~1.710 | — | ✅ Implementado (`app/features/materiais/`) |
| `emprestimo` | ~2.583 | `pessoa`, `usuario` | ✅ Implementado (`app/features/emprestimos/`) |
| `emprestimo_item` | ~3.591 | `emprestimo`, `material` | ✅ Implementado (mesma feature, sub-recurso) |
| `procedimento` | **0 linhas** | — | ❌ Não implementado — feature parece não usada |
| `procedimento_realizado` | **0 linhas** | `procedimento`, `pessoa`, `voluntario` | ❌ Não implementado — feature parece não usada |

## Mapa de foreign keys

```txt
estado
 └─ municipio (id_estado)

estado, municipio, hospital
 └─ pessoa (id_estado, id_municipio, id_hospital)

pessoa
 ├─ avaliacao_social (id_pessoa)
 ├─ composicao_familiar (id_pessoa)
 ├─ acompanhamento (id_paciente, id_acompanhante — sem FK real)
 ├─ estadia_acompanhante (id_pessoa)
 ├─ emprestimo (id_pessoa)
 └─ procedimento_realizado (id_pessoa)

usuario
 ├─ estadia (id_usuario)
 └─ emprestimo (id_usuario)

quarto
 └─ estadia (id_quarto)

estadia
 └─ estadia_acompanhante (id_estadia)

voluntario
 ├─ disponibilidade (id_voluntario)
 └─ procedimento_realizado (id_voluntario)

material
 └─ emprestimo_item (id_material)

emprestimo
 └─ emprestimo_item (id_emprestimo)

procedimento
 └─ procedimento_realizado (id_procedimento)
```

## Decisões / achados que precisam de atenção antes de implementar

1. ✅ **`acompanhamento` × `estadia_acompanhante` — duas tabelas para o
   mesmo conceito.** `acompanhamento` (mais antiga, 41 linhas, sem FK de
   verdade — só índice) parece ter sido substituída por
   `estadia_acompanhante` (648 linhas, FK real pra `estadia` e `pessoa`,
   contextual por estadia — é exatamente o padrão relacional correto que já
   tínhamos decidido adotar ao remover `pessoa.tipo`, ver
   `pessoa.legacy.md`). **Decisão confirmada (2026-09-10):** migrar dados de
   `acompanhamento` pra dentro do conceito de `estadia_acompanhante` na ETL
   (cruzando com a `estadia` correspondente de cada paciente) e não trazer
   `acompanhamento` como tabela própria no schema novo — só
   `EstadiaAcompanhante` foi modelada. Ainda falta validar na ETL:
   `acompanhamento` tem casos que não têm uma `estadia` correspondente?
2. **`disponibilidade`, `procedimento` e `procedimento_realizado` estão
   vazias (0 linhas) em produção.** Ou a funcionalidade nunca foi usada de
   fato, ou os dados foram limpos em algum momento. **Decisão sugerida:**
   perguntar à instituição se essas funcionalidades (disponibilidade de
   voluntário, procedimentos realizados) são usadas hoje na prática antes
   de investir tempo implementando — pode ser que não valha a pena migrar.
3. ✅ **`pessoa.tipo`, `estadia.tipo_pessoa` e `estadia_acompanhante` —
   suposição de sobreposição estava errada.** Já decidido
   (`pessoa.legacy.md`) que `tipo` não migra para `Pessoa`. **Decisão
   confirmada (2026-09-10), ver `estadia.legacy.md`:** verificação contra a
   tela real do legado (`untFrmManutencaoEstadia.dfm`) mostrou que
   `tipo_pessoa` e `estadia_acompanhante` são usados **simultaneamente** na
   mesma tela — não são o mesmo conceito. `tipo_pessoa` é o papel da pessoa
   que ocupa aquele leito (aquela linha de `estadia`); `estadia_acompanhante`
   é gente que acompanha sem necessariamente ter leito próprio. **Os dois
   foram mantidos** (`tipo_pessoa` como enum de verdade em `Estadia`,
   `EstadiaAcompanhante` como tabela relacionada própria).
4. **`material.ativo`, `estadia.ativo`, `hospital.ativo`, `quarto.ativo`,
   `voluntario.ativo`, `procedimento.ativo` seguem o mesmo padrão
   `varchar(3)` 'Sim'/'Não'** que já corrigimos em `pessoa`/`usuario` —
   modelar todos como `boolean` na ETL, não como string.
5. **`estadia.data_entrada`/`data_saida` são `datetime`, não `date`** —
   diferente de `pessoa.data_nascimento`/`data_cadastro`, que são `date`.
   Atenção ao mapear os tipos corretos por tabela (não assumir que tudo é
   `date` como em `pessoa`).

## Backlog de features (ordem sugerida)

Ordem baseada em dependência de FK (não dá pra implementar `estadia` sem
`quarto`, por exemplo) e volume/uso real dos dados.

1. ✅ **`estados` / `municipios` / `hospitais`** — tabelas de apoio (FK de
   `pessoa`), pequenas e sem regra de negócio própria (só CRUD/consulta
   simples, `municipio` provavelmente só populado uma vez via seed, não tem
   tela de cadastro no legado). Pré-requisito pra exibir nome do
   estado/município/hospital na tela de pessoa em vez do ID cru.
   **Implementado (2026-09-10):** endpoints de leitura (`GET` lista/detalhe)
   em `app/features/estados/`, `app/features/hospitais/`,
   `app/features/municipios/`; migração Alembic
   `0002_estados_municipios_hospitais` cria as tabelas e adiciona FK real em
   `pessoa.id_estado/id_municipio/id_hospital` (antes inteiros soltos).
   Serviços de apoio no frontend (`dto/mapper/model/service`, sem página de
   listagem própria — não estão no menu). Dados reais (27 estados, ~5.570
   municípios, 13 hospitais) ainda não carregados — entram via ETL
   (`docs/migracao-postgres.md`), não por seed nem pela migração Alembic.
2. ✅ **`quartos`** — pré-requisito de `estadias`. Poucos registros (25),
   CRUD simples. **Implementado (2026-09-10):** CRUD completo (diferente de
   `estados`/`hospitais`/`municipios` — o legado tem tela de manutenção
   própria) em `app/features/quartos/`; migração
   `alembic/versions/0003_quartos.py`. `numero`/`leito` modelados como
   `String`, não `Integer` — o dado real tem valores não numéricos (ex.:
   "2 leitos", "Sala de Convivência"), apesar do rótulo "Número de leitos"
   na UI legada. 8 testes novos (35 passando no total). Serviço de apoio no
   frontend (`dto/mapper/model/service`, CRUD completo); sem página própria
   ainda — vira combo de seleção quando `estadias` (próximo item) for
   implementada.
3. ✅ **`estadias`** — feature central do abrigo (~4.434 registros).
   **Implementado (2026-09-10):** CRUD completo (`app/features/estadias/`)
   + sub-recurso `EstadiaAcompanhante`, endpoint `POST
   /api/estadias/{id}/encerrar` (atalho pro fluxo real do legado — uma
   estadia é encerrada, não deletada). Migração
   `alembic/versions/0004_estadias.py`. 15 testes novos (42 passando no
   total). Serviço de apoio no frontend com CRUD completo; ainda sem
   tela própria — rota placeholder no `app.routes.ts` continua.
4. ✅ **`voluntarios`** — CRUD simples (40 registros), sem dependências.
   **Implementado (2026-09-10):** CRUD completo em
   `app/features/voluntarios/`, migração
   `alembic/versions/0005_voluntarios.py`, mesmo padrão de `pessoas` (busca
   por nome/CPF, inativação lógica). 7 testes novos (49 passando no total).
   Serviço de apoio no frontend com CRUD completo; sem página própria ainda
   — rota placeholder no `app.routes.ts` continua.
5. ✅ **`materiais`** — CRUD simples (~1.710 registros), pré-requisito de
   `emprestimos`. **Implementado (2026-09-10):** CRUD completo em
   `app/features/materiais/`, migração
   `alembic/versions/0006_materiais.py`. `situacao` modelado como `String`
   livre (campo `TcxDBTextEdit` no legado, não um combo fechado — diferente
   de `estadia.situacao`); `ativo` como `bool | None` (opcional no dump,
   igual `estadia.ativo`). Filtro `apenas_disponiveis_emprestimo` já pronto
   pro combo de seleção de item na feature `emprestimos`. 8 testes novos
   (57 passando no total). Serviço de apoio no frontend com CRUD completo;
   sem página própria ainda.
6. ✅ **`emprestimos`** (+ `emprestimo_item`) — depende de `pessoas`,
   `usuarios` e `materiais`. **Implementado (2026-09-10):** CRUD completo
   em `app/features/emprestimos/` + sub-recurso `EmprestimoItem` (`GET`/
   `POST`/`PUT`, sem exclusão — no legado um item não é removido, só tem a
   situação atualizada pra "Devolvido"). Migração
   `alembic/versions/0007_emprestimos.py`. `situacao` (texto livre, mesmo
   padrão de `material.situacao`) e `renovacao` (texto livre, não
   data/boolean — dado real tem histórico corrido tipo "até 22/03/2019 ...
   Devolvido 02/07/2019") modelados como `String`. 9 testes novos (66
   passando no total). Serviço de apoio no frontend com CRUD completo;
   sem página própria ainda.
7. ✅ **`avaliacao_social` / `composicao_familiar`** — sub-rotinas de
   `pessoa` com controle de acesso (só assistente social, regra que
   precisava ser criada do zero — o legado não implementava essa
   restrição). **Implementado (2026-09-10):** primeira infraestrutura de
   autorização do backend —
   `app/features/auth/dependencies.py` (`usuario_atual` decodifica o JWT de
   `POST /api/auth/login`; `exigir_perfil(*perfis)` retorna 403 se
   `Usuario.perfil` não bater) — até aqui nenhum endpoint exigia
   autenticação. Os dois routers novos
   (`app/features/avaliacao_social/`, `app/features/composicao_familiar/`)
   usam `dependencies=[Depends(exigir_perfil("assistente_social"))]` no
   `APIRouter` inteiro. Endpoints aninhados sob pessoa
   (`/api/pessoas/{pessoa_id}/avaliacoes-sociais`,
   `.../composicao-familiar`). Migração
   `alembic/versions/0008_avaliacao_social_composicao_familiar.py`. 10
   testes novos, incluindo 401 sem token e 403 com perfil errado (76
   passando no total). Frontend: `authInterceptor` novo
   (`core/http/auth.interceptor.ts`) anexa o Bearer token do
   `AuthService` em toda chamada à API — primeira vez que o token
   guardado no login é realmente usado; serviços de apoio em
   `features/pessoas/avaliacao-social/` e
   `features/pessoas/composicao-familiar/`.
8. **`disponibilidade` / `procedimentos`** — só depois de confirmar com a
   instituição se ainda são usados (ver achado 2 acima). **Decisão
   (2026-09-10): não implementar agora.** Ficam de fora deliberadamente até
   o resto do sistema estar 100% migrado — aí sim confirma-se com a
   instituição se valem a pena (0 registros em produção sugere que talvez
   não). Backlog considerado concluído para efeitos de "features
   principais" com essa exceção intencional.

## Atividades de infraestrutura / ETL

- [x] Escrever o script de ETL — em Python, não pgloader (ver decisão em
  `docs/migracao-postgres.md`), testado de ponta a ponta contra o dump
  real e contra Postgres real (2026-09-11).
- [x] Decidir e documentar o destino de `acompanhamento` (achado 1) —
  reconciliado automaticamente com `estadia_acompanhante` quando
  inambíguo (paciente com 1 única estadia); casos ambíguos ficam listados
  pra revisão manual, não inseridos por heurística.
- [ ] Confirmar com a instituição se `disponibilidade`/`procedimento*` são
  usados (achado 2) antes de priorizar — **único item de infraestrutura
  ainda genuinamente pendente**, depende de resposta da instituição, não
  de código.
- [x] Decidir `tipo_pessoa` vs `estadia_acompanhante` (achado 3) — não
  eram redundantes, os dois foram mantidos (ver `estadia.legacy.md`).
- [x] Mapear todos os campos `varchar(3)` 'Sim'/'Não' → `boolean` na ETL
  (achado 4) — feito em `app/scripts/etl/transformacoes.py` pra todas as
  tabelas, não só `pessoa`/`usuario`.
- [x] Rodar `python -m app.scripts.hash_senhas_pendentes --confirmar`
  logo após a carga inicial de dados — testado contra Postgres real, 7
  senhas hasheadas com sucesso.
- [x] Adicionar FK de verdade nos models novos assim que as tabelas de
  apoio existirem — `Pessoa.id_hospital`/`id_municipio`/`id_estado` já são
  `ForeignKey` de verdade desde a migração `0002`.

## Pós-conclusão: `emprestimo_historico` (2026-09-11)

Backlog original (acima) foi concluído em 2026-09-10. Em 2026-09-11, ao
implementar a tela de Empréstimos no frontend (item 8 de
`abrigo-frontend/docs/atividades.md`), foi descoberto que o legado ganhou
uma tabela nova — `emprestimo_historico` — **depois** do dump de produção
usado na migração (script `Scripts/Atualização Setembro 2026/Criar tabela
emprestimo_historico.sql`, 2026-09-09, mesmo autor). Não estava no
inventário original deste documento porque não existia no dump. Trilha de
auditoria de alterações do empréstimo (observação, itens) — implementada
via migração `0010`, ver `app/features/emprestimos/emprestimo.legacy.md`
pra detalhes da lógica replicada do legado.
