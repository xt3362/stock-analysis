"""Ticker repository port (interface)."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.infrastructure.persistence.models import Ticker


class TickerRepository(Protocol):
    """
    Tickerリポジトリのインターフェース.

    ポート&アダプターパターンにおけるポート（抽象）として機能する。
    具体的な実装はinframstructure層で提供される。
    """

    def get_by_id(self, ticker_id: int) -> "Ticker | None":
        """IDでTickerを取得する."""
        ...

    def get_by_symbol(self, symbol: str) -> "Ticker | None":
        """シンボルでTickerを取得する."""
        ...

    def get_all(self) -> list["Ticker"]:
        """全てのTickerを取得する."""
        ...

    def save(self, ticker: "Ticker") -> "Ticker":
        """Tickerを保存する（新規作成または更新）."""
        ...

    def delete(self, ticker_id: int) -> bool:
        """TickerをIDで削除する. 削除成功時はTrue."""
        ...
