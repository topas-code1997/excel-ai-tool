# Slack連携機能 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 分析完了後にオプトインでSlackの指定チャンネルへ結果を通知できるようにする

**Architecture:** 独立モジュール `slack_notifier.py` にSlack送信ロジックを切り出し、`app.py` の `/analyze` エンドポイントから呼び出す。フロントエンドにチェックボックスとチャンネル入力欄を追加し、分析後にSlack送信の成功/失敗をUIに表示する。

**Tech Stack:** slack-sdk, python-dotenv, Flask（既存）, vanilla JS（既存）

---

## ファイル構成

| ファイル | 変更種別 | 役割 |
|----------|----------|------|
| `slack_notifier.py` | 新規作成 | Slack送信ロジック（`send_slack_message` 関数） |
| `tests/test_slack_notifier.py` | 新規作成 | `slack_notifier.py` のユニットテスト |
| `app.py` | 変更 | `/analyze` にSlack通知処理を追加、dotenv読み込みを追加 |
| `tests/test_app.py` | 変更 | Slack統合テストを追加 |
| `templates/index.html` | 変更 | チェックボックス・チャンネル入力欄・結果バナーを追加 |
| `requirements.txt` | 変更 | `slack-sdk`、`python-dotenv` を追記 |

---

## Task 1: 依存関係を追加する

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: requirements.txt に依存関係を追記する**

`requirements.txt` を以下の内容に書き換える:

```
flask
openai
pandas
openpyxl
pytest
slack-sdk
python-dotenv
```

- [ ] **Step 2: パッケージをインストールする**

```bash
pip install slack-sdk python-dotenv
```

Expected: `Successfully installed slack-sdk-...` が表示される

- [ ] **Step 3: インストールを確認する**

```bash
python -c "import slack_sdk; import dotenv; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: コミット**

```bash
git add requirements.txt
git commit -m "chore: add slack-sdk and python-dotenv dependencies"
```

---

## Task 2: `slack_notifier.py` をTDDで実装する

**Files:**
- Create: `slack_notifier.py`
- Create: `tests/test_slack_notifier.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_slack_notifier.py` を作成:

```python
import pytest
from unittest.mock import patch, MagicMock

STATS = {'rows': 100, 'cols': 5, 'missing_values': 2, 'numeric_summary': {}}


def test_send_slack_message_success():
    from slack_notifier import send_slack_message
    with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test'}):
        with patch('slack_notifier.WebClient') as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            send_slack_message('#general', 'data.csv', 'テスト分析', STATS)
    mock_client.chat_postMessage.assert_called_once()
    kwargs = mock_client.chat_postMessage.call_args[1]
    assert kwargs['channel'] == '#general'
    assert 'data.csv' in kwargs['text']
    assert 'テスト分析' in kwargs['text']
    assert '100' in kwargs['text']


def test_send_slack_message_no_token(monkeypatch):
    from slack_notifier import send_slack_message
    monkeypatch.delenv('SLACK_BOT_TOKEN', raising=False)
    with pytest.raises(ValueError, match='SLACK_BOT_TOKEN'):
        send_slack_message('#general', 'data.csv', 'サマリー', STATS)


