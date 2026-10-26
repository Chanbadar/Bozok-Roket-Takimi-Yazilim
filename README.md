# Bozok Roket Takımı - Yer İstasyonu Arayüzü (Ground Station)
Yozgat Bozok Üniversitesi Fizik ve Astronomi Topluluğu Roket Takımı Yazılım Reposu

TEKNOFEST Orta İrtifa Roket Yarışması gereksinimlerine ve telemetri standartlarına uygun gerçek zamanlı masaüstü yer istasyonu yazılımı.

---

## 🚀 Özellikler
* **Canlı Telemetri Panelleri:**
  * **Roket Verileri:** İrtifa, Düşey Hız, Çift Basınç (DPS368 & BMP390), BMI088 İvmeölçer & Jiroskop, Çift GPS (NEO M9N & QUECTEL) ve uydu durumu, Pil gerilimi.
  * **Görev Yükü Verileri:** İç & dış titreşim ivmeleri, LSM6 çift IMU, GPS koordinatları, uydu sayısı ve ayrılma mekanizması rozeti.
* **Gerçek Zamanlı Grafikler (PyQtGraph - 60 FPS):**
  * İrtifa Grafiği (Apogee takibi)
  * Düşey Hız Grafiği (Tırmanış ve iniş hızı)
  * Çift Basınç Sensör Eğrileri (DPS368 vs BMP390)
  * 3 Eksen İvme (AccX, AccY, AccZ ve Bileşke İvme)
  * Roket ve Görev Yükü Pil Seviyesi Grafikleri
* **Canlı Harita & GPS İzleme:**
  * Roket ve Görev Yükü koordinatlarını harita üzerinde canlı takip, uçuş rotası izi (trail) ve fırlatma rampasına olan anlık mesafe hesabı.
* **Uçuş Durum Çubuğu (State Machine):**
  * Rampa Bekleme ➔ Motor Yanışı ➔ Serbest Tırmanış ➔ Drog Paraşüt ➔ Görev Yükü Ayrıldı ➔ Ana Paraşüt ➔ Kurtarma/İniş.
* **Fizik Tabanlı Uçuş Simülatörü:**
  * Donanım bağlı değilken tek tuşla (`▶ TEST SİMÜLASYONU`) gerçek bir uçuşu saniye saniye simüle etme.
* **CSV Uçuş Kaydedici (Data Logger):**
  * Tüm sensör ve telemetri verilerini zaman damgalı `.csv` dosyası olarak kaydetme.
* **TEKNOFEST Hakem Yer İstasyonu Paketi:**
  * Şartnameye uygun 14 float + durum byte'ı içeren ikili (binary) hakem paketi üretimi.

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Hızlı Başlatma (Windows)
Proje kök dizinindeki veya `2_Ground_Control/` altındaki `run.bat` dosyasına çift tıklayın.  
*(Eğer `.venv` ortamı yoksa veya eksik kütüphaneler varsa `run.bat` otomatik olarak sanal ortamı kurar, `requirements.txt` bağımlılıklarını eksiksiz yükler ve yer istasyonunu başlatır).*

### 2. Manuel Kurulum (Terminal / PowerShell)
Projeyi yeni `pull` veya `clone` ettiyseniz:
```powershell
# 1. 2_Ground_Control dizinine geçin:
cd 2_Ground_Control

# 2. Sanal ortamı oluşturun:
python -m venv .venv

# 3. Sanal ortamı aktif edin:
.\.venv\Scripts\activate

# 4. Gerekli kütüphaneleri yükleyin:
pip install -r requirements.txt

# 5. Uygulamayı başlatın:
python app.py
```

---

## 📁 Proje Mimarisi
```
Bozok-Roket-Takimi-Yazilim/
├── run.bat                     # Kök başlatıcı (2_Ground_Control'e yönlendirir)
├── requirements.txt            # Python bağımlılıkları (PySide6-Essentials, PyQtGraph vb.)
└── 2_Ground_Control/           # 2. Takım: Yer İstasyonu Yazılımı
    ├── app.py                  # Yer İstasyonu başlatıcı
    ├── run.bat                 # Otomatik kurulum ve başlatma betiği
    ├── requirements.txt        # Takım içi bağımlılık dosyası
    ├── telemetry/
    │   └── core/
    │       ├── telemetry_model.py      # Roket & Görev Yükü veri modelleri
    │       ├── flight_simulator.py     # Gerçekçi roket uçuş simülatörü
    │       ├── serial_manager.py       # Seri port (XBee/LoRa/USB) okuyucu & parser
    │       ├── data_logger.py          # CSV uçuş kaydedici
    │       └── referee_transmitter.py  # TEKNOFEST Hakem İstasyonu haberleşmesi
    └── ui/
        ├── main_window.py      # Ana pencere
        ├── styles.py           # Havacılık/Uzay koyu tema (QSS)
        └── components/
            ├── header_bar.py           # Port/Baud/Simülasyon kontrol barı
            ├── telemetry_panel.py      # Telemetri veri kartları
            ├── real_time_charts.py     # Canlı PyQtGraph grafik panelleri
            ├── map_widget.py           # Canlı GPS harita ve radar
            └── flight_state_widget.py  # Uçuş durum göstergesi
```
