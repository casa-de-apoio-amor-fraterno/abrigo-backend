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
| `estado` | 27 (fixo, lista de UFs) | — | ❌ Não implementado |
| `municipio` | ~5.570 (fixo, IBGE) | `estado` | ❌ Não implementado |
| `hospital` | 14 | — | ❌ Não implementado |
| `quarto` | 25 | — | ❌ Não implementado |
| `voluntario` | 40 | — | ❌ Não implementado (placeholder no frontend) |
| `disponibilidade` | **0 linhas** | `voluntario` | ❌ Não implementado — feature parece não usada |
| `estadia` | ~4.434 | `pessoa`, `quarto`, `usuario` | ❌ Não implementado (placeholder no frontend) |
| `estadia_acompanhante` | ~648 | `estadia`, `pessoa` | ❌ Não implementado — ver decisão abaixo |
| `acompanhamento` | 41 | `pessoa` (id_paciente/id_acompanhante — **sem FK de verdade**, só índice) | ❌ Não implementado — ver decisão abaixo |
| `avaliacao_social` | ~1.312 | `pessoa` | ❌ Não implementado (sub-rotina restrita à assistente social) |
| `composicao_familiar` | ~3.612 | `pessoa` | ❌ Não implementado (sub-rotina restrita à assistente social) |
| `material` | ~1.710 | — | ❌ Não implementado (placeholder no frontend) |
| `emprestimo` | ~2.583 | `pessoa`, `usuario` | ❌ Não implementado (placeholder no frontend) |
| `emprestimo_item` | ~3.591 | `emprestimo`, `material` | ❌ Não implementado |
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

1. **`acompanhamento` × `estadia_acompanhante` — duas tabelas para o mesmo
   conceito.** `acompanhamento` (mais antiga, 41 linhas, sem FK de verdade —
   só índice) parece ter sido substituída por `estadia_acompanhante` (648
   linhas, FK real pra `estadia` e `pessoa`, contextual por estadia — é
   exatamente o padrão relacional correto que já tínhamos decidido adotar
   ao remover `pessoa.tipo`, ver `pessoa.legacy.md`). **Decisão sugerida:**
   migrar dados de `acompanhamento` pra dentro do conceito de
   `estadia_acompanhante` na ETL (cruzando com a `estadia` correspondente de
   cada paciente) e não trazer `acompanhamento` como tabela própria no
   schema novo. Precisa validação: `acompanhamento` tem casos que não têm
   uma `estadia` correspondente?
2. **`disponibilidade`, `procedimento` e `procedimento_realizado` estão
   vazias (0 linhas) em produção.** Ou a funcionalidade nunca foi usada de
   fato, ou os dados foram limpos em algum momento. **Decisão sugerida:**
   perguntar à instituição se essas funcionalidades (disponibilidade de
   voluntário, procedimentos realizados) são usadas hoje na prática antes
   de investir tempo implementando — pode ser que não valha a pena migrar.
3. **`pessoa.tipo`, `estadia.tipo_pessoa` e `estadia_acompanhante` se
   sobrepõem.** Já decidido (`pessoa.legacy.md`) que `tipo` não migra para
   `Pessoa`. Falta decidir se `Estadia.tipo_pessoa` continua como campo
   próprio ou se é totalmente substituído pela existência (ou não) de uma
   linha em `estadia_acompanhante` associada — a segunda opção é mais
   normalizada e evita o campo redundante.
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

1. **`estados` / `municipios` / `hospitais`** — tabelas de apoio (FK de
   `pessoa`), pequenas e sem regra de negócio própria (só CRUD/consulta
   simples, `municipio` provavelmente só populado uma vez via seed, não tem
   tela de cadastro no legado). Pré-requisito pra exibir nome do
   estado/município/hospital na tela de pessoa em vez do ID cru.
2. **`quartos`** — pré-requisito de `estadias`. Poucos registros (25),
   CRUD simples.
3. **`estadias`** — feature central do abrigo (~4.434 registros). Já tem
   rota placeholder no frontend. Envolve decidir o ponto 3 acima
   (`tipo_pessoa` vs `estadia_acompanhante`) antes de desenhar o schema novo.
4. **`voluntarios`** — CRUD simples (40 registros), sem dependências.
5. **`materiais`** — CRUD simples (~1.710 registros), pré-requisito de
   `emprestimos`.
6. **`emprestimos`** (+ `emprestimo_item`) — depende de `pessoas`,
   `usuarios` e `materiais`.
7. **`avaliacao_social` / `composicao_familiar`** — sub-rotinas de `pessoa`
   com controle de acesso (só assistente social, regra que precisa ser
   criada do zero — o legado não implementava essa restrição).
8. **`disponibilidade` / `procedimentos`** — só depois de confirmar com a
   instituição se ainda são usados (ver achado 2 acima).

## Atividades de infraestrutura / ETL

- [ ] Escrever o script de ETL (`pgloader` + mapeamentos por tabela) —
  ver `docs/migracao-postgres.md`.
- [ ] Decidir e documentar o destino de `acompanhamento` (achado 1).
- [ ] Confirmar com a instituição se `disponibilidade`/`procedimento*` são
  usados (achado 2) antes de priorizar.
- [ ] Decidir `tipo_pessoa` vs `estadia_acompanhante` (achado 3) antes de
  desenhar o model de `Estadia`.
- [ ] Mapear todos os campos `varchar(3)` 'Sim'/'Não' → `boolean` na ETL
  (achado 4) — não só `pessoa`/`usuario`.
- [ ] Rodar `python -m app.scripts.hash_senhas_pendentes --confirmar` logo
  após a carga inicial de dados.
- [ ] Adicionar FK de verdade nos models novos assim que as tabelas de
  apoio (`estados`, `municipios`, `hospitais`, `quartos`) existirem — hoje
  `Pessoa.id_hospital`/`id_municipio`/`id_estado` são inteiros soltos.
