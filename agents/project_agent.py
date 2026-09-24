import re


class ProjectAgent:

    def __init__(self):
        self.malzeme_eslesmeleri = {
            "beton": [
                "beton", "c20", "c25", "c30", "c35", "c40",
                "c45", "c50", "betonarme"
            ],
            "çimento": [
                "çimento", "cimento"
            ],
            "kum": [
                "kum", "ince kum", "sıva kumu", "şap kumu"
            ],
            "çakıl": [
                "çakıl", "çakil", "agrega", "mıcır", "micir"
            ],
            "tuğla": [
                "tuğla", "tugla", "tuğla duvar"
            ],
            "gazbeton": [
                "gazbeton", "ytong"
            ],
            "demir": [
                "demir", "donatı", "donati", "nervürlü",
                "inşaat demiri", "hasır çelik"
            ],
            "çelik": [
                "çelik", "celik", "profil", "çelik profil",
                "ipe", "hea", "heb", "ipe"
            ],
            "alçı": [
                "alçı", "alci", "alçı sıva", "alci siva"
            ],
            "alçıpan": [
                "alçıpan", "alcipan", "alcıpan"
            ],
            "sıva": [
                "sıva", "siva", "kaba sıva", "ince sıva"
            ],
            "boya": [
                "boya", "plastik boya", "silikonlu boya",
                "akrilik boya"
            ],
            "seramik": [
                "seramik", "yer seramiği", "duvar seramiği"
            ],
            "fayans": [
                "fayans"
            ],
            "parke": [
                "parke", "laminat parke"
            ],
            "laminat": [
                "laminat"
            ],
            "mermer": [
                "mermer"
            ],
            "granit": [
                "granit", "granit seramik"
            ],
            "cam": [
                "cam", "ısıcam", "ısı cam"
            ],
            "ahşap": [
                "ahşap", "ahsap", "kereste"
            ],
            "yalıtım": [
                "yalıtım", "yalitim", "ısı yalıtımı",
                "ses yalıtımı"
            ],
            "izolasyon": [
                "izolasyon"
            ],
            "kiremit": [
                "kiremit"
            ],
            "membran": [
                "membran", "bitümlü membran"
            ],
            "şap": [
                "şap", "sap"
            ],
            "su yalıtımı": [
                "su yalıtımı", "su yalitimi"
            ],
            "kapı": [
                "kapı", "kapi", "kapı kasası"
            ],
            "pencere": [
                "pencere", "doğrama", "dograma"
            ],
            "alüminyum": [
                "alüminyum", "aluminyum"
            ],
            "PVC": [
                "pvc"
            ],
            "elektrik kablosu": [
                "kablo", "kablo hattı", "elektrik kablosu"
            ],
            "priz": [
                "priz"
            ],
            "anahtar": [
                "anahtar", "elektrik anahtarı"
            ],
            "armatür": [
                "armatür", "aydınlatma armatürü"
            ],
            "boru": [
                "boru", "pprc", "pex", "pe-x"
            ],
            "radyatör": [
                "radyatör", "petek"
            ]
        }

        self.birimler = [
            "m²",
            "m2",
            "m³",
            "m3",
            "mt",
            "metre",
            "metretül",
            "metretul",
            "adet",
            "kg",
            "ton",
            "cm",
            "mm",
            "lt",
            "litre"
        ]

    # ---------------------------------------------------------
    # METİN NORMALİZASYONU
    # ---------------------------------------------------------

    def normalize(self, metin):
        if not metin:
            return ""

        metin = metin.lower()

        # Farklı m²/m³ yazımlarını standartlaştır
        metin = metin.replace("㎡", "m²")
        metin = metin.replace("㎥", "m³")

        return metin

    # ---------------------------------------------------------
    # SAYI DÖNÜŞTÜRME
    # ---------------------------------------------------------

    def sayiya_cevir(self, deger):
        try:
            deger = deger.strip()

            # 1.250,50 -> 1250.50
            if "," in deger and "." in deger:
                if deger.rfind(",") > deger.rfind("."):
                    deger = deger.replace(".", "")
                    deger = deger.replace(",", ".")

            # 125,50 -> 125.50
            elif "," in deger:
                deger = deger.replace(",", ".")

            # 1.250 -> 1250
            elif "." in deger:
                parcalar = deger.split(".")

                if len(parcalar) == 2 and len(parcalar[1]) == 3:
                    deger = deger.replace(".", "")

            return float(deger)

        except (ValueError, TypeError):
            return None

    # ---------------------------------------------------------
    # BİRİM STANDARDİZASYONU
    # ---------------------------------------------------------

    def birim_duzelt(self, birim):

        birim = birim.lower().strip()

        if birim in ["m²", "m2"]:
            return "m²"

        if birim in ["m³", "m3"]:
            return "m³"

        if birim in [
            "mt",
            "metre",
            "metretül",
            "metretul"
        ]:
            return "m"

        if birim == "adet":
            return "adet"

        if birim == "kg":
            return "kg"

        if birim == "ton":
            return "ton"

        if birim == "cm":
            return "cm"

        if birim == "mm":
            return "mm"

        if birim in ["lt", "litre"]:
            return "litre"

        return birim

    # ---------------------------------------------------------
    # SAYFA SINIFLANDIRMA
    # ---------------------------------------------------------

    def sayfa_siniflandir(self, metin):

        mimari_anahtarlar = [
            "mimari",
            "architecture",
            "architectural",
            "kat planı",
            "kat plani",
            "floor plan",
            "cephe",
            "elevation",
            "kesit",
            "section",
            "oda",
            "salon",
            "mutfak",
            "banyo",
            "wc",
            "çatı",
            "cati",
            "roof",
            "kapı",
            "pencere"
        ]

        statik_anahtarlar = [
            "statik",
            "structural",
            "kolon",
            "column",
            "kiriş",
            "kiris",
            "beam",
            "temel",
            "foundation",
            "donatı",
            "donati",
            "betonarme",
            "reinforced concrete",
            "çelik",
            "steel",
            "döşeme",
            "doseme"
        ]

        elektrik_anahtarlar = [
            "elektrik",
            "electrical",
            "aydınlatma",
            "aydinlatma",
            "priz",
            "anahtar",
            "pano",
            "kablo",
            "circuit",
            "lighting"
        ]

        mekanik_anahtarlar = [
            "mekanik",
            "mechanical",
            "tesisat",
            "havalandırma",
            "havalandirma",
            "hvac",
            "ısıtma",
            "isitma",
            "soğutma",
            "sogutma",
            "sıhhi",
            "sihhi",
            "temiz su",
            "pis su",
            "yangın",
            "yangin"
        ]

        sonuc = []

        if any(k in metin for k in mimari_anahtarlar):
            sonuc.append("mimari")

        if any(k in metin for k in statik_anahtarlar):
            sonuc.append("statik")

        if any(k in metin for k in elektrik_anahtarlar):
            sonuc.append("elektrik")

        if any(k in metin for k in mekanik_anahtarlar):
            sonuc.append("mekanik")

        if not sonuc:
            sonuc.append("diger")

        return sonuc

    # ---------------------------------------------------------
    # MALZEME TESPİTİ
    # ---------------------------------------------------------

    def malzeme_bul(self, metin):

        bulunan = []

        for malzeme, anahtarlar in self.malzeme_eslesmeleri.items():

            for anahtar in anahtarlar:

                if anahtar in metin:
                    bulunan.append(malzeme)
                    break

        return sorted(set(bulunan))

    # ---------------------------------------------------------
    # METRAJ TESPİTİ
    # ---------------------------------------------------------

    def metraj_bul(self, metin, sayfa_no):

        metrajlar = []

        # Örnek:
        # 125 m2
        # 125,50 m²
        # 1.250,50 m²
        # 42 m3
        # 250 adet
        # 150 kg

        desen = re.compile(
            r"(\d+(?:[.,]\d+)*)\s*"
            r"(m²|m2|m³|m3|mt|metre|metretül|metretul|"
            r"adet|kg|ton|cm|mm|lt|litre)\b",
            re.IGNORECASE
        )

        satirlar = metin.splitlines()

        for satir in satirlar:

            eslesmeler = desen.findall(satir)

            for miktar_ham, birim_ham in eslesmeler:

                miktar = self.sayiya_cevir(miktar_ham)

                if miktar is None:
                    continue

                birim = self.birim_duzelt(birim_ham)

                metrajlar.append({
                    "miktar": miktar,
                    "birim": birim,
                    "sayfa": sayfa_no,
                    "kaynak": satir.strip()
                })

        return metrajlar

    # ---------------------------------------------------------
    # MALZEME + METRAJ EŞLEŞTİRME
    # ---------------------------------------------------------

    def malzeme_metrajlarini_bul(self, metin, sayfa_no):

        sonuc = []

        satirlar = metin.splitlines()

        for satir in satirlar:

            satir_malzemeleri = self.malzeme_bul(satir)

            if not satir_malzemeleri:
                continue

            satir_metrajlari = self.metraj_bul(
                satir,
                sayfa_no
            )

            for metraj in satir_metrajlari:

                for malzeme in satir_malzemeleri:

                    sonuc.append({
                        "malzeme": malzeme,
                        "miktar": metraj["miktar"],
                        "birim": metraj["birim"],
                        "sayfa": sayfa_no,
                        "kaynak": metraj["kaynak"],
                        "guven": "yüksek"
                    })

        return sonuc

    # ---------------------------------------------------------
    # ANA ANALİZ
    # ---------------------------------------------------------

    def analyze(self, project_data):

        sayfalar = project_data.get("sayfalar", [])

        mimari = []
        statik = []
        elektrik = []
        mekanik = []
        diger = []

        malzemeler = set()

        metrajlar = []

        sayfa_detaylari = []

        toplam_metraj = 0

        # -----------------------------------------------------
        # SAYFALARI ANALİZ ET
        # -----------------------------------------------------

        for sayfa in sayfalar:

            sayfa_no = sayfa.get("sayfa")

            ham_metin = sayfa.get("metin") or ""

            metin = self.normalize(ham_metin)

            if not metin.strip():

                diger.append(sayfa_no)

                sayfa_detaylari.append({
                    "sayfa": sayfa_no,
                    "siniflar": ["diger"],
                    "metin_var": False,
                    "malzemeler": [],
                    "metraj_sayisi": 0
                })

                continue

            siniflar = self.sayfa_siniflandir(metin)

            if "mimari" in siniflar:
                mimari.append(sayfa_no)

            if "statik" in siniflar:
                statik.append(sayfa_no)

            if "elektrik" in siniflar:
                elektrik.append(sayfa_no)

            if "mekanik" in siniflar:
                mekanik.append(sayfa_no)

            if "diger" in siniflar:
                diger.append(sayfa_no)

            # Malzemeleri bul
            sayfa_malzemeleri = self.malzeme_bul(metin)

            for malzeme in sayfa_malzemeleri:
                malzemeler.add(malzeme)

            # Metrajları bul
            sayfa_metrajlari = self.malzeme_metrajlarini_bul(
                metin,
                sayfa_no
            )

            metrajlar.extend(sayfa_metrajlari)

            toplam_metraj += len(sayfa_metrajlari)

            sayfa_detaylari.append({
                "sayfa": sayfa_no,
                "siniflar": siniflar,
                "metin_var": True,
                "malzemeler": sayfa_malzemeleri,
                "metraj_sayisi": len(sayfa_metrajlari)
            })

        # -----------------------------------------------------
        # SONUÇ
        # -----------------------------------------------------

        return {

            "durum": "analiz_tamamlandi",

            "toplam_sayfa": len(sayfalar),

            "sayfa_siniflari": {
                "mimari": sorted(set(mimari)),
                "statik": sorted(set(statik)),
                "elektrik": sorted(set(elektrik)),
                "mekanik": sorted(set(mekanik)),
                "diger": sorted(set(diger))
            },

            "sayfa_detaylari": sayfa_detaylari,

            "tespit_edilen_malzemeler": sorted(
                list(malzemeler)
            ),

            "tespit_edilen_olcu_sayisi": toplam_metraj,

            "metrajlar": metrajlar,

            "istatistik": {
                "mimari_sayfa": len(set(mimari)),
                "statik_sayfa": len(set(statik)),
                "elektrik_sayfa": len(set(elektrik)),
                "mekanik_sayfa": len(set(mekanik)),
                "malzeme_sayisi": len(malzemeler),
                "metraj_sayisi": len(metrajlar)
            }
        }
