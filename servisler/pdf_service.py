from pypdf import PdfReader


def pdf_oku(dosya_yolu: str) -> dict:
    """
    PDF projesini okur ve sayfalardaki metinleri çıkarır.
    """

    reader = PdfReader(dosya_yolu)

    sayfalar = []

    for numara, sayfa in enumerate(reader.pages, start=1):
        metin = sayfa.extract_text() or ""

        sayfalar.append({
            "sayfa": numara,
            "metin": metin
        })

    return {
        "sayfa_sayisi": len(reader.pages),
        "sayfalar": sayfalar
    }
