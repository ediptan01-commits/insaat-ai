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

            # Malzeme tespiti
            malzeme_listesi = [
                "beton",
                "çimento",
                "tuğla",
                "gazbeton",
                "demir",
                "çelik",
                "alçı",
                "sıva",
                "boya",
                "seramik",
                "fayans",
                "parke",
                "laminat",
                "mermer",
                "granit",
                "cam",
                "ahşap",
                "yalıtım",
                "izolasyon",
                "kiremit",
                "membran"
            ]

            for malzeme in malzeme_listesi:
                if malzeme in metin:
                    malzemeler.add(malzeme)

            # Ölçü ifadelerini yakala
            olculer = re.findall(
                r"\b\d+(?:[.,]\d+)?\s*(?:m2|m²|m3|m³|cm|mm|m|metre)\b",
                metin
            )

            olcu_sayisi += len(olculer)

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
            "durum": "analiz_tamamlandi"
        }
