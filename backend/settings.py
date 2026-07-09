from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    google_api_key: str = ""
    use_fallback: bool = False
    chroma_db_path: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    )
    docs_path: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "documents.json")
    )
    iot_path: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "iot_data.json")
    )
    static_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

    # Neo4j Settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "industrialpass"

    # JWT Settings
    secret_key: str = "super_secret_industrial_key"
    postgres_uri: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vectors"
    redis_uri: str = "redis://localhost:6379/0"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
