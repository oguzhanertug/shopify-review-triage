import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


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
        "max_tokens": 4096,  # bazı modeller (ör. nemotron) once uzun bir ic
                             # muhakeme uretiyor; kucuk bir limit arac cagrisina
                             # ulasmadan yaniti kesebiliyor. 8192 denendi, iyilesme
                             # gormedik (bkz. NOTES.md) - modelin dogal rastgeleligi
                             # (temperature=0 verilmedi) sonucu etkilemis olabilir.
        "temperature": 0,  # bu guvenlige kritik bir siniflandirma - tutarlilik
                           # rastgele yaraticiliktan daha degerli
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
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        tool_calls = data["choices"][0]["message"]["tool_calls"]
        arguments_raw = tool_calls[0]["function"]["arguments"]
        arguments = json.loads(arguments_raw)
    except (requests.RequestException, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        print(f"[LLM HATASI] Beklenmeyen yanıt, hataya kapalı davranılıyor: {exc}")
        return None

    missing = [field for field in required if field not in arguments]
    if missing:
        print(f"[LLM HATASI] Eksik alanlar {missing}, hataya kapalı davranılıyor")
        return None

    return arguments
