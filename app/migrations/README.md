# Database Migrations

このディレクトリはAlembicを使用したデータベーススキーマのバージョン管理を行います。

## 概要

- **マイグレーションツール**: Alembic
- **データベース**: PostgreSQL

## 基本的な使い方

### マイグレーション状態の確認

```bash
# 現在のマイグレーションバージョンを確認
alembic current

# マイグレーション履歴を表示
alembic history --verbose
```

### 新しいマイグレーションの作成

モデル（`src/models/`）を変更した後:

```bash
# モデルの変更を自動検出してマイグレーションファイルを生成
alembic revision --autogenerate -m "変更の説明"

# 例: 新しいカラムを追加した場合
alembic revision --autogenerate -m "Add volume_profile column to daily_prices"
```

**注意**:
- 自動生成されたマイグレーションファイルは必ず確認してください
- Enumの変更やインデックスの削除など、一部の操作は手動で調整が必要な場合があります

### データベースの更新

```bash
# 最新バージョンまでマイグレーション実行
alembic upgrade head

# 特定のバージョンまで更新
alembic upgrade <revision_id>

# 1つ先のバージョンに更新
alembic upgrade +1
```

### データベースのロールバック

```bash
# 1つ前のバージョンに戻す
alembic downgrade -1

# 特定のバージョンに戻す
alembic downgrade <revision_id>

# 全てのマイグレーションを取り消す（全テーブル削除）
alembic downgrade base
```

## プロジェクト固有の情報

### 現在のデータベーステーブル

1. **alembic_version** - マイグレーション管理テーブル（自動作成）

### データベース設定

データベース接続設定は`.env`ファイルで管理されています:

設定を変更した後は、Alembicが自動的に新しい接続先を使用します。

## データベースの完全な再構築

既存のテーブルを全て削除して再作成する場合:

```bash
# 全テーブルを削除
alembic downgrade base

# 全テーブルを再作成
alembic upgrade head
```

**警告**: `downgrade base`は全データが削除されます。本番環境では絶対に実行しないでください。

## トラブルシューティング

### エラー: Target database is not up to date

```bash
# 現在のバージョンを確認
alembic current

# データベースを最新状態に更新してから、新しいマイグレーションを作成
alembic upgrade head
alembic revision --autogenerate -m "新しい変更"
```

### エラー: relation "xxx" does not exist

マイグレーションファイルのテーブル作成順序が間違っている可能性があります。
外部キー制約のあるテーブルは、参照先テーブルの後に作成される必要があります。

```bash
# マイグレーションをやり直す
alembic downgrade base
alembic upgrade head
```

## ベストプラクティス

1. **マイグレーション前にバックアップを取る**
   - 本番環境では特に重要です

2. **マイグレーションファイルを確認する**
   - `--autogenerate`は完璧ではありません
   - 生成されたファイルを必ずレビューしてください

3. **downgradeの実装を確認する**
   - 各マイグレーションはロールバック可能であるべきです

4. **マイグレーションは小さく保つ**
   - 1つのマイグレーションで1つの変更を行う
   - デバッグやロールバックが容易になります

5. **本番環境での注意点**
   - マイグレーション実行前にメンテナンスモードに切り替える
   - 大量データがある場合、時間がかかる可能性があります
   - インデックス作成は特に時間がかかります

## 参考リンク

- [Alembic公式ドキュメント](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- プロジェクトのモデル定義: `src/models/`
