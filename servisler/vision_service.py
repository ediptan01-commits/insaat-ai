"""OpenAI Responses API ile proje sayfalarının görsel analiz adaptörü."""
import json
import os
import urllib.error
import urllib.request

MODEL_VARSAYILAN = "gpt-4.1-mini"
SAYFA_PARTI_BOYUTU = 8
VARSAYILAN_MAKS_SAYFA = 40

def _yanit_metni(response):
    parcalar = []
    for item in response.get("output", []):
        if item.get("type") == "message":
            parcalar.extend(c.get("text", "") for c in item.get("content", []) if c.get("type") == "output_text")
    return "\n".join(parcalar).strip()

def _json_bulgularini_coz(metin):
    """JSON nesnesini düz, code-fence ve JSON-string biçimlerinden çıkarır."""
    aday = metin.strip()
    for _ in range(3):
        if aday.startswith("```"):
            satirlar = aday.splitlines()
            if satirlar and satirlar[0].startswith("```"):
                satirlar = satirlar[1:]
            if satirlar and satirlar[-1].strip() == "```":
                satirlar = satirlar[:-1]
            aday = "\n".join(satirlar).strip()
        try:
            cozulen = json.loads(aday)
        except json.JSONDecodeError:
            bas = aday.find("{")
            son = aday.rfind("}")
            if bas < 0 or son <= bas:
                return None
            try:
                cozulen = json.loads(aday[bas:son + 1])
            except json.JSONDecodeError:
                return None
        if isinstance(cozulen, dict):
            return cozulen
        if isinstance(cozulen, str):
            aday = cozulen.strip()
            continue
        return None
    return None

