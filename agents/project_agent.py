import re


class ProjectAgent:

    def analyze(self, project_data):
        sayfalar = project_data.get("sayfalar", [])

        mimari = []
        statik = []
        elektrik = []
        mekanik = []
        diger = []

        malzemeler = set()
        olcu_sayisi = 0

        for sayfa in sayfalar:
            metin = (sayfa.get("metin") or "").lower()
            sayfa_no = sayfa.get("sayfa")

            if not metin.strip():
                diger.append(sayfa_no)
                continue

            # Sayfa türü tespiti
            if any(k in metin for k in [
                "mimari", "architecture", "plan", "cephe",
                "kesit", "kat planı", "floor plan", "oda"
            ]):
                mimari.append(sayfa_no)

            elif any(k in metin for k in [
                "statik", "structural", "kolon", "kiriş",
                "temel", "donatı", "betonarme", "çelik"
            ]):
                statik.append(sayfa_no)

            elif any(k in metin for k in [
                "elektrik", "electrical", "aydınlatma",
                "priz", "pano", "kablo"
            ]):
                elektrik.append(sayfa_no)

            elif any(k in metin for k in [
                "mekanik", "mechanical", "tesisat",
                "havalandırma", "ısıtma", "sıhhi"
            ]):
                mekanik.append(sayfa_no)

            else:
                diger.append(sayfa_no)

                    # Malzeme ve metraj tespiti

        malzeme_eslesmeleri = {
            "beton": ["beton", "c beton", "c20", "c25", "c30", "c35", "c40"],
            "çimento": ["çimento", "cimento"],
            "tuğla": ["tuğla", "tugla"],
            "gazbeton": ["gazbeton", "ytong"],
            "demir": ["demir", "donatı", "donati", "nervürlü"],
            "çelik": ["çelik", "celik", "profil"],
            "alçı": ["alçı", "alci", "alçıpan", "alcıpan"],
            "sıva": ["sıva", "siva"],
            "boya": ["boya"],
            "seramik": ["seramik"],
            "fayans": ["fayans"],
            "parke": ["parke"],
            "laminat": ["laminat"],
            "mermer": ["mermer"],
            "granit": ["granit"],
            "cam": ["cam"],
            "ahşap": ["ahşap", "ahsap"],
            "yalıtım": ["yalıtım", "yalitim"],
            "izolasyon": ["izolasyon"],
            "kiremit": ["kiremit"],
            "membran": ["membran"],
            "şap": ["şap", "sap"]
        }

        metrajlar = []

        for sayfa in sayfalar:

            metin = (sayfa.get("metin") or "").lower()
            sayfa_no = sayfa.get("sayfa")

            if not metin.strip():
                continue

            # Malzemeleri bul
            for malzeme, anahtarlar in malzeme_eslesmeleri.items():

                if any(anahtar in metin for anahtar in anahtarlar):
                    malzemeler.add(malzeme)

                    # Malzemenin geçtiği satırları incele
                    satirlar = metin.splitlines()

                    for satir in satirlar:

                        if not any(anahtar in satir for anahtar in anahtarlar):
                            continue

                        # Örnekleri yakala:
                        # 125 m2
                        # 125,50 m²
                        # 42.5 m3
                        # 250 mt
                        # 35 metre
                        eslesmeler = re.findall(
                            r"(\d+(?:[.,]\d+)?)\s*(m²|m2|m³|m3|m|mt|metre|metretül|metretul|adet|kg|ton|cm|mm)\b",
                            satir
                        )

                        for miktar, birim in eslesmeler:

                            try:
                                miktar = float(miktar.replace(",", "."))

                                birim_ham = birim.lower()

                                if birim_ham in ["m²", "m2"]:
                                    birim = "m²"

                                elif birim_ham in ["m³", "m3"]:
                                    birim = "m³"

                                elif birim_ham in ["mt", "metre", "metretül", "metretul"]:
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
                                    "malzeme": malzeme,
                                    "miktar": miktar,
                                    "birim": birim,
                                    "sayfa": sayfa_no,
                                    "kaynak": satir.strip()
                                })

                                olcu_sayisi += 1

                            except ValueError:
                                continue

        return {
            "toplam_sayfa": len(sayfalar),
            "sayfa_siniflari": {
                "mimari": mimari,
                "statik": statik,
                "elektrik": elektrik,
                "mekanik": mekanik,
                "diger": diger
            },
            "tespit_edilen_malzemeler": sorted(list(malzemeler)),
            "tespit_edilen_olcu_sayisi": olcu_sayisi,
                    "metrajlar": metrajlar,
            "durum": "analiz_tamamlandi"
        }
