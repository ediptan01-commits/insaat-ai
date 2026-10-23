# insaat-ai

İnşaat ustaları için yapay zekâ destekli ölçü defteri.

## Proje analizi ve yaklaşık ön metraj

Yükleme uçları PDF ve görselleri 50 MB ile sınırlar ve geçici dosyaya parça parça yazar; boyut sınırı aşılırsa anlaşılır bir hata döner. Yükleme formunda kuru odalar için laminat veya tüm odalar için seramik ön metraj varsayımı seçilebilir; bu tercih miktar, teknik föy tüketimi ve maliyete yansıtılır.

Görsel analiz, yalnızca paftada açıkça yazılmış ve adı ölçülü odayla eşleşen seramik/laminat kaplama notlarını varsayımdan öncelikli kullanır. Belirsiz kaplama notu olan oda kaplama maliyetine katılmaz; kaynak notu ve oda eşleşmesi raporda görünür.

Belgede seramik, fayans, parke veya laminat için açık m² metrajı varsa aynı sınıftaki oda alanları toplam miktara ikinci kez eklenmez. Oda adı kaynak satırında eşleşirse yalnızca o odanın türetilmiş alanı atlanır; oda kapsamı yazmayan toplam metraj, ilgili malzeme sınıfındaki tüm türetilmiş oda alanlarının yerine kullanılır ve atlananlar raporlanır.

