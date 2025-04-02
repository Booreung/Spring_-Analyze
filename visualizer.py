# 데이터 흐름을 시각화
# 목표 : 실행 흐름을 한눈에 볼 수 있도록 그래프 형태로 표현
# 방법 : networkx + Graphviz 사용
# 결과 : UI -> Controller -> Service -> DAO -> SQL 실행 흐름이 시각화됨
# 작성자 : smkim060811@gmail.com

import json
import networkx as nx
import matplotlib.pyplot as plt
from graphviz import Digraph


# log_watcher.py에서 생성한 실행흐름 json 파일
LOG_OUTPUT_PATH = "execution_flow.json"


# json 파일 불러오기
def load_execution_flow():
    try:
        with open(LOG_OUTPUT_PATH, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("### 실행 흐름 파일이 없습니댜.")
        return []
    

# 시각화 def
def visulize_execution_flow():
    execution_flow = load_execution_flow()
    if not execution_flow:
        print("### 파일이 없습니다.")
        return
    
    # 그래프 확장명, 그릴 방식 정함
    G = Digraph(format="png", engine="dot")

    for flow in execution_flow:
        # node 라벨명 선언
        controller_label = f'{flow["controller"]["class"]}\n{flow["controller"]["function"]}'
        dao_label = f'{flow["dao"]["class"]}\n{flow["dao"]["method"]}' if flow.get("dao") else None  

        # Controller 포인트 style
        G.node(controller_label, shape="box", color="lightblue", style="filled")

        # Dao 포인트 style & Controller -> Dao 선 연결
        if dao_label:
            G.node(dao_label, shape="ellipse", color="lightgreen", style="filled")
            G.edge(controller_label, dao_label, label="calls")

        for sql in flow["sql"]:
            # SQL 라벨명 선언
            sql_label = f'{sql["query_type"]}\n{sql["class"]}.{sql["method"]}'
            # SQL 포인트 style
            G.node(sql_label, shape="parallelogram", color="lightcoral", style="filled")
            # Dao -> SQL 선 연결
            if dao_label:
                G.edge(dao_label, sql_label, label="executes")


    # 실행 흐름 그래프 저장
    output_path = G.render(filename="execution_flow")
    print(f"### 실행 흐름 그래프 저장 완료: {output_path}")
    plt.imshow(plt.imread(output_path))
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    visulize_execution_flow()

        


