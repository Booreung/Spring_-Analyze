# 전체적인 파일을 모듈화 관리
# 모듈들을 순차적 or 병렬적으로 실행할 수 있도록 함
# log_watcher.py -> 실시간 로그 감지 
# http_sniffer.py -> HTTP 요청을 가로채 추적 시작
# visualizer.py -> 실시간 로그 감지 후 실행 흐름을 시각화 (원하는 시점은 일단 선택 사항)
# web_dashboard.py -> Flask 웹 대시보드 실행
# 방법 : subprocess 모듈을 활용해서 각 파일을 백그라운드에서 실행
#        threading 또는 multithreading을 사용해서 병렬 실행

# Trouble : 모듈로 각 파일을 실행시키는 과정에서 직접 터미널에 입력해서 실행하는 http_sniffer.py 에서의 mitmproxy문제
#           web_dashboard.py 가 실행되지 않는 문제 발생
# 해결방법 : http_sniffer.py는 모듈화 하지 않고 실행 명령어를 이용해 subproccess.Popen으로 터미널에서 실행하는 것과 같은 환경을 만듦(다른 프로세스로 동작)
#           기존 명령어인 mitmproxy 로 실행하려니 디코딩 문제가 생겨 mitmdump 명령어로 바꾼 뒤 실행(실행을 블로킹 하지 않는 방법으로 수정)
#           app.py파일 이름을 web_dashboard.py로 변경 뒤 관계 경로로 script를 바꿔주니 해결 -> 하위 폴더가 있는 구조면 맞는 경로를 찾아야함. 


# 주의할점
# 1. 다른 프로젝트에서 분석을 위해서 이 소스코드를 실행 할 시 http_sniffer.py에 포트 번호 또는 url을 지정해줘야함 (단, loacl일때만 사용할것)
# 2. log_watcher.py에서 해당 소스코드의 [].log 파일을 잘 찾고 그 파일의 경로를 다시 코드에 집어넣어야함
# 3. 항상 포트번호 신경쓰기 -> 폐쇠망일 경우엔 더더욱 사용할 수 있는지 체크해야함


import subprocess
import time
import signal
import sys
import datetime
import threading

# Windows 환경에서 UTF-8 출력 강제 설정
sys.stdout.reconfigure(encoding="utf-8")

# 실행할 모듈 리스트
MODULES = {
    "log_watcher": "log_watcher.py",
    "visualizer": "visualizer.py",
    "web_dashboard": "web_dashboard\web_dashboard.py"
}

# mitmproxy 실행 명령어
MITMPROXY_CMD_UI = ["mitmproxy", "--mode", "reverse:http://localhost:8082", "-p", "8080", "-s", "http_sniffer.py"]


def start_mitmproxy():
    """ mitmproxy 실행 """
    print("### http_sniffer 실행 중...")
    process =  subprocess.Popen(
        MITMPROXY_CMD_UI,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    time.sleep(2)

    return process
    

# 실행할 프로세스 저장 리스트
processes = {}

# 실시간 프로세스 출력 읽기
def read_process_output(name, process):
    """각 프로세스의 실시간 출력을 읽어와 표시"""
    for line in process.stdout:
        print(f"[{name}] {line.strip()}")  # .decode() 제거

# 모듈 실행
def start_modules():
    for name, script in MODULES.items():
        try:
            print(f"### {name} 실행 중...")
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",  # UTF-8 강제 설정
                bufsize=1,
                universal_newlines=True
            )
            processes[name] = process

            # 각 프로세스 출력을 별도 스레드에서 읽어오기
            thread = threading.Thread(target=read_process_output, args=(name, process), daemon=True)
            thread.start()

        except Exception as e:
            now = datetime.datetime.now()
            print(f"### [{now}] {name} 실행 실패: {e}")

# 실행 중인 모듈 종료
def stop_modules():
    print("\n### 모든 프로세스 종료 중...")
    for name, process in processes.items():
        print(f"⏹ {name} 종료")
        process.terminate()
        process.wait()
    print("### 모든 모듈이 정상 종료되었습니다.")

# Ctrl+C (KeyboardInterrupt) 감지 시 종료
def signal_handler(sig, frame):
    print("\n### Ctrl+C 감지 -> 모든 프로세스 종료")
    stop_modules()
    sys.exit(0)

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    # mitmproxy 실행 + 모듈 실행
    mitmproxy_process = start_mitmproxy()
    start_modules()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
        mitmproxy_process.terminate()
        mitmproxy_process.wait()
