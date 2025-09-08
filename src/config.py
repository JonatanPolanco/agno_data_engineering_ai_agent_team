from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class AppSettings(BaseSettings):
    """Configuración centralizada de la aplicación."""
    
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        extra='ignore'
    )
    
    # Google Cloud
    google_project_id: str
    google_api_key: str
    data_store_id: str
    
    # Database
    db_file_path: str = "tmp/agents.db"
    db_table_prefix: str = "team"
    
    # Models
    default_llm_pro: str = "gemini-2.5-pro"
    default_llm_flash: str = "gemini-2.5-flash"

# Instancia singleton
settings = AppSettings()