def test_send_slack_message_api_error():
    from slack_notifier import send_slack_message
    from slack_sdk.errors import SlackApiError
    with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test'}):
        with patch('slack_notifier.WebClient') as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.chat_postMessage.side_effect = SlackApiError(
                message='channel_not_found',
                response={'error': 'channel_not_found'},
            )
            with pytest.raises(SlackApiError):
                send_slack_message('#invalid', 'data.csv', 'サマリー', STATS)
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_slack_notifier.py -v
```

Expected: `ImportError: No module named 'slack_notifier'` または `ModuleNotFoundError`

- [ ] **Step 3: `slack_notifier.py` を実装する**

```python
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def send_slack_message(channel: str, filename: str, summary: str, stats: dict) -> None:
    token = os.environ.get('SLACK_BOT_TOKEN')
    if not token:
        raise ValueError('SLACK_BOT_TOKENが設定されていません。')

    client = WebClient(token=token)

    rows = stats.get('rows', '-')
    cols = stats.get('cols', '-')
    missing = stats.get('missing_values', '-')

    text = (
        f"📊 Excel/CSV AI 分析結果\n"
        f"ファイル: {filename}\n\n"
        f"【データ概要】\n"
        f"• 行数: {rows:,}\n"
        f"• 列数: {cols:,}\n"
        f"• 欠損値: {missing:,}\n\n"
        f"【AI分析サマリー】\n"
        f"{summary}"
    )

    client.chat_postMessage(channel=channel, text=text)
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest tests/test_slack_notifier.py -v
```

Expected:
```
tests/test_slack_notifier.py::test_send_slack_message_success PASSED
tests/test_slack_notifier.py::test_send_slack_message_no_token PASSED
tests/test_slack_notifier.py::test_send_slack_message_api_error PASSED
3 passed
```

- [ ] **Step 5: 既存テストが壊れていないことを確認する**

```bash
pytest tests/ -v
```

Expected: 既存テスト含めて全て PASSED

- [ ] **Step 6: コミット**

```bash
git add slack_notifier.py tests/test_slack_notifier.py
git commit -m "feat: add slack_notifier module with send_slack_message"
```

---

## Task 3: `app.py` にSlack通知を統合する

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app.py`

- [ ] **Step 1: 失敗するテストを `tests/test_app.py` に追加する**

`tests/test_app.py` の末尾に以下を追記する:

```python
def test_analyze_without_slack_notify(client):
    mock_result = {
        'success': True,
        'summary': 'テスト分析',
        'stats': {'rows': 2, 'cols': 3, 'missing_values': 0, 'numeric_summary': {}},
        'chart_data': None,
    }
    with patch('app.analyze', return_value=mock_result):
        with patch('app.send_slack_message') as mock_slack:
            resp = client.post('/analyze', data={
                'file': (io.BytesIO(SAMPLE_CSV), 'data.csv'),
                'api_key': 'test-key',
            }, content_type='multipart/form-data')
    data = json.loads(resp.data)
    assert data['success'] is True
    mock_slack.assert_not_called()


def test_analyze_with_slack_notify(client):
    mock_result = {
        'success': True,
        'summary': 'テスト分析',
        'stats': {'rows': 2, 'cols': 3, 'missing_values': 0, 'numeric_summary': {}},
        'chart_data': None,
    }
    with patch('app.analyze', return_value=mock_result):
        with patch('app.send_slack_message') as mock_slack:
            resp = client.post('/analyze', data={
                'file': (io.BytesIO(SAMPLE_CSV), 'data.csv'),
                'api_key': 'test-key',
                'slack_notify': 'true',
                'slack_channel': '#general',
            }, content_type='multipart/form-data')
    data = json.loads(resp.data)
    assert data['success'] is True
    assert data.get('slack_sent') is True
    mock_slack.assert_called_once_with(
        channel='#general',
        filename='data.csv',
        summary='テスト分析',
        stats={'rows': 2, 'cols': 3, 'missing_values': 0, 'numeric_summary': {}},
    )


def test_analyze_with_slack_empty_channel(client):
    mock_result = {
        'success': True,
        'summary': 'テスト分析',
        'stats': {'rows': 2, 'cols': 3, 'missing_values': 0, 'numeric_summary': {}},
        'chart_data': None,
    }
    with patch('app.analyze', return_value=mock_result):
        resp = client.post('/analyze', data={
            'file': (io.BytesIO(SAMPLE_CSV), 'data.csv'),
            'api_key': 'test-key',
            'slack_notify': 'true',
            'slack_channel': '',
        }, content_type='multipart/form-data')
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'チャンネル名' in data['slack_error']


def test_analyze_with_slack_api_error(client):
    mock_result = {
        'success': True,
        'summary': 'テスト分析',
        'stats': {'rows': 2, 'cols': 3, 'missing_values': 0, 'numeric_summary': {}},
        'chart_data': None,
    }
    with patch('app.analyze', return_value=mock_result):
        with patch('app.send_slack_message', side_effect=Exception('channel_not_found')):
            resp = client.post('/analyze', data={
                'file': (io.BytesIO(SAMPLE_CSV), 'data.csv'),
                'api_key': 'test-key',
                'slack_notify': 'true',
                'slack_channel': '#invalid',
            }, content_type='multipart/form-data')
    data = json.loads(resp.data)
    assert data['success'] is True
    assert 'slack_error' in data
    assert 'channel_not_found' in data['slack_error']
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_app.py::test_analyze_without_slack_notify tests/test_app.py::test_analyze_with_slack_notify tests/test_app.py::test_analyze_with_slack_empty_channel tests/test_app.py::test_analyze_with_slack_api_error -v
```

