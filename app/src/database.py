"""Database configuration - backward compatibility alias.

This module re-exports from infrastructure.persistence.database.
New code should import directly from src.infrastructure.persistence.database.
"""

from src.infrastructure.persistence.database import Base

__all__ = ["Base"]
