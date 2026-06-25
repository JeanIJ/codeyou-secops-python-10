import os
import requests
from typing import Any, Optional

class TrelloClient:
    def __init__(self):
        self.key = os.environ.get("TRELLO_KEY")
        self.token = os.environ.get("TRELLO_TOKEN")
        self.list_id = os.environ.get("TRELLO_LIST_ID")

        if not self.key or not self.token or not self.list_id:
            raise RuntimeError(
                "Missing Trello env vars. Run:\n"
                "  export TRELLO_KEY='...'\n"
                "  export TRELLO_TOKEN='...'\n"
                "  export TRELLO_LIST_ID='...'"
            )

    def create_card(self, name: str, desc: str, due: Optional[str] = None) -> dict[str, Any]:
        url = "https://api.trello.com/1/cards"
        params = {
            "key": self.key,
            "token": self.token,
            "idList": self.list_id,
            "name": name,
            "desc": desc,
        }
        if due:
            params["due"] = due

        r = requests.post(url, params=params, timeout=10)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Trello create failed ({r.status_code}): {r.text[:200]}")
        return r.json()