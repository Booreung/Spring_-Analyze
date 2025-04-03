# 전체적인 파일을 모듈화 관리
# 모듈들을 순차적 or 병렬적으로 실행할 수 있도록 함
# log_watcher.py -> 실시간 로그 감지 
# http_sniffer.py -> HTTP 요청을 가로채 추적 시작
# visualizer.py -> 실시간 로그 감지 후 실행 흐름을 시각화 (원하는 시점은 일단 선택 사항)
# web_dashboard.py -> Flask 웹 대시보드 실행
# 방법 : subprocess 모듈을 활용해서 각 파일을 백그라운드에서 실행
#        threading 또는 multithreading을 사용해서 병렬 실행


# 주의할점
# 1. 다른 프로젝트에서 분석을 위해서 이 소스코드를 실행 할 시 http_sniffer.py에 포트 번호 또는 url을 지정해줘야함 (단, loacl일때만 사용할것)
# 2. log_watcher.py에서 해당 소스코드의 [].log 파일을 잘 찾고 그 파일의 경로를 다시 코드에 집어넣어야함
# 3. 항상 포트번호 신경쓰기 -> 폐쇠망일 경우엔 더더욱 사용할 수 있는지 체크해야함


import subprocess
import time
import signal
import sys
import datetime

# 백그라운드 실행 파일 모듈 리스트
MODUELS = [
    "log_watcher.py",
    "http_sniffer.py",
    "visualizer.py",
    "web_dashboard.py"
]

# 실행할 프로세스 저장 리스트
processes = []

# 모듈을 subprocess로 실행
def start_modules():
    for module in MODUELS:
        try:
            print(f"### {module} 실행 중 -- -- -- --")
            process = subprocess.Popen(["python" , module], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(process)
        except Exception as e:
            now = datetime.datetime.now()
            print(f"{[now]} {module} 실행 실패 : {e}")


# 실행중인 모듈 종료
def stop_modules():
    print("\n### 모든 프로세스 종료중-- -- -- --")
    for process in processes:
        process.terminate()  # 종료 시그널을 보냄
        process.wati()       # 종료될 때까지 대기
    print("### 모든 모듈이 정상 종료되었습니다.")


# signal 핸들러
def signal_handler(sig, frame):
    # """Ctrl + C (KeyboardInterrupt) 시 안전하게 종료"""
    print("### Ctrl + C 감지 -> 모든 프로세스를 종료합니다.")
    start_modules()
    sys.exit()


if __name__ == "__main__":
    # 종료 시그널 핸들러 설정
    signal.signal(signal.SIGINT, signal_handler)

    # 모듈 실행 
    start_modules()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
