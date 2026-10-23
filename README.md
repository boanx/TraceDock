<img src="tracedock.png" alt="TraceDock logosu" width="96" />

# TraceDock

**Hazırlayan: Ahmet Yusuf Ozyurt**

CSV, NI TDMS ve Exlab ölçüm verilerini zaman çizelgesinde düzenlemek, karşılaştırmak ve dışa aktarmak için Windows masaüstü uygulaması.

## Exlab desteği

**Exlab ile toplanmış ölçüm verileri işlenebilir.** Exlab üzerinden CSV, TXT veya TSV olarak dışa aktarılan dosyalar ve desteklenen TDMBIN kayıtları, **Exlab dosyası ekle** düğmesiyle yüklenir. Kanal adları, birimler ve desteklenen zaman damgaları korunur.

Exlab `.tdmbin` dosyaları **Exlab dosyası ekle** düğmesiyle doğrudan açılır. Gönderilen EX1629 kaydıyla aynı v8 / double biçimi ve kanallara göre bloklu veya satır sıralı düzen desteklenir. Bilinmeyen sürüm ve veri düzenleri açıklayıcı hatayla reddedilir.

## Temel özellikler

- CSV, Strain Gauge / Exlab ve NI TDMS içe aktarma.
- Her kaynak veya kanal için frekans, test süresi, ad ve çarpan düzenleme.
- Çok satırlı zaman çizelgesi: aynı satırdaki paketleri uç uca ekleme, farklı satırları aynı grafikte üst üste gösterme.
- Dosya/Kanal sütununda sağ tıklayarak mevcut veya yeni satıra işaretli kanalları ekleme.
- Grafik yalnızca zaman çizelgesindeki paketleri gösterir; kaynak seçimi grafiğe otomatik eğri eklemez.
- Yakınlaştırma, kaydırma, çapraz imleç, prob ve kanal istatistikleri.
- Görünür veya seçili aralığı CSV'ye, grafiği PNG'ye aktarma; nokta/virgül ondalık seçimi.
- Büyük dosyalarda arka plan işlemleri, çok çekirdekli okuma ve ayrıntı düzeyine göre grafik çizimi.
- Liquid Glass görünümü, kaydırılabilir sol panel ve ayarlanabilir alt paneller.

Kaynaklar arasında otomatik frekans eşitlemesi yapılmaz. Her paket özgün örneklerini korur. TDMS dönüşümü sırasında aynı dosyanın kanalları en yüksek kanal hızına eşitlenir; bu işlem diğer kaynakların frekansını değiştirmez.

Zaman çizelgesinde örneklerin zamanı kanalın **Hz** ayarından hesaplanır: `paket başlangıcı + örnek indeksi / Hz`. Kaynak zaman sütunundaki duraklamalar veya saat sıfırlanmaları çizelgeye taşınmaz. Paket süresi, eklenen kanalların en büyük `N/Hz` değeridir. Aynı satırdaki ikinci paket ilk paketin bittiği anda başlar; prob etiketleri, prob tablosu ve CSV çıktısı bu birikimli zamanı kullanır. Örneğin 100 Hz'de 1.000 örnekten sonra ikinci paket **00:00:10.0000** noktasında başlar. Daha kısa kanalların eksik ölçümleri doldurulmaz.

İsteğe bağlı **Seçili kanal sırasına göre** eşleştirmesi, paketlere eklenen kanalların ilkini ilkine, ikincisini ikincisine bağlar (kaynak tablodaki sıralarıyla). Kanal adlarının veya kaynak sütun numaralarının aynı olması gerekmez. Birleştirilecek kanalları her pakette aynı sırada seçin. Eşleşen parçalar aynı renkte çizilir; paket sınırındaki son ve ilk örnekler, çarpanları farklı olsa da bağlanır. Çarpan yalnızca Y değerini değiştirir. Ad veya kaynak sütun numarasıyla eşleştirme ve **Ayrı çizgiler** seçenekleri de kullanılabilir.

## İndirme

