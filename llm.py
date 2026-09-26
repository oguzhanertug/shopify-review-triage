import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Varsayilan model TEK yerde tanimli (classify.py ve draft.py buradan alir; iki
# dosyada kopya olunca biri guncellenmeyip kalkmis modeli cagirmisti).
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
MAX_TOKENS = 4096  # nemotron gibi modeller once uzun bir ic muhakeme uretiyor; limit
                   # cok kucukse arac cagrisina ulasmadan kesilir (finish_reason=length)
REASONING_EFFORT = "low"  # "low" / "medium" / "high" / None (saglayici varsayilani).
                          # nemotron bazen muhakemede donguye giriyor (bkz. NOTES.md);
                          # "low" ile gercek yanit orani ~%35'ten 6/8'e cikti (kucuk orneklem)
REQUEST_TIMEOUT = 90  # ücretsiz modeller yavaş: ölçülen yanıt süresi ~45 sn'ye çıkıyor
RETRY_DELAY = 5
# Geçici sayılan durumlar. 404 BİLEREK yok: "model artık mevcut değil" kalıcı bir
# yapılandırma hatasıdır, yeniden denemek düzeltmez.
TRANSIENT_STATUSES = {408, 429, 500, 502, 503, 504}


def call_tool(model, system_prompt, user_content, tool_name, tool_description, parameters, required):
    """
    Modeli belirtilen aracı zorunlu olarak çağırmaya zorlar, yapılandırılmış
    çıktıyı döndürür. Ücretsiz modeller zorunlu araç çağrısını her zaman doğru
    desteklemeyebilir — yanıt beklenen şemaya uymuyorsa None döner. Çağıran
    taraf bunu "hataya kapalı, insana yönlendir" olarak yorumlamalı; asla
    varsayılan olarak güvenli/otomatik bir karara düşmemeli.
    """
    payload = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "temperature": 0,  # guvenlige kritik siniflandirma: tutarlilik, yaraticilik degil
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": parameters,
                        "required": required,
                    },
                },
            }
        ],
        "tool_choice": {"type": "function", "function": {"name": tool_name}},
    }
    if REASONING_EFFORT:
        payload["reasoning"] = {"effort": REASONING_EFFORT}
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = _post_with_retry(payload, headers)
        if response.status_code >= 400:
            # Gövde çoğu zaman düzeltme yolunu söyler (ör. "bu slug'ı kullan").
            print(f"[LLM HATASI] HTTP {response.status_code}: {response.text.strip()[:200]} — hataya kapalı davranılıyor")
            return None
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"[LLM HATASI] istek başarısız, hataya kapalı davranılıyor: {exc}")
        return None

    try:
        raw = data["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
        arguments = json.loads(raw)
        if not isinstance(arguments, dict):
            raise TypeError("arguments bir nesne değil")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        print(f"[LLM HATASI] araç çağrısı okunamadı ({_describe(data)}), hataya kapalı davranılıyor: {exc}")
        return None

    missing = [field for field in required if field not in arguments]
    if missing:
        print(f"[LLM HATASI] Eksik alanlar {missing}, hataya kapalı davranılıyor")
        return None

    # Alanın var olması yetmez, türü de doğru olmalı: "false" yazısı Python'da
    # doğru sayılır ve "insana git" kararını "otomatik yanıtla"ya çevirirdi.
    for field, schema in parameters.items():
        if field in arguments and not _type_matches(arguments[field], schema):
            print(f"[LLM HATASI] '{field}' beklenen türde değil, hataya kapalı davranılıyor")
            return None

    return arguments


def _post_with_retry(payload, headers):
    # Yalnızca geçici altyapı hatalarında (aksaklık, zaman aşımı) bir kez daha
    # dener. Format hatasında (model araç çağırmadı) yeniden denemeyiz: aynı
    # girdiye aynı cevabı verir ve ücretsiz günlük kotayı boşuna harcar.
    for attempt in (1, 2):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        except requests.Timeout:
            if attempt == 2:
                raise
        else:
            if not _is_transient(response) or attempt == 2:
                return response
        print(f"[LLM] geçici hata, {RETRY_DELAY} sn sonra bir kez daha denenecek")
        time.sleep(RETRY_DELAY)


def _is_transient(response):
    if response.status_code in TRANSIENT_STATUSES:
        return True
    # OpenRouter sağlayıcı hatalarını çoğu zaman HTTP 200 içinde, gövdede
    # {"error": {"code": 503, ...}} olarak döndürür.
    try:
        body = response.json()
    except ValueError:
        return False
    error = body.get("error") if isinstance(body, dict) else None
    return isinstance(error, dict) and error.get("code") in TRANSIENT_STATUSES


def _describe(data):
    # Hatanın NEDENİNİ günlüğe yazar (model mi beceremedi, sağlayıcı mı hata verdi?).
    if not isinstance(data, dict):
        return "yanıt bir nesne değil"
    if "error" in data:
        return f"sağlayıcı hatası: {str(data['error'])[:150]}"
    try:
        return f"finish_reason={data['choices'][0].get('finish_reason')}"
    except (KeyError, IndexError, AttributeError):
        return "yanıtta choices yok"


def _type_matches(value, schema):
    expected = schema.get("type")
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    return True
