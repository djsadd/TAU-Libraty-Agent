import requests
from read_kabis import parse_payload, flatten_copies
API = "http://89.250.88.12:8000"


def get_token(username: str, password: str) -> str:
    r = requests.post(f"{API}/auth/token", data={
        "username": username,
        "password": password,
        "grant_type": "password",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def api_get(path: str, token: str):
    return requests.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})


token = get_token("admin", "admin123")
json_kabis = api_get("/get_books_range", token).json()
rows = parse_payload(json_kabis)
rows_flat = flatten_copies(rows)

for row in rows_flat:
    print(row)
    break