import io
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

SAMPLE_CSV = b"name,sales,profit\nAlice,1000,200\nBob,2000,400\nCarol,1500,300"

def test_parse_csv():
    from analyzer import parse_file
    df = parse_file(SAMPLE_CSV, 'data.csv')
    assert len(df) == 3
    assert list(df.columns) == ['name', 'sales', 'profit']

def test_parse_invalid_format():
    from analyzer import parse_file
    with pytest.raises(ValueError, match="非対応のファイル形式"):
        parse_file(b"data", 'data.txt')

def test_parse_xlsx():
    from analyzer import parse_file
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['name', 'sales'])
    ws.append(['Alice', 1000])
    buf = io.BytesIO()
    wb.save(buf)
    df = parse_file(buf.getvalue(), 'data.xlsx')
    assert len(df) == 1
    assert list(df.columns) == ['name', 'sales']

def test_parse_csv_uppercase_extension():
    from analyzer import parse_file
    df = parse_file(SAMPLE_CSV, 'data.CSV')
    assert len(df) == 3

SAMPLE_CSV_MISSING = b"name,sales,profit\nAlice,1000,\nBob,,400"

def test_generate_stats_basic():
    from analyzer import parse_file, generate_stats
    df = parse_file(SAMPLE_CSV, 'data.csv')
    stats = generate_stats(df)
    assert stats['rows'] == 3
    assert stats['cols'] == 3
    assert stats['missing_values'] == 0
    assert 'sales' in stats['numeric_summary']
    assert stats['numeric_summary']['sales']['sum'] == 4500.0
    assert stats['numeric_summary']['sales']['mean'] == 1500.0
    assert stats['numeric_summary']['sales']['max'] == 2000.0
    assert stats['numeric_summary']['sales']['min'] == 1000.0

def test_generate_stats_missing_values():
    from analyzer import parse_file, generate_stats
    df = parse_file(SAMPLE_CSV_MISSING, 'data.csv')
    stats = generate_stats(df)
    assert stats['missing_values'] == 2

def test_generate_chart_data_with_numeric():
    from analyzer import parse_file, generate_chart_data
    df = parse_file(SAMPLE_CSV, 'data.csv')
    chart = generate_chart_data(df)
    assert chart is not None
    assert chart['labels'] == ['平均', '最大', '最小']
    assert len(chart['datasets']) == 2  # sales and profit

def test_generate_chart_data_no_numeric():
    from analyzer import generate_chart_data
    df = pd.DataFrame({'name': ['Alice', 'Bob'], 'city': ['Tokyo', 'Osaka']})
    chart = generate_chart_data(df)
    assert chart is None

def test_generate_chart_data_max_3_columns():
    from analyzer import generate_chart_data
    df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3], 'd': [4]})
    chart = generate_chart_data(df)
    assert len(chart['datasets']) == 3

def test_analyze_with_ai():
    from analyzer import parse_file, generate_stats, analyze_with_ai
    df = parse_file(SAMPLE_CSV, 'data.csv')
    stats = generate_stats(df)

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "テスト分析結果"

    with patch('analyzer.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = analyze_with_ai(df, stats, 'test-key')

    assert result == "テスト分析結果"
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs['model'] == 'gpt-4o-mini'

def test_analyze_full():
    from analyzer import analyze

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "完全な分析結果"

    with patch('analyzer.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = analyze(SAMPLE_CSV, 'data.csv', 'test-key')

    assert result['success'] is True
    assert result['summary'] == "完全な分析結果"
    assert result['stats']['rows'] == 3
    assert result['chart_data'] is not None
