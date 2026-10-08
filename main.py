from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from servisler.pdf_service import pdf_oku
from servisler.image_service import gorsel_dosyasi_oku, gorsel_ai_analiz
from agents.project_agent import ProjectAgent

import tempfile
import os
import html
import fitz


DESTEKLENEN_UZANTILAR = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def proje_dosyasi_oku(dosya_yolu: str, dosya_adi: str) -> dict:
    """PDF veya tekil görsel dosyasını ortak proje analiz yapısına dönüştürür."""

    uzanti = os.path.splitext(dosya_adi)[1].lower()
    if uzanti == ".pdf":
        return pdf_oku(dosya_yolu)
    return gorsel_dosyasi_oku(dosya_yolu)

def pdf_gorsel_ai_analiz(pdf_yolu: str, maksimum_sayfa: int = 3) -> dict:
    """
    PDF sayfalarını görsele çevirir ve görsel AI ile analiz eder.
    İlk aşamada maliyet ve test amacıyla en fazla 3 sayfa analiz edilir.
    """

    sonuclar = []

    try:
        belge = fitz.open(pdf_yolu)

        toplam_sayfa = len(belge)
        analiz_sayisi = min(toplam_sayfa, maksimum_sayfa)

        for indeks in range(analiz_sayisi):

            sayfa = belge[indeks]

            matris = fitz.Matrix(2, 2)
            pixmap = sayfa.get_pixmap(
                matrix=matris,
                alpha=False
            )

            gecici_resim = tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False
            )

            resim_yolu = gecici_resim.name
            gecici_resim.close()

            pixmap.save(resim_yolu)

            try:
                analiz = gorsel_ai_analiz(resim_yolu)

                sonuclar.append({
                    "sayfa": indeks + 1,
                    "analiz": analiz
                })

            finally:
                if os.path.exists(resim_yolu):
                    os.remove(resim_yolu)

        belge.close()

        return {
            "durum": "basarili",
            "toplam_pdf_sayfasi": toplam_sayfa,
            "analiz_edilen_sayfa": analiz_sayisi,
            "sayfalar": sonuclar
        }

    except Exception as e:

        return {
            "durum": "hata",
            "mesaj": str(e)
        }

# ============================================================
# UYGULAMA
# ============================================================

app = FastAPI(
    title="İnşaat AI",
    description="Otonom inşaat proje metraj ve maliyet analiz sistemi",
    version="0.3.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ANA SAYFA TASARIMI
# ============================================================

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
    background:
        radial-gradient(
            circle at top,
            #172033 0%,
            #0b0f17 55%,
            #070a10 100%
        );

    color: #ffffff;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    min-height: 100vh;
}

.container {
    width: 94%;
    max-width: 900px;
    margin: auto;
    padding: 30px 0 60px;
}

.header {
    text-align: center;
    padding: 25px 10px 35px;
}

.logo {
    font-size: 58px;
    margin-bottom: 5px;
}

