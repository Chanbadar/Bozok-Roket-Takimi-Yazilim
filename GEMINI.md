# Git Güvenlik, Push ve Commit Kuralları

## 1. Kesin Kural: Otomatik Git Push YASAKTIR (No Automatic Push)
1. **Kullanıcı Onayı Olmadan Push Yapılamaz**: Asistan hiçbir koşulda kullanıcıdan açık, doğrudan ve net bir onay almadan `git push` komutunu çalıştıramaz.
2. **Otomatik Tetiklemeler Yasaktır**: Kod yazma, derleme, commit veya görev tamamlama sonrasında otomatik olarak uzak sunucuya (GitHub vb.) push yapılamaz.
3. **Onay Süreci**: Herhangi bir push işleminden önce, hangi branch'in nereye gönderileceği kullanıcıya açıkça bildirilmeli ve kullanıcının onayı beklenmelidir.

---

## 2. Commit ve İsimlendirme Standartları (Conventional Commits)
Kullanıcı commit mesajı, isim önerisi veya push hazırlığı istediğinde **her zaman** standart **Conventional Commits** formatında hazır, doğrudan kopyalanabilir öneriler sunulmalıdır:

* **`feat:` (veya `feat(kapsam):`)**: Projeye yeni bir ekran, modül veya işlev eklendiğinde.  
  * *Örnek:* `feat(ui): implement real-time rocket telemetry dashboard`
* **`fix:` (veya `fix(kapsam):`)**: Bir yazılım hatası veya problem düzeltildiğinde.  
  * *Örnek:* `fix(gps): resolve coordinate drift calculation error`
* **`docs:`**: Dokümantasyon veya README dosyaları güncellendiğinde.  
  * *Örnek:* `docs: update installation instructions in readme`
* **`chore:`**: Kütüphane, bağımlılık, build veya yapılandırma ayarları güncellendiğinde.  
  * *Örnek:* `chore(deps): add pyqtgraph and pyserial dependencies`
* **`refactor:`**: Kodun çalışmasını değiştirmeden yapılan mimari temizlik ve iyileştirmelerde.  
  * *Örnek:* `refactor(core): streamline serial packet parsing logic`

---

## 3. Bozok Roket Takımı - Yazılım Geliştirme ve Git İş Akışı Rehberi

Her zaman bu repoda aşağıdaki kurallara ve adımlara tam uyulmalıdır:

1. **Yeni Bir Göreve Başlarken**:
   - Ana klasörde bulunulduğundan emin olunur.
   - Güncel kod çekilir ve `develop` dalı üzerinden görev dalı (`feature/...`) açılır:
     ```bash
     git checkout develop
     git pull origin develop
     git checkout -b feature/gorev-adi
     ```

2. **Kod Yazma ve Düzenleme**:
   - Kodlar her zaman ilgili modül klasörünün altına eklenir (örn: Yer İstasyonu için `2_Ground_Control/`, Uçuş Bilgisayarı için `1_Flight_Computer/` vb.).

3. **Kodları GitHub'a Gönderme (Commit & Push)**:
   - Değişiklikler stage edilir ve Conventional Commits standardında mesajla commit atılır:
     ```bash
     git add .
     git commit -m "feat(modul-adi): yapılan işin kısa özeti"
     ```
   - Kullanıcıdan açık push onayı alındıktan sonra branch `origin`e gönderilir (Burada ASLA sayı yazılmaz, sadece dal adı yazılır):
     ```bash
     git push -u origin feature/gorev-adi
     ```

4. **Pull Request (PR) Aşaması**:
   - Push işlemi tamamlandıktan sonra kullanıcıya **`develop`** dalına Pull Request açabilmesi için GitHub bağlantısı sunulur (`compare/develop...feature/gorev-adi`).
   - **Kritik Kural**: PR hedefi (base branch) **DAİMA `develop`** olmalıdır; asla doğrudan `main`e açılmamalıdır.
   - PR numaraları (#1, #2, #5, #6...) GitHub tarafından tamamen otomatik verilir, geliştiricinin hiçbir zaman numara yazması gerekmez.
