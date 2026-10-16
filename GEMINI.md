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
