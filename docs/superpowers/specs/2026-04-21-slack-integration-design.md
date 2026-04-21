# Slack連携機能 設計ドキュメント

**日付:** 2026-04-21  
**対象プロジェクト:** Excel/CSV AI アナライザー

---

## 概要

分析完了後に結果をSlackの指定チャンネルへ自動通知する機能を追加する。通知はオプトイン（チェックボックス）方式で、チャンネル名はUIから入力する。

---

## アーキテクチャ

### 新規ファイル
- `slack_notifier.py` — Slack送信ロジックを独立モジュールとして実装

### 変更ファイル
- `app.py` — `/analyze` エンドポイントにSlack送信処理を追加
- `templates/index.html` — チェックボックスとチャンネル入力欄を追加
- `requirements.txt` — `slack-sdk` を追加

### 変更しないファイル
- `analyzer.py` — 分析ロジックはそのまま

---

## データフロー

1. ユーザーが「Slackに通知する」チェックボックスをON → チャンネル名入力欄が表示される
2. 分析ボタン押下 → FormData に `slack_notify=true`, `slack_channel=#xxx` を追加して `/analyze` へ送信
3. バックエンドで `analyze()` を実行し分析完了
4. `slack_notify=true` の場合、`send_slack_message()` を呼び出す
5. レスポンスに `slack_sent: bool` と `slack_error: str | null` を含める
6. フロントエンドで `slack_error` があれば黄色い警告バナーを表示（分析結果は正常表示）

---

## Slackメッセージ形式

```
📊 Excel/CSV AI 分析結果
ファイル: {filename}

【データ概要】
• 行数: {rows}
• 列数: {cols}
• 欠損値: {missing_values}

【AI分析サマリー】
{summary}
```

- `slack-sdk` の `WebClient.chat_postMessage()` でプレーンテキスト送信
- Block Kit は使わない（シンプルさ優先）
- ファイル名はバックエンドで `request.files['file'].filename` から取得

---

## 設定

- `SLACK_BOT_TOKEN` は `.env` ファイルから `python-dotenv` で読み込む
- `.env` は既に存在し `SLACK_BOT_TOKEN` が設定済み

---

## エラーハンドリング

### Slack送信失敗時
- `send_slack_message()` は例外をそのまま上位に投げる
- `app.py` で `try/except` し、`slack_error` フィールドをレスポンスに含める
- 分析結果（`success: true`）は常に返す — Slack失敗で分析結果が消えない

### バリデーション
| ケース | 挙動 |
|--------|------|
| `slack_notify=true` かつ `slack_channel` が空 | `slack_error: "チャンネル名を入力してください"` |
| `SLACK_BOT_TOKEN` が未設定 | 送信時に検出し `slack_error` で返す |
| トークン無効 / チャンネル不存在 | `slack-sdk` の例外を捕捉し `slack_error` で返す |

---

## UI変更

- 既存フォームの下部にセクションを追加
- 「Slackに通知する」チェックボックス（デフォルト: OFF）
- チェック時のみチャンネル入力欄を表示（例: `#general`）
- 分析後、`slack_error` があれば黄色い警告バナーを結果の上部に表示
- `slack_sent: true` の場合は緑の成功メッセージを表示

---

## 依存関係

```
slack-sdk       # Slack WebClient
python-dotenv   # .envファイル読み込み（requirements.txtに追記が必要）
```