h1 {
    font-size: 42px;
    margin: 5px 0 12px;

    background:
        linear-gradient(
            90deg,
            #8b5cf6,
            #c084fc,
            #60a5fa
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    color: #aeb8c8;
    font-size: 18px;
    line-height: 1.6;
}

.card {
    background: rgba(18, 25, 38, 0.95);
    border: 1px solid #29354a;
    border-radius: 28px;
    padding: 30px;
    margin-bottom: 25px;

    box-shadow:
        0 20px 60px rgba(0,0,0,0.35);
}

.upload-area {
    border: 2px dashed #53627c;
    border-radius: 25px;
    padding: 35px 20px;
    text-align: center;
}

.upload-icon {
    font-size: 70px;
    margin-bottom: 15px;
}

.upload-title {
    font-size: 27px;
    font-weight: bold;
    margin-bottom: 10px;
}

.upload-text {
    color: #aeb8c8;
    font-size: 18px;
    margin-bottom: 25px;
    line-height: 1.5;
}

.file-box {
    background: #182231;
    border: 1px solid #35445b;
    border-radius: 15px;
    padding: 14px;
    margin-bottom: 20px;
}

input[type="file"] {
    width: 100%;
    color: white;
    font-size: 16px;
}

.button {
    display: block;
    width: 100%;

    border: 0;
    border-radius: 18px;

    padding: 20px;

    background:
        linear-gradient(
            135deg,
            #6d28d9,
            #7c3aed,
            #8b5cf6
        );

    color: white;

    font-size: 23px;
    font-weight: bold;

    cursor: pointer;

    transition: 0.2s;

    text-decoration: none;
}

.button:hover {
    transform: translateY(-2px);

    box-shadow:
        0 10px 30px rgba(124,58,237,0.35);
}

.features-title {
    font-size: 32px;
    margin-bottom: 22px;
}

.feature {
    background: #172130;
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 15px;
    border: 1px solid #26344a;
}

.feature-icon {
    font-size: 32px;
    float: left;
    margin-right: 14px;
}

.feature h3 {
    margin: 0 0 7px;
    font-size: 22px;
}

.feature p {
    color: #aeb8c8;
    margin: 0;
    line-height: 1.5;
}

.info {
    text-align: center;
    color: #718096;
    font-size: 14px;
    margin-top: 30px;
}

</style>

</head>

<body>

<div class="container">

    <div class="header">

        <div class="logo">🏗️</div>

        <h1>İnşaat AI</h1>

        <div class="subtitle">
            Yapay zekâ destekli otonom
            inşaat proje analiz sistemi
        </div>

    </div>


    <div class="card">

        <div class="upload-area">

            <div class="upload-icon">
                📄
            </div>

            <div class="upload-title">
                Proje dosyanızı yükleyin
            </div>

            <div class="upload-text">
                PDF, JPG/JPEG, PNG veya WEBP proje dosyanızı yükleyin.
                PDF metni çıkarılır; görsel dosyaları görsel analiz
                arayüzüne hazırlanır.
            </div>


            <!--
                ÖNEMLİ:
                Burada JavaScript fetch KULLANILMIYOR.
                Dosya doğrudan sunucuya gönderiliyor.
            -->

            <form
                action="/proje/analiz-et"
                method="post"
                enctype="multipart/form-data"
            >

                <div class="file-box">

                    <input
                        type="file"
                        name="dosya"
                        accept=".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/jpeg,image/png,image/webp"
                        required
                    >

                </div>


                <button
                    type="submit"
                    class="button"
                >
                    🚀 Projeyi Analiz Et
                </button>

            </form>

        </div>

    </div>


    <div class="card">

        <div class="features-title">
            🤖 Sistem Özellikleri
        </div>


        <div class="feature">

            <div class="feature-icon">
                📐
            </div>

            <h3>Metraj</h3>

            <p>
                Projede bulunan ölçü ve miktarları
                analiz eder.
            </p>

        </div>


        <div class="feature">

            <div class="feature-icon">
                🧱
            </div>

            <h3>Malzeme</h3>

            <p>
                Projede kullanılan yapı malzemelerini
                tespit eder.
            </p>

        </div>


        <div class="feature">

            <div class="feature-icon">
                💰
            </div>

            <h3>Maliyet</h3>

            <p>
                Gelecek aşamada malzeme, işçilik,
                nakliye ve diğer maliyetleri hesaplar.
            </p>

        </div>


        <div class="feature">

            <div class="feature-icon">
                🤖
            </div>

            <h3>Otonom Analiz</h3>

            <p>
                Proje sayfalarını otomatik olarak
                sınıflandırır ve analiz eder.
            </p>

        </div>

    </div>


    <div class="info">
        İnşaat AI • Sürüm 0.3.0
    </div>

</div>

</body>

</html>
"""


# ============================================================
# SONUÇ SAYFASI
# ============================================================

def sonuc_sayfasi(
    dosya_adi,
    sonuc,
    analiz
):

    toplam_sayfa = sonuc.get(
        "sayfa_sayisi",
        0
    )

    gorsel_sayfa_sayisi = analiz.get(
        "gorsel_analizi",
        {}
    ).get(
        "girdi_sayfa_sayisi",
        0
    )

    mimari = analiz.get(
        "sayfa_siniflari",
        {}
    ).get(
        "mimari",
        []
    )

    statik = analiz.get(
        "sayfa_siniflari",
        {}
    ).get(
        "statik",
        []
    )

    elektrik = analiz.get(
        "sayfa_siniflari",
        {}
    ).get(
        "elektrik",
        []
    )

    mekanik = analiz.get(
        "sayfa_siniflari",
        {}
    ).get(
        "mekanik",
        []
    )

    diger = analiz.get(
        "sayfa_siniflari",
        {}
    ).get(
        "diger",
        []
    )

    malzemeler = analiz.get(
        "tespit_edilen_malzemeler",
        []
    )

    metrajlar = analiz.get(
        "metrajlar",
        []
    )

    dosya_adi = html.escape(
        str(dosya_adi)
    )


    malzeme_html = ""

    if malzemeler:

        for malzeme in malzemeler:

            malzeme_html += f"""
            <span class="tag">
                {html.escape(str(malzeme))}
            </span>
            """

    else:

        malzeme_html = """
        <span class="muted">
            Henüz malzeme tespit edilmedi.
        </span>
        """


    metraj_html = ""

    if metrajlar:

        for item in metrajlar[:100]:

            malzeme = html.escape(
                str(item.get("malzeme", "-"))
            )

            miktar = html.escape(
                str(item.get("miktar", "-"))
            )

            birim = html.escape(
                str(item.get("birim", "-"))
            )

            sayfa = html.escape(
                str(item.get("sayfa", "-"))
            )

            kaynak = html.escape(
                str(item.get("kaynak", ""))
            )

            metraj_html += f"""
            <tr>

                <td>{malzeme}</td>

                <td>
                    <strong>{miktar}</strong>
                </td>

                <td>{birim}</td>

                <td>{sayfa}</td>

                <td>{kaynak}</td>

            </tr>
            """

    else:

        metraj_html = """
        <tr>
            <td colspan="5">
                Bu PDF'de metin tabanlı ölçü bulunamadı.
            </td>
        </tr>
        """


    return f"""
<!DOCTYPE html>

<html lang="tr">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Proje Analizi - İnşaat AI</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    margin: 0;

    background:
        linear-gradient(
            180deg,
            #080c13,
            #111827
        );

    color: white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

}}

