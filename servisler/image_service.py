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
            "mesaj": "OPENAI_API_KEY Render ortamında bulunamadı."
        }

    try:
        client = OpenAI(api_key=api_key)

        image_url = _resim_data_url(resim_yolu)

        prompt = """
Sen profesyonel bir inşaat proje analiz yapay zekasısın.

Bu görsel bir mimari, statik, elektrik veya mekanik proje çizimi olabilir.

Görseli dikkatli şekilde incele.

SADECE görselde gerçekten görülebilen veya okunabilen bilgileri raporla.
Okunamayan ölçüleri kesinmiş gibi tahmin etme.
Bir bilgi görünmüyorsa "bilinmiyor" yaz.

Şunları tespit etmeye çalış:

1. Çizim türü
2. Kat / bölüm bilgisi
3. Odalar ve görünen isimleri
4. Yaklaşık oda alanları
5. Duvarlar
6. Kapılar
7. Pencereler
8. Görünen ölçüler
9. Kolonlar
10. Kirişler
11. Döşemeler
12. Merdiven
13. Elektrik sembolleri
14. Prizler
15. Anahtarlar
16. Aydınlatmalar
17. Sıhhi tesisat elemanları
18. Lavabo, klozet, duş vb.
19. Havalandırma / mekanik elemanlar
20. Çatı veya çatıya ait görünen elemanlar
21. Görünen yapı malzemeleri
22. Metraj hesabında kullanılabilecek ölçüler
23. Görselin okunabilirlik durumu

Her önemli bulgu için güven seviyesini belirt:

"yüksek"
"orta"
"düşük"

Kesin olmayan hiçbir ölçüyü gerçek ölçü gibi verme.

Cevabı SADECE geçerli JSON olarak döndür.

JSON formatı:

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
                "okunabilirlik": "analiz sonucu JSON olarak okunamadı",
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
