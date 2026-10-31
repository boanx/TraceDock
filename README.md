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

## Kompakt satırlar ve lejant çizim önbelleği (v1.0.19)

Zaman çizelgesinin veri satırları sabit 76 yerine yazı ölçülerine göre, 96 DPI değerinde yaklaşık 42 piksel yüksekliğinde çizilir. İki satırlı paket adı/zaman bilgisi ve satır seçimi aynı geometriyi kullanır.

Lejantın metin ve çizgileri pencere boyutu/DPI/konum değişmediğinde şeffaf görüntü önbelleğinden çizilir; kanal adına tıklayarak Y ekseni seçimi korunur. Önbelleğe grafikteki eski eğriler alınmaz. Kanal/etiket değişikliği lejantı yeniden oluşturur. Sürükleme sırasında kenar boşluğu hesapları ertelenir ve daha küçük min/max çizim özeti kullanılır; fare bırakılınca ayrıntılı çizim yenilenir. Kaynak örnekler, prob hesapları ve dışa aktarılan sayısal veriler değişmez. Performans ölçümü veya arayüz işlev testi çalıştırılmadı.

## İnce başlık ve satır/paket görünürlüğü (v1.0.20)

Daraltılmış zaman çizelgesinin başlığındaki yazı ve Genişlet düğmesi küçültülüp dikey boşlukları azaltıldı; 96 DPI değerinde başlık yaklaşık yarı yüksekliğe iner.

Zaman çizelgesindeki satır başlığına veya satırın boş kısmına sağ tıklayıp Satırı gizle / Satırı göster seçebilirsiniz. Paket üzerinde sağ tıklanınca ayrıca Paketi gizle / Paketi göster bulunur. Tümünü göster bütün satır ve paketleri açar. Gizli öğeler çizelgeden silinmez; gri ve Gizli etiketiyle kalır. Gizleme grafiği, lejantı, görünür kanal istatistiklerini, prob görünümünü ve grafik CSV/PNG dışa aktarımını etkiler. Ham kaynaklar, kayıtlı problar, paket sırası, toplam süre ve sonraki paketlerin zaman konumları korunur.

Satırın gizlenmesi içindeki bütün paketleri baskılar; satırı tekrar gösterdiğinizde daha önce tek başına gizlediğiniz paketler gizli kalır. Paketler için bağımsız görünürlük ayarı korunur. Bu ayarlar mevcut oturum içindir. Arayüz işlev testi çalıştırılmadı.

## Eğri renklerini değiştirme (v1.0.21)

Lejanttaki eğri adına sol veya sağ tıklayıp “Eğri rengini değiştir…” seçeneğini kullanın. Lejant kapalıysa grafikteki eğriye sağ tıklayarak aynı menüyü açabilirsiniz. Açılan renk seçicisinden renk seçin; İptal mevcut rengi korur. “Varsayılan renge dön” otomatik palet rengini geri yükler.

Seçim aynı satırdaki eşleştirilmiş eğrinin bütün devam paketlerine, lejanttaki çizgiye, prob işaretlerine ve PNG çıktısına uygulanır. Başka satırdaki eğriler bağımsızdır. Gizle/göster, filtre, çarpan veya yakınlaştırma değişince renk korunur; renk değişirken yakınlaştırma korunur. Lejant önbelleği yeni renkle yeniden oluşturulur. Renkler mevcut oturum içindir; kaynak dosya ve CSV sayısal değerleri etkilenmez. Sağ sürükleme ile kaydırma ve prob üzerinde sağ tıkla etiket aç/kapat korunur. Arayüz işlev testi çalıştırılmadı.

### Dosya, kanal ve paket birimlerini düzenleme

Dosya/Kanal tablosuna Birim sütunu eklendi. Kanalın Birim hücresine çift tıklayarak tek kanalın; dosya satırındaki hücreye çift tıklayarak dosyadaki tüm kanalların birimini düzenleyebilirsiniz. Dosya/Kanal sağ tık menüsünde de Birim değiştir bulunur. Zaman çizelgesindeki pakete sağ tıklayıp Paket birimini değiştir ile yalnızca o pakete ortak birim atayın. Kaynak birimlerini kullan bu paket atamasını kaldırır.

Birim düzenlemesi etiket/metaveri değişikliğidir; örnekler otomatik dönüştürülmez. Örneğin N → kN dönüşümü için ayrıca 0,001 çarpanı girilmelidir. Y eksenleri etkin eğrilerin birimlerini gösterir; aynı eksende farklı birimler varsa her biri listelenir, eksik birim “birimsiz” olarak belirtilir. Farklı fiziksel büyüklükleri mevcut Y ekseni seçenekleriyle ayırabilirsiniz. Lejant ve CSV başlıkları birimi içerir; farklı birimli devam paketleri CSV içinde ayrı seriler olarak aktarılır. Birim ayarları mevcut oturum içindir.

## Low pass, High pass ve Band pass (v1.0.22)

Kesim alanının yanındaki kutudan Low pass, High pass veya Band pass seçin; ardından Uygula düğmesine basın. Low pass, kesim üzerindeki yüksek frekansları zayıflatır. High pass, kesim altındaki düşük frekansları ve DC bileşenini zayıflatır. Band pass seçildiğinde Alt (Hz) ve Üst (Hz) alanları görünür; bant dışındaki bileşenler zayıflatılır. Varsayılan tür Low pass olarak kalır. Tür/sınır değişiklikleri Uygula ile etkinleşir; hazırlık bitene kadar önceki etkin görünüm korunur.

