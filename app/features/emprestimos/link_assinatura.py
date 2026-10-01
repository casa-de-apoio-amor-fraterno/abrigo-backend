"""Assinatura remota do contrato de comodato (link sem login + CPF).

Só vale pra contratos pendentes (empréstimo sem "Comodato" assinado). Ver
`models.EmprestimoLinkAssinatura` pro desenho de segurança (hash do token,
expiração, uso único, trava por tentativas de CPF)."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.features.emprestimos import service
from app.features.emprestimos.models import (
    Emprestimo,
    EmprestimoContrato,
    EmprestimoItem,
    EmprestimoLinkAssinatura,
)
from app.features.materiais.models import Material
from app.features.pessoas.models import Pessoa
from app.features.usuarios.models import Usuario

VALIDADE_HORAS = 48
# Sem I/O/0/1, que se confundem ao digitar/ler.
_ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO_CODIGO = 8
MAX_TENTATIVAS_CPF = 5


class LinkInvalido(Exception):
    """Token inexistente, expirado, já usado, revogado ou travado — a
    mensagem diz o motivo (o token é secreto, então não vaza nada)."""


class LinkNaoEncontrado(LinkInvalido):
    """Token/código que não existe — o router conta isso por IP (freio contra
    chute de código)."""


class CpfIncorreto(Exception):
    def __init__(self, tentativas_restantes: int) -> None:
        super().__init__("Os dígitos do CPF não conferem.")
        self.tentativas_restantes = tentativas_restantes


class PessoaSemCpf(Exception):
    pass


def _agora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _gerar_codigo() -> str:
    return "".join(secrets.choice(_ALFABETO_CODIGO) for _ in range(TAMANHO_CODIGO))


def formatar_codigo(codigo: str) -> str:
    return f"{codigo[:4]}-{codigo[4:]}"


def _normalizar_codigo(valor: str) -> str | None:
    """Devolve o código em maiúsculas sem hífen/espaço se `valor` tiver o
    formato de código curto; `None` se parecer um token longo."""
    limpo = "".join(c for c in valor.upper() if c.isalnum())
    if len(limpo) == TAMANHO_CODIGO and len(valor) <= TAMANHO_CODIGO + 3:
        return limpo
    return None


def _so_digitos(valor: str | None) -> str:
    return "".join(c for c in (valor or "") if c.isdigit())


def criar_link(
    db: Session, emprestimo: Emprestimo, id_usuario: int
) -> tuple[EmprestimoLinkAssinatura, str, str]:
    if service._buscar_contrato_original(db, emprestimo.id) is not None:
        raise service.ContratoJaAssinado("Este empréstimo já tem um contrato de comodato assinado.")
    pessoa = db.get(Pessoa, emprestimo.id_pessoa)
    if pessoa is None or len(_so_digitos(pessoa.cpf)) != 11:
        raise PessoaSemCpf(
            "A pessoa deste empréstimo não tem CPF válido cadastrado — "
            "ele é necessário para confirmar a identidade na assinatura."
        )

    # Um link ativo por empréstimo: o novo invalida os anteriores.
    db.execute(
        update(EmprestimoLinkAssinatura)
        .where(
            EmprestimoLinkAssinatura.id_emprestimo == emprestimo.id,
            EmprestimoLinkAssinatura.usado_em.is_(None),
            EmprestimoLinkAssinatura.revogado.is_(False),
        )
        .values(revogado=True)
    )

    token = secrets.token_urlsafe(32)
    codigo = _gerar_codigo()
    agora = _agora()
    link = EmprestimoLinkAssinatura(
        id_emprestimo=emprestimo.id,
        id_usuario=id_usuario,
        token_hash=_hash(token),
        codigo_hash=_hash(codigo),
        criado_em=agora,
        expira_em=agora + timedelta(hours=VALIDADE_HORAS),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    service._registrar_historico(
        db,
        emprestimo.id,
        id_usuario,
        "Link de assinatura",
        "Link de assinatura remota gerado para o contrato de comodato.",
    )
    return link, token, formatar_codigo(codigo)


def listar_ativos(db: Session, emprestimo_id: int) -> list[EmprestimoLinkAssinatura]:
    return list(
        db.scalars(
            select(EmprestimoLinkAssinatura)
            .where(
                EmprestimoLinkAssinatura.id_emprestimo == emprestimo_id,
                EmprestimoLinkAssinatura.usado_em.is_(None),
                EmprestimoLinkAssinatura.revogado.is_(False),
                EmprestimoLinkAssinatura.expira_em > _agora(),
            )
            .order_by(EmprestimoLinkAssinatura.criado_em.desc())
        )
    )


def revogar(db: Session, emprestimo_id: int, link_id: int) -> bool:
    link = db.get(EmprestimoLinkAssinatura, link_id)
    if link is None or link.id_emprestimo != emprestimo_id:
        return False
    link.revogado = True
    db.commit()
    return True


def validar_link(db: Session, token: str) -> EmprestimoLinkAssinatura:
    codigo = _normalizar_codigo(token)
    if codigo is not None:
        criterio = EmprestimoLinkAssinatura.codigo_hash == _hash(codigo)
    else:
        criterio = EmprestimoLinkAssinatura.token_hash == _hash(token)
    link = db.scalar(select(EmprestimoLinkAssinatura).where(criterio))
    if link is None:
        raise LinkNaoEncontrado("Link ou código inválido.")
    if link.revogado:
        raise LinkInvalido("Este link foi cancelado. Peça um novo à equipe.")
    if link.usado_em is not None or service._buscar_contrato_original(db, link.id_emprestimo) is not None:
        raise LinkInvalido("Este contrato já foi assinado.")
    if link.expira_em <= _agora():
        raise LinkInvalido("Este link expirou. Peça um novo à equipe.")
    if link.tentativas_cpf >= MAX_TENTATIVAS_CPF:
        raise LinkInvalido("Este link foi bloqueado por excesso de tentativas. Peça um novo à equipe.")
    return link


def _conferir_cpf(db: Session, link: EmprestimoLinkAssinatura, cpf_final: str) -> Pessoa:
    """Confere os 4 últimos dígitos do CPF cadastrado (o token/código do link
    é o segredo principal; o CPF é o segundo fator, e o limite de tentativas
    por link segura o chute nos 10 mil casos possíveis)."""
    emprestimo = db.get(Emprestimo, link.id_emprestimo)
    pessoa = db.get(Pessoa, emprestimo.id_pessoa) if emprestimo else None
    cpf_cadastrado = _so_digitos(pessoa.cpf if pessoa else None)
    if pessoa is None or len(cpf_cadastrado) != 11:
        raise LinkInvalido("Não foi possível confirmar sua identidade. Procure a equipe.")
    if not hmac.compare_digest(_so_digitos(cpf_final), cpf_cadastrado[-4:]):
        link.tentativas_cpf += 1
        db.commit()
        raise CpfIncorreto(max(MAX_TENTATIVAS_CPF - link.tentativas_cpf, 0))
    return pessoa


def resumo_contrato(db: Session, token: str, cpf_final: str) -> dict:
    """Dados do contrato mostrados depois que o CPF confere."""
    link = validar_link(db, token)
    pessoa = _conferir_cpf(db, link, cpf_final)
    emprestimo = db.get(Emprestimo, link.id_emprestimo)
    itens = list(
        db.scalars(
            select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo.id).order_by(EmprestimoItem.id)
        )
    )
    inicio, termino, dias = service._prazo_vigencia_contrato(emprestimo)
    descricoes = []
    for item in itens:
        material = db.get(Material, item.id_material)
        descricoes.append(
            {
                "descricao": material.descricao if material else f"Material #{item.id_material}",
                "numero_patrimonio": material.numero_patrimonio if material else None,
            }
        )
    return {
        "nome_pessoa": pessoa.nome,
        "numero_contrato": emprestimo.numero_contrato,
        "itens": descricoes,
        "data_inicio": inicio,
        "data_termino": termino,
        "dias": dias,
    }


def pdf_previa(db: Session, token: str, cpf_final: str) -> bytes:
    """Contrato completo sem assinatura, pra pessoa ler antes de assinar."""
    link = validar_link(db, token)
    pessoa = _conferir_cpf(db, link, cpf_final)
    emprestimo = db.get(Emprestimo, link.id_emprestimo)
    usuario = db.get(Usuario, link.id_usuario)
    itens = list(db.scalars(select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo.id)))
    return service._gerar_pdf_contrato(db, emprestimo, pessoa, usuario, itens, None)  # type: ignore[arg-type]


def assinar(db: Session, token: str, cpf_final: str, assinatura_png_base64: str) -> EmprestimoContrato:
    link = validar_link(db, token)
    _conferir_cpf(db, link, cpf_final)
    emprestimo = db.get(Emprestimo, link.id_emprestimo)
    contrato = service.criar_contrato(db, emprestimo, link.id_usuario, assinatura_png_base64, "Comodato")
    link.usado_em = _agora()
    db.commit()
    service._registrar_historico(
        db,
        emprestimo.id,
        link.id_usuario,
        "Assinatura remota",
        "Contrato assinado pela própria pessoa, por link e confirmação de CPF.",
    )
    return contrato
