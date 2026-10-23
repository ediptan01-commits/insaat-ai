from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from servisler.pdf_service import pdf_oku
from servisler.image_service import gorsel_dosyasi_oku
from servisler import quantity_service
from agents.project_agent import ProjectAgent

import tempfile
import os
import html
import json
import asyncio
import re


DESTEKLENEN_UZANTILAR = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MAKS_YUKLEME_BAYT = 50 * 1024 * 1024


async def _yuklemeyi_gecici_dosyaya_yaz(dosya: UploadFile, uzanti: str) -> str:
    """Yüklemeyi belleğe bütünüyle almadan boyut sınırıyla geçici dosyaya yazar."""
    gecici_yol = None
    toplam_bayt = 0
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=uzanti) as temp:
            gecici_yol = temp.name
            while True:
                parca = await dosya.read(1024 * 1024)
                if not parca:
                    break
                toplam_bayt += len(parca)
                if toplam_bayt > MAKS_YUKLEME_BAYT:
                    raise HTTPException(
                        status_code=413,
                        detail="Dosya boyutu 50 MB sınırını aşıyor. Daha küçük bir PDF veya görsel yükleyin.",
                    )
                temp.write(parca)
        if toplam_bayt == 0:
            raise HTTPException(status_code=400, detail="Yüklenen dosya boş.")
        return gecici_yol
    except Exception:
        if gecici_yol and os.path.exists(gecici_yol):
            os.remove(gecici_yol)
        raise


def proje_dosyasi_oku(dosya_yolu: str, dosya_adi: str) -> dict:
    """PDF veya tekil görsel dosyasını ortak proje analiz yapısına dönüştürür."""

    uzanti = os.path.splitext(dosya_adi)[1].lower()
    if uzanti == ".pdf":
        return pdf_oku(dosya_yolu)
    return gorsel_dosyasi_oku(dosya_yolu)


def _fiyat_bolgesini_duzenle(deger: str) -> str:
    """Web fiyat araması için kısa konum alanını güvenli biçimde sınırlar."""
    bolge = str(deger or "").strip()
    if not bolge or len(bolge) > 60:
        return "Türkiye geneli"
    if any(not (karakter.isalpha() or karakter.isspace() or karakter in "-,'’.") for karakter in bolge):
        return "Türkiye geneli"
    return bolge


def _olcu_birimi_varsayimini_duzenle(deger: str) -> str:
    """Birim varsayımını izinli değerlerle sınırlar; varsayılan güvenlidir."""
    secim = str(deger or "belirsiz").strip().lower()
    return secim if secim in {"belirsiz", "cm", "m"} else "belirsiz"


def _kuru_alan_kaplamasini_duzenle(deger: str) -> str:
    secim = str(deger or "laminat").strip().lower()
    return secim if secim in {"laminat", "seramik"} else "laminat"


def _analiz_bilesenlerini_dogrula() -> None:
    beklenen = 2
    ajan_surumu = getattr(ProjectAgent, "ANALIZ_API_SOZLESME_SURUMU", 1)
    metraj_surumu = getattr(quantity_service, "METRAJ_API_SOZLESME_SURUMU", 1)
    if ajan_surumu != beklenen or metraj_surumu != beklenen:
        raise RuntimeError(
            "Sunucudaki uygulama dosyaları farklı sürümlerde. ZIP içindeki main.py, "
            "agents/project_agent.py ve servisler/quantity_service.py dosyalarını birlikte güncelleyip yeniden dağıtın."
        )


# ============================================================
# UYGULAMA
# ============================================================

