# Migração MySQL 5.5 → PostgreSQL + pgvector

## Decisão

O `abrigo-backend` usa **PostgreSQL** (com a extensão `pgvector`) como banco
de dados, no lugar de seguir com o MySQL 5.5 do sistema legado ou migrar
para MySQL 8/9.

## Por quê

- **MySQL 5.5 é insustentável independente de vetor**: lançado em 2010, sem
  suporte/patches de segurança desde dezembro de 2018. Continuar nele é um
  risco em si.
- **Um banco só, fazendo tudo.** Rodar um banco vetorial dedicado (Pinecone,
  Weaviate, Qdrant, Milvus) ao lado do banco relacional significa mais um
  sistema pra manter, pagar e manter sincronizado — sem necessidade real
  para o volume de dados de um abrigo. Dado o tamanho da equipe/orçamento de
  uma ONG, isso não se paga.
- **`pgvector` é maduro** — índices ANN de verdade (HNSW/IVFFlat), gratuito,
  extremamente usado em produção. O `VECTOR` nativo do MySQL 9 (2024) ainda
  é recente e faz busca por força bruta, sem índice aproximado.
- **Reaproveita a stack já montada**: SQLAlchemy + Alembic continuam
  funcionando: só troca o dialeto (`psycopg` no lugar de `pymysql`).

## O que muda na estratégia de migração de schema

