from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str
    events_api_url: str
    events_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()