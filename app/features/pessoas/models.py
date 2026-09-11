from datetime import date

from sqlalchemy import Date, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Pessoa(Base):
    """Mapeia a tabela `pessoa` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    Não inclui o campo legado `tipo` (Paciente/Acompanhante/Emprestimo) — ver
    `pessoa.legacy.md`: é um papel contextual de uma estadia, não um atributo
    permanente da pessoa, e deve ser modelado em `Estadia.tipo_pessoa` (ou na
    entidade de empréstimo), não aqui. Na migração de dados, o valor de
    `tipo` é lido do dump só para popular `estadia.tipo_pessoa` correspondente,
    depois descartado.
    """

    __tablename__ = "pessoa"

    id: Mapped[int] = mapped_column("id_pessoa", primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    data_nascimento: Mapped[date] = mapped_column(Date)
    rg: Mapped[str | None] = mapped_column(String(15), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    profissao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cartao_sus: Mapped[str | None] = mapped_column(String(60), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ponto_referencia: Mapped[str | None] = mapped_column(String(60), nullable=True)
    id_hospital: Mapped[int | None] = mapped_column(ForeignKey("hospital.id_hospital"), nullable=True)
    id_municipio: Mapped[int | None] = mapped_column(ForeignKey("municipio.id_municipio"), nullable=True)
    id_estado: Mapped[int | None] = mapped_column(ForeignKey("estado.id_estado"), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    acompanhamento_social: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_cadastro: Mapped[date | None] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(default=True)

    # Feature nova (2026-09-11) — o legado (`untFrmManutencaoPessoa.pas`)
    # capturava a foto pela webcam e salvava como arquivo `.bmp` em disco
    # (`pessoas\<id_pessoa>.bmp`, fora do banco), sem coluna correspondente
    # na tabela `pessoa`. Não há dado real pra migrar (arquivos ficavam na
    # máquina onde o Delphi rodava, fora do dump e do controle de versão) —
    # aqui vira BLOB no próprio Postgres, sem exigir storage externo.
    foto: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    foto_content_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    @property
    def tem_foto(self) -> bool:
        return self.foto is not None

    contatos: Mapped[list["PessoaContato"]] = relationship(
        order_by="PessoaContato.id", cascade="all, delete-orphan"
    )

    @property
    def telefone_principal(self) -> str | None:
        """Usado na listagem/consulta — o telefone `principal` (ou o
        primeiro cadastrado, se nenhum foi marcado como principal). Ver
        `pessoa.legacy.md` (seção Contatos) pra decisão de normalizar
        telefone numa tabela própria."""
        if not self.contatos:
            return None
        principal = next((c for c in self.contatos if c.principal), self.contatos[0])
        return principal.numero


class PessoaContato(Base):
    """Telefone(s) de contato de uma pessoa — normalizado numa tabela
    própria (2026-09-11): o campo `pessoa.telefone` legado era texto livre
    sem estrutura (`varchar(60)`, um único `TcxDBTextEdit` no Delphi, sem
    máscara) e o dado real de produção mistura múltiplos números, nome de
    quem atende e observações no mesmo campo (ex.: "Sidney 42-98818-3580
    Esposa 98827-3809"). Ver `pessoa.legacy.md` pra detalhes da migração
    (heurística de separação em `app/scripts/etl/transformacoes.py`)."""

    __tablename__ = "pessoa_contato"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    numero: Mapped[str] = mapped_column(String(60))
    nome_contato: Mapped[str | None] = mapped_column(String(60), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    principal: Mapped[bool] = mapped_column(default=False)
