from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MaterialLocal(Base):
    """Onde um material está fisicamente (ex.: 'Casa', 'Bazar') ou o estado
    de estar emprestado ('Empréstimo'). Era o campo `material.local`, texto
    livre no legado — fechado numa tabela própria em 2026-09-26 (mesmo
    padrão de `Hospital`, CRUD simples id+nome) pra permitir cadastrar
    novos pontos da CAAF sem depender de código, sem risco de variação de
    texto. Migração 0027 seedou a tabela com os 3 valores reais
    encontrados em produção e converteu `Material.local` pra
    `Material.id_local` (FK)."""

    __tablename__ = "material_local"

    id: Mapped[int] = mapped_column("id_material_local", primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    ativo: Mapped[bool] = mapped_column(default=True)
