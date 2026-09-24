from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from servisler.pdf_service import pdf_oku
import tempfile
import os

app = FastAPI(
    title="İnşaat AI",
    description="Otonom inşaat metraj ve maliyet analiz sistemi",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# ANA SAYFA
# --------------------------------------------------

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
            font-family: Arial, Helvetica, sans-serif;
            background: #0b0f14;
            color: white;
        }

        .container {
            width: 100%;
            max-width: 900px;
            margin: auto;
            padding: 25px 18px 50px;
        }

        .header {
            text-align: center;
            padding: 30px 10px;
        }

        .logo {
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #aab4c3;
            font-size: 16px;
            line-height: 1.5;
        }

        .card {
            background: #121821;
            border: 1px solid #263140;
            border-radius: 18px;
            padding: 25px;
            margin-top: 20px;
        }

        .card h2 {
            margin-top: 0;
        }

        .upload-area {
            border: 2px dashed #40506a;
            border-radius: 16px;
            padding: 35px 20px;
            text-align: center;
            margin-top: 20px;
        }

        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }

        input[type="file"] {
            width: 100%;
            margin: 20px 0;
            padding: 12px;
            background: #1a222e;
            color: white;
            border-radius: 10px;
            border: 1px solid #344154;
        }

        button {
            width: 100%;
            padding: 15px;
            border: 0;
            border-radius: 12px;
            background: #6d3df5;
            color: white;
            font-size: 17px;
            font-weight: bold;
            cursor: pointer;
        }

        button:disabled {
            opacity: 0.5;
        }

        .features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 20px;
        }

        .feature {
            background: #18202b;
            border-radius: 12px;
            padding: 16px;
        }

        .feature-title {
            font-weight: bold;
            margin-bottom: 5px;
        }

        .feature-text {
            color: #9da8b8;
            font-size: 13px;
        }

        #sonuc {
            display: none;
            margin-top: 20px;
            background: #101923;
            border-radius: 14px;
            padding: 20px;
        }

        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
            color: #b9a5ff;
        }

        .success {
            color: #49d17d;
            font-weight: bold;
        }

        .error {
            color: #ff6464;
            font-weight: bold;
        }

        .footer {
            text-align: center;
            color: #687587;
            font-size: 13px;
            margin-top: 35px;
        }

        @media (max-width: 600px) {

            .logo {
                font-size: 34px;
            }

            .features {
                grid-template-columns: 1fr;
            }

            .card {
                padding: 18px;
            }

        }

    </style>
</head>

<body>

<div class="container">

    <div class="header">

        <div class="logo">
            🏗️ İnşaat AI
        </div>

        <div class="subtitle">
            Yapay zekâ destekli otonom
            metraj ve maliyet analiz sistemi
        </div>

    </div>


    <div class="card">

        <h2>📁 Proje Analizi</h2>

        <p class="subtitle">
            İnşaat projenizin PDF dosyasını yükleyin.
            Sistem projeyi analiz ederek metraj ve
            malzeme bilgilerini çıkarmaya başlayacak.
        </p>


        <div class="upload-area">

            <div class="upload-icon">
                📄
            </div>

            <strong>
                Proje PDF'sini yükleyin
            </strong>

            <p class="subtitle">
                PDF formatındaki mimari veya teknik projeler
            </p>

            <form id="uploadForm">

                <input
                    type="file"
                    id="dosya"
                    name="dosya"
                    accept=".pdf"
                    required
                >

                <button type="submit">
                    🚀 Projeyi Analiz Et
                </button>

            </form>

        </div>


        <div class="loading" id="loading">

            ⏳ Proje yükleniyor ve okunuyor...
            <br><br>
            Lütfen bekleyin.

        </div>


        <div id="sonuc"></div>

    </div>


    <div class="card">

        <h2>🤖 Sistem Özellikleri</h2>

        <div class="features">

            <div class="feature">
                <div class="feature-title">
                    📐 Metraj
                </div>
                <div class="feature-text">
                    Projedeki ölçüleri ve miktarları analiz eder.
                </div>
            </div>

            <div class="feature">
                <div class="feature-title">
                    🧱 Malzeme
                </div>
                <div class="feature-text">
                    Kullanılacak malzemeleri belirler.
                </div>
            </div>

            <div class="feature">
                <div class="feature-title">
                    💰 Maliyet
                </div>
                <div class="feature-text">
                    Malzeme ve işçilik maliyetlerini hesaplar.
                </div>
            </div>

            <div class="feature">
                <div class="feature-title">
                    👷 İşçilik
                </div>
                <div class="feature-text">
                    İşçilik miktarlarını ve maliyetlerini analiz eder.
                </div>
            </div>

            <div class="feature">
                <div class="feature-title">
                    🔍 Kontrol
                </div>
                <div class="feature-text">
                    Hesapları kontrol eden denetim sistemi.
                </div>
            </div>

            <div class="feature">
                <div class="feature-title">
                    📊 Rapor
                </div>
                <div class="feature-text">
                    Profesyonel proje maliyet raporu oluşturur.
                </div>
            </div>

        </div>

    </div>


    <div class="footer">

        İnşaat AI • Otonom Metraj ve Maliyet Analiz Sistemi

    </div>

</div>


<script>

const form = document.getElementById("uploadForm");
const dosya = document.getElementById("dosya");
const loading = document.getElementById("loading");
const sonuc = document.getElementById("sonuc");

form.addEventListener("submit", async function(e) {

    e.preventDefault();

    if (!dosya.files.length) {
        alert("Lütfen bir PDF dosyası seçin.");
        return;
    }

    const file = dosya.files[0];

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Sadece PDF dosyaları yüklenebilir.");
        return;
    }

    const formData = new FormData();

    formData.append("dosya", file);

    loading.style.display = "block";
    sonuc.style.display = "none";

    try {

        const response = await fetch("/proje/yukle", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        loading.style.display = "none";
        sonuc.style.display = "block";

        if (!response.ok) {

            sonuc.innerHTML =
                `<div class="error">
                    ❌ Hata oluştu
                 </div>
                 <br>
                 ${data.detail || "Bilinmeyen hata"}`;

            return;
        }

        sonuc.innerHTML =
            `<div class="success">
                ✅ Proje başarıyla yüklendi
            </div>
            <br>
            📄 Sayfa sayısı:
            <strong>${data.sayfa_sayisi}</strong>
            <br><br>
            🤖 PDF analiz için hazır.`;

    } catch (error) {

        loading.style.display = "none";
        sonuc.style.display = "block";

        sonuc.innerHTML =
            `<div class="error">
                ❌ Sunucuya bağlanılamadı.
             </div>
             <br>
             ${error}`;

    }

});

</script>

</body>
</html>
"""


# --------------------------------------------------
# SAĞLIK KONTROLÜ
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "durum": "çalışıyor",
        "sistem": "İnşaat AI",
        "surum": "0.2.0"
    }


# --------------------------------------------------
# PROJE PDF YÜKLEME
# --------------------------------------------------

@app.post("/proje/yukle")
async def proje_yukle(dosya: UploadFile = File(...)):

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
    "durum": "başarılı",
    "mesaj": "Proje PDF'si başarıyla okundu.",
    "dosya_adi": dosya.filename,
    "sayfa_sayisi": sonuc["sayfa_sayisi"],
        },
        status_code=200
        
    except Exception as hata:

        raise HTTPException(
            status_code=500,
            detail=f"PDF okunurken hata oluştu: {str(hata)}"
        )

    finally:

        if gecici_dosya and os.path.exists(gecici_dosya):

            os.remove(gecici_dosya)