Örnek: 100 Hz veride Low pass 10 Hz, High pass 1 Hz veya Band pass 1–20 Hz seçilebilir. Her türde frekanslar pozitif ve örnekleme hızının yarısından küçük olmalıdır; Band pass için alt < üst koşulu aranır. Nokta/virgül kabul edilir. Farklı kanal hızları eşitlenmez; her kanal kendi örnekleme hızıyla filtrelenir.

Üç tür de SOS Butterworth ileri/geri filtreleme kullanır; tasarımda iki geçiş telafisi ile girilen sınırlar birleşik −3 dB noktalarıdır. Prototip derecesi 4, band pass tasarımının tek yön derecesi 8’dir. Kayıt ve boşluk kenarlarında sınır etkileri olabilir; üç örnekten kısa sonlu parçalar ham kalır. Örnek sayıları ve zamanlar korunur. Ham örnekler değiştirilmez.

Önbellek türü, alt/üst sınırları ve kanal Hz değerini birlikte izler. Grafik etiketi, lejant, problar, istatistikler, CSV ve PNG etkin filtreyi kullanır; etkin tür ve frekanslar başlıklarda belirtilir. Filtreli görünüm kutusunu kapatarak ham veriye dönün. Önceki renk, birim ve gizle/göster özellikleri korunur. Arayüz işlev testi çalıştırılmadı.

## Satır başlangıçları, sürükleme ve snap (v1.0.23)

Her zaman çizelgesi satırının başlangıç zamanı vardır; varsayılan 0 saniyedir. Aktif satır için Başlangıç… düğmesini kullanın, satırın sol başlığına çift tıklayın veya sağ tık → Satır başlangıcını değiştir seçin. Pozitif/sıfır saniye (12,5 veya 12.5) ya da HH:MM:SS.SSSS girilebilir. Başlık altındaki zaman satırın başlangıcını gösterir.

Sol satır başlığını yatay sürüklemek o satırdaki bütün paketleri birlikte kaydırır. Paketlerin kendi üzerindeki sürükleme mevcut sıralama/satır değiştirme işlevini korur. Sürükleme sırasında çizelge önizlenir; bırakınca grafik, prob ve CSV/PNG zamanları güncellenir. Ölçek sürükleme boyunca sabit kalır; isterseniz sonra Sığdır düğmesini kullanın. Ham örnekler, frekans, paket süreleri ve satır içindeki uç uca sıra değişmez.

Üst satıra snap kutusu açıkken satırın başlangıcı, bir üst satırın başlangıç/bitişine 10 mantıksal piksel yaklaşınca hizalanır; mor kılavuz hedefi gösterir. Shift basılı tutulursa o sürüklemede snap atlanır. Sağ tık menüsündeki Üst satırın başlangıcına hizala / bitişine hizala komutları tam hizalama yapar. İlk satırda bu komutlar pasiftir. Boş üst satırın bitişi başlangıcına eşittir. Snap tek seferlik hizalamadır; üst satır daha sonra taşınırsa alt satır otomatik takip etmez.

Paketleri ayrı ayrı gizlemek için pakete sağ tıklayıp Paketi gizle / göster seçin veya satır sağ tık → Paket görünürlüğü listesindeki işaretleri açıp kapatın. Gizli paketlerin süre ve zaman konumları korunur; satır gizli ise paket işaretleri ayrı saklanır, grafikte görünmesi için satırın da açık olması gerekir. Yeni özellikler mevcut oturum içindir. Arayüz işlev testi çalıştırılmadı.

## Aynı satırda devam ve tek lejant adı (v1.0.24)

Varsayılan kanal eşleştirmesi Seçili kanal sırasına göre oldu: aynı satırdaki paketlerin birinci seçili kanalı birinci eğrinin, ikinci seçili kanalı ikinci eğrinin devamı olur. Kaynak dosyalarda kanal adları farklı olsa da sıradaki eş kanal aynı renk/iz üzerinde uç uca devam eder. Seçili kanal sırası kaynak tablosundaki kanal sırasıdır. Birden fazla ölçüm kanalı tek fiziksel seriye karıştırılmaz; her biri ayrı devam eder. Gelişmiş eşleştirme seçenekleri kutuda korunur.

Lejantta her görünür satır yalnızca bir adla yer alır; temsil çizgisi satırın ilk görünür eğrisinin rengindedir. Satıra sağ tık → Satır adını değiştir ile lejant adını da değiştirebilirsiniz. Lejant adına tıklanan renk/eksen işlemi satırdaki görünür eğrilerin tümüne uygulanır; tek eğri için doğrudan eğriye sağ tıklayın. Paketleri ayrı ayrı gizleme, satır başlangıcı ve snap özellikleri korunur. Arayüz işlev testi çalıştırılmadı.

## Uzun satır adları (v1.0.25)

Zaman çizelgesindeki sol satır başlığı, kutunun kullanılabilir genişliği ve gerçek font ölçüsüne göre üç noktayla kısaltılır; uzun ad paket alanına taşmaz. Uzun adın üzerine fareyi getirince tam adı gösteren bilgi kutusu açılır. Başlık gösterimindeki satır sonları tek satıra düzleştirilir. Gerçek satır adı ve lejant adı değiştirilmez. Arayüz işlev testi çalıştırılmadı.

