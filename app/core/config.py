from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: int
    database_username: str
    database_password: str
    database_name: str
    database_key: str

    secret_key: str
    algorithm: str

    access_token_expire_minutes: int
    refresh_token_expire_days: int

    model_config = {
        "env_file": ".env"
    }


settings = Settings()
