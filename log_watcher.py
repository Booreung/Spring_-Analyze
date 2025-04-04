# Spring 로그 실시간 분석 (Controller -> Service -> DAO 추적)
# 목표 : Spring 로그 파일을 실시간으로 읽어서 백엔드 실행 흐름 분석
# 방법 : watchdog 라이브러리를 사용해 로그 변경 감지
# 결과 : Controller -> Service -> DAO 실행 흐름 자동 감지
# 작성자 : smkim060811@gmail.com

# Trouble : 로그를 파일로 남기는 것에서 어려움이 있었음 , 파일의 변경시점마다 변화를 감지하는건 그다지 어렵지 않은 코드
# 해결방법 : 자바의 로그를 찍어주는 log4j에서 로그가 console에만 나오지 않게 appender를 추가 시켜서 파일 형식으로 저장을 성공함


import time
import os
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import threading
import subprocess
import sys

# 로그 파일 경로
LOG_FILE_PATH = "/efc_dev/logs/application.log"
LOG_DIR = os.path.dirname(LOG_FILE_PATH)

# 로그 -> json 저장 파일
LOG_OUTPUT_PATH = "execution_flow.json"

# 정규식 패턴 (Controller → DAO → SQL 추적)
patterns = {
    "controller": re.compile(r"\[\s*([\w\d_.]+controller)\.([\w\d_]+)?\s*\]", re.IGNORECASE),
    "dao": re.compile(r"\[([\w\d_.]+dao)\.([\w\d_]+)\]\s+=+([\w\d_]+)=+", re.IGNORECASE),
    "service" : re.compile(r"\[([\w\d_.]+service)\.([\w\d_]+)\]\s+=+([\w\d_]+)=+", re.IGNORECASE),
    "sql": re.compile(r"(SELECT|UPDATE|INSERT|DELETE).*SQL_ID:\s+([\w\d_.]+)\.(\w+)", re.IGNORECASE)
}


# 실행 흐름 JSON 저장(누적방식)
def save_execution_flow(execution_flows):
    # 데이터 불러오기
    if os.path.exists(LOG_OUTPUT_PATH):
        print("### 실행 흐름을 저장하겠습니다. 데이터를 읽기 시작")
        with open(LOG_OUTPUT_PATH, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
                print("### 데이터 읽기 실패")
    else:
        existing_data = []

    # 새 실행 흐름 추가
    with open(LOG_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    print(f"### 실행 흐름이 {LOG_OUTPUT_PATH}에 누적 저장되었습니다.")


class LogHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_position = 0  # 마지막으로 읽은 위치
    

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("application.log"):
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                f.seek(self.last_position)  # 마지막 읽은 위치부터 읽기
                new_lines = f.readlines()
                self.last_position = f.tell()  # 현재 파일 위치 저장

            if not new_lines:
                return  # 새로운 로그가 없으면 리턴

            execution_flows = []  # 실행 흐름 리스트
            temp_flow = {"controller": None, "service" : None , "dao": None, "sql": []}

            for line in new_lines:
                if match := patterns["controller"].search(line):
                    if temp_flow["controller"]:
                        execution_flows.append(temp_flow)  # 이전 흐름 저장
                        temp_flow = {"controller": None, "service" : None , "dao": None, "sql": []}

                    temp_flow["controller"] = {
                        "class": match.group(1),
                        "function": match.group(2) if match.group(2) else "Unknown"
                    }
                elif match := patterns["service"].search(line):
                    temp_flow["service"] = {
                        "class": match.group(1),
                        "method": match.group(2)
                    }

                elif match := patterns["dao"].search(line):
                    temp_flow["dao"] = {
                        "class": match.group(1),
                        "method": match.group(2)
                    }

                elif match := patterns["sql"].search(line):
                    temp_flow["sql"].append({
                        "query_type": match.group(1),
                        "class": match.group(2),
                        "method": match.group(3)
                    })


            if temp_flow["controller"]:
                execution_flows.append(temp_flow)  

            # 실행 흐름 출력
            if execution_flows:
                print("\n### 실행 흐름 추적 결과 ###")
                for flow in execution_flows:
                    result = []
                    if flow["controller"]:
                        result.append(f"Controller: {flow['controller']}")
                    if flow["service"]:
                        result.append(f"Service: {flow['service']}")
                    if flow["dao"]:
                        result.append(f"DAO: {flow['dao']}")
                    if flow["sql"]:
                        sql_strings = [f"{sql['query_type']}.{sql['class']}.{sql['method']}\n" for sql in flow["sql"]]
                        result.append(f"SQL: {', '.join(sql_strings)}")

                    print(" -> ".join(result))


            #실행 흐름 Json 저장
            if execution_flows:
                save_execution_flow(execution_flows)


                # 실행 흐름 시각화 갱신
                subprocess.Popen([sys.executable, "visualizer.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                


# 파일 감시 설정
observer = Observer()
event_handler = LogHandler()
observer.schedule(event_handler, path=LOG_DIR, recursive=False)
observer.start()

try:
    print("## 로그 감지 시작 ##")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
