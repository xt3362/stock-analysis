# テスト規約

## 実行コマンド

```bash
make test        # テスト実行
make typecheck   # 型チェック
make format      # 
make lint        # 
```

## ディレクトリ構造

```
tests/
├── conftest.py                    # 共通フィクスチャ
└── infrastructure/persistence/repositories/
    └── test_*.py                  # リポジトリテスト
```

`src/` の構造をミラーする。

## フィクスチャ（conftest.py）

```python
@pytest.fixture
def engine() -> Engine:
    """インメモリSQLite"""
    return create_engine("sqlite:///:memory:")

@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    """テスト用DBセッション"""
    Base.metadata.create_all(engine)
    ...
```

## テストファイル命名

- ファイル: `test_<対象モジュール>.py`
- クラス: `Test<対象クラス>`
- メソッド: `test_<動作>` または `test_<動作>_<条件>`

## SQLAlchemy型抑制

テストファイル先頭に追加:

```python
# pyright: reportArgumentType=false
# pyright: reportGeneralTypeIssues=false
```

## 非同期テスト

`asyncio` ではなく `anyio` を使用。
