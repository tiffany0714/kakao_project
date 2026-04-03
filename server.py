import json
import os
import subprocess
import threading
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import anthropic

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

API_KEY = "YOUR_API_KEY_HERE"
client = anthropic.Anthropic(api_key=API_KEY)

DATA_PATH = os.path.join('frontend', 'data', 'current_data.json')

update_status = {"running": False, "logs": []}

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/data/current_data.json')
def get_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/update', methods=['POST'])
def update():
    if update_status["running"]:
        return jsonify({"message": "이미 업데이트 중이에요!"}), 400

    def run_update():
        update_status["running"] = True
        update_status["logs"] = []
        try:
            proc = subprocess.Popen(
                ["python", "update_data.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            for line in proc.stdout:
                update_status["logs"].append(line.strip())
            proc.wait()
            update_status["logs"].append("✅ 업데이트 완료!")
        except Exception as e:
            update_status["logs"].append(f"❌ 오류: {e}")
        finally:
            update_status["running"] = False

    threading.Thread(target=run_update).start()
    return jsonify({"message": "업데이트 시작!"})

@app.route('/update/status')
def update_status_route():
    return jsonify({
        "running": update_status["running"],
        "logs": update_status["logs"]
    })

@app.route('/strategy', methods=['POST'])
def generate_strategy():
    body = request.json
    my_product = body.get('my_product', {})
    top_products = body.get('top_products', [])
    top_text = '\n'.join([
        f"{i+1}위: {p['name']} (계절: {p.get('season','?')})"
        for i, p in enumerate(top_products[:20])
    ])
    prompt = (
        "카카오 선물하기 유아동 카테고리 랭킹 분석을 해줘.\n"
        "[우리 상품]\n"
        f"- 상품명: {my_product.get('name')}\n"
        f"- 현재 순위: {my_product.get('rank')}위\n"
        f"- 계절: {my_product.get('season')}\n"
        "[상위 1~20위 상품]\n"
        f"{top_text}\n"
        "위 상위권 상품들의 특성을 분석해서 우리 상품의 순위를 올리기 위한 구체적인 전략을 3줄 이내로 간결하게 알려줘. "
        "번호 없이 핵심만, 한국어로."
    )
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify({"strategy": message.content[0].text.strip()})

if __name__ == '__main__':
    print("서버 시작: http://localhost:5000")
    app.run(port=5000, debug=True)