.container {{

    width: 94%;
    max-width: 1000px;

    margin: auto;

    padding: 25px 0 60px;

}}

.card {{

    background: #121a27;

    border: 1px solid #29364a;

    border-radius: 25px;

    padding: 25px;

    margin-bottom: 20px;

}}

h1 {{

    font-size: 34px;

    margin-top: 0;

}}

h2 {{

    font-size: 25px;

}}

.success {{

    background: #102c20;

    border: 1px solid #248957;

    color: #6ee7a0;

    padding: 20px;

    border-radius: 18px;

    font-size: 20px;

    margin-bottom: 20px;

}}

.grid {{

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(140px, 1fr)
        );

    gap: 12px;

}}

.stat {{

    background: #182231;

    border-radius: 17px;

    padding: 20px;

}}

.stat-number {{

    font-size: 32px;

    font-weight: bold;

}}

.stat-label {{

    color: #9ca9bc;

    margin-top: 5px;

}}

.tags {{

    display: flex;

    flex-wrap: wrap;

    gap: 8px;

}}

.tag {{

    background: #312e81;

    color: #ddd6fe;

    padding: 9px 13px;

    border-radius: 30px;

}}

table {{

    width: 100%;

    border-collapse: collapse;

    min-width: 650px;

}}

.table-container {{

    overflow-x: auto;

}}

th,
td {{

    border-bottom: 1px solid #29364a;

    padding: 12px;

    text-align: left;

}}

th {{

    color: #a78bfa;

}}

td {{

    color: #d4dbe7;

}}

.button {{

    display: block;

    width: 100%;

    padding: 18px;

    text-align: center;

    text-decoration: none;

    color: white;

    background: #6d28d9;

    border-radius: 16px;

    font-size: 20px;

    font-weight: bold;

    margin-top: 20px;

}}

.muted {{

    color: #8d99aa;

}}

.warning {{

    background: #30251a;

    border: 1px solid #755322;

    color: #f3c978;

    padding: 15px;

    border-radius: 15px;

    margin-top: 15px;

}}

</style>

</head>

<body>

<div class="container">


<div class="card">

    <div class="success">
        ✅ Proje başarıyla analiz edildi
    </div>

    <h1>
        🏗️ Proje Analiz Raporu
    </h1>

    <p>
        <strong>Dosya:</strong>
        {dosya_adi}
    </p>

</div>


