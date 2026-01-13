from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "123456"
    DATABASE_NAME: str = "vote"
    
    # DATABASE_HOST: str = "localhost"
    # DATABASE_PORT: int = 5432
    # DATABASE_USER: str = "postgres"
    # DATABASE_PASSWORD: str = "123457"
    # DATABASE_NAME: str = "vote2"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    DATABASE_TYPE: str = "sqlite"  # postgres or sqlite

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_TYPE == "sqlite":
            return f"sqlite+aiosqlite:///./{self.DATABASE_NAME}.db"
        return f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    class Config:
        env_file = ".env"


settings = Settings()
