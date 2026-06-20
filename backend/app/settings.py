from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI-Enhanced IDS Backend"
    environment: str = "dev"


settings = Settings()