<div class="card">

    <h2>📊 Proje Özeti</h2>

    <div class="grid">

        <div class="stat">

            <div class="stat-number">
                {toplam_sayfa}
            </div>

            <div class="stat-label">
                Toplam Sayfa
            </div>

        </div>


        <div class="stat">

            <div class="stat-number">
                {len(mimari)}
            </div>

            <div class="stat-label">
                Mimari
            </div>

        </div>


        <div class="stat">

            <div class="stat-number">
                {len(statik)}
            </div>

            <div class="stat-label">
                Statik
            </div>

        </div>


        <div class="stat">

            <div class="stat-number">
                {len(elektrik)}
            </div>

            <div class="stat-label">
                Elektrik
            </div>

        </div>


        <div class="stat">

            <div class="stat-number">
                {len(mekanik)}
            </div>

            <div class="stat-label">
                Mekanik
            </div>

        </div>


        <div class="stat">

            <div class="stat-number">
                {len(metrajlar)}
            </div>

            <div class="stat-label">
                Tespit Edilen Ölçü
            </div>

        </div>

    </div>

</div>


<div class="card">

    <h2>🧱 Tespit Edilen Malzemeler</h2>

    <div class="tags">

        {malzeme_html}

    </div>

</div>


<div class="card">

    <h2>📐 Metrajlar</h2>

    <div class="table-container">

        <table>

            <thead>

                <tr>

                    <th>Malzeme</th>
                    <th>Miktar</th>
                    <th>Birim</th>
                    <th>Sayfa</th>
                    <th>Kaynak</th>

                </tr>

            </thead>

            <tbody>

                {metraj_html}

            </tbody>

        </table>

    </div>

</div>


<div class="card">

    <h2>📑 Sayfa Sınıflandırması</h2>

    <p>
        📐 Mimari:
        <strong>{mimari}</strong>
    </p>

    <p>
        🏗️ Statik:
        <strong>{statik}</strong>
    </p>

    <p>
        ⚡ Elektrik:
        <strong>{elektrik}</strong>
    </p>

    <p>
        🔧 Mekanik:
        <strong>{mekanik}</strong>
    </p>

    <p>
        📄 Diğer:
        <strong>{diger}</strong>
    </p>

</div>


<div class="card">

    <h2>🤖 Analiz Durumu</h2>

    <p>
        Sistem yüklenen proje dosyasını başarıyla okudu.
    </p>

    <p>
        Sayfalar sınıflandırıldı ve
        metin içerisindeki malzeme/metraj bilgileri
        tarandı.
    </p>

    <p>
        🖼️ {gorsel_sayfa_sayisi} sayfanın görseli,
        görsel AI entegrasyonuna aktarılmak üzere hazırlandı.
    </p>

<div class="warning">

    <h3>🤖 Görsel AI Analizi</h3>

    <p>
        Görsel AI analiz durumu:
        <strong>
            {analiz.get("gorsel_analizi", {}).get("durum", "bilinmiyor")}
        </strong>
    </p>

    <p>
        Analiz edilen sayfa:
        <strong>
            {analiz.get("gorsel_analizi", {}).get("analiz_edilen_sayfa", 0)}
        </strong>
    </p>

    <p>
        PDF toplam sayfa:
        <strong>
            {analiz.get("gorsel_analizi", {}).get("toplam_pdf_sayfasi", 0)}
        </strong>
    </p>

  </div>

</div>


<a
    href="/"
    class="button"
>
    ← Yeni Proje Analiz Et
</a>


</div>

</body>

