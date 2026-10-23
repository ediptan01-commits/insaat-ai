"""OpenAI Responses API ile proje sayfalarının görsel analiz adaptörü."""
import json
import os
import urllib.error
import urllib.request

MODEL_VARSAYILAN = "gpt-4.1-mini"
MAKS_GORSEL_SAYISI = 8

def _yanit_metni(response):
    parcalar = []
    for item in response.get("output", []):
        if item.get("type") == "message":
            parcalar.extend(c.get("text", "") for c in item.get("content", []) if c.get("type") == "output_text")
    return "\n".join(parcalar).strip()

def _json_bulgularini_coz(metin):
    """JSON nesnesini düz, code-fence ve JSON-string biçimlerinden çıkarır."""
    aday = metin.strip()
    for _ in range(3):
        if aday.startswith("```"):
            satirlar = aday.splitlines()
            if satirlar and satirlar[0].startswith("```"):
                satirlar = satirlar[1:]
            if satirlar and satirlar[-1].strip() == "```":
                satirlar = satirlar[:-1]
            aday = "\n".join(satirlar).strip()
        try:
            cozulen = json.loads(aday)
        except json.JSONDecodeError:
            bas = aday.find("{")
            son = aday.rfind("}")
            if bas < 0 or son <= bas:
                return None
            try:
                cozulen = json.loads(aday[bas:son + 1])
            except json.JSONDecodeError:
                return None
        if isinstance(cozulen, dict):
            return cozulen
        if isinstance(cozulen, str):
            aday = cozulen.strip()
            continue
        return None
    return None

def gorsel_ai_analiz(project_data):
    sayfalar = project_data.get("gorsel_analiz_girdisi", {}).get("sayfalar", [])
    if not sayfalar:
        return {"durum": "gorsel_yok", "sayfa_sayisi": 0}
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"durum": "api_anahtari_eksik", "sayfa_sayisi": len(sayfalar), "mesaj": "Görsel AI için sunucuda OPENAI_API_KEY tanımlanmalıdır."}

    secilenler = sayfalar[:MAKS_GORSEL_SAYISI]
    icerik = [{"type": "input_text", "text": (
        "Bu görseller inşaat projesi sayfalarıdır. Türkçe yanıt ver ve yalnızca JSON döndür. "
        "Şema: {\"cizim_turu\": string, \"odalar\": [{\"ad\": string, \"olcu\": string|null}], "
        "\"olculer\": [string], \"kapilar\": [string], \"pencereler\": [string], "
        "\"malzemeler\": [string], \"belirsizlikler\": [string]}. Okunmayan ölçüyü tahmin etme; "
        "belirsizliği belirt. Sayfa numaraları yükleme sırasıyla 1'den başlar. Bu bir ön incelemedir; "
        "uygulama hesabı veya mühendislik onayı verme."
    )}]
    for sayfa in secilenler:
        icerik.extend([
            {"type": "input_text", "text": f"Sayfa {sayfa.get('sayfa', '?')}:"},
            {"type": "input_image", "image_url": sayfa["veri_url"], "detail": "high"},
        ])
    payload = {
        "model": os.getenv("OPENAI_VISION_MODEL", MODEL_VARSAYILAN),
        "input": [{"role": "user", "content": icerik}],
        "max_output_tokens": 2500,
        "text": {"format": {"type": "json_object"}},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses", data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return {"durum": "gorsel_ai_hatasi", "sayfa_sayisi": len(secilenler), "mesaj": f"Görsel AI isteği başarısız oldu (HTTP {error.code})."}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {"durum": "gorsel_ai_hatasi", "sayfa_sayisi": len(secilenler), "mesaj": "Görsel AI servisine ulaşılamadı veya geçersiz yanıt alındı."}
    metin = _yanit_metni(result)
    bulgular = _json_bulgularini_coz(metin)
    if bulgular is None:
        return {"durum": "yanit_cozumlenemedi", "sayfa_sayisi": len(secilenler), "ham_yanit": metin[:12000]}
    return {"durum": "tamamlandi", "model": payload["model"], "sayfa_sayisi": len(secilenler), "atlanmis_sayfa_sayisi": max(0, len(sayfalar)-len(secilenler)), "bulgular": bulgular}