İç cephe boya ve astar miktarı, ölçüsü doğrulanmış oda çevrelerinden hesaplanan duvar alanına ve seçilmiş üretici ürünlerindeki kapsama aralığına dayanır: [Primera Plast boya, 11–13 m²/L/kat](https://polisan.com.tr/primera-plast_p14337), [Dolgulu Astar, 10–12 m²/L/kat](https://polisan.com.tr/dolgulu-astar_p123). Boyada iki kat, astarda tek kat ve %10 uygulama payı alınır; miktar ve maliyet aralığı ürün kaynağıyla gösterilir.

Render'a dağıtım için ZIP içindeki bütün dosyaları ve alt klasörleri aynı sürümden birlikte yükleyin. Yalnızca `main.py` dosyasını değiştirmek analiz ajanı ile metraj servisini farklı sürümlerde bırakabilir; `/health` yanıtındaki `analiz_bilesenleri_uyumlu` alanı bileşen sözleşmelerini kontrol eder.

Ürün tipi veya teknik sınıfı açıkça belirtilmemiş malzemelere kaynaklı karşılaştırılabilir fiyat bulunmuş gibi maliyet yazılmaz; satır, eksik özellik açıklamasıyla raporda kalır.

Uygulama PDF'nin bütün sayfalarındaki mevcut metin çıkarımını `pypdf` ile sürdürür.
PyMuPDF, görsel analiz sınırına kadar olan sayfaları en fazla 2000 piksel uzun
kenarlı PNG'ye dönüştürür; sınır üstündeki sayfalar gereksiz yere belleğe
yüklenmez ve raporda görünür. Tekil JPG/JPEG, PNG ve WEBP görselleri de yüklenebilir; bunlar
Pillow ile doğrulanıp aynı görsel analiz girdi yapısına eklenir. Görseller
`pdf_oku()` veya `gorsel_dosyasi_oku()` sonucundaki
`gorsel_analiz_girdisi.sayfalar[]` alanında MIME türüne uygun veri URL'leri
olarak bulunur. `ProjectAgent.analyze()` bu sayfaları OpenAI Responses API
üzerinden görsel analizine gönderir. Render ortamında `OPENAI_API_KEY`
tanımlanmalıdır; model adı `OPENAI_VISION_MODEL` ile değiştirilebilir
(varsayılan `gpt-4.1-mini`). Sayfalar 8'erli gruplar halinde işlenir;
`MAX_VISION_PAGES` varsayılan olarak 40 sayfadır. Sınırı aşan ya da servis
hatası nedeniyle işlenemeyen sayfalar raporda gösterilir.

`servisler/quantity_service.py` görsel ajanın oda ölçülerinden oda alanlarını,
seramik ve laminat zemin metrajını, yaklaşık iç cephe boya/astar ihtiyacını
çıkarır. Boya ve astar için duvar alanı, ölçüsü doğrulanmış odaların çevresi
ile seçilen tavan yüksekliğinin çarpımlarının toplamıdır; ortak duvarlar oda
yüzü başına sayılır, kapı/pencere açıklıkları düşülmez. Seramik alanına bağlı
boya ve astar, ölçüsü doğrulanmış oda duvar alanına dayalı aralıkla raporlanır: [Primera Plast 11–13 m²/L/kat](https://polisan.com.tr/primera-plast_p14337), [Dolgulu Astar 10–12 m²/L/kat](https://polisan.com.tr/dolgulu-astar_p123). Seramik alanına bağlı yapıştırıcı ihtiyacı, [Kalekim 1051 teknik föyündeki 3–5 kg/m² tüketim aralığı](https://www.kalekim.com/int-tr/1051-kalekim)
ile miktar ve maliyet aralığı olarak raporlanır; karo/derz bilgisi olmadan
derz dolgusu hesaplanmaz. Sarfiyat ve uygulama
payı varsayımları raporda gösterilir. Oda alanından türetilen fiyatlandırılabilir miktarlara yalnızca
çizimde yazılı olduğu belirtilen oda ölçüleri girer. Birimi çizimde görünmeyen
ölçüler varsayılan olarak dışarıda bırakılır; kullanıcı yükleme formunda cm veya
m varsayımını seçerse bu ölçülere dayanan metraj tahmin olarak işaretlenir.
Tahmini ölçüler varsayım seçilmediğinde fiyatlandırılan miktara katılmaz;
sonuç ekranında dışarıda bırakılma nedeni gösterilir. Kaplama fire payı,
boya sarfiyatı ve oda alanı katsayıları yaklaşık ön metraj varsayımlarıdır;
statik, tesisat, duvar, kapı/pencere ve kesin uygulama miktarları için gerekli
çizim ve teknik şartname yoksa uygulama bunları hesaplanamayan kalemler olarak
belirtir.
Taşıyıcı çizelgede eleman tipi, adet, üç boyut ve ölçü birimi okunabiliyorsa
kolon/kiriş/temel/döşeme beton hacmi bu değerlerden türetilir ve kaynak satırı
ile raporlanır. Aynı sayfada beton hacmi zaten yazılıysa çift sayımı önlemek
için bu türetme yapılmaz. Donatı çizelgesinde çap ve toplam çubuk boyu (veya
adet × tekil boy) yazıyorsa teorik kg miktarı nominal dairesel kesit alanı ve
0,00785 kg/mm²/m çelik yoğunluğuyla hesaplanır. Kaynak satırı ve hesap
bileşenleri gösterilir; kanca, bindirme, fire ve saha kaybı eklenmez. Aynı
sayfada donatı kg/ton metrajı yazılıysa türetme çift sayımı önlemek için
atlanır. Kullanılan nominal kütle yaklaşımı [CEDD Construction Standard 2](https://www.cedd.gov.hk/filemanager/eng/content_77/CS2-2012-Rev-05-180926.pdf)
ile uyumludur.

Görsel ajan, okunabilir pafta sınıflarını ve açıkça yazılmış metraj satırlarını
sayfa numarası ve kaynak metniyle raporlamaya çalışır. Görselden sayılan
elemanlar “öngörülen”, doğrudan yazılı miktarlar “belgede yazılı” olarak
ayrılır. Aynı sayfa/malzeme/miktar için kaynak satırı da eşleşirse metin ve
görsel okuması çift sayılmaz. Rapor, belge üzerinde okunan değerleri,
hesaplanmış oda alanlarını ve açık ölçü birimi varsayımlarını ayrı ayrı gösterir.
Türetilmiş malzeme miktarları ve fiyat satırları dayanak oda adlarını,
sayfa numaralarını ve okunan ölçü metnini de gösterir. Fiyat tablosunda bu
metraj dayanağı, tedarikçi fiyat kaynaklarından ayrı sunulur.
Metin tabanlı bir satırdaki miktar birden fazla malzeme adıyla eşleşirse
otomatik toplam dışında bırakılır ve satır sonuç raporunda doğrulama için
gösterilir; olası çift sayım maliyete taşınmaz.
Yazılı metraj taraması tuğla ve gazbetonun yanında bims/briket blokları;
gazbeton ve seramik yapıştırıcısı, derz dolgusu, duvar örme harcı ve hazır
sıva harcı gibi yaygın sarf malzemelerini de birimleriyle tanır. Bu kalemler
yalnızca belgede miktar ve uyumlu birim açıkça yazıyorsa maliyet araştırmasına
aktarılır.
Metin metrajı sayı çözümleyicisi Türkçe binlik ve ondalık ayırıcıları birlikte
okumayı destekler (ör. `1.250,50 m³`).

`agents/pricing_agent.py` Responses API web aramasıyla Türkiye'deki güncel
tedarikçi fiyatlarını araştırır. Fiyata yalnızca arama sonuçlarında bulunan
URL'lerle eşleşen ve istenen birimle uyumlu gözlenen teklifler girer. İki farklı
tedarikçi alan adı bulunursa aralık hesaplanır; tek doğrulanmış kaynak varsa
gözlenen fiyat tek kaynak etiketiyle gösterilir. Yalnızca HTTP/HTTPS kaynakları
kullanılır; aynı URL ve aynı fiyatın tekrarlanan alıntıları tekilleştirilir.
Fiyat bulunamazsa tahmini değer üretilmez. Yükleme formundaki
fiyat bölgesi (varsayılan Türkiye geneli) arama konumunu etkiler;
`OPENAI_PRICE_MODEL` fiyat araştırma modelini belirler. Görsel ve fiyat ajanı hatalarında metin analizi sürer;
durum raporlanır. Web araması ve model kullanımının OpenAI API ücretleri
olabilir.
Fiyat araştırması en fazla üç farklı malzeme/birimlik gruplar halinde yapılır; aynı
kalem yinelenen metraj satırlarında tekrar aranmaz. Bir grup başarısız olsa
bile diğer grupların sonuçları korunur. Fiyat tablosu, fiyatı doğrulanan malzeme satırı sayısını ve toplam satıra
oranını gösterir. Araştırma başarısız olsa veya API anahtarı eksik olsa bile
metraj satırları fiyat durumu ve kaynak dayanağıyla raporda korunur.

Yükleme formunda fiyat bölgesi, kaplama fire yüzdesi (0–25) ve tavan
yüksekliği (2–5 m) ayarlanabilir. Açıklık sayımları kapı/pencere miktarına
aktarılır ve çizelge verisi ile görsel sayım raporda birbirinden ayrılır.

Dosya yükleme alanında veri işleme bilgisi kullanıcıya gösterilir: görsel
inceleme için proje sayfalarının görselleri, fiyat araştırması için çıkarılan
malzeme ve miktar özeti sunucuda yapılandırılmış OpenAI API'ye gönderilir.
Dosyalar, yapılandırılmış model sağlayıcısı üzerinden işlenir; hassas veya
kişisel bilgiler içeren belgeler yüklenmeden önce kullanıcı tarafından gözden
geçirilmelidir.

Görsel/fiyat bulguları yaklaşık ön incelemedir; teklif, kesin keşif veya
mühendislik onayı değildir.
Sonuç ekranındaki “Raporu yazdır / PDF olarak kaydet” düğmesi, tabloları A4 yatay
sayfa düzeninde tarayıcı yazdırma penceresine gönderir.

Bir PDF sayfasının görseli oluşturulamazsa PDF metin analizi çalışmaya devam
eder; ilgili sayfanın `gorsel.durum` alanı `olusturulamadi` olur ve hata kodu
raporda sunulur. PyMuPDF kurulu değilse görsel analiz durumu ayrıca belirtilir.

## Render dağıtımı

Render build adımında `pip install -r requirements.txt` kullanın. PyMuPDF,
gerekli PDF render bileşenlerini Python paketiyle sağladığından ayrıca
Poppler veya sistem paketi kurulumu gerekmez. Mevcut başlatma biçimi
(ör. `uvicorn main:app --host 0.0.0.0 --port $PORT`) değişmeden kalabilir.

