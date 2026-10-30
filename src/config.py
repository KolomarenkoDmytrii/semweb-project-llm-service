from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    CHEMISTRY_API_BASE: str = "http://localhost:8000"

    # Use the base URL of KoboldCpp's OpenAI-compatible API.
    # The code adds /v1 if it is not already present.
    KOBOLD_API_URL: str = "http://localhost:5001"
    KOBOLD_MODEL: str = "mistral"
    KOBOLD_API_KEY: str = "not-needed"

    MCP_SERVER_PORT: int = 3000
    DEBUG: bool = True


settings = Settings()
