"""Universe repository port (interface)."""

from datetime import date
from typing import TYPE_CHECKING, Dict, List, Protocol

import pandas as pd

if TYPE_CHECKING:
    from src.infrastructure.persistence.models import Universe


class UniverseRepository(Protocol):
    """
    Universeリポジトリのインターフェース.

    ポート&アダプターパターンにおけるポート（抽象）として機能する。
    具体的な実装はinfrastructure層で提供される。
    """

    def get_by_id(self, universe_id: int) -> "Universe | None":
        """IDでUniverseを取得する."""
        ...

    def get_by_name(self, name: str) -> "Universe | None":
        """名前でUniverseを取得する."""
        ...

    def get_latest(self) -> "Universe | None":
        """最新のUniverseを取得する."""
        ...

    def get_symbols(self, universe_id: int) -> List[str]:
        """Universe内の全シンボルを取得する."""
        ...

    def get_universe_prices(
        self,
        universe_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, pd.DataFrame]:
        """
        Universe内の全銘柄の価格データを取得する.

        Args:
            universe_id: UniverseのID
            start_date: 取得開始日
            end_date: 取得終了日

        Returns:
            銘柄別の価格DataFrame {symbol: DataFrame}
        """
        ...
