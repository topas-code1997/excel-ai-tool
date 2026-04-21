from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from analyzer import analyze
from slack_notifier import send_slack_message

load_dotenv()

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

    filename = file.filename
    try:
        result = analyze(file.read(), filename, api_key)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'エラーが発生しました: {str(e)}'})

    slack_notify = request.form.get('slack_notify', '').lower() == 'true'
    if slack_notify:
        slack_channel = request.form.get('slack_channel', '').strip()
        if not slack_channel:
            result['slack_error'] = 'チャンネル名を入力してください。'
        else:
            try:
                send_slack_message(
                    channel=slack_channel,
                    filename=filename,
                    summary=result['summary'],
                    stats=result['stats'],
                )
                result['slack_sent'] = True
            except ValueError as e:
                result['slack_error'] = str(e)
            except Exception as e:
                result['slack_error'] = f'Slack送信エラー: {str(e)}'

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
