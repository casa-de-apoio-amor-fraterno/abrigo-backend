from pydantic import BaseModel


class LoginRequest(BaseModel):
    usuario: str
    senha: str


class SessaoResponse(BaseModel):
    nome: str
    token: str
    perfil: str
    usuario_id: int
