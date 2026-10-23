import re
from servisler.vision_service import gorsel_ai_analiz
from servisler.quantity_service import miktarlari_hesapla
from agents.pricing_agent import guncel_maliyet_hesapla

SAYI_DESENI = r"(?:\d{1,3}(?:[., ]\d{3})+|\d+)(?:[.,]\d+)?"
ANALIZ_API_SOZLESME_SURUMU = 2


class ProjectAgent:

    # ============================================================
    # MALZEME TANIMLARI
    # ============================================================

    MALZEMELER = {
        "beton": {
            "anahtarlar": [
                "beton",
                "c20",
                "c25",
                "c30",
                "c35",
                "c40"
            ],
            "birimler": ["m³", "m3"]
        },

        "demir": {
            "anahtarlar": [
                "demir",
                "donatı",
                "donati",
                "nervürlü",
                "nervurlu"
            ],
            "birimler": ["kg", "ton"]
        },

        "tuğla": {
            "anahtarlar": ["tuğla", "tugla"],
            "birimler": ["m²", "m2", "adet"]
        },

        "gazbeton": {
            "anahtarlar": ["gazbeton", "ytong"],
            "birimler": ["m²", "m2", "adet"]
        },

        "gazbeton yapıştırıcısı": {
            "anahtarlar": ["gazbeton yapıştırıcı", "ytong yapıştırıcı"],
            "birimler": ["kg", "ton"]
        },

        "bims blok": {
            "anahtarlar": ["bims blok", "bims briket", "bims"],
            "birimler": ["m²", "m2", "adet"]
        },

        "beton briket": {
            "anahtarlar": ["beton briket", "briket"],
            "birimler": ["m²", "m2", "adet"]
        },

        "çimento": {
            "anahtarlar": ["çimento", "cimento"],
            "birimler": ["kg", "ton"]
        },

        "çelik": {
            "anahtarlar": ["çelik", "celik", "profil"],
            "birimler": ["kg", "ton", "m", "adet"]
        },

        "alçı": {
            "anahtarlar": [
                "alçı",
                "alci",
                "alçıpan",
                "alcipan"
            ],
            "birimler": ["m²", "m2", "kg", "adet"]
        },

        "sıva": {
            "anahtarlar": ["sıva", "siva"],
            "birimler": ["m²", "m2"]
        },

        "boya": {
            "anahtarlar": ["boya"],
            "birimler": ["m²", "m2", "kg", "lt", "l"]
        },

        "seramik": {
            "anahtarlar": ["seramik"],
            "birimler": ["m²", "m2", "adet"]
        },

        "seramik yapıştırıcısı": {
            "anahtarlar": ["seramik yapıştırıcı", "fayans yapıştırıcı", "karo yapıştırıcı"],
            "birimler": ["kg", "ton"]
        },

        "derz dolgusu": {
            "anahtarlar": ["derz dolgusu", "derz dolgu"],
            "birimler": ["kg", "ton"]
        },

        "duvar örme harcı": {
            "anahtarlar": ["duvar örme harcı", "duvar örgü harcı", "örgü harcı"],
            "birimler": ["kg", "ton"]
        },

        "hazır sıva harcı": {
            "anahtarlar": ["hazır sıva harcı", "hazir siva harci", "makine sıva harcı"],
            "birimler": ["kg", "ton"]
        },

        "fayans": {
            "anahtarlar": ["fayans"],
            "birimler": ["m²", "m2", "adet"]
        },

        "parke": {
            "anahtarlar": ["parke"],
            "birimler": ["m²", "m2"]
        },

        "laminat": {
            "anahtarlar": ["laminat"],
            "birimler": ["m²", "m2"]
        },

        "mermer": {
            "anahtarlar": ["mermer"],
            "birimler": ["m²", "m2", "m"]
        },

        "granit": {
            "anahtarlar": ["granit"],
            "birimler": ["m²", "m2", "m"]
        },

        "cam": {
            "anahtarlar": ["cam"],
            "birimler": ["m²", "m2", "adet"]
        },

        "ahşap": {
            "anahtarlar": ["ahşap", "ahsap"],
            "birimler": ["m²", "m2", "m", "adet"]
        },

        "yalıtım": {
            "anahtarlar": ["yalıtım", "yalitim"],
            "birimler": ["m²", "m2", "m³", "m3"]
        },

        "izolasyon": {
            "anahtarlar": ["izolasyon"],
            "birimler": ["m²", "m2", "m³", "m3"]
        },

        "kiremit": {
            "anahtarlar": ["kiremit"],
            "birimler": ["m²", "m2", "adet"]
        },

        "membran": {
            "anahtarlar": ["membran"],
            "birimler": ["m²", "m2", "adet"]
        },

        "şap": {
            "anahtarlar": ["şap", "sap"],
            "birimler": ["m²", "m2", "m³", "m3"]
        }
    }

    # ============================================================
    # BİRİM DÖNÜŞTÜRME
    # ============================================================

    @staticmethod
    def birim_normalize(birim):

        birim = birim.lower().strip()

        if birim in ["m²", "m2"]:
            return "m²"

        if birim in ["m³", "m3"]:
            return "m³"

        if birim in [
            "m",
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

        if birim in ["lt", "l"]:
            return "lt"

        return birim

    # ============================================================
    # SAYI OKUMA
    # ============================================================

    @staticmethod
    def sayi_oku(deger):

        deger = deger.strip().replace(" ", "")

        # Türkçe binlik kullanım:
        # 4.850
        # 4,850
        #
        # Ondalık:
        # 4,85
        # 4.85

        if "," in deger and "." in deger:

            # 4.850,50
            if deger.rfind(",") > deger.rfind("."):
                deger = deger.replace(".", "")
                deger = deger.replace(",", ".")

            # 4,850.50
            else:
                deger = deger.replace(",", "")

        elif "," in deger or "." in deger:
            ayrac = "," if "," in deger else "."
            parcalar = deger.split(ayrac)
            if len(parcalar) > 2 or (
                len(parcalar) == 2
                and len(parcalar[1]) == 3
                and parcalar[0].isdigit()
            ):
                deger = "".join(parcalar)
            elif ayrac == ",":
                deger = deger.replace(",", ".")

        try:
            return float(deger)

        except ValueError:
            return None

    # ============================================================
    # SAYFA SINIFLANDIRMA
    # ============================================================

    def sayfa_siniflandir(self, metin, sayfa_no):

        mimari = [
            "mimari",
            "architecture",
            "plan",
            "kat planı",
            "kat plani",
            "zemin kat",
            "oda",
            "salon",
            "mutfak",
            "yatak odası",
            "yatak odasi"
        ]

        statik = [
            "statik",
            "structural",
            "kolon",
            "kiriş",
            "kiris",
            "temel",
            "donatı",
            "donati",
            "betonarme"
        ]

        elektrik = [
            "elektrik",
            "electrical",
            "aydınlatma",
            "aydinlatma",
            "priz",
            "pano",
            "kablo"
        ]

        mekanik = [
            "mekanik",
            "mechanical",
            "tesisat",
            "havalandırma",
            "havalandirma",
            "ısıtma",
            "isitma",
            "sıhhi",
            "sihhi"
        ]

        if any(k in metin for k in mimari):
            return "mimari"

        if any(k in metin for k in statik):
            return "statik"

        if any(k in metin for k in elektrik):
            return "elektrik"

        if any(k in metin for k in mekanik):
            return "mekanik"

        return "diger"

    # ============================================================
    # ODA / ALAN TESPİTİ
    # ============================================================

    def alanlari_tespit_et(self, satirlar, sayfa_no):

        alanlar = []

        oda_kelimeleri = [
            "salon",
            "mutfak",
            "yatak odası",
            "yatak odasi",
            "oda",
            "banyo",
            "ebeveyn banyo",
            "wc",
            "hol",
            "giriş",
            "giris",
            "veranda",
            "teras",
            "balkon"
        ]

        alan_regex = re.compile(
            rf"({SAYI_DESENI})"
            r"\s*m(?:²|2)"
        )

        for satir in satirlar:

            satir_kucuk = satir.lower().strip()

            if not any(
                kelime in satir_kucuk
                for kelime in oda_kelimeleri
            ):
                continue

            eslesmeler = alan_regex.findall(
                satir_kucuk
            )

            for miktar_ham in eslesmeler:

                miktar = self.sayi_oku(
                    miktar_ham
                )

                if miktar is None:
                    continue

                alanlar.append({
                    "alan_adi": satir.strip(),
                    "miktar": miktar,
                    "birim": "m²",
                    "sayfa": sayfa_no,
                    "kaynak": satir.strip()
                })

        return alanlar

    # ============================================================
    # KAPI / PENCERE TESPİTİ
    # ============================================================

    def aciklari_tespit_et(self, satirlar, sayfa_no):

        kapilar = []
        pencereler = []

        for satir in satirlar:

            kucuk = satir.lower().strip()

            # Kapı satırları
            if (
                "kapı" in kucuk
                or "kapi" in kucuk
                or re.search(r"\bk[0-9]+\b", kucuk)
            ):

                adet_eslesme = re.search(
                    rf"({SAYI_DESENI})\s*adet",
                    kucuk
                )

                adet = 1

                if adet_eslesme:
                    okunan = self.sayi_oku(
                        adet_eslesme.group(1)
                    )

                    if okunan is not None:
                        adet = okunan

                kapilar.append({
                    "tip": "kapı",
                    "adet": adet,
                    "sayfa": sayfa_no,
                    "kaynak": satir.strip()
                })

            # Pencere satırları
            if (
                "pencere" in kucuk
                or re.search(r"\bp[0-9]+\b", kucuk)
            ):

                adet_eslesme = re.search(
                    rf"({SAYI_DESENI})\s*adet",
                    kucuk
                )

                adet = 1

                if adet_eslesme:
                    okunan = self.sayi_oku(
                        adet_eslesme.group(1)
                    )

                    if okunan is not None:
                        adet = okunan

                pencereler.append({
                    "tip": "pencere",
                    "adet": adet,
                    "sayfa": sayfa_no,
                    "kaynak": satir.strip()
                })

        return kapilar, pencereler

    # ============================================================
    # METRAJ TESPİTİ
    # ============================================================

    def metraj_tespit_et(
        self,
        satir,
        malzeme,
        anahtarlar,
        izinli_birimler,
        sayfa_no
    ):

        sonuc = []

        # Ölçü regex'i
        regex = re.compile(
            rf"({SAYI_DESENI})"
            r"\s*"
            r"(m²|m2|m³|m3|m|mt|metre|"
            r"metretül|metretul|adet|kg|ton|cm|mm|lt|l)"
            r"\b"
        )

        for eslesme in regex.finditer(satir):

            miktar_ham = eslesme.group(1)
            birim_ham = eslesme.group(2)

            miktar = self.sayi_oku(
                miktar_ham
            )

            if miktar is None:
                continue

            birim = self.birim_normalize(
                birim_ham
            )

            # cm / mm kesinlikle metraj değildir.
            if birim in ["cm", "mm"]:
                continue

            # Malzemenin izin verilen birimi değilse atla.
            if birim not in izinli_birimler:
                continue

            # Aynı satırda "duvar kalınlığı 10 cm"
            # gibi bir ölçü varsa cm zaten filtrelenir.

            sonuc.append({
                "malzeme": malzeme,
                "miktar": miktar,
                "birim": birim,
                "sayfa": sayfa_no,
                "kaynak": satir.strip()
            })

        return sonuc

    # ============================================================
    # ANA ANALİZ
    # ============================================================

    def analyze(
        self,
        project_data,
        fiyat_bolgesi="Türkiye geneli",
        fire_yuzdesi=10,
        tavan_yuksekligi=2.8,
        olcu_birimi_varsayimi="belirsiz",
        kuru_alan_kaplamasi="laminat",
    ):

        sayfalar = project_data.get(
            "sayfalar",
            []
        )
        gorsel_girdisi = project_data.get(
            "gorsel_analiz_girdisi",
            {}
        )
        gorsel_girdi_sayfasi = gorsel_girdisi.get(
            "sayfalar",
            []
        )

        mimari = []
        statik = []
        elektrik = []
        mekanik = []
        diger = []

        malzemeler = set()

        metrajlar = []
        metraj_belirsizlikleri = []
        alanlar = []
        kapilar = []
        pencereler = []
        gorsel_analizi = gorsel_ai_analiz(project_data)

        # ========================================================
        # SAYFALARI İŞLE
        # ========================================================

        for sayfa in sayfalar:

            metin = (
                sayfa.get("metin") or ""
            ).lower()

            sayfa_no = sayfa.get(
                "sayfa"
            )

            if not metin.strip():

                diger.append(
                    sayfa_no
                )

                continue

            sinif = self.sayfa_siniflandir(
                metin,
                sayfa_no
            )

            if sinif == "mimari":
                mimari.append(sayfa_no)

            elif sinif == "statik":
                statik.append(sayfa_no)

            elif sinif == "elektrik":
                elektrik.append(sayfa_no)

            elif sinif == "mekanik":
                mekanik.append(sayfa_no)

            else:
                diger.append(sayfa_no)

            satirlar = metin.splitlines()

            # ====================================================
            # ODA ALANLARI
            # ====================================================

            alanlar.extend(
                self.alanlari_tespit_et(
                    satirlar,
                    sayfa_no
                )
            )

            # ====================================================
            # KAPI / PENCERE
            # ====================================================

            k, p = self.aciklari_tespit_et(
                satirlar,
                sayfa_no
            )

            kapilar.extend(k)
            pencereler.extend(p)

            # ====================================================
            # MALZEME METRAJI
            # ====================================================

            for satir in satirlar:
                adaylar = []
                for malzeme, bilgi in self.MALZEMELER.items():
                    anahtarlar = bilgi["anahtarlar"]
                    if not any(anahtar in satir for anahtar in anahtarlar):
                        continue
                    bulunan = self.metraj_tespit_et(
                        satir,
                        malzeme,
                        anahtarlar,
                        bilgi["birimler"],
                        sayfa_no,
                    )
                    adaylar.extend(bulunan)

                # A single line may mention synonyms (e.g. seramik/fayans)
                # or several products that share the same amount and unit.
                # If the parser cannot map that occurrence to one material,
                # keep it out of priced quantities and show the source line.
                grouped_candidates = {}
                for item in adaylar:
                    grouped_candidates.setdefault((item["miktar"], item["birim"]), []).append(item)
                for (_, _), group in grouped_candidates.items():
                    candidate_materials = {item["malzeme"] for item in group}
                    if len(candidate_materials) > 1:
                        belirsizlik = {
                            "sayfa": sayfa_no,
                            "kaynak": satir.strip(),
                            "aday_malzemeler": sorted(candidate_materials),
                            "miktar": group[0]["miktar"],
                            "birim": group[0]["birim"],
                            "neden": "Aynı miktar ve birim birden fazla malzeme adıyla eşleşti; çift sayımı önlemek için fiyatlandırmaya alınmadı.",
                        }
                        if belirsizlik not in metraj_belirsizlikleri:
                            metraj_belirsizlikleri.append(belirsizlik)
                        continue
                    item = group[0]
                    malzemeler.add(item["malzeme"])
                    metrajlar.append(item)

        # ========================================================
        # TEKRARLARI TEMİZLE
        # ========================================================

        benzersiz_metrajlar = []

        gorulen = set()

        for item in metrajlar:

            anahtar = (
                item["malzeme"],
                item["miktar"],
                item["birim"],
                item["sayfa"],
                item["kaynak"]
            )

            if anahtar in gorulen:
                continue

            gorulen.add(anahtar)

            benzersiz_metrajlar.append(
                item
            )

        metrajlar = benzersiz_metrajlar

        # Metin içeriği bulunmayan taranmış paftaları, görsel ajanın pafta
        # sınıflandırmasıyla rapora ekle. Metin sınıflandırmasını değiştirme.
        metinsiz_sayfalar = {
            s.get("sayfa") for s in sayfalar if not (s.get("metin") or "").strip()
        }
        disiplin_listeleri = {
            "mimari": mimari,
            "statik": statik,
            "elektrik": elektrik,
            "mekanik": mekanik,
            "diger": diger,
        }
        gorsel_bulgular = gorsel_analizi.get("bulgular", {})
        for pafta in gorsel_bulgular.get("sayfalar", []) if isinstance(gorsel_bulgular, dict) else []:
            sayfa_no = pafta.get("sayfa")
            disiplin = str(pafta.get("disiplin", "")).casefold().strip()
            if sayfa_no not in metinsiz_sayfalar or disiplin not in disiplin_listeleri:
                continue
            for liste in disiplin_listeleri.values():
                if sayfa_no in liste:
                    liste.remove(sayfa_no)
            if sayfa_no not in disiplin_listeleri[disiplin]:
                disiplin_listeleri[disiplin].append(sayfa_no)
        for liste in disiplin_listeleri.values():
            liste.sort(key=lambda deger: (deger is None, deger))

        malzeme_miktarlari = miktarlari_hesapla(
            gorsel_analizi,
            metrajlar,
            fire_yuzdesi=fire_yuzdesi,
            tavan_yuksekligi=tavan_yuksekligi,
            olcu_birimi_varsayimi=olcu_birimi_varsayimi,
            kuru_alan_kaplamasi=kuru_alan_kaplamasi,
        )
        maliyet_analizi = guncel_maliyet_hesapla(malzeme_miktarlari, fiyat_bolgesi)

        # ========================================================
        # SONUÇ
        # ========================================================

        return {

            "toplam_sayfa":
                len(sayfalar),

            "sayfa_siniflari": {

                "mimari":
                    mimari,

                "statik":
                    statik,

                "elektrik":
                    elektrik,

                "mekanik":
                    mekanik,

                "diger":
                    diger
            },

            "tespit_edilen_malzemeler":
                sorted(
                    list(malzemeler)
                ),

            "tespit_edilen_olcu_sayisi":
                len(metrajlar),

            "metrajlar":
                metrajlar,

            "metraj_belirsizlikleri":
                metraj_belirsizlikleri,

            "alanlar":
                alanlar,

            "kapilar":
                kapilar,

            "pencereler":
                pencereler,

            "gorsel_analizi": gorsel_analizi,

            "malzeme_miktarlari": malzeme_miktarlari,

            "maliyet_analizi": maliyet_analizi,

            "durum":
                "analiz_tamamlandi"
                                           }
