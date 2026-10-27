from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    app_title: str = "To‘lov nazorati"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
