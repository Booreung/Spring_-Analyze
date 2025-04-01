# Spring 로그 실시간 분석 (Controller -> Service -> DAO 추적)
# 목표 : Spring 로그 파일을 실시간으로 읽어서 백엔드 실행 흐름 분석
# 방법 : watchdog 라이브러리를 사용해 로그 변경 감지
# 결과 : Controller -> Service -> DAO 실행 흐름 자동 감지
# 작성자 : smkim060811@gmail.com


import re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


## sample
log_lines = [
    "2025-03-31 09:20:42,482 DEBUG [efc.b.lo.bi.controller.LnAplcController] ",
    "2025-03-31 09:20:42,483 DEBUG [efc.b.lo.dao.qc.Qblo200m_01DAO] ======================retrieveLnAplcList===================",
    "2025-03-31 09:20:42,503 DEBUG [java.sql.PreparedStatement] SELECT /* SQL_ID: Qblo200m_01DAO.retrieveLnAplcList */",
    "2025-03-31 09:20:42,600 DEBUG [java.sql.PreparedStatement] UPDATE /* SQL_ID: Qblo300m_02DAO.updateLoanStatus */",
    "2025-03-31 09:20:42,700 DEBUG [java.sql.PreparedStatement] INSERT /* SQL_ID: Qblo400m_03DAO.insertNewLoan */",
    "2025-03-31 09:20:42,800 DEBUG [java.sql.PreparedStatement] DELETE /* SQL_ID: Qblo500m_04DAO.deleteOldRecords */"
]


# 로그 파일 경로 설정 (프로젝트의 로그 파일)
# LOG_FILE_PATH = "/efc_dev/logs/application.log"
LOG_FILE_PATH = "/efc_dev/logs/application.log"


# 로그 정규식 패턴
patterns = {
    "controller": re.compile(r"\[\s*([\w\d_.]+controller\.[\w\d_]+)\s*\]"),
    "dao": re.compile(r"\[([\w\d_.]+dao.[\w\d_]+)\]\s+=+([\w\d_]+)=+"),
    "sql": re.compile(r"(SELECT|UPDATE|INSERT|DELETE).*SQL_ID:\s+([\w\d_.]+)\.(\w+)", re.IGNORECASE)
}

class LogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == LOG_FILE_PATH:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

            excution_flow = {
                "controller" : None,
                "dao" : None,
                "sql" : []
            }

            # 최신 로그에서 실행 흐름 추출
            for line in lines[-50]: # 최근 50줄만
                if match := patterns["controller"].search(line):
                    excution_flow["controller"] = {
                        "class" : match.group(1),
                        "funtion" : match.group(2)
                    }
                elif match := patterns["dao"].search(line):
                    excution_flow["dao"] = {
                        "class" : match.group(1),
                        "method" : match.group(2)
                    }
                elif match := patterns["sql"].search(line):
                    excution_flow["sql"].append({
                        "class" : match.group(1),
                        "method" : match.group(2)
                    })

            # 결과 출력
            print("\n ### 실행 흐름 추적 결과")
            for key, value in excution_flow.items():
                if value:
                    print(f"=>> {key.capitalize()} -> {value}")  


# 파일 감시 설정
observer = Observer()
event_handler = LogHandler()
observer.schedule(event_handler, path=LOG_FILE_PATH, recursive=False)
observer.start()


# 로그 감지 시작
try:
    print("## 로그 감지 시작 ##")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()