Expected: `ImportError` または `FAILED`（`send_slack_message` が未インポート）

- [ ] **Step 3: `app.py` を更新する**

`app.py` を以下の内容に書き換える:

```python
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from analyzer import analyze
from slack_notifier import send_slack_message

load_dotenv()

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_file():
    file = request.files.get('file')
    api_key = request.form.get('api_key', '').strip()

    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'ファイルが選択されていません。'})

    if not api_key:
        return jsonify({'success': False, 'error': 'APIキーが入力されていません。'})

    filename = file.filename
    try:
        result = analyze(file.read(), filename, api_key)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'エラーが発生しました: {str(e)}'})

    slack_notify = request.form.get('slack_notify', '').lower() == 'true'
    if slack_notify:
        slack_channel = request.form.get('slack_channel', '').strip()
        if not slack_channel:
            result['slack_error'] = 'チャンネル名を入力してください。'
        else:
            try:
                send_slack_message(
                    channel=slack_channel,
                    filename=filename,
                    summary=result['summary'],
                    stats=result['stats'],
                )
                result['slack_sent'] = True
            except Exception as e:
                result['slack_error'] = f'Slack送信エラー: {str(e)}'

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
```

- [ ] **Step 4: 追加したテストが通ることを確認する**

```bash
pytest tests/test_app.py -v
```

Expected: 全テスト PASSED（既存テスト含む）

- [ ] **Step 5: 全テストを実行する**

```bash
pytest tests/ -v
```

Expected: 全テスト PASSED

- [ ] **Step 6: コミット**

```bash
git add app.py tests/test_app.py
git commit -m "feat: integrate Slack notification into /analyze endpoint"
```

---

## Task 4: フロントエンドにSlack連携UIを追加する

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: Slack設定セクションをHTMLに追加する**

`templates/index.html` の `<button id="analyze-btn"...` の直前に以下を追加する（`<div class="form-group">` 末尾の後、ボタンの前）:

```html
            <div class="form-group slack-section">
                <label class="checkbox-label">
                    <input type="checkbox" id="slack-notify">
                    Slackに通知する
                </label>
                <div id="slack-channel-group" class="hidden">
                    <label for="slack-channel">通知先チャンネル</label>
                    <input type="text" id="slack-channel" placeholder="#general">
                </div>
            </div>
```

- [ ] **Step 2: Slack結果バナー用HTMLを追加する**

`<div id="results" class="hidden">` の直後（`<div class="card">` の前）に以下を追加する:

```html
            <div id="slack-success" class="slack-banner slack-success hidden">✅ Slackに通知しました</div>
            <div id="slack-warning" class="slack-banner slack-warning hidden"></div>
```

- [ ] **Step 3: CSSを `static/style.css` に追加する**

`static/style.css` の末尾に以下を追記する:

