from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "REGIME REAPER"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./reaper.db"

    SECRET_KEY: str = "change-this-in-production"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    SCRAPFLY_KEY: Optional[str] = None

    DISCORD_BOT_TOKEN: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None        # #reaper-main (default)
    DISCORD_HOT_DEALS_WEBHOOK: Optional[str] = None   # #hot-deals (BUY NOW only)
    DISCORD_SCAN_LOG_WEBHOOK: Optional[str] = None    # #scan-log
    DISCORD_INVENTORY_WEBHOOK: Optional[str] = None   # #inventory-log
    DISCORD_WATCHLIST_WEBHOOK: Optional[str] = None   # #reaper-watchlist
    DISCORD_ALERT_CHANNEL_ID: Optional[str] = None
    DISCORD_GUILD_ID: Optional[str] = None

    NHTSA_VIN_URL: str = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin"

    DEFAULT_LOCATION: str = "Tampa, FL"
    DEFAULT_RADIUS: int = 75
    DEFAULT_MAX_PRICE: int = 2500
    DEFAULT_MIN_PRICE: int = 1000
    DEFAULT_MAX_MILEAGE: int = 200000
    DEFAULT_MIN_YEAR: int = 2005
    DEFAULT_MAX_REPAIR_BUDGET: int = 500
    DEFAULT_TARGET_PROFIT: int = 1500
    DEFAULT_ALERT_SCORE_THRESHOLD: int = 75

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
