import re


class ProjectAgent:

    def analyze(self, project_data):

        sayfalar = project_data.get(
            "sayfalar",
            []
        )

        mimari = []
        statik = []
        elektrik = []
        mekanik = []
        diger = []

        malzemeler = set()

        olcu_sayisi = 0

        metrajlar = []


        # ====================================================
        # SAYFA SINIFLANDIRMA
        # ====================================================

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


            # MİMARİ

            if any(
                kelime in metin
                for kelime in [
                    "mimari",
                    "architecture",
                    "plan",
                    "cephe",
                    "kesit",
                    "kat planı",
                    "kat plani",
                    "floor plan",
                    "oda"
                ]
            ):

                mimari.append(
                    sayfa_no
                )


            # STATİK

            elif any(
                kelime in metin
                for kelime in [
                    "statik",
                    "structural",
                    "kolon",
                    "kiriş",
                    "kiris",
                    "temel",
                    "donatı",
                    "donati",
                    "betonarme",
                    "çelik",
                    "celik"
                ]
            ):

                statik.append(
                    sayfa_no
                )


            # ELEKTRİK

            elif any(
                kelime in metin
                for kelime in [
                    "elektrik",
                    "electrical",
                    "aydınlatma",
                    "aydinlatma",
                    "priz",
                    "pano",
                    "kablo"
                ]
            ):

                elektrik.append(
                    sayfa_no
                )


            # MEKANİK

            elif any(
                kelime in metin
                for kelime in [
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
            ):

                mekanik.append(
                    sayfa_no
                )


            else:

                diger.append(
                    sayfa_no
                )


        # ====================================================
        # MALZEME SÖZLÜĞÜ
        # ====================================================

        malzeme_eslesmeleri = {

            "beton": [
                "beton",
                "c beton",
                "c20",
                "c25",
                "c30",
                "c35",
                "c40"
            ],

            "çimento": [
                "çimento",
                "cimento"
            ],

            "tuğla": [
                "tuğla",
                "tugla"
            ],

            "gazbeton": [
                "gazbeton",
                "ytong"
            ],

            "demir": [
                "demir",
                "donatı",
                "donati",
                "nervürlü",
                "nervurlu"
            ],

            "çelik": [
                "çelik",
                "celik",
                "profil"
            ],

            "alçı": [
                "alçı",
                "alci",
                "alçıpan",
                "alcipan"
            ],

            "sıva": [
                "sıva",
                "siva"
            ],

            "boya": [
                "boya"
            ],

            "seramik": [
                "seramik"
            ],

            "fayans": [
                "fayans"
            ],

            "parke": [
                "parke"
            ],

            "laminat": [
                "laminat"
            ],

            "mermer": [
                "mermer"
            ],

            "granit": [
                "granit"
            ],

            "cam": [
                "cam"
            ],

            "ahşap": [
                "ahşap",
                "ahsap"
            ],

            "yalıtım": [
                "yalıtım",
                "yalitim"
            ],

            "izolasyon": [
                "izolasyon"
            ],

            "kiremit": [
                "kiremit"
            ],

            "membran": [
                "membran"
            ],

            "şap": [
                "şap",
                "sap"
            ]
        }


        # ====================================================
        # METRAJ TESPİTİ
        # ====================================================

        for sayfa in sayfalar:

            metin = (
                sayfa.get("metin") or ""
            ).lower()

            sayfa_no = sayfa.get(
                "sayfa"
            )


            if not metin.strip():

                continue


            satirlar = metin.splitlines()


            for malzeme, anahtarlar in (
                malzeme_eslesmeleri.items()
            ):

                malzeme_bulundu = any(
                    anahtar in metin
                    for anahtar in anahtarlar
                )


                if not malzeme_bulundu:

                    continue


                malzemeler.add(
                    malzeme
                )


                for satir in satirlar:

                    if not any(
                        anahtar in satir
                        for anahtar in anahtarlar
                    ):

                        continue


                    eslesmeler = re.findall(

                        r"(\d+(?:[.,]\d+)?)"
                        r"\s*"
                        r"(m²|m2|m³|m3|m|mt|"
                        r"metre|metretül|metretul|"
                        r"adet|kg|ton|cm|mm)\b",

                        satir
                    )


                    for miktar, birim_ham in (
                        eslesmeler
                    ):

                        try:

                            miktar = float(
                                miktar.replace(
                                    ",",
                                    "."
                                )
                            )


                            birim_ham = (
                                birim_ham.lower()
                            )


                            if birim_ham in [
                                "m²",
                                "m2"
                            ]:

                                birim = "m²"


                            elif birim_ham in [
                                "m³",
                                "m3"
                            ]:

                                birim = "m³"


                            elif birim_ham in [
                                "mt",
                                "metre",
                                "metretül",
                                "metretul"
                            ]:

                                birim = "m"


                            elif birim_ham == "adet":

                                birim = "adet"


                            elif birim_ham == "kg":

                                birim = "kg"


                            elif birim_ham == "ton":

                                birim = "ton"


                            elif birim_ham == "cm":

                                birim = "cm"


                            elif birim_ham == "mm":

                                birim = "mm"


                            else:

                                birim = "m"


                            metrajlar.append({

                                "malzeme":
                                    malzeme,

                                "miktar":
                                    miktar,

                                "birim":
                                    birim,

                                "sayfa":
                                    sayfa_no,

                                "kaynak":
                                    satir.strip()

                            })


                            olcu_sayisi += 1


                        except ValueError:

                            continue


        # ====================================================
        # SONUÇ
        # ====================================================

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
                olcu_sayisi,

            "metrajlar":
                metrajlar,

            "durum":
                "analiz_tamamlandi"

        }
