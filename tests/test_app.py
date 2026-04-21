import io
import json
import pytest
from unittest.mock import patch

SAMPLE_CSV = b"name,sales,profit\nAlice,1000,200\nBob,2000,400"

@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_index(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'<html' in resp.data.lower()

def test_analyze_no_file(client):
    resp = client.post('/analyze', data={'api_key': 'test-key'})
    data = json.loads(resp.data)
    assert data['success'] is False
    assert 'ファイル' in data['error']

def test_analyze_no_api_key(client):
    resp = client.post('/analyze', data={
        'file': (io.BytesIO(SAMPLE_CSV), 'data.csv'),
    }, content_type='multipart/form-data')
    data = json.loads(resp.data)
    assert data['success'] is False
    assert 'APIキー' in data['error']

def test_analyze_success(client):
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
        }, content_type='multipart/form-data')
    data = json.loads(resp.data)
    assert data['success'] is True
    assert data['summary'] == 'テスト分析'

def test_analyze_invalid_format(client):
    resp = client.post('/analyze', data={
        'file': (io.BytesIO(b'data'), 'data.txt'),
        'api_key': 'test-key',
    }, content_type='multipart/form-data')
    data = json.loads(resp.data)
    assert data['success'] is False
    assert '非対応' in data['error']


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
