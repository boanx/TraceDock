# Arayüz ve DPI değişikliği


## 21 Ekim 2026 — Kompakt düğmeler ve ekran ölçeği

- Aktarma düğmeleri tek sırada yan yana kalır; panel daralınca yatay kaydırılır. Grafik CSV, seçili aralık CSV, istatistik CSV ve grafik PNG işlevleri korunur.
- Veri dosyası düğmeleri paneli dolduracak şekilde uzamaz; aynı uyarlanabilir satır düzenini kullanır. Dosya listesi kayıt sayısına göre1–4 satırdır; fazlası kaydırılır.
- `tracedock_dpi.py` Tk penceresi açılmadan Windows Per Monitor V2 farkındalığı ister. Monitör değişince pencere DPI'sı izlenir; Tk fontları, özel düğmeler ve tablo sütun ölçümleri yenilenir. Matplotlib'in kendi piksel oranı ayrıca çarpılmaz.
- `build.ps1`, `TraceDock.manifest` dosyasını EXE'ye gömer. Bu manifest DPI sanallaştırmasının neden olabileceği bitmap bulanıklığını engellemeyi amaçlar. Laptop/harici monitör keskinliği bu değişiklikle henüz fiziksel olarak doğrulanmadı; panel çözünürlüğü veya Windows metin işleme etkileri için sonuç gözlenmeli.
- v1.0.9 paketlemesine dahil edildi. Test çalıştırılmadı.

Dosyalar: TraceDock.py, tracedock_layout.py, tracedock_theme.py, tracedock_dpi.py, TraceDock.manifest, build.ps1.
v1.0.9 sürümü için imzalı commit, etiket ve EXE yayını hazırlanır.

Ek düzenleme: sol panel varsayılan oranı %24; minimum genişliği 220 piksel. Sabit 460 piksel içerik zorlaması kaldırıldı. Gömülü TkAgg canvas için DPI değişiminde backend piksel oranı güncellemesi çağrılır.
