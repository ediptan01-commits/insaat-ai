from fastapi import FastAPI

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
