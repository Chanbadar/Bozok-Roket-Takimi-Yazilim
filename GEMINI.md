# Git Güvenlik ve Push Kuralları (Git Safety Rules)

## Kesin Kural: Otomatik Git Push YASAKTIR (No Automatic Push)
1. **Kullanıcı Onayı Olmadan Push Yapılamaz**: Asistan hiçbir koşulda kullanıcıdan açık, doğrudan ve net bir onay almadan `git push` komutunu çalıştıramaz.
2. **Otomatik Tetiklemeler Yasaktır**: Kod yazma, derleme, commit veya görev tamamlama sonrasında otomatik olarak uzak sunucuya (GitHub vb.) push yapılamaz.
3. **Onay Süreci**: Herhangi bir push işleminden önce, hangi branch'in nereye gönderileceği kullanıcıya açıkça bildirilmeli ve kullanıcının onayı beklenmelidir.