```css
.checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    color: #e2e8f0;
    font-size: 0.95rem;
}

.checkbox-label input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: #6366f1;
    cursor: pointer;
}

.slack-section {
    margin-top: 8px;
}

#slack-channel-group {
    margin-top: 10px;
}

#slack-channel-group label {
    display: block;
    margin-bottom: 6px;
    color: #94a3b8;
    font-size: 0.875rem;
}

#slack-channel-group input {
    width: 100%;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
    color: #e2e8f0;
    font-size: 0.95rem;
    box-sizing: border-box;
}

.slack-banner {
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 12px;
    font-size: 0.9rem;
}

.slack-success {
    background: #14532d;
    color: #86efac;
    border: 1px solid #16a34a;
}

.slack-warning {
    background: #713f12;
    color: #fde68a;
    border: 1px solid #d97706;
}
```

- [ ] **Step 4: JavaScriptにSlack関連ロジックを追加する**

`templates/index.html` のスクリプト内で、既存の `const errorMsg = ...` 宣言の後（`let chartInstance = null;` の前）に以下を追加する:

```javascript
        const slackNotifyCheckbox = document.getElementById('slack-notify');
        const slackChannelGroup = document.getElementById('slack-channel-group');
        const slackChannelInput = document.getElementById('slack-channel');
        const slackSuccess = document.getElementById('slack-success');
        const slackWarning = document.getElementById('slack-warning');

        slackNotifyCheckbox.addEventListener('change', () => {
            slackChannelGroup.classList.toggle('hidden', !slackNotifyCheckbox.checked);
        });
```

- [ ] **Step 5: FormData送信にSlackフィールドを追加する**

`analyzeBtn.addEventListener('click', async () => {` 内の `formData.append('api_key', ...)` の後に以下を追加する:

```javascript
            if (slackNotifyCheckbox.checked) {
                formData.append('slack_notify', 'true');
                formData.append('slack_channel', slackChannelInput.value.trim());
            }
```

- [ ] **Step 6: 分析結果表示にSlackバナーを追加する**

`renderResults` 関数の先頭（`document.getElementById('summary-text')...` の前）に以下を追加する:

```javascript
            slackSuccess.classList.add('hidden');
            slackWarning.classList.add('hidden');
            if (data.slack_sent) {
                slackSuccess.classList.remove('hidden');
            }
            if (data.slack_error) {
                slackWarning.textContent = '⚠️ ' + data.slack_error;
                slackWarning.classList.remove('hidden');
            }
```

- [ ] **Step 7: 手動でUIを確認する**

```bash
python app.py
```

ブラウザで `http://localhost:5000` を開き、以下を確認する:
1. 「Slackに通知する」チェックボックスが表示される
2. チェックを入れるとチャンネル入力欄が表示される
3. チェックを外すと入力欄が消える
4. 分析実行後、Slack送信成功なら緑バナー、失敗なら黄バナーが表示される

- [ ] **Step 8: コミット**

```bash
git add templates/index.html static/style.css
git commit -m "feat: add Slack notification UI with checkbox and channel input"
```

---

## Task 5: 全体確認とまとめ

- [ ] **Step 1: 全テストを実行する**

```bash
pytest tests/ -v
```

Expected: 全テスト PASSED（`test_slack_notifier.py` 3件 + `test_app.py` 8件 + `test_analyzer.py` 9件）

- [ ] **Step 2: サーバーを起動して動作確認する**

```bash
python app.py
```

`http://localhost:5000` で以下のシナリオをテストする:
- チェックボックスOFF → 通常通り分析できる（Slack通知なし）
- チェックボックスON・チャンネル空 → 黄色バナー「チャンネル名を入力してください」
- チェックボックスON・無効チャンネル → 黄色バナーにエラー内容
- チェックボックスON・有効チャンネル → 緑バナー「Slackに通知しました」

- [ ] **Step 3: 最終コミット**

```bash
git add -A
git commit -m "feat: complete Slack integration for Excel AI analyzer"
```