def gorsel_ai_analiz(project_data):
    gorsel_girdisi = project_data.get("gorsel_analiz_girdisi", {})
    sayfalar = gorsel_girdisi.get("sayfalar", [])
    onceden_atlanan_sayfalar = gorsel_girdisi.get("atlanmis_sayfalar", [])
    render_edilemeyen = [
        s.get("sayfa") for s in project_data.get("sayfalar", [])
        if s.get("gorsel", {}).get("durum") != "hazir"
    ]
    if not sayfalar:
        renderer_eksik = any(
            s.get("gorsel", {}).get("hata_kodu") == "pdf_renderer_kurulu_degil"
            for s in project_data.get("sayfalar", [])
        )
        return {
            "durum": "pdf_renderer_kurulu_degil" if renderer_eksik else "gorsel_yok",
            "sayfa_sayisi": 0,
            "islenemeyen_sayfalar": sorted(set(render_edilemeyen + onceden_atlanan_sayfalar)),
            "mesaj": (
                "PDF sayfaları görüntüye çevrilemedi. Sunucuda PyMuPDF bağımlılığının kurulu olduğunu kontrol edin."
                if renderer_eksik
                else "Görsel AI için işlenebilir sayfa görseli yok."
            ),
        }
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "durum": "api_anahtari_eksik",
            "sayfa_sayisi": len(sayfalar),
            "islenemeyen_sayfalar": sorted(set(render_edilemeyen + onceden_atlanan_sayfalar)),
            "atlanmis_sayfa_sayisi": len(set(render_edilemeyen + onceden_atlanan_sayfalar)),
            "mesaj": "Görsel AI için sunucuda OPENAI_API_KEY tanımlanmalıdır.",
        }

    try:
        sayfa_limiti = max(1, int(os.getenv("MAX_VISION_PAGES", VARSAYILAN_MAKS_SAYFA)))
    except ValueError:
        sayfa_limiti = VARSAYILAN_MAKS_SAYFA
    secilenler = sayfalar[:sayfa_limiti]
    atlanan = sayfalar[len(secilenler):]
    ortak_talimat = (
        "Bu görseller inşaat projesi paftalarıdır. Türkçe yanıt ver ve yalnızca JSON döndür. "
        "Şema: {\"cizim_turu\": string, \"sayfalar\": [{\"sayfa\": number, \"cizim_turu\": string, "
        "\"disiplin\": \"mimari\"|\"statik\"|\"elektrik\"|\"mekanik\"|\"diger\"}], "
        "\"odalar\": [{\"sayfa\": number|null, \"ad\": string, \"olcu\": string|null, "
        "\"uzunluk\": number|null, \"genislik\": number|null, "
        "\"olcu_birimi\": \"m\"|\"cm\"|\"mm\"|\"belirsiz\", "
        "\"olcu_kaynagi\": \"cizimde_yazili\"|\"tahmini\"|\"belirsiz\"}], "
        "\"olculer\": [string], \"kapilar\": [string], \"pencereler\": [string], "
        "\"malzemeler\": [string], \"oda_zemin_kaplamalari\": [{\"sayfa\": number|null, \"oda_adi\": string, \"malzeme\": string, \"kaynak_metni\": string}], "
        "\"acik_metrajlar\": [{\"sayfa\": number|null, "
        "\"malzeme\": string, \"miktar\": number, \"birim\": string, "
        "\"kaynak_metni\": string, \"guven\": \"yuksek\"|\"orta\"|\"dusuk\", "
        "\"turu\": \"cizimde_yazili\"|\"gorselde_sayim\"}], "
        "\"tasiyici_elemanlar\": [{\"sayfa\": number|null, \"tur\": \"kolon\"|\"kiris\"|\"temel\"|\"doseme\", "
        "\"adet\": number|null, \"boy\": number|null, \"en\": number|null, \"kalinlik\": number|null, "
        "\"olcu_birimi\": \"m\"|\"cm\"|\"mm\"|\"belirsiz\", \"beton_sinifi\": string|null, "
        "\"kaynak_metni\": string, \"guven\": \"yuksek\"|\"orta\"|\"dusuk\"}], "
        "\"donati_cubuklari\": [{\"sayfa\": number|null, \"cap_mm\": number|null, \"adet\": number|null, "
        "\"boy_m\": number|null, \"toplam_boy_m\": number|null, \"celik_sinifi\": string|null, "
        "\"kaynak_metni\": string, \"guven\": \"yuksek\"|\"orta\"|\"dusuk\"}], "
        "\"aciklar\": [{\"sayfa\": number|null, \"tur\": \"ic_kapi\"|\"celik_kapi\"|\"balkon_kapisi\"|\"pencere\", "
        "\"adet\": number, \"olcu\": string|null, \"kaynak_metni\": string, "
        "\"guven\": \"yuksek\"|\"orta\"|\"dusuk\", \"turu_kaynagi\": \"cizelgede_yazili\"|\"gorselde_sayim\"}], "
        "\"belirsizlikler\": [string]}. Okunmayan ölçüyü tahmin etme. "
        "Uzunluk/genişliği çizimdeki birimde yaz; birim görünmüyorsa belirsiz seç. "
        "Her fiziksel mekânı yalnızca bir kez yaz; aynı odayı farklı adlarla tekrarlama. "
        "Yalnızca paftada açıkça belirtilen oda zemin kaplamalarını oda_zemin_kaplamalari listesine ekle; "
        "oda_adi odalar listesindeki adla aynı olsun, malzeme ve kısa kaynak_metni çizimdeki not/mahal listesinden gelsin. "
        "Ölçek, görünüş veya genel renk izleniminden zemin kaplaması çıkarma; oda için açık kaplama notu yoksa satır ekleme. "
        "Ölçü çizimde okunmuyorsa sayı uydurma, null yaz. "
        "Malzeme miktarını yalnızca çizimdeki açık metraj/poz satırından oku; kısa kaynak metnini aynen yaz ve turu cizimde_yazili yap. "
        "Açık miktar yok ama elemanları gerçekten sayabiliyorsan yalnız adet cinsinden gorselde_sayim olarak ekle; "
        "tahmini uzunluk, alan, ağırlık veya hacim uydurma. Sayfa numarası yükleme sırasındaki gerçek sayfa numarasıdır. "
        "Kapı/pencere çizelgesindeki adetleri veya planda ayırt edilebilir açıklık sembollerini aciklar listesine ekle. "
        "Malzemesi/tipi belirsiz doğramayı çelik kapı ya da PVC diye varsayma; genel pencere/kapı türü kullan. "
        "Çizelgede yazılı adet için kısa kaynak satırı ve cizelgede_yazili; plandan sembol sayımı için gorselde_sayim yaz. "
        "Taşıyıcı elemanları yalnızca açık ölçü/adet çizelgesinden oku; boy, en, kalınlık ve adet alanlarının hepsi çizimde okunmuyorsa ekleme. "
        "Kolonda boy=kat yüksekliği, kirişte boy=açıklık uzunluğu, temelde boy=temel uzunluğu, döşemede boy=kenar uzunluğu anlamındadır. "
        "Ölçekten boyut, plandaki işaretlerden adet veya donatıdan beton hacmi çıkarma; beton sınıfını yalnızca yazıyorsa belirt. "
        "Donatı çubuklarını yalnızca donatı/çubuk büküm çizelgesinden oku; çap, adet ve tekil boy veya yazılı toplam boy açık değilse ekleme. "
        "Çubuk sayısını plandaki çizgilerden sayma, büküm/ankraj boyu uydurma ve donatı kg miktarını tahmin etme; kaynağı ve çapı koru. "
        "Bu bir ön incelemedir; uygulama hesabı veya mühendislik onayı verme."
    )
    birlesik = {"sayfalar": [], "odalar": [], "olculer": [], "kapilar": [], "pencereler": [], "malzemeler": [], "oda_zemin_kaplamalari": [], "acik_metrajlar": [], "tasiyici_elemanlar": [], "donati_cubuklari": [], "aciklar": [], "belirsizlikler": []}
    basarili_partiler = 0
    hata_partileri = []
    for baslangic in range(0, len(secilenler), SAYFA_PARTI_BOYUTU):
        parti = secilenler[baslangic:baslangic + SAYFA_PARTI_BOYUTU]
        icerik = [{"type": "input_text", "text": ortak_talimat}]
        for sayfa in parti:
            icerik.extend([
                {"type": "input_text", "text": f"Sayfa {sayfa.get('sayfa', '?')}:"},
                {"type": "input_image", "image_url": sayfa["veri_url"], "detail": "high"},
            ])
        payload = {
            "model": os.getenv("OPENAI_VISION_MODEL", MODEL_VARSAYILAN),
            "input": [{"role": "user", "content": icerik}],
            "max_output_tokens": 5000,
            "text": {"format": {"type": "json_object"}},
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses", data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            hata_partileri.append({"sayfalar": [s.get("sayfa") for s in parti], "mesaj": f"HTTP {error.code}"})
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            hata_partileri.append({"sayfalar": [s.get("sayfa") for s in parti], "mesaj": "Servis hatası veya geçersiz yanıt"})
            continue
        bulgular = _json_bulgularini_coz(_yanit_metni(result))
        if bulgular is None:
            hata_partileri.append({"sayfalar": [s.get("sayfa") for s in parti], "mesaj": "AI yanıtı çözümlenemedi"})
            continue
        basarili_partiler += 1
        for anahtar, deger in bulgular.items():
            if anahtar in birlesik and isinstance(deger, list):
                birlesik[anahtar].extend(deger)
            elif anahtar not in birlesik or not birlesik[anahtar]:
                birlesik[anahtar] = deger

    if not basarili_partiler:
        return {
            "durum": "gorsel_ai_hatasi" if hata_partileri else "gorsel_yok",
            "sayfa_sayisi": 0,
            "islenemeyen_sayfalar": [s for hata in hata_partileri for s in hata["sayfalar"]],
            "mesaj": hata_partileri[0]["mesaj"] if hata_partileri else "Görsel girdisi yok.",
        }
    for anahtar in ("sayfalar", "odalar", "olculer", "kapilar", "pencereler", "malzemeler", "oda_zemin_kaplamalari", "acik_metrajlar", "tasiyici_elemanlar", "donati_cubuklari", "aciklar", "belirsizlikler"):
        tekil = []
        gorulen = set()
        for deger in birlesik[anahtar]:
            kimlik = json.dumps(deger, ensure_ascii=False, sort_keys=True)
            if kimlik not in gorulen:
                gorulen.add(kimlik)
                tekil.append(deger)
        birlesik[anahtar] = tekil
    hata_sayfalari = {s for hata in hata_partileri for s in hata["sayfalar"]}
    basarili_sayfa_sayisi = sum(1 for s in secilenler if s.get("sayfa") not in hata_sayfalari)
    islenemeyen = sorted(set(
        [s for hata in hata_partileri for s in hata["sayfalar"]]
        + [s.get("sayfa") for s in atlanan]
        + render_edilemeyen
        + onceden_atlanan_sayfalar
    ), key=lambda sayfa: (sayfa is None, sayfa))
    tamamlandi = not islenemeyen
    return {
        "durum": "tamamlandi" if tamamlandi else "kismi_tamamlandi",
        "model": payload["model"],
        "sayfa_sayisi": basarili_sayfa_sayisi,
        "gonderilen_sayfa_sayisi": len(secilenler),
        "atlanmis_sayfa_sayisi": len(set([s.get("sayfa") for s in atlanan] + onceden_atlanan_sayfalar)),
        "atlanmis_sayfalar": sorted(set([s.get("sayfa") for s in atlanan] + onceden_atlanan_sayfalar)),
        "islenemeyen_sayfalar": islenemeyen,
        "parti_hatalari": hata_partileri,
        "bulgular": birlesik,
    }
