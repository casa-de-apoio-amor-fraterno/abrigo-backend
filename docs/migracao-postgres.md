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

## Plano de ETL (MySQL → Postgres)

1. **Nunca rodar contra o dump/produção diretamente na primeira tentativa.**
   Restaurar o dump `sgf_abrigo` num MySQL local descartável primeiro.
2. Rodar `alembic upgrade head` no Postgres alvo (cria o schema vazio).
3. Usar [`pgloader`](https://pgloader.io/) para copiar os dados do MySQL
   local pro Postgres, com um script de mapeamento explícito por tabela (não
   um `pgloader mysql://... postgresql://...` genérico) — precisa tratar:
   - **Datas zero do MySQL**: `data_cadastro date NOT NULL DEFAULT
     '0000-00-00'` — `0000-00-00` não existe no Postgres. Mapear pra `NULL`
     quando o valor for zero, ou pra uma data sentinela documentada.
   - **`ativo` como `varchar(3)` ('Sim'/'Não')** → `boolean` (`'Sim'` →
     `true`, qualquer outra coisa → `false`).
   - **`pessoa.tipo`** (`varchar(12)`, 'Paciente'/'Acompanhante'/'Emprestimo')
     **não é copiado pra `pessoa`** — não existe mais nesse schema (ver
     `app/features/pessoas/pessoa.legacy.md`). Em vez disso, o valor de
     `pessoa.tipo` de cada registro é usado para popular
     `estadia.tipo_pessoa` na migração da tabela `estadia` (quando essa
     feature for implementada) — reconciliando com a coluna
     `estadia.tipo_pessoa` que o próprio legado já tinha.
   - **`usuario.senha`** migra como está (texto plano) — o backend já trata
     isso (`app/features/auth/service.py`, migração "preguiçosa" pro hash no
     primeiro login). Não expor esse texto plano em lugar nenhum além do
     banco.
4. Validar contagens de linha e uma amostra de registros por tabela antes de
   considerar a migração concluída.
5. **Rodar `python -m app.scripts.hash_senhas_pendentes --confirmar` logo em
   seguida.** O login já migra senha de texto plano pra hash sozinho, mas só
   no primeiro acesso de cada usuário — sem esse passo, toda senha
   importada do MySQL fica em texto plano no Postgres até cada pessoa
   logar. Não faz sentido esperar: hashear tudo em lote assim que os dados
   chegam elimina esse texto plano de uma vez.
6. Só depois de validado: repetir o processo contra o dump/produção de
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
- [x] `alembic/versions/0001_estrutura_inicial.py` cria `usuario` e `pessoa`.
- [ ] Script de ETL (`pgloader` + mapeamentos) — a fazer.
- [ ] Rodar a migração contra uma cópia de teste do dump antes de produção.
- [ ] Habilitar `pgvector` de fato numa coluna (`vector(N)`) quando a
      funcionalidade de busca semântica for implementada.
