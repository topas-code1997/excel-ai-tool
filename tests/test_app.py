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
