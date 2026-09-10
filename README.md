# Abrigo — Backend

Backend em Python (FastAPI) do sistema de gestão da **Casa de Apoio Amor
Fraterno**.

> **Este é um projeto de uma organização sem fins lucrativos (ONG).** O
> código é aberto para que voluntários e desenvolvedores da comunidade
> possam contribuir gratuitamente com a manutenção e evolução do sistema
> usado pela instituição. Nenhuma receita é gerada a partir deste software;
> contribuições de código são bem-vindas via *pull request*.

## Contexto

Este projeto substitui o **abrigo-legacy** ("Argos — Controle de
Atendimento"), um sistema desktop em Delphi com banco **MySQL 5.5** usado
hoje pela Casa de Apoio Amor Fraterno para controlar atendimentos, estadias,
voluntários, empréstimos de materiais e acompanhamento social de pessoas
atendidas. Este backend expõe uma API REST consumida pelo
[`abrigo-frontend`](https://github.com/casa-de-apoio-amor-fraterno/abrigo-frontend) (Angular).

O banco de dados do sistema novo é **PostgreSQL + pgvector** (não MySQL) —
ver [`docs/migracao-postgres.md`](docs/migracao-postgres.md) para a decisão
completa e o plano de migração dos dados.

**Atenção:** os dados e credenciais do sistema legado (banco MySQL de
produção, arquivos `.mwb`, backups) **não fazem parte deste repositório** e
não devem ser commitados aqui — eles ficam apenas no ambiente local/da
instituição.

## Tecnologias

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x (ORM)
- Pydantic / pydantic-settings
- Alembic (migrações de banco)
- PostgreSQL + [pgvector](https://github.com/pgvector/pgvector) (via psycopg) —
  ver [`docs/migracao-postgres.md`](docs/migracao-postgres.md)
- Pytest

## Estrutura

```txt
app/
├── core/
│   ├── config.py       -> configurações (variáveis de ambiente)
│   └── database.py     -> engine, sessão, Base declarativa
│
├── features/
│   {area-de-negocio}/
│       models.py       -> modelo SQLAlchemy (tabela)
│       schemas.py       -> DTOs Pydantic (request/response)
│       service.py        -> regra de negócio / acesso a dados
│       router.py         -> endpoints FastAPI
│       {rotina}.legacy.md -> origem no sistema Delphi legado
│
└── main.py              -> criação do app, registro de routers
```

### Mapeamento do sistema legado (Delphi) para as áreas do backend

| Unit Delphi (`fonte/Unt/...`) | Feature proposta (`app/features/...`) |
| --- | --- |
| `Pessoa` (cadastro, avaliação social, composição familiar) | `pessoas/` (implementado como referência) |
| `Voluntario` | `voluntarios/` |
| `Estadia` | `estadias/` |
| `Emprestimo` | `emprestimos/` |
| `Material` | `materiais/` |
| `Procedimento` / `ProcedimentoRealizado` | `procedimentos/` |
| `Acompanhamento` | `acompanhamentos/` |
| `Hospital` / `Municipio` / `Estado` | `cadastros_base/` |
| `Quarto` / `Disponibilidade` | `quartos/` |
| `Usuario` | `usuarios/` (+ `auth/` para login) |

Cada feature nova deve seguir o mesmo padrão da feature `pessoas/` (que serve
de referência) e documentar sua origem em um `.legacy.md`.

## Banco de dados: PostgreSQL novo, populado por ETL do MySQL legado

O MySQL 5.5 de produção (desde 2013) tem dados reais de pessoas atendidas,
estadias, voluntários etc., mas o **destino** é um Postgres novo — os dados
chegam lá via ETL (`pgloader`), não por migração in-place. Ver
[`docs/migracao-postgres.md`](docs/migracao-postgres.md) para a decisão e o
plano completo.

Uma vez que o Postgres novo tiver dados reais, a regra de sempre passa a
valer: migrações Alembic (`alembic/versions/`) devem ser **aditivas**
(`ALTER TABLE ... ADD COLUMN`, novas tabelas) — nunca `DROP`/recriar uma
tabela com dado real sem antes migrar o conteúdo para o novo formato.

Ao mapear uma tabela do dump legado num `models.py` novo, usar os mesmos
nomes de coluna reais (confirmados no dump, não só nos formulários Delphi —
ver `pessoa.legacy.md` para um caso em que o formulário escondia uma coluna
que existe de verdade) em vez de inventar um schema do zero.

### Exemplo aplicado: login e senha em texto plano

O sistema legado guarda e compara a senha em **texto plano**
(`SELECT ... FROM usuario WHERE login = :Login AND senha = :Senha`, ver
`app/features/usuarios/usuario.legacy.md`) e **nunca checa se o usuário está
ativo** — um bug de segurança real, corrigido deliberadamente no sistema
novo. A migração de senha não força reset de ninguém: o schema já nasce com
`usuario.senha_hash`, e o login (`app/features/auth/service.py`) usa hash se
existir, ou valida pelo texto plano legado e grava o hash na hora (lazy
migration no primeiro login do sistema novo).

## Desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
copy .env.example .env      # ajustar DATABASE_URL para o Postgres local

uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`; documentação automática em
`http://localhost:8000/docs`.

```bash
pytest      # testes
ruff check .  # lint
```

```bash
alembic upgrade head                          # aplica migrações pendentes
python -m app.scripts.criar_usuario admin senha123 "Administrador"  # cria/atualiza um usuário
python -m app.scripts.hash_senhas_pendentes --confirmar  # hasheia em lote senha legada em texto plano
```

## Licença

[MIT](LICENSE).
