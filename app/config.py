import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read individual parameters with default values
DB_USER: str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT: str = os.getenv("DB_PORT", "3306")
DB_NAME: str = os.getenv("DB_NAME", "fastapi_demo")
DB_DRIVER: str = os.getenv("DB_DRIVER", "mysql+pymysql")

# Dynamic URL construction for SQLAlchemy
DATABASE_URL: str = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Keep the verification flag in case you migrate to SQLite in the future
IS_SQLITE: bool = DATABASE_URL.startswith("sqlite")
