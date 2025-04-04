# 데이터 흐름을 시각화
# 목표 : 실행 흐름을 한눈에 볼 수 있도록 그래프 형태로 표현
# 방법 : networkx + Graphviz 사용
# 결과 : UI -> Controller -> Service -> DAO -> SQL 실행 흐름이 시각화됨
# 작성자 : smkim060811@gmail.com

# Trouble : 디자인 문제 -> 크기를 키우자니 글씨가 깨지고 글씨를 유지하자니 크기가 너무 작아진다
# 해결방법 : 없음.. 그냥 확대해서 보는게 제일 머리가 안아프다.

import json
import networkx as nx
import matplotlib.pyplot as plt
from graphviz import Digraph
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time


# 실행 흐름 데이터 파일 경로
LOG_OUTPUT_PATH = "execution_flow.json"

# 그래프 저장 경로
GRAPH_OUTPUT_PATH = "execution_flow.png"


# 실행 흐름 JSON 로드
def load_execution_flow():
    try:
        with open(LOG_OUTPUT_PATH, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("### 실행 흐름 파일을 찾을 수 없습니다.")
        return []


# 실행 흐름 시각화
def visualize_execution_flow():
    execution_flow = load_execution_flow()
    if not execution_flow:
        print("### 실행 흐름 데이터가 없습니다.")
        return

    # Graphviz 방향 그래프 생성
    G = Digraph(format="png", engine="dot")
    G.attr(rankdir="TB")
    G.attr(ranksep="1.0", nodesep="0.8")

    for flow in execution_flow:
        # 컨트롤러 노드 추가
        controller = flow.get("controller", {})
        controller_label = f'{controller.get("class", "UnknownController")}\n{controller.get("function", "UnknownFunction")}'
        G.node(controller_label, shape="box", color="lightblue", style="filled", fontsize="16", width="2", height="1")

        # 서비스(Service) 노드 추가
        service = flow.get("service")
        service_label = None
        if service:
            service_label = f'{service.get("class", "UnknownService")}\n{service.get("method", "UnknownMethod")}'
            G.node(service_label, shape="diamond", color="orange", style="filled", fontsize="16", width="2", height="1")
            G.edge(controller_label, service_label, label="calls", color="gray60")  # Controller -> Service 연결

        # DAO 노드 추가
        dao = flow.get("dao")
        dao_label = None
        if dao:
            dao_label = f'{dao.get("class", "UnknownDAO")}\n{dao.get("method", "UnknownMethod")}'
            G.node(dao_label, shape="ellipse", color="lightgreen", style="filled", fontsize="16", width="2", height="1")
            if service_label:
                G.edge(service_label, dao_label, label="calls", color="gray60")  # Service -> DAO 연결
            else:
                G.edge(controller_label, dao_label, label="calls", color="gray60")  # Controller -> DAO 연결 (Service 없을 때)

        # SQL 노드 추가
        for sql in flow.get("sql", []):
            sql_label = f'{sql.get("query_type", "SQL")}\n{sql.get("class", "UnknownClass")}.{sql.get("method", "UnknownMethod")}'
            G.node(sql_label, shape="parallelogram", color="lightcoral", style="filled", fontsize="16", width="2", height="1")
            if dao_label:
                G.edge(dao_label, sql_label, label="executes", color="gray60")  # DAO -> SQL 연결
            elif service_label:
                G.edge(service_label, sql_label, label="executes", color="gray60")  # Service -> SQL 연결 (DAO 없을 때)
            else:
                G.edge(controller_label, sql_label, label="executes", color="gray60")  # Controller -> SQL 연결 (DAO & Service 없을 때)


    # 실행 흐름 그래프 저장 및 출력
    output_path = G.render(filename="execution_flow")
    print(f"### 실행 흐름 그래프 저장 완료: {output_path}")

    # Matplotlib으로 이미지 출력
    # plt.imshow(plt.imread(output_path))
    # plt.axis("off")
    # plt.show()

class JSONFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(LOG_OUTPUT_PATH):
            print("### 실행 흐름 JSON 변경 감지 됨 => 그래프 최신화 시작\n")
            visualize_execution_flow()



if __name__ == "__main__":
    print("### 실행 흐를 시각화 감시 시작")
    event_handler = JSONFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(os.path.abspath(LOG_OUTPUT_PATH)),recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

        