## Paket zamanları, komşu taşıma ve kenar snap (v1.0.26)

Paketin üzerine sol basıp yatay sürüklemek artık doğrudan zamanını değiştirir. Sağa taşırken seçili paket ve sağındaki paketler, sola taşırken seçili paket ve solundakiler aynı miktarda kayar; paket süreleri ve aralarındaki mevcut boşluklar korunur. Sola taşıma, etkilenen ilk paket sıfıra gelince durur. Yön değiştirildiğinde önizleme sürükleme başlangıcındaki konumlardan yeniden hesaplanır. Satır başlığı sürüklemesi bütün satırı taşımayı sürdürür. Ctrl+sürükle eski paket sıralama/satır değiştirme işlemidir; hedef satırdaki paketler bu işlemde uç uca yeniden sıralanır.

Paket kenarlarına snap açıkken taşınan paketin hem başlangıcı hem bitişi, diğer üst ve alt satırlardaki tüm paketlerin başlangıç/bitiş kenarlarıyla karşılaştırılır. 10 mantıksal piksel yakınlıktaki geçerli en yakın kenara hizalanır; mor kılavuz gösterilir. Shift snap’i geçici kapatır. Gizli paketler de zamanlarını koruduğundan snap hedefidir. Eski Üst satırın başlangıcına/bitişine hizala menüleri kaldırıldı.

Pakete sağ tıklayıp Paket başlangıç zamanını değiştir veya Paket bitiş zamanını değiştir seçin. Saniye veya HH:MM:SS.SSSS girilebilir. Bu iki işlem paketin süresini korur ve yalnızca o paketi taşır; başka paketleri itmez. Aynı satırda, gizli paketler dahil başka bir paketle çakışma varsa uyarı verilir ve değişiklik uygulanmaz. Bitiş ve başlangıç kenarlarının tam temas etmesi çakışma değildir. Farklı satırların üst üste gelmesine izin verilir.

Grafik, problar, lejant grupları ve CSV/PNG zamanları paket konumlarını kullanır. Ham örnekler/frekanslar değiştirilmez; paketleri tek tek gizle/göster korunur. Yeni konumlar mevcut oturum içindir. Arayüz işlev testi çalıştırılmadı.

## Yalnızca bitişik paketlerin birlikte taşınması (v1.0.27)

Paket sürüklemede hareket yönündeki bütün paketler yerine yalnızca bitişik paket zinciri birlikte kayar. Arada boşluk varsa zincir orada kesilir; boşluğun ötesindeki paketler yerlerinde kalır. Bitişiklik sürükleme başlangıcındaki konumlara göre belirlenir; kayan zincir ayrı bir pakete ulaştığında çakışmadan durur. Yeni konumda tekrar sürüklemeye başlanırsa artık bitişik olan paketler yeni zincire katılabilir. Sıfırın önüne taşımaya izin verilmez. Üst/alt satır kenarlarına snap aynı sınırları kullanır; ulaşılamayan hedefe snap yapılmaz. Sayısal yuvarlama toleransı dışında pozitif boşluklar bitişik kabul edilmez. Manuel zaman/çakışma kontrolü ve gizle/göster korunur. Arayüz işlev testi çalıştırılmadı.

## Kanal bazında CSV ve boşluklara sıfır (v1.0.28)

Görünen grafiği CSV’ye aktar ve Seçili aralığı CSV’ye aktar artık paket bazında değil, satır içindeki kanal eşleştirmesine göre kanal bazında sütun üretir. Aynı kanala ait paketler tek değer sütununda devam eder; başlıklarda paket/dosya adı yerine satır ve kanal adı, birim ve etkin filtre bulunur. Ayrı çizgiler görünümünde bile CSV paket başına çoğaltılmaz; seçili kanal sırası kullanılır. Birimleri farklı kanallar sayısal olarak karıştırılmadan ayrı sütunlarda tutulur.

Zaman çizelgesinde paketlerin arasında boşluk varsa o süre CSV’de 0 ile doldurulur. Gizlenen paketlerin boşlukları da 0 olur. Kanalın ortak çizelge aralığındaki başlangıç/son boşlukları da doldurulur; çizelgenin dışındaki grafik boşluğu aktarılmaz. Aralık seçimi gerçek bir örnek içermese bile aradaki 0 örneklerini aktarabilir. Kaynak paketteki NaN/eksik ölçümler 0’a çevrilmez; mevcut boş hücre gösterimini korur.

Ölçüm örnekleri yeniden örneklenmez. Her kanalın boşluğu, önceki paketin veri hızında doldurulur; başlangıç boşluğunda ilk paketin hızı kullanılır. Paketlerin farklı veri hızları korunur. Kanalların zaman dizileri aynıysa tek ortak time sütunu, farklıysa her kanal için time/value çifti yazılır. Bu nedenle farklı Hz verilerde satır numarası ortak bir zaman anlamına gelmez; ilgili zaman sütununu kullanın. Ölçüm değerleri, çarpan, birim, etkin ham/filtreli seçim ve HH:MM:SS.SSSS biçimi korunur.

Boşluklar bütün boyutta RAM’e alınmadan parçalar halinde yazılır. Aynı kanala ait paketlerin zaman aralıkları çakışmışsa belirsiz veri yazmak yerine hata gösterilir. Kaynak dosyalar değiştirilmez. İstatistik CSV ve PNG işlevleri korunur. Arayüz işlev testi çalıştırılmadı.

