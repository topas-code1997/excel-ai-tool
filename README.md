# Excel/CSV AI アナライザー

Excel・CSVファイルをアップロードすると、AIが自動でデータを分析・要約するWebアプリ。

## セットアップ

pip install -r requirements.txt
python app.py

ブラウザで http://localhost:5000 を開く。

## 使い方

1. OpenAI APIキーを入力
2. .csv または .xlsx ファイルを選択
3. 「分析する」をクリック

## テスト実行

pytest tests/ -v