app = FastAPI(
    title="İnşaat AI",
    description="Otonom inşaat proje metraj ve maliyet analiz sistemi",
    version="0.6.26"
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

.processing-note {
    max-width: 620px;
    margin: -8px auto 20px;
    color: #c3ccda;
    font-size: 13px;
    line-height: 1.5;
    text-align: left;
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

.region-field {
    max-width: 620px;
    margin: 0 auto 18px;
    text-align: left;
}

.region-field label {
    display: block;
    color: #dce4f0;
    font-size: 15px;
    margin-bottom: 8px;
}

.region-field input {
    width: 100%;
    border: 1px solid #35445b;
    border-radius: 12px;
    padding: 13px 15px;
    background: #101a28;
    color: #fff;
    font: inherit;
}

.region-field select {
    width: 100%;
    border: 1px solid #35445b;
    border-radius: 12px;
    padding: 13px 15px;
    background: #101a28;
    color: #fff;
    font: inherit;
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
                En fazla 50 MB dosya kabul edilir.
                Sayfalar incelenir; metraj, yaklaşık malzeme miktarı ve
                seçtiğiniz bölge için kaynaklı fiyat aralığı raporlanır.
            </div>

            <p class="processing-note">
                Görsel inceleme için sayfa görselleri; fiyat araştırması için
                malzeme ve miktar özeti sunucuda yapılandırılan OpenAI API'ye gönderilir.
            </p>


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

                <div class="region-field">
                    <label for="fiyat_bolgesi">Fiyat araştırma bölgesi</label>
                    <input id="fiyat_bolgesi" name="fiyat_bolgesi" type="text"
                           maxlength="60" value="Türkiye geneli"
                           placeholder="Örn. İstanbul, Ankara, İzmir">
                    <small>Fiyatlar bölgeye göre değişebilir. Şehir yazmazsan Türkiye geneli aranır.</small>
                </div>

                <div class="region-field">
                    <label for="kuru_alan_kaplamasi">Kuru odalar için zemin varsayımı</label>
                    <select id="kuru_alan_kaplamasi" name="kuru_alan_kaplamasi">
                        <option value="laminat" selected>Kuru odalarda laminat; mutfak, ıslak hacimler ve balkon seramik</option>
                        <option value="seramik">Bütün odalarda seramik</option>
                    </select>
                    <small>Bu seçim, oda ölçülerinden türetilen yaklaşık metraj varsayımını belirler.</small>
                </div>

                <div class="region-field">
                    <label for="olcu_birimi_varsayimi">Çizimde oda ölçüsünün birimi yazmıyorsa</label>
                    <select id="olcu_birimi_varsayimi" name="olcu_birimi_varsayimi">
                        <option value="belirsiz" selected>Varsayım yapma, ölçüyü dışarıda bırak</option>
                        <option value="cm">cm kabul et (örn. 550 × 260)</option>
                        <option value="m">m kabul et</option>
                    </select>
                    <small>Seçilen varsayıma dayanan metrajlar yaklaşık olarak işaretlenir.</small>
                </div>

                <div class="region-field">
                    <label for="fire_yuzdesi">Kaplama kesim/fire payı (%)</label>
                    <input id="fire_yuzdesi" name="fire_yuzdesi" type="number"
                           min="0" max="25" step="1" value="10">
                </div>

                <div class="region-field">
                    <label for="tavan_yuksekligi">Tavan yüksekliği (m)</label>
                    <input id="tavan_yuksekligi" name="tavan_yuksekligi" type="number"
                           min="2" max="5" step="0.05" value="2.8">
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
                Yazılı metrajları okur; oda alanlarını ve
                yaklaşık kaplama miktarlarını hesaplar.
            </p>

        </div>


        <div class="feature">

            <div class="feature-icon">
                🧱
            </div>

            <h3>Malzeme</h3>

            <p>
                Paftalarda yazılı veya sayılabilen
                malzeme kalemlerini kaynaklarıyla ayırır.
            </p>

        </div>


        <div class="feature">

            <div class="feature-icon">
                💰
            </div>

            <h3>Maliyet</h3>

            <p>
                Kaynaklı güncel birim fiyatlarla
                yaklaşık malzeme maliyeti çıkarır.
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
        İnşaat AI • Sürüm 0.6.10
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

    gorsel_analizi = analiz.get("gorsel_analizi", {})
    gorsel_sayfa_sayisi = gorsel_analizi.get("sayfa_sayisi", 0)
    gorsel_durum = html.escape(str(gorsel_analizi.get("durum", "bilinmiyor")))
    if gorsel_analizi.get("durum") in ("tamamlandi", "kismi_tamamlandi"):
        gorsel_ozet = f"Görsel AI {gorsel_sayfa_sayisi} sayfayı analiz etti."
        islenemeyen_sayfalar = gorsel_analizi.get("islenemeyen_sayfalar", [])
        if islenemeyen_sayfalar:
            atlananlar = ", ".join(str(s) for s in islenemeyen_sayfalar)
            gorsel_ozet += f" {len(islenemeyen_sayfalar)} sayfa analiz dışında kaldı ({atlananlar}); rapor kısmi."
    elif gorsel_analizi.get("durum") == "api_anahtari_eksik":
        gorsel_ozet = "Görsel analiz için sunucu API anahtarı bekleniyor."
        islenemeyen_sayfalar = gorsel_analizi.get("islenemeyen_sayfalar", [])
        if islenemeyen_sayfalar:
            atlananlar = ", ".join(str(s) for s in islenemeyen_sayfalar)
            gorsel_ozet += f" Görsel sınırı veya oluşturma nedeniyle işlenmeyen sayfalar: {atlananlar}."
    elif gorsel_analizi.get("durum") == "pdf_renderer_kurulu_degil":
        gorsel_ozet = "PDF sayfaları görsele çevrilemedi; sunucudaki PyMuPDF kurulumu kontrol edilmeli."
        islenemeyen_sayfalar = gorsel_analizi.get("islenemeyen_sayfalar", [])
        if islenemeyen_sayfalar:
            atlananlar = ", ".join(str(s) for s in islenemeyen_sayfalar)
            gorsel_ozet += f" Etkilenen sayfalar: {atlananlar}."
    elif gorsel_analizi.get("durum") == "gorsel_yok":
        gorsel_ozet = str(gorsel_analizi.get("mesaj", "Görsel AI için işlenebilir sayfa bulunamadı."))
    else:
        gorsel_ozet = "Görsel AI analizi tamamlanamadı; durum aşağıda gösteriliyor."
    gorsel_bulgular = html.escape(json.dumps(
        gorsel_analizi.get("bulgular", gorsel_analizi.get("ham_yanit", gorsel_analizi.get("mesaj", {}))),
        ensure_ascii=False,
        indent=2,
    ))
    gorsel_veri = gorsel_analizi.get("bulgular", {})
    gorsel_oda_satirlari = []
    zemin_notlari = gorsel_veri.get("oda_zemin_kaplamalari", []) if isinstance(gorsel_veri, dict) else []
    if not isinstance(zemin_notlari, list):
        zemin_notlari = []
    oda_norm = lambda deger: re.sub(r"\W+", " ", str(deger or "").casefold()).strip()
    for oda in gorsel_veri.get("odalar", []) if isinstance(gorsel_veri, dict) else []:
        if not isinstance(oda, dict):
            continue
        olcu_metni = oda.get("olcu") or "{} × {} {}".format(
            oda.get("uzunluk", "?"), oda.get("genislik", "?"), oda.get("olcu_birimi", "birim belirsiz")
        )
        eslesen_zeminler = [
            f"{zemin.get('malzeme', '')} — {zemin.get('kaynak_metni', '')}"
            for zemin in zemin_notlari if isinstance(zemin, dict)
            and oda_norm(zemin.get("oda_adi")) == oda_norm(oda.get("ad"))
            and (zemin.get("sayfa") is None or oda.get("sayfa") is None or zemin.get("sayfa") == oda.get("sayfa"))
        ]
        gorsel_oda_satirlari.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(oda.get("ad", "Oda"))),
                html.escape(str(olcu_metni)),
                html.escape(str(oda.get("sayfa") or "Belirtilmedi")),
                html.escape(str(oda.get("olcu_kaynagi", "Görsel AI okuması"))),
                html.escape(" / ".join(eslesen_zeminler) if eslesen_zeminler else "Belirtilmedi"),
            )
        )
    gorsel_odalar_html = "".join(gorsel_oda_satirlari) or (
        '<tr><td colspan="5">Görsel analizinden oda ölçüsü çıkarılamadı.</td></tr>'
    )
    def gorsel_liste_html(alan):
        degerler = gorsel_veri.get(alan, []) if isinstance(gorsel_veri, dict) else []
        if not isinstance(degerler, list):
            return "<li>{}</li>".format(html.escape(str(degerler)))
        return "".join("<li>{}</li>".format(html.escape(str(v))) for v in degerler) or "<li>Belirtilmedi</li>"
    aciklik_satirlari = []
    aciklik_adlari = {
        "ic_kapi": "İç kapı",
        "celik_kapi": "Çelik giriş kapısı",
        "balkon_kapisi": "Balkon kapısı",
        "pencere": "Pencere",
    }
    for aciklik in gorsel_veri.get("aciklar", []) if isinstance(gorsel_veri, dict) else []:
        if not isinstance(aciklik, dict):
            continue
        aciklik_satirlari.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(aciklik_adlari.get(aciklik.get("tur"), str(aciklik.get("tur", "Açıklık")))),
                html.escape(str(aciklik.get("adet", "-"))),
                html.escape(str(aciklik.get("sayfa") or "Belirtilmedi")),
                html.escape(str(aciklik.get("turu_kaynagi", "Görsel AI"))),
            )
        )
    aciklik_html = "".join(aciklik_satirlari) or '<tr><td colspan="4">Güvenilir açıklık sayımı çıkarılamadı.</td></tr>'

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

    metraj_belirsizlik_satirlari = []
    for belirsizlik in analiz.get("metraj_belirsizlikleri", []):
        sayfa = f"Sayfa {belirsizlik.get('sayfa')}: " if belirsizlik.get("sayfa") else ""
        adaylar = ", ".join(str(aday) for aday in belirsizlik.get("aday_malzemeler", []))
        metraj_belirsizlik_satirlari.append(
            "<li><strong>{}</strong>{} <em>{}</em> — {}</li>".format(
                html.escape(sayfa),
                html.escape(str(belirsizlik.get("kaynak", ""))),
                html.escape(adaylar),
                html.escape(str(belirsizlik.get("neden", "Miktar netleştirilmeli."))),
            )
        )
    metraj_belirsizlik_html = "".join(metraj_belirsizlik_satirlari) or "<li>Belirsiz metraj satırı yok.</li>"

    miktar_analizi = analiz.get("malzeme_miktarlari", {})
    def metraj_dayanagi_html(kalem):
        cubuklar = kalem.get("kaynak_donati_cubuklari") or []
        if cubuklar:
            satirlar = []
            for cubuk in cubuklar:
                satir = [f"Ø{cubuk.get('cap_mm', '?')} mm"]
                if cubuk.get("sayfa") is not None:
                    satir.append(f"Sayfa {cubuk['sayfa']}")
                if cubuk.get("adet") is not None and cubuk.get("boy_m") is not None:
                    satir.append(f"{cubuk['adet']} × {cubuk['boy_m']} m")
                else:
                    satir.append(f"Toplam boy {cubuk.get('toplam_boy_m', '?')} m")
                satir.append(f"{cubuk.get('kg_metre', '?')} kg/m × {cubuk.get('toplam_boy_m', '?')} m = {cubuk.get('agirlik_kg', '?')} kg")
                satir.append(str(cubuk.get("kaynak_metni", "")))
                satirlar.append("<br>".join(html.escape(deger) for deger in satir))
            return "<br>".join(satirlar)
        bilesenler = kalem.get("kaynak_bilesenler") or []
        if bilesenler:
            satirlar = []
            for bilesen in bilesenler:
                satir = [str(bilesen.get("tur", "eleman")).title()]
                if bilesen.get("sayfa") is not None:
                    satir.append(f"Sayfa {bilesen['sayfa']}")
                satir.append(
                    f"{bilesen.get('adet', '?')} × {bilesen.get('boy_m', '?')} × "
                    f"{bilesen.get('en_m', '?')} × {bilesen.get('kalinlik_m', '?')} m"
                )
                satir.append(f"{bilesen.get('hacim_m3', '?')} m³")
                satir.append(str(bilesen.get("kaynak_metni", "")))
                satirlar.append("<br>".join(html.escape(deger) for deger in satir))
            return "<br>".join(satirlar)
        odalar = kalem.get("kaynak_odalar") or []
        if odalar:
            satirlar = []
            for oda in odalar:
                parcalar = [str(oda.get("ad") or "Oda")]
                if oda.get("sayfa") is not None:
                    parcalar.append(f"Sayfa {oda['sayfa']}")
                if oda.get("alan_m2") is not None:
                    parcalar.append(f"{oda['alan_m2']} m²")
                if oda.get("olcu_metni"):
                    parcalar.append(f"ölçü: {oda['olcu_metni']}")
                if oda.get("olcu_notu"):
                    parcalar.append(str(oda["olcu_notu"]))
                if oda.get("zemin_kaplama"):
                    parcalar.append(f"Zemin: {oda['zemin_kaplama']}")
                if oda.get("zemin_kaplama_kaynagi"):
                    parcalar.append(str(oda["zemin_kaplama_kaynagi"]))
                satirlar.append("<br>".join(html.escape(parca) for parca in parcalar))
            teknik_url = kalem.get("teknik_kaynagi_url")
            if teknik_url:
                satirlar.append(
                    '<a href="{}" target="_blank" rel="noopener noreferrer">Üretici teknik föyü</a>'.format(
                        html.escape(str(teknik_url), quote=True)
                    )
                )
            return "<br>".join(satirlar)
        sayfa = f"Sayfa {kalem.get('sayfa')}: " if kalem.get("sayfa") else ""
        kaynak = kalem.get("kaynak_metni") or kalem.get("kaynak") or ""
        return html.escape(sayfa + str(kaynak)) or "Kaynak bilgisi yok"

    miktar_satirlari = []
    for kalem in miktar_analizi.get("malzeme_miktarlari", []):
        gosterilen_miktar = kalem.get("miktar", "-")
        if kalem.get("miktar_min") is not None and kalem.get("miktar_max") is not None:
            gosterilen_miktar = f"{kalem['miktar_min']}–{kalem['miktar_max']}"
        miktar_satirlari.append(
            "<tr><td>{}</td><td><strong>{}</strong></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(kalem.get("malzeme", "-"))),
                html.escape(str(gosterilen_miktar)),
                html.escape(str(kalem.get("birim", "-"))),
                ("Öngörülen miktar" if kalem.get("tahmin") else "Belgede yazılı miktar")
                + (f" • güven: {kalem['guven']}" if kalem.get("guven") else ""),
                metraj_dayanagi_html(kalem),
            )
        )
    miktar_html = "".join(miktar_satirlari) or (
        '<tr><td colspan="5">Oda ölçüleri yeterli olmadığı için miktar çıkarılamadı.</td></tr>'
    )
    oda_alan_satirlari = []
    for oda in miktar_analizi.get("oda_alanlari", []):
        olcu_notu = oda.get("olcu_notu") or oda.get("olcu_kaynagi") or "Ölçü bilgisi"
        oda_alan_satirlari.append(
            "<tr><td>{}</td><td>{} × {} m</td><td>{} m²</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(oda.get("ad", "Oda"))),
                html.escape(str(oda.get("uzunluk_m", "-"))),
                html.escape(str(oda.get("genislik_m", "-"))),
                html.escape(str(oda.get("alan_m2", "-"))),
                html.escape(str(oda.get("sayfa") or "Belirtilmedi")),
                html.escape(str(oda.get("zemin_kaplama", "belirsiz"))),
                html.escape(str(olcu_notu)),
            )
        )
    oda_alan_html = "".join(oda_alan_satirlari) or '<tr><td colspan="6">Alan hesabına uygun oda ölçüsü yok.</td></tr>'
    varsayim_html = "".join(
        f"<li>{html.escape(str(madde))}</li>"
        for madde in miktar_analizi.get("varsayimlar", [])
    )
    kapsam_disi_html = "".join(
        f"<li>{html.escape(str(madde))}</li>"
        for madde in miktar_analizi.get("kapsam_disi", [])
    )
    atlanan_oda_html = "".join(
        f"<li>{html.escape(str(oda))}</li>"
        for oda in miktar_analizi.get("hesaplanamayan_odalar", [])
    ) or "<li>Hesap dışında bırakılan oda yok.</li>"
    atlanan_yapisal_html = "".join(
        f"<li>{html.escape(str(eleman))}</li>"
        for eleman in miktar_analizi.get("hesaplanamayan_yapisal_elemanlar", [])
    ) or "<li>Çift sayımı önlemek için dışarıda bırakılan yapısal hacim yok.</li>"
    atlanan_donati_html = "".join(
        f"<li>{html.escape(str(cubuk))}</li>"
        for cubuk in miktar_analizi.get("hesaplanamayan_donati_cubuklari", [])
    ) or "<li>Çift sayımı önlemek için dışarıda bırakılan donatı çizelgesi satırı yok.</li>"
    maliyet_analizi = analiz.get("maliyet_analizi", {})
    maliyet_satirlari = []
    for kalem in maliyet_analizi.get("kalemler", []):
        kalem_adi = html.escape(str(kalem.get("malzeme", "-")))
        gosterilen_miktar = kalem.get("miktar", "-")
        if kalem.get("miktar_min") is not None and kalem.get("miktar_max") is not None:
            gosterilen_miktar = f"{kalem['miktar_min']}–{kalem['miktar_max']}"
        if kalem.get("tahmin"):
            kalem_adi += " (öngörülen miktar)"
        if kalem.get("fiyat_durumu") != "kaynakli_web_fiyati":
            fiyat_mesajlari = {
                "api_anahtari_eksik": "Fiyat araştırması için OPENAI_API_KEY tanımlı değil",
                "fiyat_arama_hatasi": "Fiyat araştırma servisine ulaşılamadı",
                "kaynak_veya_birim_fiyat_dogrulanamadi": "Kaynak veya birim fiyat doğrulanamadı",
                "urun_tanimi_eksik": "Ürün tipi veya teknik özellikleri eksik; yanıltıcı fiyat eklenmedi",
            }
            fiyat_mesaji = fiyat_mesajlari.get(
                kalem.get("fiyat_durumu"),
                "Uyumlu, doğrulanabilir fiyat kaynağı bulunamadı",
            )
            fiyat_mesaji = kalem.get("fiyat_dogrulama_notu", fiyat_mesaji)
            maliyet_satirlari.append(
                "<tr><td>{}</td><td>{} {}</td><td>{}</td><td colspan=\"3\">{}</td></tr>".format(
                    kalem_adi,
                    html.escape(str(gosterilen_miktar)),
                    html.escape(str(kalem.get("birim", "-"))),
                    metraj_dayanagi_html(kalem),
                    html.escape(fiyat_mesaji),
                )
            )
            continue
        kaynaklar = "<br>".join(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a> — ₺{} / {}'.format(
                html.escape(str(kaynak.get("url", "")), quote=True),
                html.escape(str(kaynak.get("ad") or kaynak.get("url", "Kaynak"))),
                html.escape(str(kaynak.get("görülen_fiyat", "-"))),
                html.escape(str(kalem.get("birim", ""))),
            )
            for kaynak in kalem.get("kaynaklar", [])
        ) or "Kaynak bağlantısı yok"
        birim_fiyat_min = f"{kalem['min_birim_fiyat_try']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        birim_fiyat_max = f"{kalem['max_birim_fiyat_try']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if kalem.get("fiyat_kaynak_sayisi") == 1:
            birim_fiyat_html = f"₺{birim_fiyat_min} (tek kaynak)"
            kaynaklar += "<br><small>Tek bağımsız fiyat kaynağı; aralık değildir.</small>"
        else:
            birim_fiyat_html = f"₺{birim_fiyat_min}–₺{birim_fiyat_max}"
        maliyet_satirlari.append(
            "<tr><td>{}</td><td>{} {}</td><td>{}</td><td>{}</td><td>₺{}–₺{}</td><td>{}<br><small>KDV: {}</small></td></tr>".format(
                kalem_adi,
                html.escape(str(gosterilen_miktar)),
                html.escape(str(kalem.get("birim", "-"))),
                metraj_dayanagi_html(kalem),
                birim_fiyat_html,
                f"{kalem['min_tutar_try']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"{kalem['max_tutar_try']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                kaynaklar,
                html.escape(str(kalem.get("kdv_durumu", "belirtilmemiş"))),
            )
        )
    maliyet_html = "".join(maliyet_satirlari) or (
        '<tr><td colspan="6">Fiyat araştırması için hesaplanabilir malzeme miktarı yok.</td></tr>'
    )
    maliyet_durum = html.escape(str(maliyet_analizi.get("durum", "fiyat_bekliyor")))
    maliyet_bolge = html.escape(str(maliyet_analizi.get("bolge", "Türkiye geneli")))
    fiyat_hatalari = maliyet_analizi.get("fiyat_arama_hatalari", [])
    fiyat_hatasi_html = "".join(
        f"<li>{html.escape(str(hata.get('mesaj', 'Bilinmeyen fiyat arama hatası')))}</li>"
        for hata in fiyat_hatalari
        if isinstance(hata, dict)
    )
    fiyatlanan_kalem_sayisi = maliyet_analizi.get("fiyatlanan_kalem_sayisi", 0)
    toplam_fiyat_kalemi = maliyet_analizi.get("toplam_kalem_sayisi", 0)
    fiyat_kapsami = (
        f"{fiyatlanan_kalem_sayisi}/{toplam_fiyat_kalemi} malzeme satırı (%{maliyet_analizi.get('fiyat_kapsam_yuzdesi', 0)})"
        if toplam_fiyat_kalemi
        else "Fiyatlanabilir malzeme satırı yok"
    )
    toplam_min = maliyet_analizi.get("toplam_min_try")
    toplam_max = maliyet_analizi.get("toplam_max_try")
    if toplam_min is not None and toplam_max is not None:
        toplam_maliyet_html = "₺{}–₺{}".format(
            f"{toplam_min:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            f"{toplam_max:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        )
    else:
        toplam_maliyet_html = "Kaynaklı fiyat bulunamadı"
    def fiyat_araligi_html(minimum, maksimum):
        if minimum is None or maksimum is None:
            return "—"
        return "₺{}–₺{}".format(
            f"{minimum:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            f"{maksimum:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        )
    belge_miktari_toplami = fiyat_araligi_html(
        maliyet_analizi.get("belgede_yazili_miktar_toplam_min_try"),
        maliyet_analizi.get("belgede_yazili_miktar_toplam_max_try"),
    )
    ongoru_miktari_toplami = fiyat_araligi_html(
        maliyet_analizi.get("ongorulen_miktar_toplam_min_try"),
        maliyet_analizi.get("ongorulen_miktar_toplam_max_try"),
    )
    maliyet_tarihi = html.escape(str(maliyet_analizi.get("fiyat_referans_tarihi", "")))


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

@page {{
    size: A4 landscape;
    margin: 12mm;
}}

@media print {{
    body {{ background: #fff !important; color: #111 !important; }}
    .container {{ width: 100%; max-width: none; padding: 0; margin: 0; }}
    .card {{ background: #fff !important; color: #111 !important; border: 1px solid #aaa; border-radius: 0; box-shadow: none; }}
    h1, h2, h3, p, li, td, th, strong, .success, .warning {{ color: #111 !important; }}
    .success, .warning {{ background: #fff !important; border-color: #888; }}
    .no-print {{ display: none !important; }}
    .table-container {{ overflow: visible; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
    th, td {{ border: 1px solid #777; padding: 4px; overflow-wrap: anywhere; }}
    tr, h2, h3 {{ break-inside: avoid; page-break-inside: avoid; }}
    a {{ color: #111 !important; overflow-wrap: anywhere; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
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

    <button class="button no-print" type="button" onclick="window.print()">
        Raporu yazdır / PDF olarak kaydet
    </button>

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

    <h2>🏠 AI Tarafından Okunan Mekânlar</h2>
    <p>Çizim türü: <strong>{html.escape(str(gorsel_veri.get('cizim_turu', 'Belirlenemedi') if isinstance(gorsel_veri, dict) else 'Belirlenemedi'))}</strong></p>
    <div class="table-container">
        <table>
            <thead><tr><th>Mekân</th><th>Çizimde okunan ölçü</th><th>Sayfa</th><th>Ölçü kaynağı</th><th>Paftadaki kaplama notu</th></tr></thead>
            <tbody>{gorsel_odalar_html}</tbody>
        </table>
    </div>
    <h3>Çizimde belirtilen malzemeler</h3><ul>{gorsel_liste_html('malzemeler')}</ul>
    <h3>Kapı ve pencere sayımları</h3>
    <div class="table-container">
        <table><thead><tr><th>Tür</th><th>Adet</th><th>Sayfa</th><th>Kaynak türü</th></tr></thead><tbody>{aciklik_html}</tbody></table>
    </div>
    <div class="grid">
        <div><h3>Kapılar</h3><ul>{gorsel_liste_html('kapilar')}</ul></div>
        <div><h3>Pencereler</h3><ul>{gorsel_liste_html('pencereler')}</ul></div>
    </div>
    <h3>Belirsizlikler</h3><ul>{gorsel_liste_html('belirsizlikler')}</ul>
    <details><summary>Ham AI bulguları</summary><pre style="white-space: pre-wrap; overflow-wrap: anywhere;">{gorsel_bulgular}</pre></details>

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

    <h3>Metrajda belirsiz satırlar</h3>
    <p>Bir satır birden fazla malzemeyle eşleşirse aynı miktarı iki kez fiyatlandırmamak için otomatik toplama alınmaz.</p>
    <ul>{metraj_belirsizlik_html}</ul>

</div>


<div class="card">

    <h2>🧮 Yaklaşık Malzeme Miktarları</h2>
    <p>Hesap durumu: <strong>{html.escape(str(miktar_analizi.get('durum', 'hesaplanamadi')))}</strong></p>
    <div class="table-container">
        <table>
            <thead><tr><th>Malzeme</th><th>Miktar</th><th>Birim</th><th>Tür</th><th>Hesabın dayanağı</th></tr></thead>
            <tbody>{miktar_html}</tbody>
        </table>
    </div>
    <h3>Oda alanı hesabı</h3>
    <div class="table-container">
        <table>
            <thead><tr><th>Mekân</th><th>Boyut</th><th>Alan</th><th>Sayfa</th><th>Zemin kaplama</th><th>Ölçü notu</th></tr></thead>
            <tbody>{oda_alan_html}</tbody>
        </table>
    </div>
    <h3>Metraja alınmayan odalar</h3>
    <p>Ölçüsü, birimi veya kaplaması doğrulanmayan ve yazılı metrajla çakışabilecek oda alanları ilgili varsayımsal toplamdan çıkarıldı.</p>
    <ul>{atlanan_oda_html}</ul>
    <h3>Yapısal hacim doğrulama notları</h3>
    <ul>{atlanan_yapisal_html}</ul>
    <h3>Donatı doğrulama notları</h3>
    <ul>{atlanan_donati_html}</ul>
    <h3>Hesap varsayımları</h3>
    <ul>{varsayim_html}</ul>
    <h3>Bu çizimden hesaplanamayanlar</h3>
    <ul>{kapsam_disi_html}</ul>

</div>


<div class="card">

    <h2>💰 Güncel Fiyatlarla Yaklaşık Malzeme Maliyeti</h2>
    <p>Fiyat araştırma durumu: <strong>{maliyet_durum}</strong></p>
    <p>Fiyat bölgesi: <strong>{maliyet_bolge}</strong> {f'• Referans tarihi: {maliyet_tarihi}' if maliyet_tarihi else ''}</p>
    <p>Fiyat kapsamı: <strong>{html.escape(fiyat_kapsami)}</strong></p>
    {f'<p class="muted">Fiyat sağlayıcısı yanıtı:<ul>{fiyat_hatasi_html}</ul></p>' if fiyat_hatasi_html else ''}
    <p>Kaynaklı kalemlerin yaklaşık toplamı: <strong>{toplam_maliyet_html}</strong></p>
    <p>Miktar türüne göre: belgede yazılı <strong>{belge_miktari_toplami}</strong> • öngörülen <strong>{ongoru_miktari_toplami}</strong></p>
    <div class="table-container">
        <table>
            <thead><tr><th>Malzeme</th><th>Miktar</th><th>Metraj dayanağı</th><th>Birim fiyat aralığı</th><th>Kalem tutarı</th><th>Fiyat kaynakları</th></tr></thead>
            <tbody>{maliyet_html}</tbody>
        </table>
    </div>
    <p>{html.escape(str(maliyet_analizi.get('kapsam_notu', 'Toplam yaklaşık bir piyasa göstergesidir; teklif değildir.')))}</p>
    <div class="warning">Bu yaklaşık ön maliyet, araştırmada karşılaştırılabilir fiyatı bulunan kalemleri kapsar. İşçilik, nakliye, vergi belirsizliği, bölgesel fark ve çizimde yer almayan işler ayrıca değerlendirilmelidir.</div>

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
        {gorsel_ozet}
    </p>

    <p>Görsel analiz durumu: <strong>{gorsel_durum}</strong></p>
    <p>Güncel fiyat araştırması durumu: <strong>{maliyet_durum}</strong></p>

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
        "surum": "0.6.26",
        "analiz_bilesenleri_uyumlu": (
            getattr(ProjectAgent, "ANALIZ_API_SOZLESME_SURUMU", 1) == 2
            and getattr(quantity_service, "METRAJ_API_SOZLESME_SURUMU", 1) == 2
        )
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
    dosya: UploadFile = File(...),
    fiyat_bolgesi: str = Form("Türkiye geneli"),
    fire_yuzdesi: float = Form(10, ge=0, le=25),
    tavan_yuksekligi: float = Form(2.8, ge=2, le=5),
    olcu_birimi_varsayimi: str = Form("belirsiz"),
    kuru_alan_kaplamasi: str = Form("laminat"),
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

        _analiz_bilesenlerini_dogrula()

        gecici_dosya = await _yuklemeyi_gecici_dosyaya_yaz(dosya, uzanti)


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

        fiyat_bolgesi = _fiyat_bolgesini_duzenle(fiyat_bolgesi)
        olcu_birimi_varsayimi = _olcu_birimi_varsayimini_duzenle(olcu_birimi_varsayimi)
        kuru_alan_kaplamasi = _kuru_alan_kaplamasini_duzenle(kuru_alan_kaplamasi)
        analiz = await asyncio.to_thread(
            ProjectAgent().analyze, sonuc, fiyat_bolgesi, fire_yuzdesi, tavan_yuksekligi, olcu_birimi_varsayimi, kuru_alan_kaplamasi
        )


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

            "malzeme_miktarlari":
                analiz.get("malzeme_miktarlari", {}),

            "maliyet_analizi":
                analiz.get("maliyet_analizi", {}),

            "analiz":
                analiz

        }


    except HTTPException:
        raise

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
    dosya: UploadFile = File(...),
    fiyat_bolgesi: str = Form("Türkiye geneli"),
    fire_yuzdesi: float = Form(10, ge=0, le=25),
    tavan_yuksekligi: float = Form(2.8, ge=2, le=5),
    olcu_birimi_varsayimi: str = Form("belirsiz"),
    kuru_alan_kaplamasi: str = Form("laminat"),
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

        _analiz_bilesenlerini_dogrula()

        gecici_dosya = await _yuklemeyi_gecici_dosyaya_yaz(dosya, uzanti)


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

        fiyat_bolgesi = _fiyat_bolgesini_duzenle(fiyat_bolgesi)
        olcu_birimi_varsayimi = _olcu_birimi_varsayimini_duzenle(olcu_birimi_varsayimi)
        kuru_alan_kaplamasi = _kuru_alan_kaplamasini_duzenle(kuru_alan_kaplamasi)
        analiz = await asyncio.to_thread(
            ProjectAgent().analyze, sonuc, fiyat_bolgesi, fire_yuzdesi, tavan_yuksekligi, olcu_birimi_varsayimi, kuru_alan_kaplamasi
        )


        # ----------------------------------------------------
        # RAPOR SAYFASI
        # ----------------------------------------------------

        return sonuc_sayfasi(
            dosya.filename,
            sonuc,
            analiz
        )


    except Exception as hata:

        hata_durumu = hata.status_code if isinstance(hata, HTTPException) else 500
        hata_mesaji = hata.detail if isinstance(hata, HTTPException) else str(hata)

        hata_metni = html.escape(
            str(hata_mesaji)
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

            status_code=hata_durumu
        )


    finally:

        if (
            gecici_dosya
            and os.path.exists(gecici_dosya)
        ):

            os.remove(
                gecici_dosya
            )
