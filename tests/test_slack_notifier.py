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
