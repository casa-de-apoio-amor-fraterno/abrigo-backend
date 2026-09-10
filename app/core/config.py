from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://usuario:senha@localhost:3306/abrigo"
    cors_origins: list[str] = ["http://localhost:4200"]


settings = Settings()
