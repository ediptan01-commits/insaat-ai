from fastapi import FastAPI, UploadFile, File, HTTPException
from servisler.pdf_service import pdf_oku
import tempfile
import os

app = FastAPI(
    title="İnşaat AI",
    description="Otonom inşaat metraj ve maliyet analiz sistemi",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "uygulama": "İnşaat AI",
        "durum": "çalışıyor",
        "surum": "0.1.0"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/proje/yukle")
async def proje_yukle(dosya: UploadFile = File(...)):

    if not dosya.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Şimdilik sadece PDF dosyaları kabul ediliyor."
        )

    gecici_dosya = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp:
            gecici_dosya = temp.name

            icerik = await dosya.read()
            temp.write(icerik)

        sonuc = pdf_oku(gecici_dosya)

        return {
            "basarili": True,
            "dosya_adi": dosya.filename,
            "sayfa_sayisi": sonuc["sayfa_sayisi"],
            "mesaj": "Proje PDF'i başarıyla okundu.",
            "sayfalar": sonuc["sayfalar"]
        }

    except Exception as hata:
        raise HTTPException(
            status_code=500,
            detail=f"PDF analiz hatası: {str(hata)}"
        )

    finally:
        if gecici_dosya and os.path.exists(gecici_dosya):
            os.remove(gecici_dosya)
