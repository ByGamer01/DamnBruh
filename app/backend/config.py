import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Privy Configuration
    PRIVY_APP_ID = os.getenv("PRIVY_APP_ID")
    PRIVY_APP_SECRET = os.getenv("PRIVY_APP_SECRET")
    
    # Database Configuration
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "betting_game")
    
    # Security Configuration  
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-for-jwt-signing-minimum-32-chars-long")
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Game Configuration
    MIN_BET_AMOUNT = Decimal(os.getenv("MIN_BET_AMOUNT", "0.001"))
    MAX_BET_AMOUNT = Decimal(os.getenv("MAX_BET_AMOUNT", "10.0"))
    HOUSE_EDGE = Decimal(os.getenv("HOUSE_EDGE", "0.02"))
    MAX_DAILY_WITHDRAWAL = Decimal(os.getenv("MAX_DAILY_WITHDRAWAL", "100.0"))
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    MAX_BETS_PER_MINUTE = int(os.getenv("MAX_BETS_PER_MINUTE", "10"))
    
    # Affiliate Configuration
    DEFAULT_COMMISSION_RATE = Decimal(os.getenv("DEFAULT_COMMISSION_RATE", "0.05"))  # 5%
    
    # Validation
    @classmethod
    def validate(cls):
        required_fields = ["PRIVY_APP_ID", "PRIVY_APP_SECRET"]
        missing = [field for field in required_fields if not getattr(cls, field)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

settings = Settings()
settings.validate()