## Ortak Hz ve örnek tekrarıyla CSV (v1.0.29)

Grafik ve seçili aralık CSV aktarımında artık bütün kanallar tek ortak örnekleme hızına getirilir. Ortak hız, aktarılan görünür kanal/paketlerin en yüksek Hz değeridir. Her zaman noktasında son alınmış örneğin değeri tekrarlanır (zero-order hold); interpolasyon uygulanmaz. 100 Hz → 500 Hz örneğinde her değer 5 satır boyunca aynıdır. Oran tam sayı değilse tekrar sayısı örnekler arasında değişebilir; zaman adımı yine bütün CSV’de sabittir. Aynı kanalda farklı Hz paketler de aynı ortak saate aktarılır. Kaynak veriler ve grafikteki Hz değerleri değiştirilmez.

Ortak saat sıfıra bağlıdır: t = n / ortak_Hz. Sadece seçilen görünür/aralık içindeki bu saat noktaları yazılır. Paket bitişi hariç tutulur; değer paket boşluğuna taşınmaz. Paketler arasındaki ve kanalın çizelge içindeki başlangıç/son boşlukları 0 olur. Kaynak NaN değerler interpolasyon veya sıfıra dönüştürülmeden eksik değer olarak kalır. Alt örnekler ortak saatte bir sonraki örneğe kadar tekrar edilir.

CSV başlığı time, time_s, kanal sütunları şeklindedir. time eski HH:MM:SS.SSSS gösterimini korur; time_s saniyeyi 17 anlamlı basamakla yazar. Yüksek Hz veride time metni yuvarlanıp aynı görünebileceği için diğer uygulamalarda hassas zaman ekseni olarak time_s kullanın. Ölçüm değerleri de 17 anlamlı basamakla yazılır. CSV yeniden TraceDock’a eklendiğinde hassas time_s kullanılır ve iki zaman sütunu ölçüm kanalı sayılmaz. Ondalık/ayraç tercihi korunur.

CSV yanında <dosya>.csv.metadata.json işlem kaydı oluşturulur: ortak Hz, örnek tekrar yöntemi, boşluk değeri, aralık/satır sayısı, kaynak dosya/kanal adları, her paketin özgün Hz ve örnek sayısı, başlangıç/bitiş, birim, çarpan ve filtre bilgisi kaydedilir. CSV’nin SHA-256 özeti de bu kayıttadır. Bu kayıt özgün örneklerle dışa aktarımdaki tekrarlama işleminin ayırt edilmesini sağlar; yeni ölçüm üretmez. Büyük tekrarlar parçalı hazırlanıp yazılır; bütün eşitlenmiş veri RAM’e alınmaz. Arayüz işlev testi çalıştırılmadı.

## Kaydetme istemeden içe aktarma (v1.0.30)

TDMS eklerken artık ara/senkronize CSV için kaydetme konumu sorulmaz. TDMS kanalları uygulamanın sistem geçici klasöründe oluşturduğu özel ikili önbelleğe alınır ve oradan hazırlanır; hazırlık tamamlandığında, hata veya iptalde bu geçici dosyalar temizlenir. Kanal verileri uygulama içinde kalır, kullanıcı klasörüne ara CSV yazılmaz. Kaynak dosya adı, kanal adları, birimler ve ID bilgileri korunur. TDMS ayar penceresi Hz/çarpan girişini sürdürür; ondalıklı Hz değerleri de kabul edilir.

İçe aktarımda her kanalın özgün/verilen frekansı ve örnek sayısı korunur. Ortak en yüksek Hz’ye örnek tekrarı yalnızca grafik/aralık CSV dışa aktarımında yapılır. Exlab TDMBIN ve metin biçimleri mevcut doğrudan içe aktarma yoluyla kaydetme istemeden açılır. Nihai CSV konumu yalnızca Görünen grafiği CSV’ye aktar veya Seçili aralığı CSV’ye aktar seçildiğinde sorulur; ortak Hz, boşluklara 0, hassas time_s ve metadata.json işlem kaydı korunur. Arayüz işlev testi çalıştırılmadı.

## İlk paketten otomatik satır adı (v1.0.31)

Dosya/veri adı uygulama içinde değiştirildiyse, bu veriden boş bir zaman çizelgesi satırına eklenen ilk paket satıra kendi adını verir. Lejant ve CSV kanal başlıkları da satır adını kullanır. Sonradan aynı satıra eklenen paketler satır adını değiştirmez. Yeni satıra ekleme, boş satıra Ctrl+sürükle ile taşıma ve Tümünü sırala ile satırı yeniden oluşturma aynı ilk-paket kuralını kullanır. Adı özgün dosya adıyla aynı olan paket otomatik ad atamaz. Kayıtlı özgün ad korunur; yalnızca görünür satır adı güncellenir. Arayüz işlev testi çalıştırılmadı.

## Fare zamanında satır değerleri (v1.0.32)

Grafik altındaki fare okuması artık sol/sağ Y ekseninin fare yüksekliğindeki koordinatını değil, imlecin zamanına karşılık gelen satır ölçümlerini gösterir. Süre HH:MM:SS.SSSS biçimindedir. Tek kanallı satır “Satır adı = değer birim”; çok kanallı satır kanal adları ve ayrı değerler halinde yazılır. Yalnızca grafikteki görünür satır/kanallar listelenir. Uzun okuma alanı tek satırda kalır; sığmazsa kendi yatay kaydırma çubuğuyla okunur.

