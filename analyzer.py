import io
import pandas as pd
from openai import OpenAI


def parse_file(file_bytes, filename):
    lower = filename.lower()
    if lower.endswith('.csv'):
        return pd.read_csv(io.BytesIO(file_bytes))
    elif lower.endswith('.xlsx'):
        return pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError(f"非対応のファイル形式です: {filename}")
