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
Atendimento"), um sistema desktop em Delphi com banco MySQL usado hoje pela
Casa de Apoio Amor Fraterno para controlar atendimentos, estadias,
voluntários, empréstimos de materiais e acompanhamento social de pessoas
atendidas. Este backend expõe uma API REST consumida pelo
[`abrigo-frontend`](https://github.com/casa-de-apoio-amor-fraterno/abrigo-frontend) (Angular).

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
- MySQL (via PyMySQL) — mesmo banco de dados do sistema legado, migrado
  incrementalmente
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
| `Usuario` | `usuarios/` |

Cada feature nova deve seguir o mesmo padrão da feature `pessoas/` (que serve
de referência) e documentar sua origem em um `.legacy.md`.

## Desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
copy .env.example .env      # ajustar DATABASE_URL para o MySQL local

uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`; documentação automática em
`http://localhost:8000/docs`.

```bash
pytest      # testes
ruff check .  # lint
```

## Licença

[MIT](LICENSE).
