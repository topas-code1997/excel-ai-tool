from flask import Flask, request, jsonify, render_template
from analyzer import analyze

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_file():
    file = request.files.get('file')
    api_key = request.form.get('api_key', '').strip()

    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'ファイルが選択されていません。'})

    if not api_key:
        return jsonify({'success': False, 'error': 'APIキーが入力されていません。'})

    try:
        result = analyze(file.read(), file.filename, api_key)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'エラーが発生しました: {str(e)}'})


if __name__ == '__main__':
    app.run(debug=True)
