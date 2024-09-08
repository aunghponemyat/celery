from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app: str = ""
    task_table: str = ""
    broker: str = ""
    tidb_dsn: str = ""


@lru_cache
def get_settings() -> Settings:
    settings = Settings(_env_file=".env")
    return settings