Değer imleç zamanında veya ondan önceki en son gerçek örnektir; araya yeni/interpole değer üretilmez. Her kanal kendi Hz ve paket konumunu kullanır. Etkin ham/filtreli veri, çarpan ve birim dikkate alınır. Paket boşluğu, kanalın dışında kalan zaman veya eksik ölçüm “—” ile gösterilir; eski paketin son değeri boşluğa taşınmaz. Kaydırma sırasında okuma ve çapraz imleç yeni görünümdeki aynı zamanı kullanır.

Paket başlangıçlarına göre küçük bir arama indeksi hazırlanır; her fare hareketinde büyük ölçüm dizileri kopyalanmaz. Filtre, isim veya görünürlük değişiminde okuma yenilenir. CSV aktarımındaki ortak Hz/örnek tekrarı kuralları değişmez. Arayüz işlev testi çalıştırılmadı.

## Prob limiti (v1.0.33)

Her paket/kanal için prob üst sınırı 5’ten 20’ye çıkarıldı. P1–P20 etiketleri, prob tablosu ve mevcut ekle/sil işlemleri aynı şekilde kullanılır. Arayüz işlev testi çalıştırılmadı.


## Sekme görünümü (v1.0.34)
Kanal istatistikleri ve Problar sekmelerinin seçime bağlı boyut farkı giderildi. Seçili sekme turkuaz zemin ve kenarlıkla vurgulanır; yazı ve iç boşluk ölçüleri tüm durumlarda aynı kalır.
Arayüz işlev testi çalıştırılmadı.


## TraceDock CSV bilgileri (v1.0.35)
Grafik ve seçili aralık CSV aktarımları artık her sütunun zaman çizelgesi satır adını, satır grubunu, birimini ve atanan Y eksenini (Sol 1 / Sol 2 / Sağ 1 / Sağ 2) CSV içinde saklar. Dosyayı yeniden adlandırmak veya yalnızca CSV dosyasını taşımak bu bilgileri kaybettirmez.
CSV ekle ile açıldığında birimler ve eksen atamaları otomatik yüklenir. Boş veya yeni bir zaman çizelgesi satırına eklerken kayıtlı satır adları ve grupları otomatik oluşturulur. Dolu bir satırı açıkça hedeflerseniz o satır korunur. Tümünü sırala da kayıtlı grupları kullanır. Dosyayı açmak grafiğe otomatik veri eklemez.
Başlıktan sonraki TraceDock, Unit ve CommonRate satırları üst bilgidir; ölçüm örneği değildir. Başka uygulamalarda sayısal veri okurken bu üç satırı atlayın. CSV ayıracı ve ondalık seçimi geçerliliğini korur. Yanındaki .metadata.json işlem kaydı da üretilmeye devam eder.
Bu bilgiler bu sürüm ve sonrası ile yeniden dışa aktarılan CSVlerde bulunur. Önceki sürümlerin kaydetmediği eksen atamaları geri getirilemez. Aktarılan dosya kanal tablosudur; özgün paket sınırlarını yeniden oluşturmaz.
Arayüz işlev testi çalıştırılmadı.


## TDMS içe aktarma hızı (v1.0.36)
TDMS dosyası artık ağdan veya diskten büyük bloklarla tek seferde uygulamanın geçici alanına alınır. Tüm kanallar yerel dosyadan tek geçişte birlikte çözümlenir; kanal başına ağ üzerinde küçük okuma işlemleri tekrarlanmaz. Kanal dizileri geçici NPY dosyalarına parça parça yazılır; tüm kaynak dosyanın RAMe yüklenmesi gerekmez.
Kopyalama ve çözümleme sırasında ilerleme ve iptal desteği vardır. Başarı, hata ve iptal sonrasında uygulamanın geçici dosyaları temizlenir. Kanalların sayısal değerleri, birimleri, özgün Hz bilgileri ve çarpan ayarları korunur. CSV kaydetme sorusu eklenmez. Kaynak dosya kopyalama sırasında değişirse içe aktarma durdurulur.
Arayüz işlev testi çalıştırılmadı.


## Uzun çizelgelerde kısa paket görünürlüğü (v1.0.37)
Saatler süren zaman çizelgesindeki saniyelik paketler artık en az 10 mantıksal piksel genişliğinde çizilir ve seçilebilir. Bu yalnızca görünür tıklama alanıdır; gerçek başlangıç, bitiş, süre, grafik ve CSV örnekleri değişmez. Çakışan tıklama alanlarında gerçek zaman aralığına en yakın paket seçilir.
Yeni eklenen paket ekranda çok kısa kalıyorsa zaman çizelgesi otomatik yakınlaşır ve pakete kayar. Tüm çizelgeye dönmek için Sığdır düğmesini kullanın. Paket üzerinde bekleyince kaynak/kanal adı ve gerçek başlangıç, bitiş ve süre bilgileri görünür. Daraltılmış çizelge kendiliğinden genişlemez.
Doğrulama: açık uygulamada kanalın mevcut satıra eklenmesi ve çift tıklamayla grafikte incelenmesi kontrol edildi. Dokuz saatlik çizelgeye 23,6 saniyelik paket ekleme, yeni satıra ekleme, asgari genişlik, otomatik yakınlaşma ve zamanların değişmemesi uygulama bileşenleriyle doğrulandı.