</html>
"""


# ============================================================
# ANA SAYFA
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa_route():

    return ana_sayfa()


# ============================================================
# SAĞLIK KONTROLÜ
# ============================================================

@app.get("/health")
async def health():

    return {
        "durum": "çalışıyor",
        "sistem": "İnşaat AI",
        "surum": "0.3.0"
    }


# ============================================================
# TEST
# ============================================================

@app.get("/test")
async def test():

    return {
        "durum": "başarılı",
        "mesaj": "Sunucu cevap veriyor"
    }


# ============================================================
# JSON API - PDF YÜKLE
# ============================================================

@app.post("/proje/yukle")
async def proje_yukle(
    dosya: UploadFile = File(...)
):

    if not dosya.filename:

        raise HTTPException(
            status_code=400,
            detail="Dosya seçilmedi."
        )


    uzanti = os.path.splitext(dosya.filename)[1].lower()
    if uzanti not in DESTEKLENEN_UZANTILAR:

        raise HTTPException(
            status_code=400,
            detail="PDF, JPG/JPEG, PNG veya WEBP dosyaları yüklenebilir."
        )


    gecici_dosya = None


    try:

        # ----------------------------------------------------
        # PDF'Yİ OKU
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=uzanti
        ) as temp:

            gecici_dosya = temp.name

            icerik = await dosya.read()

            temp.write(icerik)


        # ----------------------------------------------------
        # PDF VEYA GÖRSEL ANALİZİ
        # ----------------------------------------------------

        sonuc = proje_dosyasi_oku(
            gecici_dosya,
            dosya.filename
        )


        # ----------------------------------------------------
        # PROJE AJANI
        # ----------------------------------------------------

        analiz = ProjectAgent().analyze(sonuc)

        gorsel_analizi = pdf_gorsel_ai_analiz(gecici_dosya)

        analiz["gorsel_analizi"] = gorsel_analizi


        # ----------------------------------------------------
        # CEVAP
        # ----------------------------------------------------

        return {

            "durum": "başarılı",

            "mesaj":
                "Proje dosyası başarıyla okundu ve analiz edildi.",

            "dosya_adi":
                dosya.filename,

            "sayfa_sayisi":
                sonuc["sayfa_sayisi"],

            "gorsel_analizi":
                analiz.get("gorsel_analizi", {}),

            "analiz":
                analiz

        }


    except Exception as hata:

        raise HTTPException(

            status_code=500,

            detail=
                f"Proje dosyası okunurken hata oluştu: {str(hata)}"

        )


    finally:

        if (
            gecici_dosya
            and os.path.exists(gecici_dosya)
        ):

            os.remove(
                gecici_dosya
            )


# ============================================================
# WEB FORMU - PDF ANALİZ ET
#
# BURADA FETCH YOK.
# TARAYICI DOSYAYI DOĞRUDAN SUNUCUYA GÖNDERİYOR.
# ============================================================

@app.post(
    "/proje/analiz-et",
    response_class=HTMLResponse
)
async def proje_analiz_et(
    dosya: UploadFile = File(...)
):

    if not dosya.filename:

        return HTMLResponse(
            """
            <h2>❌ Dosya seçilmedi.</h2>
            <a href="/">Geri dön</a>
            """,
            status_code=400
        )


    uzanti = os.path.splitext(dosya.filename)[1].lower()
    if uzanti not in DESTEKLENEN_UZANTILAR:

        return HTMLResponse(
            """
            <h2>❌ PDF, JPG/JPEG, PNG veya WEBP dosyaları yüklenebilir.</h2>
            <a href="/">Geri dön</a>
            """,
            status_code=400
        )


    gecici_dosya = None


    try:

        # ----------------------------------------------------
        # GEÇİCİ PDF
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=uzanti
        ) as temp:

            gecici_dosya = temp.name

            icerik = await dosya.read()

            temp.write(icerik)


        # ----------------------------------------------------
        # PDF VEYA GÖRSEL OKUMA
        # ----------------------------------------------------

        sonuc = proje_dosyasi_oku(
            gecici_dosya,
            dosya.filename
        )


        # ----------------------------------------------------
        # AI PROJE ANALİZİ
        # ----------------------------------------------------

        analiz = ProjectAgent().analyze(
            sonuc
        )

        gorsel_analizi = pdf_gorsel_ai_analiz(gecici_dosya)

        analiz["gorsel_analizi"] = gorsel_analizi


        # ----------------------------------------------------
        # RAPOR SAYFASI
        # ----------------------------------------------------

        return sonuc_sayfasi(
            dosya.filename,
            sonuc,
            analiz
        )


    except Exception as hata:

        hata_metni = html.escape(
            str(hata)
        )

        return HTMLResponse(

             f"""
            <!DOCTYPE html>

            <html lang="tr">

            <head>

            <meta charset="UTF-8">

            <meta name="viewport"
                  content="width=device-width,
                           initial-scale=1.0">

            <title>Hata</title>

            <style>

            body {{
                background:#090d14;
                color:white;
                font-family:Arial;
                padding:30px;
            }}

            .error {{
                max-width:700px;
                margin:auto;
                background:#25151a;
                border:1px solid #8b2635;
                border-radius:20px;
                padding:30px;
            }}

            a {{
                color:#a78bfa;
            }}

            </style>

            </head>

            <body>

            <div class="error">

                <h1>❌ Analiz sırasında hata oluştu</h1>

                <p>
                    {hata_metni}
                </p>

                <br>

                <a href="/">
                    ← Ana sayfaya dön
                </a>

            </div>

            </body>

            </html>
            """,

            status_code=500
        )


    finally:

        if (
            gecici_dosya
            and os.path.exists(gecici_dosya)
        ):

            os.remove(
                gecici_dosya
            )
