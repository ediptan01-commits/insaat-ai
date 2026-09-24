from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from servisler.pdf_service import pdf_oku
from agents.project_agent import ProjectAgent

import tempfile
import os


# =========================================================
# UYGULAMA
# =========================================================

app = FastAPI(
    title="İnşaat AI",
    description="Otonom inşaat metraj ve proje analiz sistemi",
    version="0.3.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ANA SAYFA
# =========================================================

@app.get("/", response_class=HTMLResponse)
def ana_sayfa():

    return """
<!DOCTYPE html>
<html lang="tr">
<head>

<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>İnşaat AI</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #0b0f17;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    width: 92%;
    max-width: 900px;
    margin: 40px auto;
}

h1 {
    text-align: center;
    font-size: 42px;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: #aab3c5;
    font-size: 18px;
    margin-bottom: 35px;
}

.upload-box {
    border: 2px dashed #53627d;
    border-radius: 25px;
    padding: 40px 20px;
    text-align: center;
    background: #111722;
}

.icon {
    font-size: 70px;
}

h2 {
    font-size: 28px;
}

input[type="file"] {
    width: 100%;
    padding: 15px;
    background: #182130;
    border-radius: 12px;
    color: white;
    margin: 20px 0;
}

button {
    width: 100%;
    padding: 20px;
    border: 0;
    border-radius: 15px;
    background: #713cff;
    color: white;
    font-size: 21px;
    font-weight: bold;
    cursor: pointer;
}

button:disabled {
    opacity: 0.6;
}

.result {
    margin-top: 25px;
    padding: 25px;
    border-radius: 18px;
    background: #111722;
}

.success {
    color: #43df7b;
}

.error {
    color: #ff5c5c;
}

.loading {
    color: #ffc857;
}

.card {
    margin-top: 30px;
    padding: 25px;
    border-radius: 20px;
    background: #111722;
}

.feature {
    padding: 20px;
    margin-top: 15px;
    border-radius: 15px;
    background: #192230;
}

pre {
    white-space: pre-wrap;
    word-break: break-word;
    color: #cbd5e1;
}

</style>

</head>

<body>

<div class="container">

<h1>🏗️ İnşaat AI</h1>

<div class="subtitle">
Otonom proje analiz, metraj ve maliyet sistemi
</div>


<div class="upload-box">

<div class="icon">📄</div>

<h2>Proje PDF'sini yükleyin</h2>

<p>
PDF formatındaki mimari veya teknik projeler
</p>

<input
    id="dosya"
    type="file"
    accept=".pdf,application/pdf"
>


<button
    id="analizBtn"
    onclick="projeyiAnalizEt()"
>
🚀 Projeyi Analiz Et
</button>

</div>


<div
    id="sonuc"
    class="result"
    style="display:none"
></div>


<div class="card">

<h2>🤖 Sistem Özellikleri</h2>

<div class="feature">
📐 <strong>Metraj</strong><br>
Projede bulunan ölçü ve miktarları analiz eder.
</div>

<div class="feature">
🧱 <strong>Malzeme</strong><br>
Projede tespit edilen malzemeleri belirler.
</div>

<div class="feature">
💰 <strong>Maliyet</strong><br>
İlerleyen aşamada malzeme ve işçilik maliyetlerini hesaplar.
</div>

</div>

</div>


<script>

async function projeyiAnalizEt() {

    const dosyaInput = document.getElementById("dosya");
    const sonuc = document.getElementById("sonuc");
    const buton = document.getElementById("analizBtn");

    if (!dosyaInput.files || dosyaInput.files.length === 0) {

        sonuc.style.display = "block";

        sonuc.innerHTML = `
            <div class="error">
                ❌ Lütfen önce bir PDF dosyası seçin.
            </div>
        `;

        return;
    }


    const dosya = dosyaInput.files[0];


    if (!dosya.name.toLowerCase().endsWith(".pdf")) {

        sonuc.style.display = "block";

        sonuc.innerHTML = `
            <div class="error">
                ❌ Sadece PDF dosyaları yüklenebilir.
            </div>
        `;

        return;
    }


    const formData = new FormData();

    formData.append("dosya", dosya);


    buton.disabled = true;

    buton.innerText = "⏳ Proje analiz ediliyor...";


    sonuc.style.display = "block";

    sonuc.innerHTML = `
        <div class="loading">
            🤖 PDF sunucuya gönderiliyor...<br><br>
            Lütfen bekleyin.
        </div>
    `;


    try {

        const response = await fetch(
            "/proje/yukle",
            {
                method: "POST",
                body: formData
            }
        );


        const text = await response.text();


        let data;

        try {

            data = JSON.parse(text);

        } catch {

            throw new Error(
                "Sunucudan geçerli JSON cevabı alınamadı."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.detail || "Sunucu hata döndürdü."
            );

        }


        const analiz =
            data.analiz || {};


        const siniflar =
            analiz.sayfa_siniflari || {};


        const malzemeler =
            analiz.tespit_edilen_malzemeler || [];


        sonuc.innerHTML = `

            <div class="success">
                <h2>✅ Proje başarıyla analiz edildi</h2>
            </div>

            <p>
                📄 <strong>Dosya:</strong>
                ${data.dosya_adi || dosya.name}
            </p>

            <p>
                📑 <strong>Sayfa sayısı:</strong>
                ${data.sayfa_sayisi || 0}
            </p>

            <p>
                📐 <strong>Tespit edilen ölçü sayısı:</strong>
                ${analiz.tespit_edilen_olcu_sayisi || 0}
            </p>

            <p>
                🧱 <strong>Tespit edilen malzeme sayısı:</strong>
                ${malzemeler.length}
            </p>

            <hr>

            <h3>📋 Sayfa sınıfları</h3>

            <pre>
Mimari: ${JSON.stringify(siniflar.mimari || [], null, 2)}

Statik: ${JSON.stringify(siniflar.statik || [], null, 2)}

Elektrik: ${JSON.stringify(siniflar.elektrik || [], null, 2)}

Mekanik: ${JSON.stringify(siniflar.mekanik || [], null, 2)}

Diğer: ${JSON.stringify(siniflar.diger || [], null, 2)}
            </pre>

            <h3>🧱 Tespit edilen malzemeler</h3>

            <pre>${JSON.stringify(
                malzemeler,
                null,
                2
            )}</pre>

        `;

    }

    catch (hata) {

        sonuc.innerHTML = `

            <div class="error">

                <h2>❌ Analiz sırasında hata oluştu</h2>

                <p>
                    ${hata.message}
                </p>

            </div>

        `;

    }

    finally {

        buton.disabled = false;

        buton.innerText =
            "🚀 Projeyi Analiz Et";

    }

}

</script>

</body>
</html>
"""


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "durum": "çalışıyor",
        "sistem": "İnşaat AI",
        "versiyon": "0.3.0"
    }


