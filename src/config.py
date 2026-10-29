from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PORT: int = 8000
    DEBUG: bool = True
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/hospital.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()