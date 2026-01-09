"""Application configuration.

Provides database connection settings from environment variables.
"""

import os

from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


class Config:
    """Application configuration class."""

    @staticmethod
    def get_database_url() -> str:
        """
        環境変数からデータベースURLを構築する.

        Returns:
            PostgreSQLデータベースURL
        """
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "swing_trading")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
