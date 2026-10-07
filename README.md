# insaat-ai

İnşaat ustaları için yapay zekâ destekli ölçü defteri.

## PDF analizi

Uygulama PDF sayfalarındaki mevcut metin çıkarımını `pypdf` ile sürdürür.
Ek olarak PyMuPDF her sayfayı en fazla 2000 piksel uzun kenarlı PNG'ye
dönüştürür. Görseller `pdf_oku()` sonucundaki
`gorsel_analiz_girdisi.sayfalar[]` alanında `data:image/png;base64,...`
veri URL'leri olarak bulunur. Bu alan doğrudan bir sonraki görsel AI
adaptörüne aktarılabilecek şekilde düzenlenmiştir.

`ProjectAgent.analyze()` bu girdi sayfalarının sayısını ve arayüz durumunu
raporlar. Henüz bir görsel AI servisi çağrılmadığı için metraj sonuçları
mevcut metin analizinden gelir. Bir sayfanın görseli oluşturulamazsa PDF
metin analizi çalışmaya devam eder; ilgili sayfanın `gorsel.durum` alanı
`olusturulamadi` olur.

## Render dağıtımı

Render build adımında `pip install -r requirements.txt` kullanın. PyMuPDF,
gerekli PDF render bileşenlerini Python paketiyle sağladığından ayrıca
Poppler veya sistem paketi kurulumu gerekmez. Mevcut başlatma biçimi
(ör. `uvicorn main:app --host 0.0.0.0 --port $PORT`) değişmeden kalabilir.
