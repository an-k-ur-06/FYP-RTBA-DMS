import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from backend.app.core.config import settings
from backend.app.core.db import sync_engine, Base
import backend.app.models.entities # Ensures all models are registered with Base

def ensure_database_exists():
    print(f"Connecting to PostgreSQL at {settings.DB_HOST}:{settings.DB_PORT} as {settings.DB_USER}...")
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            dbname="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (settings.DB_NAME,))
        exists = cursor.fetchone()
        if not exists:
            print(f"Database '{settings.DB_NAME}' does not exist. Creating now...")
            cursor.execute(f'CREATE DATABASE "{settings.DB_NAME}";')
            print(f"Database '{settings.DB_NAME}' created successfully.")
        else:
            print(f"Database '{settings.DB_NAME}' already exists.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        sys.exit(1)

def create_tables():
    print("Creating all database tables using SQLAlchemy ORM...")
    try:
        Base.metadata.create_all(bind=sync_engine)
        print("All database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ensure_database_exists()
    create_tables()
