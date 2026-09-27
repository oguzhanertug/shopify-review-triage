import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN")
CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")

TOKEN_URL = f"https://{SHOP_DOMAIN}/admin/oauth/access_token"
GRAPHQL_URL = f"https://{SHOP_DOMAIN}/admin/api/2026-10/graphql.json"

# Client Credentials Grant: kendi mağazamıza karşı, satıcı etkileşimi olmadan
# sunucudan sunucuya erişim (bkz. shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant).
# Token 24 saatte bir doluyor; süresi dolmadan bir dakika önce yenile.
_token_cache = {"value": None, "expires_at": 0}


def _get_token():
    now = time.time()
    if _token_cache["value"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["value"]

    response = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    _token_cache["value"] = data["access_token"]
    _token_cache["expires_at"] = now + data["expires_in"]
    return _token_cache["value"]


def _graphql(query, variables=None):
    response = requests.post(
        GRAPHQL_URL,
        headers={"X-Shopify-Access-Token": _get_token(), "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise RuntimeError(f"Shopify GraphQL hatası: {data['errors']}")
    return data["data"]


ORDER_QUERY = """
query($search: String!) {
  orders(first: 1, query: $search) {
    edges {
      node {
        id
        name
        email
        displayFulfillmentStatus
      }
    }
  }
}
"""


def find_order(order_number):
    """order_number musterinin kendi yazdigi ham metin (ornegin '#1001').
    Sadece rakamlari kabul ederiz - aksi halde Shopify'nin arama söz dizimine
    (name:1001 OR ...) enjeksiyon riski olur. Rakam degilse None donup
    dogrulamayi basarisiz sayariz.
    """
    clean = order_number.strip().lstrip("#")
    if not clean.isdigit():
        return None
    data = _graphql(ORDER_QUERY, {"search": f"name:{clean}"})
    edges = data["orders"]["edges"]
    return edges[0]["node"] if edges else None


def verify(order_number, email):
    """Siparis no + e-posta gercekten eslesiyor mu?

    Donus: (eslesti: bool, order: dict | None). Siparis bulunamazsa ya da
    e-posta eslesmiyorsa False - hicbir zaman 'muhtemelen dogrudur' diye
    varsaymayiz. Boyle bir talep her zaman insana gitmeli.
    """
    order = find_order(order_number)
    if order is None or not order.get("email"):
        return False, order
    eslesiyor = order["email"].strip().lower() == email.strip().lower()
    return eslesiyor, order


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("kullanim: python shopify_admin.py <siparis_no> <eposta>")
        sys.exit(1)

    eslesti, order = verify(sys.argv[1], sys.argv[2])
    print("siparis:", order)
    print("eslesti mi:", eslesti)
