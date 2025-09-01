import requests
import redis
import os
from backend.services.crypt_service import decrypt_data, encrypt_data
from backend.services.gtoken_get_service import get_cookie_token


redis_client = redis.Redis(host="localhost", port=6379, db=0)
REDIS_KEY_G_TOKEN = "G_TOKEN"


def get_tree_record(password: str):
    url = "https://d247.com/api/front/treedata"
    payload = {"data": {}}

    res_json = fetch_api(url, method="POST", payload=payload)

    encrypted_data = res_json.get("data")
    if not encrypted_data:
        raise Exception("No 'data' field in response")

    return decrypt_data(encrypted_data, password)



def get_odds(sport_id: int, event_id: int, password: str):
    """
    Python equivalent of getOddsFn
    """
    url = f"https://d247.com/api/front/gamedataPrivate?etId={sport_id}&gmid={event_id}"

    payload = {
        "data": encrypt_data({
            "etid": sport_id,
            "gmid": event_id,
        },password=password)
    }

    res_json = fetch_api(url, method="POST", payload=payload)
    encrypted_data = res_json.get("data")

    if not encrypted_data:
        raise Exception("No 'data' field in response")

    return decrypt_data(encrypted_data, password)

def get_highlight_home_private(etid: int, password: str):
    """
    Python equivalent of getHighlightHomePrivateFn
    """
    url = f"{os.getenv('BASE_URL')}/front/highlighthomePrivate?etid={etid}"

    payload = {
        "data": encrypt_data({
            "etid": etid,
            "type": "all",
        }, password)  # <-- pass password
    }

    res_json = fetch_api(url, method="POST", payload=payload, timeout=3)
    encrypted_data = res_json.get("data")

    if not encrypted_data:
        raise Exception("No 'data' field in response")

    return decrypt_data(encrypted_data, password)
# ----------------------------------------------
#                 HELPER FUNCTIONS
# ----------------------------------------------

def fetch_api(url, method="GET", payload=None, headers=None, timeout=3):
    # 1. Try existing cookie from Redis
    cookie_value = redis_client.get(REDIS_KEY_G_TOKEN)
    if cookie_value:
        cookie_value = cookie_value.decode("utf-8")
        resp = make_request(cookie_value, headers, url, method, payload, timeout)
        if resp.status_code == 401:  # expired → refresh
            cookie_value = get_cookie_token()   # 🔥 call Selenium/Playwright here
            redis_client.setex(REDIS_KEY_G_TOKEN, 3600, cookie_value)
            resp = make_request(cookie_value, headers, url, method, payload, timeout)
    else:
        # 2. No cookie → use Selenium/Playwright
        cookie_value = get_cookie_token()
        redis_client.setex(REDIS_KEY_G_TOKEN, 3600, cookie_value)
        resp = make_request(cookie_value, headers, url, method, payload, timeout)

    resp.raise_for_status()
    return resp.json()


def make_request(cookie_value,headers=None, url=None, method="GET", payload=None, timeout=3):
    final_headers = {
        **(headers or {}),
        "Cookie": f"{cookie_value}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if method.upper() == "POST":
        return requests.post(url, headers=final_headers, json=payload, timeout=timeout)
    return requests.get(url, headers=final_headers, timeout=timeout)