## TDMS ayar penceresi (v1.0.38)
TDMS kanal hızları ve çarpanları penceresi artık ana pencere küçük olsa da DPI ölçeğine uygun 860×600 başlangıç alanını hedefler; ekran sınırları korunur. İçerik oluşturulduktan sonra boyutlandırılır. Alt düğmeler ayrı sabit satırda kalır, kanal tablosu kalan alanı kullanır ve kendi içinde kaydırılır.
Doğrulama: 30 kanallı ayar penceresi normal açılışta görüntülendi; Dosyayı ekle ve Vazgeç düğmelerinin görünür ve tamamıyla pencere sınırları içinde olduğu kontrol edildi.


## Taşınabilir TDOC projeleri (v1.0.39)
Daha sonra devam etmek veya çalışmayı paylaşmak için Projeyi kaydet düğmesi ya da Ctrl+S ile .tdoc dosyası oluşturun. Proje menüsündeki Farklı kaydet veya Ctrl+Shift+S ile ayrı bir kopya oluşturabilirsiniz. Proje aç düğmesi veya Ctrl+O ile geri yükleyin. Proje açılması mevcut çalışmanın yerini alacağı için uygulama önce uyarır; mevcut çalışmanızı önceden kaydedin.
Projeye yüklenmiş bütün veri dosyalarının sayısal ham kanal örnekleri dosyanın içinde saklanır. Yalnızca .tdoc dosyasını paylaşmak yeterlidir; özgün CSV, TDMS veya Exlab dosyaları açılışta aranmaz. Özgün dosya adları ve kaynak yolu bilgi amaçlı tutulur.
Kayıt kapsamı: dosya/kanal adları, seçili kanallar, özgün örnekleme hızları, birimler, veri ve kanal çarpanları, satır adları ve sırası, satır başlangıçları, paket sırası ve zaman konumları, paket birim geçersiz kılmaları, gizli satır/paketler, kanal eşleştirme seçimi, Y ekseni atamaları, eğri renkleri, problar ve etiket görünürlükleri, filtre türü/frekansları, lejant, grafik yakınlaştırma aralığı, seçili aralık ve temel panel/çizelge görünümü saklanır.
Filtreler ham örnekleri değiştirmez. Filtreli proje açılırken filtre sonucu ve hızlı grafik önbellekleri yeniden hazırlanır; işlem uzun dosyalarda zaman alabilir. Veriler örnek kaybı olmadan, hızlı kayıt için sıkıştırılmadan saklanır; büyük çalışmaların proje dosyası da büyük olabilir. Kaydetme/açma arka planda ilerleme ve iptal ile çalışır. Kaydetme önce geçici dosyaya yapılır, tamamlandığında hedef dosya değiştirilir; iptal edilen işlem önceki kaydı korur.
TDOC içinde JSON üst bilgisi ve sayısal NPY dizileri vardır; pickle veya çalıştırılabilir kod yüklenmez. Bozuk/desteklenmeyen proje yüklenemezse mevcut çalışma korunur. Komut satırından TraceDock.exe dosya.tdoc ile ya da .tdoc dosyasını EXE üzerine sürükleyerek açılabilir. Windows dosya ilişkilendirmesi otomatik değiştirilmez.
Doğrulama: kaynak dosyası bulunmayan proje, birebir ham örnekler, farklı Hz değerleri, çarpanların tek uygulanması, satır/paket adları ve konumları, birimler, eksenler, renkler, problar, gizli paketler, filtre yeniden oluşturma ve iptal edilen kayıtta önceki dosyanın korunması kontrol edildi.


## Birden fazla proje sekmesi (v1.0.40)
Üstteki + Yeni proje düğmesi veya Ctrl+N ile ayrı bir çalışma sekmesi oluşturulur. Proje aç / Ctrl+O artık .tdoc dosyasını mevcut çalışmayı değiştirmeden yeni sekmede açar. Zaten açık bir proje yeniden seçilirse o sekmeye geçilir.
Sekme başlığına tıklayarak ya da Ctrl+Tab / Ctrl+Shift+Tab ile projeler arasında geçiş yapılır. Çok sayıda sekme yatay kaydırma ile erişilebilir. Veri dosyaları, kanallar, satırlar/paketler, adlar/konumlar, birimler/çarpanlar, eksenler, renkler, problar, filtreler, grafik yakınlaştırması ve panel görünümü proje bazında ayrı tutulur. Sekme geçişinde kaynak dosyalar okunmaz, veri dizileri ve filtre/grafik önbellekleri bellekte kalır.
Projeyi kaydet / Ctrl+S ve Farklı kaydet / Ctrl+Shift+S yalnızca aktif projeyi .tdoc olarak kaydeder; diğer sekmelerin dosyaları etkilenmez. Başka açık sekmeye ait dosya adına yazma engellenir. Her projeyi ayrı kaydedin.
Sekmeyi kapat veya Ctrl+W aktif sekmeyi kapatır; veri içeren sekmeler için kaydedilmemiş değişikliklere karşı onay istenir. Son sekme kapatıldığında yeni boş proje oluşturulur. Birden fazla proje açıkken uygulama kapatılırsa tüm sekmelerin kapanacağı bildirilir.
Kaydetme/açma/içe aktarma/filtre gibi arka plan işlemi sürerken sekme geçişi, sekme açma ve kapatma bekletilir; sonuç yanlış projeye uygulanmaz. Birden fazla büyük projeyi açık tutmak daha fazla RAM kullanır.
Doğrulama: iki bağımsız veri kümesi ve çizelge arasında geçiş, örnek dizilerinin aynı nesne olarak kalması, farklı görünüm/prob/renk ayarları, aktif proje kaydı, yeni sekmede proje açma, zaten açık projeye dönüş, meşgul işlemde geçiş engeli, sekme kapatma onayı/yalıtımı ve görünür sekme şeridi kontrol edildi.


