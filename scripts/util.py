import urllib.parse

def convert_url_to_flow_execution_key(url: str) -> str:
    query = urllib.parse.urlparse(url).query
    params = urllib.parse.parse_qs(query)
    return params['_flowExecutionKey'][0]