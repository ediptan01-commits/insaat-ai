import base64
from pathlib import Path

from PIL import Image


DESTEKLENEN_FORMATLAR = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def gorsel_dosyasi_oku(dosya_yolu: str) -> dict:
    """Tek bir JPG/PNG/WebP dosyasını analiz ajanı için görsel girdisine çevirir."""

    yol = Path(dosya_yolu)
    baytlar = yol.read_bytes()

    with Image.open(yol) as gorsel:
        format_adi = (gorsel.format or "").upper()
        genislik, yukseklik = gorsel.size
        gorsel.verify()

    mime_type = DESTEKLENEN_FORMATLAR.get(format_adi)
    if mime_type is None:
        raise ValueError("Yalnızca JPG/JPEG, PNG veya WEBP görselleri desteklenir.")

    gorsel_girdisi = {
        "sayfa": 1,
        "mime_type": mime_type,
        "genislik": genislik,
        "yukseklik": yukseklik,
        "veri_url": f"data:{mime_type};base64,{base64.b64encode(baytlar).decode('ascii')}",
    }

    return {
        "sayfa_sayisi": 1,
        "sayfalar": [{
            "sayfa": 1,
            "metin": "",
            "gorsel": {
                "durum": "hazir",
                "mime_type": mime_type,
                "genislik": genislik,
                "yukseklik": yukseklik,
            },
        }],
        "gorsel_analiz_girdisi": {
            "surum": "1.0",
            "aciklama": "Yüklenen tek görsel, görsel analiz adaptörüne hazır.",
            "sayfalar": [gorsel_girdisi],
        },
    }
