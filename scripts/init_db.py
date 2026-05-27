import os
from dotenv import load_dotenv
import pymysql

# Load environment variables
load_dotenv()

# Read individual parameters with default values
db_host = os.getenv("DB_HOST", "localhost")
db_port = int(os.getenv("DB_PORT", 3306))
db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "your_password_here")
db_name = os.getenv("DB_NAME", "fastapi_demo")

# Connect to MySQL server to ensure the database exists
try:
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        autocommit=True
    )
    
    with conn.cursor() as cur:
        sql = f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4;"
        cur.execute(sql)
        print(f"Database ensured: {db_name}")
        
except pymysql.MySQLError as e:
    print(f"Error while connecting or creating the database: {e}")
    
finally:
    if 'conn' in locals() and conn.open:
        conn.close()

# Final URL that SQLAlchemy must consume (includes mysql+pymysql!)
DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
