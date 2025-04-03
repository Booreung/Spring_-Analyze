# HTTP 요청 감지 (UI -> Controller 추적) -> Mitmproxy 활용
# 목표 : 실제 브라우저에서 UI 이벤트가 발생하면 자동으로 감지
# 방법 : Mitmproxy를 이용해서 HTTP 요청을 가로채기
# 결과 : 어떤 URL이 호출되었는지 실시간 출력
# 작성자 : smkim060811@gmail.com

# Trouble : Port 문제 발생
# 해결방법 : mitmproxy를 작동해야하는 프로그램과 같은 포트가 아닌 다른 포트에서 실행 -> 목표 포트에서 오는 요청을 대체 포트를 통해 프록시로 전달하는 방식 사용

from mitmproxy import http, ctx
from datetime import datetime
import json
from urllib.parse import parse_qs, urlparse



class HttpSniffer:

    def __init__(self):
        self.request_times = {}  ## 요청 시간을 저장할 딕셔너리



    ## JSON 파싱 함수
    def try_parse_json(self, content):
        try:
            return json.dumps(json.loads(content), indent=4, sort_keys=True)
        except json.JSONDecodeError:
            return content
        


    def request(self, flow: http.HTTPFlow):
        ## HTTP 요청을 감지하여 로깅
        if flow.request.host == "localhost" and flow.request.port == 8082:  
            request_time = datetime.now()
            self.request_times[flow.id] = request_time  ## 요청 시간 저장

            ctx.log.info(f"[{request_time}] -> [HTTP 요청 감지] {flow.request.method} {flow.request.pretty_url}")

            ## 요청 크기 계산
            request_size = len(flow.request.content) + sum(len(v) for v in flow.request.headers.values())
            ctx.log.info(f"Request Size: {request_size} bytes")

            ## Query 파라미터 출력
            query_params = parse_qs(urlparse(flow.request.url).query)
            if query_params:
                ctx.log.info("Query parameters:")
                for param, values in query_params.items():
                    for value in values:
                        ctx.log.info(f"     {param} : {value}")

            ## Content-Type 확인 후 데이터 출력
            content_type = flow.request.headers.get('Content-Type', '')

            if flow.request.content:
                if 'application/xml' in content_type:
                    ctx.log.info("Request Body (XML):\n" + self.try_parse_json(flow.request.content.decode()))
                elif 'application/x-www-form-urlencoded' in content_type:
                    ctx.log.info("Form Data:")
                    form_data = parse_qs(flow.request.content.decode())
                    for field, values in form_data.items():
                        for value in values:
                            ctx.log.info(f"     {field} : {value}")
                else:
                    ctx.log.info(f"Request Body:\n{flow.request.content.decode('utf-8', 'ignore')}")



    def response(self, flow: http.HTTPFlow):
       ## HTTP 응답을 감지하여 로깅
        response_time = datetime.now()
        request_time = self.request_times.pop(flow.id, None)  ## 요청 시간 가져오기

        if request_time:
            elapsed_time = (response_time - request_time).total_seconds() * 1000  ## ms 단위 변환
        else:
            elapsed_time = -1  # 요청 시간이 없으면 -1로 설정

        ctx.log.info(f"[{response_time}] -> [HTTP 응답 감지] {flow.response.status_code} {flow.response.reason}")

        ## 응답 크기 계산
        response_size = len(flow.response.content) + sum(len(v) for v in flow.response.headers.values())
        ctx.log.info(f"Response Size: {response_size} bytes")

        ## 응답 속도 출력
        if elapsed_time >= 0:
            ctx.log.info(f"Response Time: {elapsed_time:.2f} ms")

        ## Content-Type 확인 후 데이터 출력
        content_type = flow.response.headers.get('Content-Type', '')
        if flow.response.content:
            if 'application/xml' in content_type:
                ctx.log.info("Response Body (XML):\n" + self.try_parse_json(flow.response.content.decode()))
            else:
                ctx.log.info(f"Response Body:\n{flow.response.content.decode('utf-8', 'ignore')}")



## Mitmproxy에서 사용할 애드온 등록
addons = [HttpSniffer()]



## mitmproxy --mode reverse:http://localhost:8082 -p 8080 -s http_sniffer.py
## mitmproxy를 직접 8082에서 실행하는 것이 아니라, 다른 포트(8080)에서 실행하고, 8082에서 오는 요청을 8080을 통해 프록시로 전달하는 방식
