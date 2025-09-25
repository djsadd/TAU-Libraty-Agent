import requests
from kabisapi.read_kabis import parse_payload, flatten_copies
API = "http://89.250.88.12:8000"
from typing import Optional, Mapping, Any


def get_token(username: str, password: str) -> str:
    r = requests.post(f"{API}/auth/token", data={
        "username": username,
        "password": password,
        "grant_type": "password",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def api_get(path: str, token: str, params: Optional[Mapping[str, Any]] = None):
    r = requests.get(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,            # <-- ВАЖНО: пробрасываем query-параметры
        timeout=50000,
    )
    # для отладки: должен быть .../get_books_range?start_pos=1&end_pos=100
    print("REQUEST URL =>", r.url)
    r.raise_for_status()
    return r

# token = get_token("admin", "admin123")
# json_kabis_len = api_get("/count_books", token).json()
# json_kabis = api_get("/get_books_range", token).json()
# rows = parse_payload(json_kabis)
# rows_flat = flatten_copies(rows)
#
# for row in rows_flat:
#     print(row)
#     break