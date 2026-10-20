# TraceDock imza doğrulaması

İmzalayan: **Ahmet Yusuf Ozyurt / boanx**

Algoritma: Ed25519; imza biçimi: OpenSSH.

Anahtar parmak izi: `SHA256:AMO81WC3H9UUA9Adn2y1hLbZ11SKWIIfbKs2SZ++tUU`

Açık anahtar: [SIGNING_KEY.pub](SIGNING_KEY.pub). Güvenilen imzalayan dosyası: [allowed_signers](allowed_signers). Özel anahtar depoda veya sürüm paketinde bulunmaz.

## Commit ve etiket

Depoyu klonladıktan sonra:

```powershell
git -c gpg.ssh.allowedSignersFile=allowed_signers verify-commit HEAD
git -c gpg.ssh.allowedSignersFile=allowed_signers verify-tag v1.0.0
```

## EXE ayrık imzası

Sürüm sayfasından `TraceDock.exe`, `TraceDock.exe.sig` ve `allowed_signers` dosyalarını aynı klasöre indirin. Windows OpenSSH'nin `ssh-keygen` aracıyla PowerShell'den şu komutu çalıştırın:

```powershell
cmd /c "ssh-keygen -Y verify -f allowed_signers -I 21059835+boanx@users.noreply.github.com -n file -s TraceDock.exe.sig < TraceDock.exe"
```

Başarılı doğrulamada `Good ... signature` mesajı görünür ve çıkış kodu sıfır olur. SHA-256 özetini ayrıca karşılaştırabilirsiniz:

```powershell
Get-FileHash .\TraceDock.exe -Algorithm SHA256
```

Sonuç sürümdeki `SHA256SUMS.txt` ile aynı olmalıdır.

## GitHub rozeti ve Windows sertifikası

Kriptografik imza yerel olarak doğrulanabilir. GitHub hesabında anahtar kayıtlı değilse commit “Verified” rozeti almayabilir. Hesap sahibi açık anahtarı GitHub → Settings → SSH and GPG keys → New SSH key bölümünde **Signing Key** türüyle kaydedebilir.

EXE için yayımlanan `.sig`, bir Authenticode sertifika imzası değildir. Windows yayıncı doğrulaması veya SmartScreen itibarı oluşturmaz. Bunun için ayrıca geçerli bir kod imzalama sertifikası gerekir.
