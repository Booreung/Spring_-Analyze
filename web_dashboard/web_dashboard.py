# 웹 대시보드 제공 (Flask 기반)
# 목표: 분석한 실행 흐름 데이터를 웹에서 확인할 수 있도록 제공
# 방법: Flask를 사용하여 JSON 데이터를 웹 UI로 출력
# 결과: 웹 UI에서 실행 흐름을 시각적으로 확인 가능

from flask import Flask, render_template, jsonify
import json
import os
import signal
import sys

app = Flask(__name__)

# 실행 흐름 파일 
LOG_OUTPUT_PATH = "execution_flow.json"


# 실행 흐름 데이터 로드 함수
def load_execution_flow():
    if os.path.exists(LOG_OUTPUT_PATH):
        with open(LOG_OUTPUT_PATH, "r" ,encoding="utf-8") as json_file:
            try:
                return json.load(json_file)
            except json.JSONDecodeError:
                return []
    return []


# app 루트 설정
@app.route('/')
def index():
    return render_template('/index.html')


@app.route('/data')
def get_execution_flow():
    # 실행 흐름 데이터를 JSON 형식으로 변환
    data = load_execution_flow()
    return jsonify(data)


def signal_handler(sig, frame):
    print("\n ### 웹 대시보드 종료")
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    app.run(debug=True, host="0.0.0.0", port=5000)