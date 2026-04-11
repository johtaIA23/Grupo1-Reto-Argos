from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    csv_path: str = "/data/ferreterias.csv"
    api_title: str = "Ferreterías Colombia API"
    api_version: str = "1.0.0"
    api_description: str = "Servicio de procesamiento de datos para el censo digital de ferreterías"
    supabase_url: str = ""
    supabase_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
