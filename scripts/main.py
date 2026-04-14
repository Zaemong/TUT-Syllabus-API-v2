import concurrent.futures
import json
import re
import math
import time
from pathlib import Path

from bs4 import BeautifulSoup
from client_manager import ClientManager
from icecream import ic

BASE_URL = "https://kyo-web.teu.ac.jp/campussy"
CAMPUSSQUARE_PATH = "campussquare.do"

manager = ClientManager()



def resolve_filepath(filename: str) -> Path:
    filepath = Path(filename)
    if not filepath.is_absolute():
        filepath = (Path(__file__).resolve().parent / filepath).resolve()
    return filepath


def load_data_map(filepath: Path) -> dict:
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_data_map(filepath: Path, data_map: dict) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data_map, f, indent=4, ensure_ascii=False)

def get_top_page():
    execution_key = manager.flow_execution_key
    req = manager.client.get("campussquare.do", params={"_flowExecutionKey": execution_key})
    soup = BeautifulSoup(req.text, "html.parser")
    return soup

def initialize_syllabus_json(filename='../data/syllabus_links.json'):
    filepath = resolve_filepath(filename)
    data_map = {}
    save_data_map(filepath, data_map)
    print(f"{filepath} を初期化しました。")


def append_paths_to_data_map(data_map: dict, new_paths: list[str]) -> None:
    for path in new_paths:
        parts = path.split('/')
        if len(parts) > 3:
            section = parts[3]
            if section not in data_map:
                data_map[section] = []
            if path not in data_map[section]:
                data_map[section].append(path)


def update_syllabus_json(new_paths, filename='../data/syllabus_links.json'):
    filepath = resolve_filepath(filename)
    data_map = load_data_map(filepath)
    append_paths_to_data_map(data_map, new_paths)
    save_data_map(filepath, data_map)
    print(f"{filepath} を更新しました。")


def extract_path_from_row(tr) -> str | None:
    row_input = tr.find("input")
    if row_input is None:
        return None

    onclick = row_input.get("onclick")
    if onclick is None:
        return None

    match = re.search(r"(/syllabus/.*?)'", str(onclick))
    if match is None:
        return None
    return match.group(1)


def get_detail_page_save_path(path: str) -> Path | None:
    parts = path.split('/')
    if len(parts) <= 3:
        return None

    section = parts[3]
    filename = Path(path).name
    return resolve_filepath(f"../data/detail_pages/{section}/{filename}")


def save_detail_page(path: str) -> None:
    time.sleep(0.5)
    save_path = get_detail_page_save_path(path)
    if save_path is None:
        print("Invalid syllabus path:", path)
        return

    save_path.parent.mkdir(parents=True, exist_ok=True)

    req = manager.client.get(f"https://kyo-web.teu.ac.jp{path}")
    if req.status_code != 200:
        print(f"Failed to fetch {path}: HTTP {req.status_code}")
        return
    
    soup = BeautifulSoup(req.text, "html.parser")
    body = soup.find("body")
    if body is None: return
    save_path.write_text(body.prettify() , encoding='utf-8')
    print(f"Saved detail page to {save_path}")


def save_detail_pages(paths: list[str], max_workers: int = 10) -> None:
    unique_paths = list(dict.fromkeys(paths))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(save_detail_page, path) for path in unique_paths]
        for future in concurrent.futures.as_completed(futures):
            future.result()


def collect_paths_for_yobi(yobi: int) -> list[str]:
    first_execution_key = manager.get_flow_execution_key_with_search(
        nendo=2026,
        yobi=yobi
    )
    soup = manager.get_page_with_flow_execution_key(first_execution_key)

    data_count_match = re.search(r"全部で\s*(\d+)件", soup.text)
    if data_count_match is None:
        print("No data count found for yobi =", yobi)
        return []

    data_count = int(data_count_match.group(1))
    page_count = math.ceil(data_count / 200)
    ic(f"yobi = {yobi}: data_count = {data_count}, page_count = {page_count}")

    paths: list[str] = []
    for page in range(1, page_count + 1):
        execution_key = manager.get_flow_execution_key_with_paging(count=200, page=page)
        print("Fetching page", page, "with execution key:", execution_key)
        table_soup = manager.get_page_with_flow_execution_key(execution_key)

        table = table_soup.find("tbody")
        if table is None:
            print("No data found for yobi =", yobi)
            continue

        for tr in table.find_all("tr"):
            path = extract_path_from_row(tr)
            if path is not None:
                paths.append(path)

    return paths


def main() -> None:
    get_top_page()
    initialize_syllabus_json()
    paths: list[str] = []

    for y in [1, 2, 3, 4, 5]:
        paths.extend(collect_paths_for_yobi(y))
        manager.refresh_flow_execution_key_with_back(200)

    update_syllabus_json(paths)
    save_detail_pages(paths)

if __name__ == "__main__":
    main()
    
