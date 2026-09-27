import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from shopify_admin import verify
from state import get_connection, save_support_request

load_dotenv()  # .env dosyasındaki değişkenleri oku

SHOP_DOMAIN = os.getenv("JUDGEME_SHOP_DOMAIN")  # beklediğimiz mağaza adresi

app = FastAPI()

# Mağaza teması, kendi alan adından (test-store-e3uhspdt.myshopify.com) bu
# sunucuya fetch() ile istek atıyor — farklı alan adı olduğu için CORS gerekir.
# "*" şimdilik (dev, tek mağaza); üretimde gerçek mağaza alan adına daraltılmalı.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.post("/webhook/review-created")
async def review_created(request: Request):
    payload = await request.json()

    incoming_domain = payload.get("shop_domain")
    if incoming_domain != SHOP_DOMAIN:
        raise HTTPException(status_code=403, detail="unknown shop_domain")

    print(payload)  # doğrulama geçince logla
    return {"status": "received"}


@app.post("/support/intake")
async def support_intake(request: Request):
    payload = await request.json()
    email = (payload.get("email") or "").strip()
    order_number = (payload.get("order_number") or "").strip()
    message = (payload.get("message") or "").strip()

    if not email or not order_number or not message:
        raise HTTPException(status_code=422, detail="email, order_number ve message zorunlu")
    if len(message) > 5000:
        raise HTTPException(status_code=422, detail="message çok uzun")

    # Musterinin beyani kanit degildir: siparis no + eposta gercekten eslesiyor mu
    # diye Shopify'a soruyoruz. Eslesmiyorsa (ya da siparis yoksa) verified=False -
    # bu talep her zaman insana gidecek, hicbir otomatik islem yapilmayacak.
    dogrulandi, _order = verify(order_number, email)

    conn = get_connection()
    request_id = save_support_request(conn, email, order_number, message, dogrulandi)
    print(f"[DESTEK TALEBİ] id={request_id} siparis={order_number} dogrulandi={dogrulandi}")
    return {"status": "received", "id": request_id}