## Kanal kutucukları ve satır oklarında DPI ölçeği (v1.0.41)
Dosya/kanal ağacındaki seçili, seçilmemiş ve kısmen seçili kutucuk görselleri artık ekran DPI değerine göre yeniden çizilir. %100 ölçekte 14 piksel, %200 ölçekte 28 piksel kullanılır. Grubu açıp kapatan yerel Treeview oklarının boyutu ve boşlukları da aynı oranda ölçeklenir. Monitör ölçeği değiştiğinde simgeler güncellenir; seçimler, açılmış/kapatılmış gruplar ve kaydırma konumu korunur.
Doğrulama: 96, 144, 192, 240 ve tekrar 96 DPI değerleriyle kutucuk/ok boyutları ve kısmi seçim durumu uygulama içinde kontrol edildi.


## Dosya içeriği açma/kapatma okunun çizimi (v1.0.42)
Dosya/Kanal ağacında yerel temanın küçük kalan ok çizimi yerine DPIa göre yeniden çizilen özel açık/kapalı ok görselleri kullanılır. Okun kendisi ve tıklama alanı birlikte büyür; yalnızca simgenin çevresindeki boşluk büyütülmez. Çocuksuz kanallarda ok gösterilmez. Yerel tek tıkla aç/kapat ve klavye davranışları korunur.
Doğrulama: %100, %150, %200, %250 ve tekrar %100 ölçekte 20/30/40/50/20 piksellik özel simge alanı, gerçek Treeview gösterge tıklama alanı, açma-kapatma ve kanal seçiminin korunması kontrol edildi.


## Tek düğmeyle veri paketi ekleme (v1.0.43)
Exlab dosyası ekle, CSV ekle ve TDMS ekle düğmeleri kaldırıldı. Projeyi kaydet düğmesinin hemen yanındaki Veri paketi ekle düğmesiyle CSV, TDMS, Exlab TDMBIN ve metin/TSV/ASC dosyaları tek seçim penceresinden eklenir. Dosya türü ikili imza ve uzantı ile otomatik belirlenir; CSV ve Exlab metinleri ortak tablo okuyucusunu kullanır.
Farklı türde dosyalar aynı anda seçilebilir ve seçildikleri sırayla yüklenir. TDMS kanal Hz ve çarpan penceresi korunur. Bir dosya okunamazsa hata gösterilir ve sıradaki dosyaya geçilir; işlem iptal edilirse kalan kuyruk temizlenir. İçe aktarma kuyruğu tamamlanmadan proje sekmesi değiştirilemez. TDMS indeks dosyası yerine asıl .tdms dosyası seçilmelidir. TDOC dosyaları için Proje aç kullanılır.
Doğrulama: tek düğmenin yeri/eski düğmelerin kaldırılması, karışık CSV/TDMS/TDMBIN/Exlab metin kuyruğu, birebir değerler, Hz ve birimler, ikili imzadan tür belirleme, işlem kuyruğunda sekme kilidi ve iptal edilen kuyruğun temizlenmesi kontrol edildi.


## Filtre görünürlüğü ve filtre kaldırma (v1.0.44)
High pass filtresinin sayısal frekans yanıtı doğrulandı: düşük frekans/DC bastırılır, yüksek frekans korunur, girilen kesim frekansı birleşik ileri/geri filtre yanıtında -3 dB noktasına karşılık gelir. Katsayı tasarımı değiştirilmedi. Filtre sonrası önceki Y ekseni sınırlarının korunması, DC seviyesi kaldırılan sinyali grafikte çok küçük veya görünmez bırakabiliyordu. Filtre uygulanırken, önbellekten tekrar uygulanırken ve ham/filtreli görünüm arasında geçerken Y eksenleri artık yeniden ölçeklenir; X ekseni yakınlaştırması korunur.
Uygula yanındaki Uygulanan filtreleri kaldır düğmesi aktif projeyi ham görünüme döndürür ve aktif projenin filtre önbelleklerini temizler. Filtre türü/frekans girişleri yeniden kullanım için hatırlanır fakat filtre etkin değildir. Kanal çarpanları ve birimler korunur; problar, paket zamanları ve diğer proje sekmeleri etkilenmez. Grafik, istatistik, prob değerleri ve CSV yeniden ham örnekleri mevcut çarpanlarıyla kullanır. İşlem sırasında düğme bekletilir.
Doğrulama: high/low/band pass geçirme-bastırma ve kesim noktaları, NaN/Inf aralıkları ve kaynakların değişmemesi, yüksek DC seviyeli sinyalin high pass sonrası görünürlüğü, X yakınlaştırmasının korunması, filtre kaldırıldıktan sonra grafik/CSV/proje durumu ve sekme yalıtımı kontrol edildi.


