from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    output_dir: str = "output"
    min_sentences: int = 1
    max_sentences: int = 5
    default_language: str = "en"
    
    class Config:
        env_prefix = "POEM_"

settings = Settings() 