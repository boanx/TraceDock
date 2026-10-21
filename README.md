<img src="tracedock.png" alt="TraceDock logosu" width="96" />

# TraceDock

**Hazırlayan: Ahmet Yusuf Ozyurt**

CSV, NI TDMS ve Exlab ölçüm verilerini zaman çizelgesinde düzenlemek, karşılaştırmak ve dışa aktarmak için Windows masaüstü uygulaması.

## Exlab desteği

**Exlab ile toplanmış ölçüm verileri işlenebilir.** Exlab üzerinden CSV, TXT veya TSV olarak dışa aktarılan dosyalar, **Strain Gauge dosyası ekle** düğmesiyle yüklenir. Kanal adları, birimler ve desteklenen zaman damgaları korunur.

Exlab'in `.tdmbin` ham dosyaları doğrudan açılmaz; önce Exlab üzerinden desteklenen bir metin biçimine dışa aktarılmalıdır.

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
