from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.estadias.models import (
    Estadia,
    EstadiaAcompanhante,
    EstadiaHistorico,
    SituacaoEstadia,
    UnidadeTempoEstadia,
)
from app.features.estadias.schemas import (
    EstadiaAcompanhanteCreate,
    EstadiaCreate,
    EstadiaUpdate,
)
from app.features.hospitais.models import Hospital
from app.features.quartos.models import Quarto

# Rótulo em português de cada campo que entra no diff de "Alteração" do
# histórico (ver `_descricao_alteracao`) — mesmo espírito de
# `emprestimos/service.py._descricao_item`, mas comparando campo a campo em
# vez de montar uma descrição fixa, já que aqui o que importa é O QUE mudou.
_ROTULOS_HISTORICO: dict[str, str] = {
    "id_quarto": "Quarto",
    "id_hospital": "Hospital",
    "tipo_pessoa": "Tipo de pessoa",
    "situacao": "Situação",
    "data_entrada": "Data de entrada",
    "data_saida": "Data de saída",
    "tempo_estadia_valor": "Tempo estadia (valor)",
    "tempo_estadia_unidade": "Tempo estadia (unidade)",
    "observacao": "Observação",
}


def _registrar_historico(
    db: Session, id_estadia: int, id_usuario: int, tipo: str, observacao: str
) -> None:
    db.add(
        EstadiaHistorico(
            id_estadia=id_estadia,
            id_usuario=id_usuario,
            tipo=tipo,
            observacao=observacao,
            # Coluna `DateTime` sem timezone (mesmo padrão de
            # `EmprestimoHistorico.data_cadastro`) — grava naive em UTC.
            data_cadastro=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    db.commit()


def _numero_quarto(db: Session, id_quarto: int | None) -> str | None:
    """Traduz `id_quarto` (chave interna) pro `numero` que o front exibe —
    sem isso, o histórico mostra o id do banco (ex.: "quarto #22") em vez
    do número real do quarto (ex.: "00"), que não têm relação nenhuma."""
    if id_quarto is None:
        return None
    quarto = db.get(Quarto, id_quarto)
    return quarto.numero if quarto else None


def _nome_hospital(db: Session, id_hospital: int | None) -> str | None:
    """Mesmo caso de `_numero_quarto`, pro campo Hospital."""
    if id_hospital is None:
        return None
    hospital = db.get(Hospital, id_hospital)
    return hospital.nome if hospital else None


# Campos de `_ROTULOS_HISTORICO` que são chave estrangeira (id de outra
# tabela) — precisam passar pelo tradutor antes de entrar no diff, senão o
# histórico mostra o id do banco em vez do valor que o front exibe.
_TRADUTORES_FK: dict[str, Callable[[Session, int | None], str | None]] = {
    "id_quarto": _numero_quarto,
    "id_hospital": _nome_hospital,
}


def _descricao_alteracao(db: Session, estadia: Estadia, dados: EstadiaUpdate) -> str | None:
    """Compara os campos relevantes ANTES de `atualizar` sobrescrevê-los —
    retorna None quando nada realmente mudou, pra não poluir o histórico
    com uma entrada "Alteração" vazia a cada PUT idempotente."""
    novos_valores = dados.model_dump()
    mudancas = []
    for campo, rotulo in _ROTULOS_HISTORICO.items():
        valor_antigo = getattr(estadia, campo)
        valor_antigo = valor_antigo.value if hasattr(valor_antigo, "value") else valor_antigo
        # `model_dump()` (modo Python, não "json") mantém enums como
        # instância — sem isso, o diff mostra "SituacaoEstadia.FINALIZADA"
        # em vez de "Finalizada".
        valor_novo = novos_valores.get(campo)
        valor_novo = valor_novo.value if hasattr(valor_novo, "value") else valor_novo
        tradutor = _TRADUTORES_FK.get(campo)
        if tradutor:
            valor_antigo = tradutor(db, valor_antigo)
            valor_novo = tradutor(db, valor_novo)
        if valor_antigo != valor_novo:
            mudancas.append(f"{rotulo}: {valor_antigo or '-'} -> {valor_novo or '-'}")
    return "; ".join(mudancas) if mudancas else None


def listar(
    db: Session,
    id_pessoa: int | None = None,
    id_pessoa_acompanhante: int | None = None,
    situacao: SituacaoEstadia | None = None,
    skip: int = 0,
    take: int = 50,
) -> tuple[list[Estadia], int]:
    consulta = select(Estadia)
    if id_pessoa_acompanhante is not None:
        # Estadias onde a pessoa aparece como acompanhante de OUTRO
        # paciente (`EstadiaAcompanhante.id_pessoa`), não como titular do
        # leito (`Estadia.id_pessoa`) — usado pela busca global, pra achar
        # a pessoa também nesse papel. Mutuamente exclusivo com `id_pessoa`.
        consulta = consulta.join(
            EstadiaAcompanhante, EstadiaAcompanhante.id_estadia == Estadia.id
        ).where(EstadiaAcompanhante.id_pessoa == id_pessoa_acompanhante)
    elif id_pessoa is not None:
        consulta = consulta.where(Estadia.id_pessoa == id_pessoa)
    if situacao is not None:
        consulta = consulta.where(Estadia.situacao == situacao)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(
        consulta.order_by(Estadia.data_entrada.desc()).offset(skip).limit(take)
    ).all()
    return list(itens), total


def buscar(db: Session, estadia_id: int) -> Estadia | None:
    return db.get(Estadia, estadia_id)


def criar(db: Session, dados: EstadiaCreate) -> Estadia:
    campos_estadia = dados.model_dump(exclude={"acompanhantes"})
    estadia = Estadia(**campos_estadia)
    db.add(estadia)
    db.flush()  # gera estadia.id sem fechar a transação, pra usar como FK abaixo

    for acompanhante in dados.acompanhantes:
        db.add(EstadiaAcompanhante(id_estadia=estadia.id, **acompanhante.model_dump()))

    db.commit()
    db.refresh(estadia)
    numero_quarto = _numero_quarto(db, estadia.id_quarto) or f"#{estadia.id_quarto}"
    _registrar_historico(
        db,
        estadia.id,
        dados.id_usuario,
        "Inclusão",
        f"Estadia criada — quarto {numero_quarto}, {estadia.tipo_pessoa.value}, "
        f"situação {estadia.situacao.value}.",
    )
    return estadia


def atualizar(db: Session, estadia: Estadia, dados: EstadiaUpdate) -> Estadia:
    descricao = _descricao_alteracao(db, estadia, dados)
    for campo, valor in dados.model_dump().items():
        setattr(estadia, campo, valor)
    db.commit()
    db.refresh(estadia)
    if descricao:
        _registrar_historico(db, estadia.id, dados.id_usuario, "Alteração", descricao)
    return estadia


def encerrar(
    db: Session,
    estadia: Estadia,
    data_saida: datetime | None = None,
    tempo_estadia_valor: int | None = None,
    tempo_estadia_unidade: UnidadeTempoEstadia | None = None,
    id_usuario: int | None = None,
) -> Estadia:
    estadia.situacao = SituacaoEstadia.FINALIZADA
    estadia.data_saida = data_saida or datetime.now(UTC).replace(tzinfo=None)
    estadia.ativo = False
    # Calculado no frontend a partir de data_entrada/data_saida (ver
    # estadia.legacy.md) — só sobrescreve quando informado, pra não apagar
    # um valor já existente ao encerrar sem passar por aqui.
    if tempo_estadia_valor is not None:
        estadia.tempo_estadia_valor = tempo_estadia_valor
    if tempo_estadia_unidade is not None:
        estadia.tempo_estadia_unidade = tempo_estadia_unidade
    db.commit()
    db.refresh(estadia)
    # Opcional (ver EstadiaEncerrarRequest.id_usuario) — só registra no
    # histórico quando quem chamou informou o usuário responsável.
    if id_usuario is not None:
        _registrar_historico(
            db,
            estadia.id,
            id_usuario,
            "Encerramento",
            f"Estadia encerrada em {estadia.data_saida.strftime('%d/%m/%Y')}.",
        )
    return estadia


def listar_acompanhantes(db: Session, estadia_id: int) -> list[EstadiaAcompanhante]:
    consulta = select(EstadiaAcompanhante).where(EstadiaAcompanhante.id_estadia == estadia_id)
    return list(db.scalars(consulta.order_by(EstadiaAcompanhante.data_entrada)).all())


def adicionar_acompanhante(
    db: Session, estadia_id: int, dados: EstadiaAcompanhanteCreate
) -> EstadiaAcompanhante:
    acompanhante = EstadiaAcompanhante(id_estadia=estadia_id, **dados.model_dump())
    db.add(acompanhante)
    db.commit()
    db.refresh(acompanhante)
    return acompanhante


def listar_historico(db: Session, estadia_id: int) -> list[EstadiaHistorico]:
    consulta = select(EstadiaHistorico).where(EstadiaHistorico.id_estadia == estadia_id)
    return list(db.scalars(consulta.order_by(EstadiaHistorico.data_cadastro.desc())).all())
