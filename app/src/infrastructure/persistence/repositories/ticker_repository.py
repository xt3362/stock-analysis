"""PostgreSQL implementation of TickerRepository."""

from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import Ticker


class PostgresTickerRepository:
    """
    PostgreSQL実装 - TickerRepository Protocolに構造的に適合.

    SQLAlchemyセッションを使用してTickerエンティティの永続化を行う。
    """

    def __init__(self, session: Session) -> None:
        """
        リポジトリを初期化する.

        Args:
            session: SQLAlchemyセッション
        """
        self._session = session

    def get_by_id(self, ticker_id: int) -> Ticker | None:
        """IDでTickerを取得する."""
        return self._session.get(Ticker, ticker_id)

    def get_by_symbol(self, symbol: str) -> Ticker | None:
        """シンボルでTickerを取得する."""
        return self._session.query(Ticker).filter(Ticker.symbol == symbol).first()

    def get_all(self) -> list[Ticker]:
        """全てのTickerを取得する."""
        return list(self._session.query(Ticker).all())

    def save(self, ticker: Ticker) -> Ticker:
        """
        Tickerを保存する（新規作成または更新）.

        Args:
            ticker: 保存するTickerエンティティ

        Returns:
            保存されたTickerエンティティ（IDが設定済み）
        """
        self._session.add(ticker)
        self._session.flush()
        return ticker

    def delete(self, ticker_id: int) -> bool:
        """
        TickerをIDで削除する.

        Args:
            ticker_id: 削除するTickerのID

        Returns:
            削除成功時はTrue、対象が存在しない場合はFalse
        """
        ticker = self.get_by_id(ticker_id)
        if ticker is None:
            return False
        self._session.delete(ticker)
        return True
