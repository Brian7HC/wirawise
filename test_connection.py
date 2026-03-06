import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": "postgres",
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

print("=" * 50)
print("Testing PostgreSQL Connection")
print("=" * 50)
print(f"Host:     {DB_CONFIG['host']}")
print(f"Port:     {DB_CONFIG['port']}")
print(f"User:     {DB_CONFIG['user']}")
print(f"Password: {'***' if DB_CONFIG['password'] else '(empty)'}")
print()

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Connection successful!")

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"\nPostgreSQL version:")
    print(f"  {version[0]}")

    cursor.close()
    conn.close()
    print("\n✅ All checks passed!")

except Exception as e:
    print("❌ Connection failed!")
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check PostgreSQL is running: pg_isready")
    print("2. Verify credentials in .env file")
    print("3. Check pg_hba.conf has 'md5' authentication")

print("=" * 50)
