import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException

load_dotenv()  # .env dosyasındaki değişkenleri oku

SHOP_DOMAIN = os.getenv("JUDGEME_SHOP_DOMAIN")  # beklediğimiz mağaza adresi

app = FastAPI()

@app.post("/webhook/review-created")
async def review_created(request: Request):
    payload = await request.json()

    incoming_domain = payload.get("shop_domain")
    if incoming_domain != SHOP_DOMAIN:
        raise HTTPException(status_code=403, detail="unknown shop_domain")

    print(payload)  # doğrulama geçince logla
    return {"status": "received"}