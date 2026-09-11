from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.core.database import Base

# Importa os models para que fiquem registrados em Base.metadata (necessário
# pro autogenerate do Alembic enxergar todas as tabelas).
from app.features.avaliacao_social import models as avaliacao_social_models  # noqa: F401
from app.features.composicao_familiar import models as composicao_familiar_models  # noqa: F401
from app.features.emprestimos import models as emprestimos_models  # noqa: F401
from app.features.estadias import models as estadias_models  # noqa: F401
from app.features.estados import models as estados_models  # noqa: F401
from app.features.hospitais import models as hospitais_models  # noqa: F401
from app.features.materiais import models as materiais_models  # noqa: F401
from app.features.municipios import models as municipios_models  # noqa: F401
from app.features.pessoas import models as pessoas_models  # noqa: F401
from app.features.quartos import models as quartos_models  # noqa: F401
from app.features.usuarios import models as usuarios_models  # noqa: F401
from app.features.voluntarios import models as voluntarios_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
