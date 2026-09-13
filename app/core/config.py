from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://usuario:senha@localhost:5432/abrigo"
    cors_origins: list[str] = ["http://localhost:4200"]

    # Sem default: um fallback conhecido aqui permitiria forjar token de
    # qualquer usuário caso a env var não seja definida em algum deploy.
    # A app deve falhar ao subir, não subir insegura silenciosamente.
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 8

    @field_validator("cors_origins")
    @classmethod
    def _rejeitar_wildcard(cls, origins: list[str]) -> list[str]:
        # A API usa allow_credentials=True (auth por Bearer token), então um
        # "*" aqui seria um wildcard efetivamente sem limite de origem para
        # requisições autenticadas — navegadores já bloqueiam
        # "*"+credentials, mas não custa recusar na config em vez de
        # depender só disso.
        if "*" in origins:
            raise ValueError(
                "cors_origins não pode conter '*' (allow_credentials=True está ativo); "
                "liste os domínios de origem explicitamente"
            )
        return origins

    @field_validator("jwt_secret_key")
    @classmethod
    def _exigir_tamanho_minimo(cls, chave: str) -> str:
        if len(chave) < 32:
            raise ValueError("jwt_secret_key precisa ter pelo menos 32 caracteres")
        return chave


settings = Settings()
