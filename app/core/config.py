from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://usuario:senha@localhost:3306/abrigo"
    cors_origins: list[str] = ["http://localhost:4200"]

    jwt_secret_key: str = "altere-esta-chave-em-producao-para-algo-com-32-bytes-ou-mais"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 8


settings = Settings()
