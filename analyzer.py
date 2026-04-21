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


def generate_stats(df):
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    numeric_summary = {}
    for col in numeric_cols:
        numeric_summary[col] = {
            'mean': round(float(df[col].mean()), 2),
            'max': round(float(df[col].max()), 2),
            'min': round(float(df[col].min()), 2),
            'sum': round(float(df[col].sum()), 2),
        }
    return {
        'rows': len(df),
        'cols': len(df.columns),
        'missing_values': int(df.isnull().sum().sum()),
        'numeric_summary': numeric_summary,
    }


def generate_chart_data(df):
    numeric_cols = df.select_dtypes(include='number').columns.tolist()[:3]
    if not numeric_cols:
        return None

    colors = [
        'rgba(99, 102, 241, 0.8)',
        'rgba(244, 63, 94, 0.8)',
        'rgba(34, 197, 94, 0.8)',
    ]

    datasets = []
    for i, col in enumerate(numeric_cols):
        datasets.append({
            'label': col,
            'data': [
                round(float(df[col].mean()), 2),
                round(float(df[col].max()), 2),
                round(float(df[col].min()), 2),
            ],
            'backgroundColor': colors[i],
        })

    return {
        'labels': ['平均', '最大', '最小'],
        'datasets': datasets,
    }
