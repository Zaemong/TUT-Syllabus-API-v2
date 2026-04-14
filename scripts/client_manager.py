import httpx
import urllib.parse
import util
from icecream import ic
from bs4 import BeautifulSoup

BASE_URL = "https://kyo-web.teu.ac.jp/campussy"
CAMPUSSQUARE_PATH = "campussquare.do"

class ClientManager:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL)

        self.flow_id = None
        self.flow_execution_key = None

        self.__authenticate()
        self.__refresh_flow_execution_key()
    
    def close(self):
        self.client.close()
    
    def __authenticate(self):
        req = self.client.get("/")
        location = req.headers['Location']
        query = urllib.parse.urlparse(location).query
        params = urllib.parse.parse_qs(query)
        self.flow_id = params['_flowId'][0]
    
    def __refresh_flow_execution_key(self):
        req = self.client.get(CAMPUSSQUARE_PATH, params={"_flowId": self.flow_id})
        self.flow_execution_key = util.convert_url_to_flow_execution_key(req.headers['Location'])

    def refresh_flow_execution_key_with_back(self, count: int) -> str:
        params = {
            "_eventId": "back",
            "_flowExecutionKey": self.flow_execution_key,
            "_flowExecutionKey": self.flow_execution_key,
            "_displayCount": count,
        }
        req = self.client.get(CAMPUSSQUARE_PATH, params=params)
        self.flow_execution_key = util.convert_url_to_flow_execution_key(req.headers['Location'])
        return self.flow_execution_key

    def get_flow_execution_key_with_paging(self, count: int, page: int) -> str:
        params = {
            "_flowExecutionKey": self.flow_execution_key,
            "_eventId_paging": "_eventId_paging",
            "_displayCount": count,
            "_pageCount": page
        }
        req = self.client.get(CAMPUSSQUARE_PATH, params=params)
        self.flow_execution_key = util.convert_url_to_flow_execution_key(req.headers['Location'])
        return self.flow_execution_key
    
    def get_flow_execution_key_with_search(
            self,
            nendo: int,
            jikanwariShozokuCd: int | None = None,
            kaikoKbnCd: int | None = None,
            yobi: int | None = None,
            jigen: int | None = None,
            kaikoKamokuNm: str | None = None,
            keyword: str | None = None
    ) -> str:
        params = {
            "_flowExecutionKey": self.flow_execution_key,
            "_eventId": "search",
            "nendo": nendo,
            "jikanwariShozokuCd": jikanwariShozokuCd,
            "kaikoKbnCd": kaikoKbnCd,
            "kaikoKamokuNm": kaikoKamokuNm,
            "yobi": yobi,
            "jigen": jigen,
            "keyword": keyword,
            "_displayCount": 200,
        }
        req = self.client.get(CAMPUSSQUARE_PATH, params=params)
        print(params["yobi"])
        self.flow_execution_key = util.convert_url_to_flow_execution_key(req.headers['Location'])
        return self.flow_execution_key

    def get_page_with_flow_execution_key(self, flow_execution_key: str) -> BeautifulSoup:
        req = self.client.get(CAMPUSSQUARE_PATH, params={"_flowExecutionKey": flow_execution_key})
        soup = BeautifulSoup(req.text, "html.parser")
        return soup
