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
