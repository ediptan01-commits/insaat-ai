"""Şematik kat planından türetilen, varsayımları görünür malzeme metrajı."""

import math
import re


ODA_ALAN_TERIMLERI = {
    "seramik": ("banyo", "wc", "tuvalet", "mutfak", "balkon", "teras"),
}


def _sayi(deger):
    if isinstance(deger, (int, float)):
        return float(deger)
    metin = str(deger or "").strip().replace(",", ".")
    try:
        return float(metin)
    except ValueError:
        return None


def _uzunlugu_metreye_cevir(deger, birim):
    sayi = _sayi(deger)
    carp = {"m": 1.0, "metre": 1.0, "cm": 0.01, "mm": 0.001}.get(str(birim or "").casefold().strip())
    return sayi * carp if sayi is not None and carp is not None and sayi > 0 else None


def _olculeri_coz(oda):
    """Oda boyutlarını m cinsine getirir; birim varsayımını not eder."""
    uzunluk = _sayi(oda.get("uzunluk"))
    genislik = _sayi(oda.get("genislik"))
    birim = str(oda.get("olcu_birimi") or oda.get("birim") or "").lower()
    kaynak = str(oda.get("olcu_kaynagi") or "").lower()

    olcu = str(oda.get("olcu") or "")
    if uzunluk is None or genislik is None:
        eslesme = re.search(
            r"(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\s*[x×]\s*"
            r"(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?",
            olcu.lower(),
        )
        if not eslesme:
            return None
        uzunluk = _sayi(eslesme.group(1))
        genislik = _sayi(eslesme.group(3))
        birim = eslesme.group(2) or eslesme.group(4) or birim

    if not uzunluk or not genislik or uzunluk <= 0 or genislik <= 0:
        return None

    if birim in ("cm", "santimetre", "santimetreler"):
        carp = 0.01
    elif birim in ("mm", "milimetre"):
        carp = 0.001
    elif birim in ("m", "metre", "metreler"):
        carp = 1.0
    elif max(uzunluk, genislik) >= 30:
        # Kat planlarındaki 550x260 biçiminde yazımlarda cm yaygındır.
        # Bu yalnızca hesap varsayımıdır; kullanıcı raporunda işaretlenir.
        carp = 0.01
        if kaynak in ("", "belirsiz"):
            kaynak = "birim çizimde belirsiz; cm varsayımı"
        else:
            kaynak += "; birim çizimde belirsiz, cm varsayımı"
    elif max(uzunluk, genislik) <= 20:
        carp = 1.0
        if kaynak in ("", "belirsiz"):
            kaynak = "birim çizimde belirsiz; m varsayımı"
        else:
            kaynak += "; birim çizimde belirsiz, m varsayımı"
    else:
        return None

    return uzunluk * carp, genislik * carp, kaynak


def _birimi_normalize_et(birim):
    metin = str(birim or "").strip().lower().replace(" ", "")
    return {
        "m2": "m²", "m^2": "m²", "m²": "m²",
        "m3": "m³", "m^3": "m³", "m³": "m³",
        "metretül": "m", "metretul": "m", "metre": "m", "mt": "m",
        "litre": "L", "lt": "L", "l": "L",
        "kilogram": "kg", "kilograms": "kg",
        "ton": "ton", "adet": "adet", "pcs": "adet",
    }.get(metin, metin)


def _metin_kaynagi_eslesiyor(birinci, ikinci):
    normalize = lambda deger: re.sub(r"\W+", " ", str(deger or "").casefold()).strip()
    a, b = normalize(birinci), normalize(ikinci)
    return bool(a and b and (a == b or (min(len(a), len(b)) >= 12 and (a in b or b in a))))