Isso **substitui** a estratégia anterior ("migração aditiva sobre o MySQL de
produção", descrita nos commits iniciais do backend). Como o Postgres começa
vazio, não existe "banco de produção já populado" nele ainda — então:

- `alembic/versions/0001_estrutura_inicial.py` **cria** as tabelas
  (`usuario`, `pessoa`) diretamente, com o schema já no formato definitivo
  (incluindo `senha_hash`, `ativo` como boolean, etc.) — não precisa dos
  passos incrementais que seriam necessários num upgrade in-place do MySQL.
- Os dados de produção reais (dump `sgf_abrigo`, MySQL 5.5) são carregados
  **depois**, via ETL — não pela migração do Alembic.
- A partir do momento em que o Postgres tiver dados reais, a regra antiga
  volta a valer: migrações futuras devem ser **aditivas** (`ALTER TABLE ADD
  COLUMN`, nunca `DROP`/recriar tabela com dado real sem migrar o conteúdo
  antes).

## Ferramenta do ETL: Python, não pgloader (decisão 2026-09-10)

O plano original previa usar [`pgloader`](https://pgloader.io/). **Trocado
por um script Python** (`app/scripts/etl_migracao.py` +
`app/scripts/etl/transformacoes.py` + `app/scripts/etl/reconciliacao.py`):
o ambiente onde o script foi desenvolvido não tinha `pgloader`, cliente
`mysql` nem `docker` disponíveis — impossível instalar ou testar um script
`pgloader` ali. Como o projeto já é Python (SQLAlchemy), e a lógica de
transformação por tabela é não-trivial (datas zeradas, Sim/Não → boolean
em mais de dez colunas diferentes, reconciliação de `acompanhamento`),
escrever isso em Python puro permite testar cada regra com `pytest`
(`tests/test_etl_transformacoes.py`, `tests/test_etl_reconciliacao.py`) sem
precisar de MySQL/Postgres reais rodando — o que não seria possível
validar numa DSL do `pgloader`. Usa `pymysql` (já em
`requirements-dev.txt`) pra ler o MySQL de origem e o `SessionLocal` da
própria aplicação pra escrever no Postgres alvo.

## Plano de ETL (MySQL → Postgres)

1. **Nunca rodar contra o dump/produção diretamente na primeira tentativa.**
   Restaurar o dump `sgf_abrigo` num MySQL local descartável primeiro.
2. Rodar `alembic upgrade head` no Postgres alvo (cria o schema vazio).
3. Rodar `python -m app.scripts.etl_migracao --mysql-url
   mysql+pymysql://usuario:senha@localhost/sgf_abrigo` (sem `--confirmar`
   primeiro — modo dry-run, só mostra quantas linhas cada tabela teria).
   O script já trata, por tabela (ver `app/scripts/etl/transformacoes.py`):
   - **Datas zero do MySQL**: `data_cadastro date NOT NULL DEFAULT
     '0000-00-00'` — `0000-00-00` não existe no Postgres. Mapear pra `NULL`
     quando o valor for zero, ou pra uma data sentinela documentada.
   - **`ativo` como `varchar(3)` ('Sim'/'Não')** → `boolean` (`'Sim'` →
     `true`, qualquer outra coisa → `false`).
   - **`pessoa.tipo`** (`varchar(12)`, 'Paciente'/'Acompanhante'/'Emprestimo')
     **não é copiado pra `pessoa`** — não existe mais nesse schema (ver
     `app/features/pessoas/pessoa.legacy.md`). Correção em relação ao plano
     original deste documento: **não** é usado pra popular
     `estadia.tipo_pessoa` — essa coluna já existe como campo próprio no
     `estadia` legado (confirmado no dump, ver
     `app/features/estadias/estadia.legacy.md`), então o ETL copia
     `estadia.tipo_pessoa` direto da tabela `estadia`, sem precisar de
     `pessoa.tipo`. `pessoa.tipo` é simplesmente descartado.
   - **`acompanhamento` → `estadia_acompanhante`**: `acompanhamento` (sem FK
     real, sem data) é reconciliada automaticamente só quando o paciente
     teve exatamente uma `estadia` (caso inambíguo); os demais casos (0 ou
     2+ estadias pro paciente) ficam listados como pendentes de revisão
     manual na saída do script, não são inseridos por heurística (ver
     `app/scripts/etl/reconciliacao.py` e achado 1 de `docs/atividades.md`).
   - **`ativo` como `varchar(3)` ('Sim'/'Não')** → `boolean` (`'Sim'` →
     `true`, qualquer outra coisa → `false`) em toda tabela que tem essa
     coluna (`hospital`, `quarto`, `usuario`, `pessoa`, `voluntario`,
     `material`, `estadia`, `emprestimo` e os campos Sim/Não de
     `avaliacao_social` — exceto `casos_cancer_familia`, que é `text` no
     legado, não `varchar(3)`, e fica como string).
   - **`usuario.senha`** migra como está (texto plano) — o backend já trata
     isso (`app/features/auth/service.py`, migração "preguiçosa" pro hash no
     primeiro login). Não expor esse texto plano em lugar nenhum além do
     banco.
4. Validar contagens de linha e uma amostra de registros por tabela antes de
   considerar a migração concluída (o script imprime a contagem por tabela
   mesmo em dry-run).
5. Rodar de novo com `--confirmar` pra gravar de verdade.
6. **Rodar `python -m app.scripts.hash_senhas_pendentes --confirmar` logo em
   seguida.** O login já migra senha de texto plano pra hash sozinho, mas só
   no primeiro acesso de cada usuário — sem esse passo, toda senha
   importada do MySQL fica em texto plano no Postgres até cada pessoa
   logar. Não faz sentido esperar: hashear tudo em lote assim que os dados
   chegam elimina esse texto plano de uma vez.
7. Só depois de validado: repetir o processo contra o dump/produção de
   verdade, num Postgres que vai ser o definitivo.

## Aviso de segurança

O dump `sgf_abrigo*.sql` (e qualquer cópia/backup do banco de produção)
**nunca deve ser commitado em nenhum repositório**, público ou privado —
contém dados pessoais reais (nomes, CPF, endereço, telefone, observações de
avaliação social) de pessoas atendidas pela instituição, além de senhas de
usuário em texto plano. Mantenha esses arquivos fora de qualquer pasta
versionada, em ambiente local/controlado.

## Status

- [x] Backend configurado para Postgres (`psycopg`) + `pgvector` instalado
      como dependência.
- [x] Migrações Alembic (`0001` a `0009`) criam todas as 16 tabelas do
      schema novo (todas as features do backlog de `docs/atividades.md`,
      exceto `disponibilidade`/`procedimentos`, deixadas de fora por
      decisão — ver esse documento).
- [x] Script de ETL (`app/scripts/etl_migracao.py` — Python, não pgloader,
      ver decisão acima) com transformações testadas
      (`tests/test_etl_transformacoes.py`,
      `tests/test_etl_reconciliacao.py`, 16 testes).
- [x] **Testado de ponta a ponta contra o dump real de produção
      (2026-09-11).** MySQL 8.0 já estava instalado localmente; como o
      dump tem `CREATE DATABASE IF NOT EXISTS sgf; USE sgf;` embutido
      (ignora qualquer nome de banco passado na hora de restaurar), a
      primeira tentativa colidiu com um banco `sgf` de um projeto de ERP
      não relacionado já existente no MySQL compartilhado da máquina,
      sobrescrevendo 8 tabelas de nomes coincidentes lá antes do erro ser
      percebido (usuário confirmou que não tinha problema, mas o dump foi
      corrigido — ver abaixo). Teste real rodou numa instância MySQL
      **totalmente isolada** (datadir e porta própria, sem nenhum outro
      banco), com o Postgres alvo simulado por SQLite (sem Postgres
      instalado no ambiente; os models não usam nenhum tipo específico do
      Postgres fora do `pgvector`, que ainda não está em uso em nenhuma
      coluna). Todas as 14 tabelas carregaram e bateram com as contagens
      documentadas em `docs/atividades.md`; a reconciliação de
      `acompanhamento` recuperou 7 de 22 registros automaticamente (15
      ficaram pendentes de revisão manual, paciente com 0 ou 2+ estadias);
      `hash_senhas_pendentes --confirmar` rodou depois e hasheou as 7
      senhas de usuário. Dois bugs reais encontrados e corrigidos com esse
      teste (ver `app/features/pessoas/pessoa.legacy.md` e
      `app/features/estadias/estadia.legacy.md`):
      1. `pessoa.data_cadastro` — 444 de 5.326 pessoas (~8,3%) têm a data
         zerada no legado; o model era `NOT NULL`, corrigido pra
         `date | None` (`alembic/versions/0009_...py`).
      2. Linhas de `EstadiaAcompanhante` reconciliadas a partir de
         `acompanhamento` não tinham `data_entrada` (a tabela legada não
         guarda essa informação) — o ETL agora usa a `data_entrada` da
         própria `estadia` do paciente como aproximação documentada.
      **O dump local (`C:\repos\caaf\sgf_abrigo 20260909 1501.sql`) foi
      corrigido** pra usar `sgf_abrigo_import` no lugar de `sgf` — nunca
      mais deve colidir com outro banco.
      **Ainda falta:** rodar contra um Postgres de verdade (só SQLite foi
      testado aqui) antes de considerar o ETL pronto pra produção — os
      tipos usados são todos padrão SQL então não é esperada diferença de
      comportamento, mas não foi validado.
- [ ] Habilitar `pgvector` de fato numa coluna (`vector(N)`) quando a
      funcionalidade de busca semântica for implementada.
