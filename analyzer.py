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


def analyze_with_ai(df, stats, api_key):
    client = OpenAI(api_key=api_key)

    sample = df.head(5).to_string()
    numeric_text = '\n'.join(
        f"  {col}: 平均={v['mean']}, 最大={v['max']}, 最小={v['min']}, 合計={v['sum']}"
        for col, v in stats['numeric_summary'].items()
    )

    prompt = f"""以下のデータを日本語で分析してください。

【データサンプル（先頭5行）】
{sample}

【統計情報】
行数: {stats['rows']}
列数: {stats['cols']}
欠損値: {stats['missing_values']}
数値列の統計:
{numeric_text if numeric_text else '  数値列なし'}

以下の点について簡潔にまとめてください：
1. データの概要
2. 注目すべき傾向や特徴
3. 気になる点や改善が必要な箇所（あれば）"""

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=1000,
    )

    return response.choices[0].message.content


def analyze(file_bytes, filename, api_key):
    df = parse_file(file_bytes, filename)
    stats = generate_stats(df)
    chart_data = generate_chart_data(df)
    summary = analyze_with_ai(df, stats, api_key)
    return {
        'success': True,
        'summary': summary,
        'stats': stats,
        'chart_data': chart_data,
    }