def miktarlari_hesapla(
    gorsel_analizi,
    metin_metrajlari=None,
    fire_yuzdesi=10,
    tavan_yuksekligi=2.8,
    olcu_birimi_varsayimi="belirsiz",
    kuru_alan_kaplamasi="laminat",
):
    """Oda ölçülerinden sınırlı bir ön metraj çıkarır.

    Kaplama payları ve boya katsayıları yaklaşık ön keşif varsayımlarıdır.
    Taşıyıcı sistem, tesisat ve kesin duvar geometrisi bu hesapta yoktur.
    """
    bulgular = gorsel_analizi.get("bulgular") or {}
    odalar = bulgular.get("odalar") or []
    hesaplanabilenler = []
    atlanan_odalar = []
    seramik_net = 0.0
    parke_net = 0.0
    seramik_odalar = []
    parke_odalar = []
    birim_varsayimi_kullanildi = False

    for oda in odalar:
        if not isinstance(oda, dict):
            continue
        olcu_kaynagi = str(oda.get("olcu_kaynagi") or "belirsiz").casefold().strip()
        # A model-inferred dimension is useful as a clue, but it is not a
        # verifiable takeoff basis. Never turn it into a priced quantity.
        if olcu_kaynagi not in ("cizimde_yazili", "çizimde yazılı", "belgede yazılı"):
            atlanan_odalar.append(
                str(oda.get("ad") or "İsimsiz oda")
                + " (ölçü çizimde doğrulanamadı; yaklaşık metraja alınmadı)"
            )
            continue
        olcu_birimi = str(oda.get("olcu_birimi") or oda.get("birim") or "").casefold().strip()
        olcu_birimi_belirsiz = olcu_birimi in ("", "belirsiz", "unknown")
        explicit_units = re.findall(r"\d+(?:[.,]\d+)?\s*(mm|cm|m)\b", str(oda.get("olcu") or "").lower())
        varsayim_uygulandi = olcu_birimi_belirsiz and not explicit_units and olcu_birimi_varsayimi in ("cm", "m")
        if olcu_birimi_belirsiz and explicit_units:
            olcu_birimi = explicit_units[0]
        elif varsayim_uygulandi:
            olcu_birimi = olcu_birimi_varsayimi
            birim_varsayimi_kullanildi = True
        if olcu_birimi not in ("m", "cm", "mm", "metre", "santimetre", "milimetre"):
            atlanan_odalar.append(
                str(oda.get("ad") or "İsimsiz oda")
                + " (ölçü birimi çizimde doğrulanamadı; yaklaşık metraja alınmadı)"
            )
            continue
        olcu = _olculeri_coz({**oda, "olcu_birimi": olcu_birimi})
        if not olcu:
            atlanan_odalar.append(str(oda.get("ad") or "İsimsiz oda"))
            continue
        uzunluk, genislik, kaynak = olcu
        alan = uzunluk * genislik
        if alan > 100 or alan < 0.5:
            atlanan_odalar.append(str(oda.get("ad") or "Oda") + " (ölçü kontrolü gerekli)")
            continue

        ad = str(oda.get("ad") or "Oda")
        kayit = {
            "ad": ad,
            "uzunluk_m": round(uzunluk, 2),
            "genislik_m": round(genislik, 2),
            "alan_m2": round(alan, 2),
            "sayfa": oda.get("sayfa"),
            "olcu_kaynagi": "çizimde yazılı ölçü (görsel AI okuması)",
            "olcu_metni": str(oda.get("olcu") or ""),
        }
        if kaynak:
            kayit["olcu_notu"] = kaynak
        if varsayim_uygulandi:
            kayit["olcu_birimi_varsayimi"] = olcu_birimi_varsayimi
            kayit["olcu_notu"] = f"Birim varsayımı: {olcu_birimi_varsayimi}"
        hesaplanabilenler.append(kayit)

        if (
            any(terim in ad.casefold() for terim in ODA_ALAN_TERIMLERI["seramik"])
            or kuru_alan_kaplamasi == "seramik"
        ):
            seramik_net += alan
            seramik_odalar.append(kayit)
        else:
            parke_net += alan
            parke_odalar.append(kayit)

    def oda_kaynaklari(odalar):
        return [
            {
                "ad": oda["ad"],
                "sayfa": oda.get("sayfa"),
                "alan_m2": oda["alan_m2"],
                "olcu_metni": oda.get("olcu_metni", ""),
                "olcu_notu": oda.get("olcu_notu", ""),
            }
            for oda in odalar
        ]

    def kaynak_sayfalari(odalar):
        return sorted({oda["sayfa"] for oda in odalar if oda.get("sayfa") is not None})

    kalemler = []
    if seramik_net:
        kalemler.append({"malzeme": "Seramik zemin kaplaması", "miktar": round(seramik_net * (1 + fire_yuzdesi / 100), 2), "birim": "m²", "net_alan_m2": round(seramik_net, 2), "tahmin": True, "kaynak": "oda ölçüsü + kaplama varsayımı", "kaynak_odalar": oda_kaynaklari(seramik_odalar), "kaynak_sayfalari": kaynak_sayfalari(seramik_odalar)})
        yapistirici_min = seramik_net * 3
        yapistirici_max = seramik_net * 5
        kalemler.append({
            "malzeme": "Seramik yapıştırıcısı",
            "miktar": round((yapistirici_min + yapistirici_max) / 2, 2),
            "miktar_min": round(yapistirici_min, 2),
            "miktar_max": round(yapistirici_max, 2),
            "birim": "kg",
            "tahmin": True,
            "kaynak": "seramik döşenecek net alan × üretici teknik föyündeki tüketim aralığı",
            "tuketim_araligi_kg_m2": "3–5",
            "teknik_kaynak_url": "https://www.kalekim.com/int-tr/1051-kalekim",
            "kaynak_odalar": oda_kaynaklari(seramik_odalar),
            "kaynak_sayfalari": kaynak_sayfalari(seramik_odalar),
        })
    if parke_net:
        kalemler.append({"malzeme": "Laminat parke", "miktar": round(parke_net * (1 + fire_yuzdesi / 100), 2), "birim": "m²", "net_alan_m2": round(parke_net, 2), "tahmin": True, "kaynak": "oda ölçüsü + kaplama varsayımı", "kaynak_odalar": oda_kaynaklari(parke_odalar), "kaynak_sayfalari": kaynak_sayfalari(parke_odalar)})

    toplam_net = seramik_net + parke_net
    if hesaplanabilenler:
        # Use the dimensions actually read from each room. Perimeters are
        # summed room-by-room so shared partitions count once on each room
        # face, as required for interior finishes. Openings are not deducted
        # because dimensions cannot yet be reliably mapped to each room.
        boyanabilir_duvar = sum(
            2 * (oda["uzunluk_m"] + oda["genislik_m"]) * tavan_yuksekligi
            for oda in hesaplanabilenler
        )
        boya_litre = boyanabilir_duvar * 2 / 11 * 1.10
        astar_litre = boyanabilir_duvar / 10 * 1.10
        kalemler.extend([
            {"malzeme": "İç cephe boya (2 kat)", "miktar": round(boya_litre, 1), "birim": "L", "hesaplanan_duvar_alani_m2": round(boyanabilir_duvar, 2), "tahmin": True, "kaynak": "ölçüsü doğrulanmış odaların çevresi × tavan yüksekliği; açıklık düşümü yok", "kaynak_odalar": oda_kaynaklari(hesaplanabilenler), "kaynak_sayfalari": kaynak_sayfalari(hesaplanabilenler)},
            {"malzeme": "İç cephe astarı", "miktar": round(astar_litre, 1), "birim": "L", "hesaplanan_duvar_alani_m2": round(boyanabilir_duvar, 2), "tahmin": True, "kaynak": "ölçüsü doğrulanmış odaların çevresi × tavan yüksekliği; açıklık düşümü yok", "kaynak_odalar": oda_kaynaklari(hesaplanabilenler), "kaynak_sayfalari": kaynak_sayfalari(hesaplanabilenler)},
        ])

    # Metinde açıkça yazılı miktarlar, modelin tahminlerinden ayrı ve kaynak
    # sayfa/satır bilgileri korunarak maliyet araştırmasına aktarılır.
    for item in metin_metrajlari or []:
        try:
            miktar = float(item.get("miktar"))
            birim = str(item.get("birim", "")).strip()
            malzeme = str(item.get("malzeme", "")).strip()
            if miktar <= 0 or not birim or not malzeme:
                continue
        except (TypeError, ValueError):
            continue
        if not any(k.get("kaynak") == "belgede yazılı metraj" and k.get("malzeme", "").casefold() == malzeme.casefold() and k.get("birim") == birim and k.get("miktar") == miktar for k in kalemler):
            kalemler.append({
                "malzeme": malzeme.title(),
                "miktar": round(miktar, 3),
                "birim": birim,
                "tahmin": False,
                "kaynak": "belgede yazılı metraj",
                "sayfa": item.get("sayfa"),
                "kaynak_metni": item.get("kaynak", ""),
            })

    # Görsel AI'nin belge üzerindeki açık metraj/poz okumaları ve gerçek
    # eleman sayımları ayrı kanıt türüyle saklanır; görünür kaynak metni rapora
    # ve fiyat araştırmasına eşlik eder.
    for item in bulgular.get("acik_metrajlar", []):
        if not isinstance(item, dict):
            continue
        try:
            miktar = float(item.get("miktar"))
            birim = _birimi_normalize_et(item.get("birim"))
            malzeme = str(item.get("malzeme", "")).strip()
            tur = item.get("turu")
            kaynak_metni = str(item.get("kaynak_metni", "")).strip()
            if miktar <= 0 or not birim or not malzeme:
                continue
            if tur == "cizimde_yazili" and not kaynak_metni:
                continue
            sayfa = item.get("sayfa")
        except (TypeError, ValueError):
            continue
        yinelenen = any(
            str(k.get("malzeme", "")).casefold() == malzeme.casefold()
            and k.get("birim") == birim
            and k.get("miktar") == miktar
            and sayfa is not None
            and k.get("sayfa") == sayfa
            and _metin_kaynagi_eslesiyor(k.get("kaynak_metni"), kaynak_metni)
            for k in kalemler
        )
        if yinelenen:
            continue
        kalemler.append({
            "malzeme": malzeme.title(),
            "miktar": round(miktar, 3),
            "birim": birim,
            "tahmin": tur != "cizimde_yazili" or item.get("guven") == "dusuk",
            "kaynak": "görsel AI: çizimde yazılı miktar" if tur == "cizimde_yazili" else "görsel AI: eleman sayımı",
            "sayfa": sayfa,
            "kaynak_metni": kaynak_metni,
            "guven": item.get("guven", "belirsiz"),
        })

    aciklik_malzeme = {
        "ic_kapi": "İç kapı (tipi belirtilmemiş)",
        "celik_kapi": "Çelik giriş kapısı",
        "balkon_kapisi": "Balkon kapısı (tipi belirtilmemiş)",
        "pencere": "Pencere doğraması (malzeme belirtilmemiş)",
    }
    for aciklik in bulgular.get("aciklar", []):
        if not isinstance(aciklik, dict):
            continue
        malzeme = aciklik_malzeme.get(str(aciklik.get("tur", "")).casefold())
        adet = _sayi(aciklik.get("adet"))
        turu_kaynagi = aciklik.get("turu_kaynagi")
        kaynak_metni = str(aciklik.get("kaynak_metni", "")).strip()
        if not malzeme or adet is None or adet <= 0 or not adet.is_integer():
            continue
        if turu_kaynagi == "cizelgede_yazili" and not kaynak_metni:
            continue
        sayfa = aciklik.get("sayfa")
        kalemler.append({
            "malzeme": malzeme,
            "miktar": int(adet),
            "birim": "adet",
            "tahmin": turu_kaynagi != "cizelgede_yazili" or aciklik.get("guven") == "dusuk",
            "kaynak": "görsel AI: kapı/pencere çizelgesi" if turu_kaynagi == "cizelgede_yazili" else "görsel AI: plandaki açıklık sayımı",
            "sayfa": sayfa,
            "kaynak_metni": kaynak_metni or str(aciklik.get("olcu") or "Sembol sayımı"),
            "guven": aciklik.get("guven", "belirsiz"),
        })

    # Structural concrete volume is derived only from explicit schedule data.
    # If a concrete volume is already written on the same page (or its page is
    # unknown), skip the derived amount to avoid counting the same scope twice.
    beton_miktar_sayfalari = set()
    beton_miktari_sayfasi_belirsiz = False
    for item in metin_metrajlari or []:
        if "beton" in str(item.get("malzeme", "")).casefold() and _birimi_normalize_et(item.get("birim")) == "m³":
            if item.get("sayfa") is None:
                beton_miktari_sayfasi_belirsiz = True
            else:
                beton_miktar_sayfalari.add(item.get("sayfa"))
    for item in bulgular.get("acik_metrajlar", []):
        if not isinstance(item, dict):
            continue
        if "beton" in str(item.get("malzeme", "")).casefold() and _birimi_normalize_et(item.get("birim")) == "m³":
            if item.get("sayfa") is None:
                beton_miktari_sayfasi_belirsiz = True
            else:
                beton_miktar_sayfalari.add(item.get("sayfa"))

    beton_gruplari = {}
    atlanan_yapisal_elemanlar = []
    for eleman in bulgular.get("tasiyici_elemanlar", []):
        if not isinstance(eleman, dict):
            continue
        sayfa = eleman.get("sayfa")
        kaynak_metni = str(eleman.get("kaynak_metni", "")).strip()
        tur = str(eleman.get("tur", "")).casefold().strip()
        if beton_miktari_sayfasi_belirsiz or sayfa in beton_miktar_sayfalari:
            atlanan_yapisal_elemanlar.append(
                f"Sayfa {sayfa or '?'} {tur}: aynı kapsamda yazılı beton miktarı bulundu; olası çift sayım nedeniyle hacim ayrıca eklenmedi."
            )
            continue
        if tur not in ("kolon", "kiris", "temel", "doseme") or not kaynak_metni:
            continue
        if eleman.get("guven") not in ("yuksek", "orta"):
            continue
        adet = _sayi(eleman.get("adet"))
        birim = str(eleman.get("olcu_birimi") or "").casefold().strip()
        if adet is None or adet <= 0 or not adet.is_integer() or adet > 50000:
            continue
        boy = _uzunlugu_metreye_cevir(eleman.get("boy"), birim)
        en = _uzunlugu_metreye_cevir(eleman.get("en"), birim)
        kalinlik = _uzunlugu_metreye_cevir(eleman.get("kalinlik"), birim)
        if not all((boy, en, kalinlik)) or max(boy, en, kalinlik) > 100:
            continue
        hacim = adet * boy * en * kalinlik
        if hacim <= 0 or hacim > 10000:
            continue
        sinif_eslesmesi = re.search(r"\bC\s*\d{2}\s*(?:/\s*\d{2})?\b", str(eleman.get("beton_sinifi") or ""), re.IGNORECASE)
        sinif = re.sub(r"\s+", "", sinif_eslesmesi.group(0)).upper() if sinif_eslesmesi else "sınıfı belirtilmemiş"
        grup = beton_gruplari.setdefault(sinif, [])
        grup.append({
            "tur": tur,
            "adet": int(adet),
            "boy_m": round(boy, 3),
            "en_m": round(en, 3),
            "kalinlik_m": round(kalinlik, 3),
            "hacim_m3": round(hacim, 3),
            "sayfa": sayfa,
            "kaynak_metni": kaynak_metni,
            "guven": eleman.get("guven"),
        })

    for sinif, bilesenler in beton_gruplari.items():
        sinif_etiketi = "" if sinif == "sınıfı belirtilmemiş" else f" {sinif}"
        kalemler.append({
            "malzeme": f"Hazır beton{sinif_etiketi}",
            "miktar": round(sum(b["hacim_m3"] for b in bilesenler), 3),
            "birim": "m³",
            "tahmin": True,
            "kaynak": "çizelgede yazılı taşıyıcı eleman ölçülerinden hacim hesabı",
            "kaynak_bilesenler": bilesenler,
            "kaynak_sayfalari": sorted({b["sayfa"] for b in bilesenler if b.get("sayfa") is not None}),
            "guven": "orta" if any(b["guven"] == "orta" for b in bilesenler) else "yuksek",
        })

    def donati_miktari_mi(item):
        aciklama = " ".join((
            str(item.get("malzeme", "")),
            str(item.get("kaynak", "")),
            str(item.get("kaynak_metni", "")),
        )).casefold()
        return any(k in aciklama for k in ("demir", "donatı", "donati", "nervürlü", "nervurlu", "rebar", "inşaat çubuğu", "insaat cubugu"))

    donati_miktar_sayfalari = set()
    donati_miktari_sayfasi_belirsiz = False
    for item in metin_metrajlari or []:
        birim = _birimi_normalize_et(item.get("birim"))
        if donati_miktari_mi(item) and birim in ("kg", "ton"):
            if item.get("sayfa") is None:
                donati_miktari_sayfasi_belirsiz = True
            else:
                donati_miktar_sayfalari.add(item.get("sayfa"))
    for item in bulgular.get("acik_metrajlar", []):
        if not isinstance(item, dict):
            continue
        birim = _birimi_normalize_et(item.get("birim"))
        if donati_miktari_mi(item) and birim in ("kg", "ton"):
            if item.get("sayfa") is None:
                donati_miktari_sayfasi_belirsiz = True
            else:
                donati_miktar_sayfalari.add(item.get("sayfa"))

    donati_gruplari = {}
    atlanan_donati_cubuklari = []
    for cubuk in bulgular.get("donati_cubuklari", []):
        if not isinstance(cubuk, dict) or cubuk.get("guven") not in ("yuksek", "orta"):
            continue
        sayfa = cubuk.get("sayfa")
        kaynak_metni = str(cubuk.get("kaynak_metni", "")).strip()
        if not kaynak_metni:
            continue
        if donati_miktari_sayfasi_belirsiz or sayfa in donati_miktar_sayfalari:
            atlanan_donati_cubuklari.append(
                f"Sayfa {sayfa or '?'} Ø{cubuk.get('cap_mm', '?')}: aynı kapsamda yazılı donatı kg/ton miktarı bulundu; olası çift sayım nedeniyle çubuk hesabı eklenmedi."
            )
            continue
        cap = _sayi(cubuk.get("cap_mm"))
        adet = _sayi(cubuk.get("adet"))
        tekil_boy = _sayi(cubuk.get("boy_m"))
        toplam_boy = _sayi(cubuk.get("toplam_boy_m"))
        if cap is None or cap < 6 or cap > 50:
            continue
        if toplam_boy is not None and toplam_boy > 0:
            toplam_uzunluk = toplam_boy
        elif adet is not None and adet > 0 and adet.is_integer() and adet <= 50000 and tekil_boy is not None and tekil_boy > 0:
            toplam_uzunluk = adet * tekil_boy
        else:
            continue
        if toplam_uzunluk > 5000000:
            continue
        # Nominal circular area (mm²) × steel density (0.00785 kg/mm² per m).
        kg_metre = (math.pi * (cap ** 2) / 4) * 0.00785
        agirlik_kg = toplam_uzunluk * kg_metre
        if not 0 < agirlik_kg < 100000000:
            continue
        sinif_eslesmesi = re.search(r"\b(?:B\d{3}[A-Z]?|S\d{3})\b", str(cubuk.get("celik_sinifi") or ""), re.IGNORECASE)
        sinif = sinif_eslesmesi.group(0).upper() if sinif_eslesmesi else ""
        donati_gruplari.setdefault((round(cap, 2), sinif), []).append({
            "cap_mm": round(cap, 2),
            "adet": int(adet) if adet is not None and adet > 0 and adet.is_integer() else None,
            "boy_m": tekil_boy,
            "toplam_boy_m": round(toplam_uzunluk, 3),
            "kg_metre": round(kg_metre, 4),
            "agirlik_kg": round(agirlik_kg, 2),
            "celik_sinifi": sinif,
            "sayfa": sayfa,
            "kaynak_metni": kaynak_metni,
            "guven": cubuk.get("guven"),
        })

    for (cap, sinif), bilesenler in donati_gruplari.items():
        sinif_etiketi = f" {sinif}" if sinif else ""
        kalemler.append({
            "malzeme": f"İnşaat donatısı Ø{cap:g} mm{sinif_etiketi}",
            "miktar": round(sum(b["agirlik_kg"] for b in bilesenler), 2),
            "birim": "kg",
            "tahmin": True,
            "kaynak": "donatı çizelgesindeki çap ve çubuk boylarından teorik ağırlık hesabı",
            "kaynak_donati_cubuklari": bilesenler,
            "kaynak_sayfalari": sorted({b["sayfa"] for b in bilesenler if b.get("sayfa") is not None}),
            "guven": "orta" if any(b["guven"] == "orta" for b in bilesenler) else "yuksek",
        })

    if not hesaplanabilenler and not kalemler:
        return {
            "durum": "olcu_yetersiz",
            "oda_alanlari": [],
            "malzeme_miktarlari": [],
            "hesaplanamayan_odalar": atlanan_odalar,
            "hesaplanamayan_yapisal_elemanlar": atlanan_yapisal_elemanlar,
            "hesaplanamayan_donati_cubuklari": atlanan_donati_cubuklari,
            "varsayimlar": ["Oda boyutları veya ölçü birimi güvenilir biçimde çözümlenemedi."],
            "kapsam_disi": ["Beton, donatı, duvar, kapı/pencere ve tesisat metrajı için yeterli çizim/spec bilgisi yok."],
        }

    return {
        "durum": "yaklasik_on_metraj" if hesaplanabilenler else "belgedeki_metrajlar",
        "oda_alanlari": hesaplanabilenler,
        "toplam_hesaplanan_net_alan_m2": round(toplam_net, 2),
        "malzeme_miktarlari": kalemler,
        "hesaplanamayan_odalar": atlanan_odalar,
        "hesaplanamayan_yapisal_elemanlar": atlanan_yapisal_elemanlar,
        "hesaplanamayan_donati_cubuklari": atlanan_donati_cubuklari,
        "varsayimlar": [
            "Oda alanından türetilen kaplama ve boya miktarlarına yalnızca çizimde yazılı olduğu işaretlenen oda ölçüleri dahil edilir; tahmini/belirsiz ölçüler fiyatlandırılan miktara katılmaz.",
            (
                f"Çizimde birimi olmayan oda ölçüleri kullanıcı seçimiyle {olcu_birimi_varsayimi} kabul edilmiştir; bu ölçülere dayanan miktarlar öngörüdür."
                if birim_varsayimi_kullanildi
                else "Çizimde birimi olmayan oda ölçüleri için varsayım seçilmedi; bu odalar metraj ve maliyete alınmadı."
            ),
            (
                "Banyo, WC, mutfak ve balkon/teras seramik; diğer odalar laminat parke varsayılmıştır."
                if kuru_alan_kaplamasi == "laminat"
                else "Bütün ölçüsü doğrulanmış odalarda seramik zemin kaplaması varsayılmıştır."
            ),
            "Seramik yapıştırıcısı, seramik net alanı için üretici teknik föyündeki 3–5 kg/m² tüketim aralığıyla hesaplanır. Ürün, tarak dişi, yüzey düzgünlüğü ve uygulamaya göre değişebilir. Derz dolgusu; karo ölçüsü ve derz genişliği bilinmediğinden hesaplanmamıştır.",
            f"Kaplama miktarına kullanıcı ayarı olan %{fire_yuzdesi:g} kesim/fire payı eklenmiştir.",
            f"Duvar boya/astar alanı, ölçüsü doğrulanmış her oda için 2 × (uzunluk + genişlik) × {tavan_yuksekligi:.2f} m tavan yüksekliğiyle hesaplanmıştır. Kapı ve pencere açıklıkları düşülmemiştir; ortak duvarlar oda yüzü başına sayılır.",
            "Boya 2 kat ve 11 m²/L; astar 10 m²/L yayılım ve her ikisine %10 uygulama payı varsayılmıştır. Ürün teknik föyü ve yüzey durumuna göre değişir.",
            "Donatı teorik ağırlığı nominal dairesel kesit alanı × 0,00785 kg/mm²/m çelik yoğunluğuyla hesaplanır; kanca, büküm, bindirme, tolerans ve saha kaybı eklenmez.",
        ],
        "kapsam_disi": [
            "Donatı miktarı; çap, çubuk adedi ve boy çizelgede açık değilse hesaplanamaz. Beton hacmi yalnızca yeterli ölçü ve adet bilgisi içeren taşıyıcı eleman çizelgelerinden türetilir.",
            "Duvar örme/sıva, kapı-pencere, elektrik ve mekanik tesisat; duvar geometrisi, açıklık ölçüleri ve teknik şartname olmadan hesaplanamaz.",
        ],
    }
