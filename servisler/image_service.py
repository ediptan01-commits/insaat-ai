import os
import base64
import json
from openai import OpenAI


def _resim_data_url(resim_yolu: str) -> str:
    with open(resim_yolu, "rb") as f:
        veri = base64.b64encode(f.read()).decode("utf-8")

    uzanti = os.path.splitext(resim_yolu)[1].lower()

    mime_tipleri = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    mime = mime_tipleri.get(uzanti, "image/png")

    return f"data:{mime};base64,{veri}"


def gorsel_ai_analiz(resim_yolu: str) -> dict:

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "durum": "hata",
            "mesaj": "OPENAI_API_KEY bulunamadı."
        }

    try:

        client = OpenAI(api_key=api_key)

        image_url = _resim_data_url(resim_yolu)

        prompt = """
Sen profesyonel bir inşaat proje analiz yapay zekasısın.

Bu görsel bir inşaat projesinin çizim sayfasıdır.

Görseli dikkatli incele.

SADECE görselde gerçekten görülebilen bilgileri raporla.

Ölçü okunmuyorsa tahmin etme.

Bir bilgi görünmüyorsa "bilinmiyor" yaz.

Özellikle şunları tespit et:

- çizim türü
- kat bilgisi
- oda isimleri
- oda alanları
- duvarlar
- kapılar
- pencereler
- ölçüler
- kolonlar
- kirişler
- döşemeler
- merdiven
- elektrik sembolleri
- prizler
- anahtarlar
- aydınlatmalar
- lavabo
- klozet
- duş
- sıhhi tesisat
- mekanik elemanlar
- çatı
- görünen yapı malzemeleri
- metraj hesabında kullanılabilecek ölçüler

Her önemli bulgu için güven seviyesi belirt:

yüksek
orta
düşük

Kesin olmayan ölçüleri gerçek ölçü olarak verme.

Cevabı sadece JSON olarak döndür.

Format:

{
    "cizim_turu": "",
    "kat_bilgisi": "",
    "okunabilirlik": "",
    "odalar": [],
    "duvarlar": [],
    "kapilar": [],
    "pencereler": [],
    "olculer": [],
    "kolonlar": [],
    "kirisler": [],
    "dosemeler": [],
    "merdiven": [],
    "elektrik": [],
    "mekanik": [],
    "sihhi_tesisat": [],
    "cati": [],
    "malzemeler": [],
    "metraj_icin_veriler": [],
    "uyarilar": []
}
"""

        response = client.responses.create(

            model="gpt-6-luna",

            input=[
                {
                    "role": "user",

                    "content": [

                        {
                            "type": "input_text",
                            "text": prompt
                        },

                        {
                            "type": "input_image",
                            "image_url": image_url,
                            "detail": "high"
                        }

                    ]
                }
            ]
        )

        sonuc = response.output_text.strip()

        try:

            veri = json.loads(sonuc)

        except json.JSONDecodeError:

            veri = {
                "cizim_turu": "bilinmiyor",
                "okunabilirlik": "JSON okunamadı",
                "ham_cevap": sonuc
            }

        return {
            "durum": "basarili",
            "analiz": veri
        }

    except Exception as e:

        return {
            "durum": "hata",
            "mesaj": str(e)
        }
