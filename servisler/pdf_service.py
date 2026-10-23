import base64
import os

from pypdf import PdfReader


GORSEL_DPI = 144
GORSEL_MAKS_KENAR = 2000


def _gorsel_sayfa_limiti():
    try:
        return max(1, int(os.getenv("MAX_VISION_PAGES", "40")))
    except ValueError:
        return 40


def _sayfa_gorseli_uret(belge, fitz, sayfa_no: int) -> dict:
    """Bir PDF sayfasını, görsel modellere aktarılabilecek PNG veri URL'sine çevirir."""

    sayfa = belge[sayfa_no - 1]
    dikdortgen = sayfa.rect
    olcek = min(
        GORSEL_DPI / 72,
        GORSEL_MAKS_KENAR / max(dikdortgen.width, dikdortgen.height),
    )
    pixmap = sayfa.get_pixmap(
        matrix=fitz.Matrix(olcek, olcek),
        alpha=False,
        colorspace=fitz.csRGB,
    )
    gorsel_bayt = pixmap.tobytes("png")

    veri = base64.b64encode(gorsel_bayt).decode("ascii")
    return {
        "sayfa": sayfa_no,
        "mime_type": "image/png",
        "genislik": pixmap.width,
        "yukseklik": pixmap.height,
        "veri_url": f"data:image/png;base64,{veri}",
    }


def pdf_oku(dosya_yolu: str) -> dict:
    """PDF metnini çıkarır ve her sayfanın görsel analiz girdisini hazırlar.

    Mevcut ``sayfa_sayisi`` ve ``sayfalar[*].metin`` alanları korunur. Görsel
    veriler ``gorsel_analiz_girdisi.sayfalar`` altında veri URL'si olarak yer
    alır; böylece ProjectAgent veya ilerideki bir görsel AI adaptörü bu alanı
    kullanabilir. Görsel oluşturma hatası mevcut metin analizini durdurmaz.
    """

    reader = PdfReader(dosya_yolu)
    sayfalar = []
    gorsel_sayfalar = []
    sayfa_sayisi = len(reader.pages)
    gorsel_limiti = _gorsel_sayfa_limiti()
    onceden_atlanan_sayfalar = list(range(gorsel_limiti + 1, sayfa_sayisi + 1))

    # PyMuPDF, Render üzerinde ayrıca Poppler kurulumu gerektirmeyen
    # paketlenmiş bir PDF renderer sağlar.
    try:
        import fitz
    except ImportError as hata:
        fitz = None
        gorsel_belge = None
        gorsel_hata = str(hata)
        gorsel_hata_kodu = "pdf_renderer_kurulu_degil"
    else:
        try:
            gorsel_belge = fitz.open(dosya_yolu)
            gorsel_hata = None
            gorsel_hata_kodu = None
        except Exception as hata:
            gorsel_belge = None
            gorsel_hata = str(hata)
            gorsel_hata_kodu = "pdf_renderer_pdf_acamadi"

    for numara, sayfa in enumerate(reader.pages, start=1):
        metin = sayfa.extract_text() or ""
        sayfa_verisi = {"sayfa": numara, "metin": metin}

        try:
            if numara > gorsel_limiti:
                sayfa_verisi["gorsel"] = {
                    "durum": "analiz_sayfa_siniri",
                    "sinir": gorsel_limiti,
                }
                sayfalar.append(sayfa_verisi)
                continue
            if gorsel_belge is None:
                raise RuntimeError(gorsel_hata or "PDF renderer kullanılamıyor.")
            gorsel = _sayfa_gorseli_uret(gorsel_belge, fitz, numara)
            sayfa_verisi["gorsel"] = {
                "durum": "hazir",
                "mime_type": gorsel["mime_type"],
                "genislik": gorsel["genislik"],
                "yukseklik": gorsel["yukseklik"],
            }
            gorsel_sayfalar.append(gorsel)
        except Exception as hata:
            # Görsel renderer/tek sayfa hatası, önceden çalışan metin
            # analizinin başarısız olmasına neden olmamalıdır.
            sayfa_verisi["gorsel"] = {
                "durum": "olusturulamadi",
                "hata_kodu": (
                    gorsel_hata_kodu
                    if gorsel_belge is None
                    else "pdf_sayfasi_gorsellestirilemedi"
                ),
                "hata": str(hata),
            }

        sayfalar.append(sayfa_verisi)

    if gorsel_belge is not None:
        gorsel_belge.close()

    return {
        "sayfa_sayisi": sayfa_sayisi,
        "sayfalar": sayfalar,
        "gorsel_analiz_girdisi": {
            "surum": "1.0",
            "aciklama": (
                "Her sayfanın PNG veri URL'si; görsel analiz adaptörüne "
                "aktarılmak üzere hazırlandı."
            ),
            "sayfalar": gorsel_sayfalar,
            "atlanmis_sayfalar": onceden_atlanan_sayfalar,
        },
    }