[Windows için TraceDock.exe](https://github.com/boanx/TraceDock/releases/latest/download/TraceDock.exe) · [Tüm sürüm dosyaları](https://github.com/boanx/TraceDock/releases/latest)

## Kullanım

1. `TraceDock.exe` dosyasını açın. Paketlenmiş EXE için Python kurulumu gerekmez.
2. CSV, Strain Gauge / Exlab veya TDMS dosyanızı yükleyin.
3. **Dosya/Kanal** sütununda dosyaya veya kanala sağ tıklayın.
4. Dosya satırına sağ tıkladığınızda yalnızca o dosyanın işaretli kanalları eklenir. **Mevcut satıra ekle** veya **Yeni satıra ekle** seçeneğini kullanın.
5. Satır içindeki paketleri sürükleyerek sıralayın veya başka bir satıra taşıyın.
6. Gerekirse Hz, süre veya çarpan hücresine çift tıklayarak düzenleyin.

### Toplu kanal seçimi

Bir kanala tıklayın, **Shift** basılıyken başka bir kanala tıklayarak aralığı seçin. **Ctrl+tık** ile ayrı kanalları seçime ekleyip çıkarabilirsiniz. Seçili satırlar üzerinde kutucuğa tıklayın veya **Boşluk** tuşuna basın; kutucuklar topluca güncellenir.

Kanal gruplama etiketleri kaldırılmıştır. Prob üzerindeki değer etiketleri kullanılmaya devam eder.

### Birden fazla Y ekseni

En fazla **Sol 1, Sol 2, Sağ 1 ve Sağ 2** olmak üzere dört bağımsız Y ekseni kullanılabilir.

- **Y eksenleri** düğmesi: zaman çizelgesindeki kanalları seçip eksene atayın. Shift / Ctrl ile çoklu seçim desteklenir.
- **Dosya/Kanal → sağ tık → Y eksenine ata** veya **Y ekseni** hücresine çift tık: kaynak kanalın eksenini seçin.
- Grafikte **lejanttaki kanal adına tıklayın**: o eğriyi bir eksene atayın.
- Aynı satırda eşleştirilen kanalın ardışık paketleri aynı eksende devam eder. Ayrı satırlardaki eğriler farklı eksenlere atanabilir.
- Eksen üzerindeki fare tekerleği yalnızca o Y eksenini yakınlaştırır. Grafik içindeki tekerlek bütün eksenleri ortak zaman etrafında yakınlaştırır.
- Kullanılan eksenler otomatik gösterilir; lejant kanalın eksenini belirtir. PNG bütün eksenleri içerir. CSV ölçüm değerleri dönüştürülmez.

Atamalar mevcut oturum içindir. **Tümünü Sol 1’e al** ile tek eksen görünümüne dönebilirsiniz.

### Grafik fare kontrolleri

| Hareket | İşlev |
| --- | --- |
| Sol tuşla sürükle | Aralık seç |
| Sağ tuşla sürükle | Grafiği kaydır |
| Sol tık | Prob ekle / kaldır |
| Prob üzerinde sağ tık | Prob etiketini aç / kapat |
| Fare tekerleği | Yakınlaştır / uzaklaştır |
| Orta tuşla sürükle | X / Y eksenlerini yakınlaştır |

**Lejantı göster** kutusuyla grafik lejantını gizleyebilir veya açabilirsiniz. Bu seçim yakınlaştırma ve prob işlemleri sırasında korunur; PNG çıktısına da yansır.

Ayrıntılar: [Kullanım kılavuzu](Kullanim.txt).

Zaman çizelgesi mevcut oturum içindir; program kapatıldığında saklanmaz. Yerel pencere cam efekti Windows sürümünün desteğine bağlıdır.

## Kaynaktan çalıştırma

Python 3.12 ve Tkinter gerekir. Windows için standart Python kurulumu Tkinter içerir.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python TraceDock.py
```

## Tek EXE oluşturma

```powershell
python -m pip install -r requirements-build.txt
.\build.ps1
```

Çıktı: `dist/TraceDock.exe`. İkon ve logo EXE içine eklenir. Oluşturma komutu otomatik test çalıştırmaz.

## Proje dosyaları

- `TraceDock.py`: ana uygulama.
- `tracedock_workers.py`: paralel veri okuma ve CSV biçimlendirme.
- `tracedock_theme.py`: tema, düğmeler ve uygulama içi pencereler.
- `Kullanim.txt`: Türkçe kullanım kılavuzu.
- `build.ps1`: taşınabilir Windows EXE oluşturma komutu.

Ölçüm dosyaları ve kullanıcı ayarları depoya dahil edilmez.

## Kriptografik imza

Commit ve sürüm etiketi Ed25519 / SSH ile imzalanır. EXE için aynı anahtarla oluşturulan **ayrık imza** (`TraceDock.exe.sig`) ve SHA-256 özeti sürüm dosyaları arasında yayımlanır. Doğrulama adımları: [SIGNING.md](SIGNING.md).

Ayrık imza, Windows Authenticode yayıncı sertifikası değildir. EXE için güvenilir yayıncı / SmartScreen garantisi sağlamaz. GitHub “Verified” rozeti için açık imza anahtarının hesap ayarlarında kayıtlı olması gerekir.


Kanal sonundaki boş / NaN / sonsuz hücreler tablo dolgusu kabul edilir ve kanal süresini uzatmaz. Sonlu sıfır değerleri ile kanalın başındaki veya ortasındaki eksik ölçümler korunur. Kaynak dosya değiştirilmez. Varsayılan eşleştirme **Kanal adına göre** seçeneğidir; farklı adlı kanalların ayrı Y eksenleri korunur.


## Dinamik yerleşim

Pencere büyütülüp küçültüldüğünde sol panel, grafik, istatistik/prob paneli ve zaman çizelgesi oranlı boyutlanır. Ayırıcıyı sürükleyerek seçtiğiniz oran sonraki boyut değişimlerinde korunur.

Kanal, istatistik, prob, TDMS ayarları ve Y eksenleri tablolarında sütunlar başlık ve hücre metinlerine göre genişler. İçerik pencereye sığmazsa yatay/dikey kaydırma çubukları otomatik görünür. Shift+fare tekerleği tabloyu yatay kaydırır. Uzun dosya adları ve dar araç çubukları da yatay kaydırılabilir.

TDMS, Y eksenleri ve bilgi/giriş pencereleri ekran ve ana pencere boyutuna göre açılır; yeniden boyutlandırılabilir.


## 21 Ekim 2026 — Kompakt düğmeler ve ekran ölçeği

- Aktarma düğmeleri tek yatay sırada kalır; panel daralınca yatay kaydırma çubuğu görünür. Grafik CSV, seçili aralık CSV, istatistik CSV ve grafik PNG işlevleri korunur.
- Veri dosyası düğmeleri paneli dolduracak şekilde uzamaz; aynı uyarlanabilir satır düzenini kullanır. Dosya listesi kayıt sayısına göre1–4 satırdır; fazlası kaydırılır.
- `tracedock_dpi.py` Tk penceresi açılmadan Windows Per Monitor V2 farkındalığı ister. Monitör değişince pencere DPI'sı izlenir; Tk fontları, özel düğmeler ve tablo sütun ölçümleri yenilenir. Matplotlib'in kendi piksel oranı ayrıca çarpılmaz.
- `build.ps1`, `TraceDock.manifest` dosyasını EXE'ye gömer. Bu manifest DPI sanallaştırmasının neden olabileceği bitmap bulanıklığını engellemeyi amaçlar. Laptop/harici monitör keskinliği bu değişiklikle henüz fiziksel olarak doğrulanmadı; panel çözünürlüğü veya Windows metin işleme etkileri için sonuç gözlenmeli.
- v1.0.9 EXE bu düzeni ve DPI bildirimini içerir. Farklı fiziksel ekranlardaki keskinlik henüz doğrulanmadı.

Sol panel başlangıçta pencere genişliğinin yaklaşık %24’ünü kullanır; ayırıcıyla oran değiştirilebilir. Panel içeriği mevcut genişliğe uyar, uzun kanal metinleri tablonun kendi kaydırma çubuğuyla okunur. Gömülü Matplotlib grafiği monitör değişiminde piksel oranını yeniden hesaplar.


## Monitörler arasında tutarlı ölçek (v1.0.10)

Fontların asıl punto değerleri saklanır; her monitörde DPI değerinden yeniden hesaplanan piksel boyutları kullanılır. Başlıklar, etiketler, girişler, düğmeler ve ttk stilleri aynı font sistemini paylaşır. Tablo sütunları gerçek hücre ve başlık fontlarıyla ölçülür. Zaman çizelgesinin satırları, sol başlık alanı ve sürükleme/tıklama koordinatları aynı ölçekle çizilir. Aktarma düğmeleri tek sırada kalır; dar alanda yatay kaydırılır.
İki fiziksel monitör arasında geçiş bu geliştirme sırasında doğrulanmadı; EXE paketlemesi ve ayrık imza doğrulaması işlev testi değildir.


## Doğrudan Exlab TDMBIN içe aktarma (v1.0.11)

“Exlab dosyası ekle” düğmesiyle .tdmbin, .csv, .txt, .tsv ve .asc dosyaları seçilebilir. TDMBIN için ara CSV üretilmez; okuma arka planda, ilerleme ve iptal desteğiyle yapılır. Kanal adları, ID, birimler ve dosyadaki sayısal örnekler korunur. Dosyanın zaman kanalı ölçüm kanalından ayrılır; kanal frekansı başlıktan alınır. İçe aktarılan kanallar mevcut zaman çizelgesi, çarpan, Y ekseni, prob ve dışa aktarma araçlarında kullanılır.
Desteklenen ikili biçim: Exlab TDMBIN sürüm 8, double (float64), 182 baytlık kanal kayıtları; düzen 0 ve 1. Dosya boyutu, bölüm sınırları ve blok/paket sayıları kontrol edilir. Kanal metadata alanlarındaki ek katsayılar otomatik uygulanmaz. Kaynak dosya değiştirilmez.


## Ayarlanabilir filtre frekansı (v1.0.13)

Aktarma düğmelerinin altındaki “Kesim (Hz)” alanına düşük geçiren filtrenin kesim frekansını girip “Uygula” düğmesine basın veya Enter kullanın. Örneğin 10, 20 veya 12,5 girilebilir; nokta ve virgül kabul edilir. “Uygula” filtreli görünümü açar. “Filtreli görünüm” kutusunu kapatarak ham veriye dönebilirsiniz. Varsayılan değer 10 Hz, başlangıç görünümü hamdır. Girilen değer, yüklenen tüm kanallarda örnekleme hızının yarısından küçük ve sıfırdan büyük olmalıdır. Uygun değilse engel olan kanal ve sınır gösterilir; değer otomatik kırpılmaz.

Her kanal kendi örnekleme hızıyla filtrelenir; kaynakların hızları eşitlenmez. Dördüncü dereceden Butterworth düşük geçiren filtre ileri ve geri uygulanır. Birleşik yanıtın −3 dB noktası girilen Hz değeridir (iki geçiş için tasarım frekansı telafi edilir). Örnek sayısı ve zaman konumları korunur; zaman gecikmesi eklenmez. Kesim frekansı üzerindeki gerçek sinyal bileşenleri de zayıflar. Bu özellik bir 50 Hz çentik filtresi değildir.

Kaynak dosya ve ham örnekler değiştirilmez. Filtre arka planda ilerleme ve iptal desteğiyle hazırlanır. Hazırlık sırasında önceki görünüm korunur; yeni sonuç tamamlanınca birlikte devreye girer. İptal veya hatada önceki sonuç geçerlidir. Ayrı kaynaklar ve eksik ölçüm aralıkları üzerinden filtre uygulanmaz. Eksik değerler korunur; üç örnekten kısa sonlu parçalar ham kalır. Kısa parçalar ile kayıt/boşluk kenarlarında filtre sınır etkileri olabilir.

Grafik, problar, istatistikler, CSV ve PNG etkin görünümü kullanır. Filtreli kanal başlıklarında “[filtreli: 10 Hz]” gibi gerçek kesim frekansı, PNG üzerinde de filtreli görünüm etiketi bulunur. Dosya adlarına varsayılan olarak “-filtreli” eklenir. Ham dışa aktarma için kutuyu kapatın. Çarpanlar filtreli değerlerin üzerine uygulanır. Hz veya süre değiştiğinde eski filtre önbelleği geçersiz olur; ham görünüme dönülür ve filtre yeniden uygulanmalıdır. Yeni kaynak eklendiğinde de filtreyi yeniden uygulayın.

Filtre tasarımı: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html
İleri/geri uygulama: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sosfiltfilt.html

## Açılır kutu ve araç satırı yerleşimi (v1.0.14)

Açılır kutular aynı ölçülen yazı tipini kullanır; varsayılan seçim ve liste seçenekleri için genişlik hesaplanır. Monitör ölçeği değiştiğinde araç satırları doğal içerik yüksekliğini yeniden alır. Zaman çizelgesi ve grafik araç çubuklarında yazının kırpılmasına ve eski satır yüksekliğinden kalan boşluklara neden olan sabit gömülü çerçeve yüksekliği kaldırıldı. Sığmayan satırlarda yatay kaydırma korunur. Fiziksel monitörlerde arayüz testi çalıştırılmadı.

## Daraltılabilir paneller (v1.0.15)

Zaman çizelgesindeki “Daralt” düğmesi paneli yalnızca başlık ve “Genişlet” düğmesinin göründüğü tek satıra sabitler. Daraltılmış panelin ayırıcısı gizlenir ve sürüklenerek yüksekliği değiştirilemez. Pencere boyutu değişse de başlık yüksekliği korunur; yeniden genişletildiğinde önceki bölme oranı geri gelir.

Veri dosyaları başlığındaki “‹” düğmesi dosya ve kanal panelini dar bir dikey yan bara kapatır. Yan bardaki “›” veya “VERİ DOSYALARI” alanına tıklayarak paneli yeniden açabilirsiniz; klavyede Enter/Boşluk da kullanılabilir. Panel açıldığında önceki genişlik oranı geri gelir. Dar yan bar pencere ve DPI değişimlerinde aynı mantıksal genişlikte kalır. Bu düzenleme fiziksel monitörlerde işlev testi çalıştırılmadan paketlendi.

## Grafik alanı ve simge düzenlemesi (v1.0.16)

Grafik kenar boşlukları sabit yüzde yerine çizilen eksen başlıkları ve sayıların gerçek piksel sınırlarına göre hesaplanır. Tek Y ekseniyle geniş pencerelerde sol boşluk küçülür; ek Y eksenleri için gereken alan korunur. Pencere boyutu ve eksen ölçeği değiştiğinde yerleşim yenilenir. Filtreli görünüm, Kesim (Hz) ve Uygula en üst araç satırındadır; satır sığmazsa yatay kaydırılabilir.

Mevcut TraceDock logosunun ICO içindeki farklı çözünürlükleri pencere simgesine ve varsayılan alt pencere simgelerine atanır. Windows görev çubuğu için uygulamaya sabit bir kimlik verilir; başlık logosu DPI değerine uygun ICO boyutunu kullanır. EXE aynı ICO kaynağıyla paketlenir. Fiziksel monitörlerde arayüz işlev testi çalıştırılmadı.

## Veri eklerken daraltılmış durumu koruma (v1.0.17)

Daraltılmış zaman çizelgesine veri veya yeni satır eklendiğinde panel otomatik genişlemez; tek başlık satırı yüksekliği ve kilitli ayırıcı korunur. Veriler grafiğe eklenmeye devam eder. Panel yalnızca Genişlet düğmesiyle açılır. Veri ekleme yolundaki eski otomatik genişletme çağrısı kaldırıldı; gizli satıra kaydırma işlemi daraltılmış durumda atlanır. Arayüz işlev testi çalıştırılmadı.

## İşlemler sırasında daraltılmış başlık yüksekliği (v1.0.18)

Daraltılmış zaman çizelgesi artık ana bölme ayırıcısından tamamen ayrılan, doğal başlık yüksekliğinde bağımsız bir alt satırdır. Filtre/okuma/dışa aktarma ilerleme çubuğunun açılıp kapanması bu satıra fazladan yükseklik veremez. Daraltılmış durumda yalnızca başlık ve Genişlet düğmesi görünür; ayırıcı yoktur. Genişletildiğinde mevcut zaman çizelgesi verileri ve önceki bölme oranı korunarak düzenleme paneli geri eklenir. Arayüz işlev testi çalıştırılmadı.
