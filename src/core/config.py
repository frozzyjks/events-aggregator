from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    events_api_url: str
    events_api_key: str

    @property
    def db_url(self) -> str:
        url = self.database_url or self.postgres_connection_string
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = ".env"


settings = Settings()