## Ortak en yüksek Hz üzerinden filtreleme (v1.0.45)
Filtreleme artık aktif projede yüklenmiş kanalların en yüksek Hz değerini ortak işleme frekansı olarak kullanır. Örneğin 1 Hz ve 1000 Hz kanalları birlikte yüklüyse filtre kesimi 1000 Hz örnekleme hızının Nyquist sınırına (500 Hzden küçük) göre doğrulanır; 1 Hz kaynak kanalı nedeniyle reddedilmez.
Düşük hızlı kanallar önce önceki örnek değerini tekrarlama (zero-order hold) ile ortak frekansa yükseltilir, ardından high/low/band pass filtresi bu ortak hızda uygulanır. Ham örnekler ve özgün kanal Hz bilgileri değiştirilmez. Örnek tekrarı yeni fiziksel ölçüm bilgisi üretmez. Filtreli grafik, hover/prob, istatistik ve CSV ortak hızdaki sonuçları kullanır. Paket süreleri özgün N/Hz hesabını korur; son örnek aralığı paketi uzatmaz.
Filtre kaldırıldığında özgün örnek sayısı ve Hz ile ham görünüme dönülür. Mevcut problar kaynak örneğine bağlı kalır; filtreli ortak örnekler üzerine eklenen probların örnek içi konumu da saklanır. TDOC açılışında ortak hızlı filtre yeniden oluşturulur. En yüksek Hz veya bir kaynak hız değişirse filtre önbelleği yeniden hazırlanmalıdır. Düşük hızlı verilerin yoğunlaştırılması filtre sırasında daha fazla RAM gerektirebilir; ham kanallar kalıcı olarak çoğaltılmaz.
CSV işlem kayıtlarında özgün source_hz/sample_count ve filtrelenmiş processing_hz/processed_sample_count ayrı yazılır.
Doğrulama: 1/1000 Hz kanallarda yüksek kesim kabulü, tekrar edilen örnekler üzerine filtre ile birebir sonuç, tüm filtre türleri, ortak Nyquist sınırı, özgün süre/veri/Hz, prob zamanı, ortak hızlı CSV, TDOC filtre/prob geri yükleme, ham görünüme dönüş, tam sayı olmayan oranlarda bitişik paketlerin yanlış çakışmaması ve eksik veri aralıkları kontrol edildi.


CSV paket aralıkları — v1.0.46
İki paket arasındaki boşluk artık 0 yerine doğrusal geçişle doldurulur. Geçiş, önceki paketin bitiş anındaki son değerinden sonraki paketin başlangıcındaki ilk değerine uzanır. Örneğin son değer 10, sonraki ilk değer 20 ve boşluk 5 saniye ise saniye başına artış 2 olur: boşluğun başında 10, 1 saniye sonra 12, 2 saniye sonra 14, sonraki paket başında 20. Hesap ortak CSV frekansının her örnek anında yapılır; çarpan/filtre uygulanmış uç değerler kullanılır.
Paketlerin içindeki örnek tekrarı yöntemi değişmez. Kanalın ilk paketinden önce ve son paketinden sonra 0 yazılır; uç değer eksik/NaN/sonsuz ise boşluk da eksik bırakılır. Bitişik paketlerde geçiş eklenmez. Kaynak örnekler, grafik, zaman çizelgesi konumları ve paket süreleri değiştirilmez. Görünen grafik ve seçili aralık CSV aktarımları aynı yöntemi kullanır. Bu bölüm önceki sürümlerdeki paketler arası sıfır doldurma açıklamasının yerini alır.


v1.0.47 — CSV işlem kaydı alanları güncellendi.


v1.0.48 — Kanal istatistikleri / Problar bölümünü daraltma
Bölümün sağ üstündeki Daralt düğmesi tabloları gizleyip tek satırlık başlık bırakır. Grafik boşalan alanı kullanır. Genişlet düğmesi tabloları aynı içerik ve seçili sekmeyle geri getirir; bölme oranı korunur. Daraltılmış bölüm pencere boyutu değişse veya veri/filtre güncellense de tek satır kalır. Bu görünüm her proje sekmesinde ayrı tutulur ve TDOC ile kaydedilir. Eski projeler bölüm açık olarak yüklenir.


v1.0.49 — Grafik kılavuz çizgileri
En küçük noktalı kılavuz çizgilerinin opaklığı ve kalınlığı artırıldı. Ara çizgilerin kontrastı da kademeli görünümü koruyacak şekilde ayarlandı. Grafik ekranı ve PNG aktarımı aynı görünümü kullanır.


v1.0.50 — Probları aktarma ve etiket yerleşimi
Kanal istatistiklerini CSV’ye aktar düğmesi artık prob kayıtlarını da aynı CSV’ye ekler. Kayıt türü sütunu kanal istatistiği ve prob satırlarını ayırır. Prob satırlarında kanal adı, prob numarası, X ve Y değeri bulunur. Mevcut ondalık/ayraç tercihi kullanılır.
Grafikte birbirine yakın prob etiketleri farklı yönlere yerleştirilir; grafik kenarında etiketler içeri alınır. Bağlantı çizgileri kutuların arkasında çizilir. Yakınlaştırma, kaydırma, pencere boyutu ve PNG çözünürlüğü değiştiğinde yerleşim yeniden hesaplanır; geometri değişmediğinde konumlar yeniden kullanılır.
