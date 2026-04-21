import io
import pytest
import pandas as pd

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
