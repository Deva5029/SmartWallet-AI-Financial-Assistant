from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # This URL now correctly uses the 'dev' user and 'dev' password
    # to match the docker-compose.yml file.
    DATABASE_URL: str = "postgresql://dev:dev@db/smartwallet"

    class Config:
        env_file = ".env"

settings = Settings()
