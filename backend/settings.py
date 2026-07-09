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

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