# =========================================================
# TEST
# =========================================================

@app.get("/test")
def test():

    return {
        "durum": "başarılı",
        "mesaj": "Sunucu cevap veriyor"
    }


# =========================================================
# PROJE PDF YÜKLEME
# =========================================================

@app.post("/proje/yukle")
async def proje_yukle(
    dosya: UploadFile = File(...)
):

    gecici_dosya = None

    try:

        # -------------------------------------------------
        # DOSYA KONTROLÜ
        # -------------------------------------------------

        if not dosya.filename:

            raise HTTPException(
                status_code=400,
                detail="Dosya seçilmedi."
            )


        if not dosya.filename.lower().endswith(".pdf"):

            raise HTTPException(
                status_code=400,
                detail="Sadece PDF dosyaları yüklenebilir."
            )


        # -------------------------------------------------
        # GEÇİCİ DOSYA
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp:

            gecici_dosya = temp.name

            icerik = await dosya.read()

            temp.write(icerik)


        # -------------------------------------------------
        # PDF OKUMA
        # -------------------------------------------------

        sonuc = pdf_oku(
            gecici_dosya
        )


        # -------------------------------------------------
        # PROJE ANALİZİ
        # -------------------------------------------------

        analiz = ProjectAgent().analyze(
            sonuc
        )


        # -------------------------------------------------
        # CEVAP
        # -------------------------------------------------

        return {

            "durum": "başarılı",

            "mesaj":
                "Proje PDF'si başarıyla okundu ve analiz edildi.",

            "dosya_adi":
                dosya.filename,

            "sayfa_sayisi":
                sonuc["sayfa_sayisi"],

            "analiz":
                analiz
        }


    except HTTPException:

        raise


    except Exception as hata:

        raise HTTPException(

            status_code=500,

            detail=
                f"PDF işlenirken hata oluştu: {str(hata)}"
        )


    finally:

        if (
            gecici_dosya
            and os.path.exists(gecici_dosya)
        ):

            os.remove(
                gecici_dosya
            )
