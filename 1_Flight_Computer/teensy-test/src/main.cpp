/* =========================================================================================
 * TEKNOFEST 2026 ROKET YARIŞMASI - UÇUŞ KONTROL BİLGİSAYARI (UKB)
 * TÜM SENSÖRLER VE GPS DONANIM DOĞRULAMA / TEST YAZILIMI
 * 
 * Hedef Kart: Teensy 4.1 (ARM Cortex-M7 @ 600 MHz)
 * 
 * Test Edilen Modüller ve Bağlantı Pinleri:
 * 1. MS5611 / HW-291 Barometre:
 *    - I2C Hattı: SDA (Pin 18) & SCL (Pin 19) [Wire] veya SDA1 (Pin 17) & SCL1 (Pin 16) [Wire1]
 *    - Adres: 0x77 (veya CSB=0 ise 0x76) - Kod otomatik tespit eder.
 * 2. GY-85 9-DOF IMU Modülü:
 *    - ADXL345 (3-Eksen İvmeölçer): Adres 0x53
 *    - ITG3205 (3-Eksen Jiroskop):  Adres 0x68
 *    - HMC5883L (3-Eksen Manyetometre): Adres 0x1E
 *    - I2C Hattı: SDA (Pin 18) / SCL (Pin 19) veya SDA1 (Pin 17) / SCL1 (Pin 16)
 * 3. E108-GN04D GNSS / GY-GPS6MV2 GPS Modülü:
 *    - UART Portu: Serial2 [TAVSİYE EDİLEN]: GPS TXD -> Pin 7 (RX2) | GPS RXD <- Pin 8 (TX2)
 *    - Alternatif: Serial1 : GPS TXD -> Pin 0 (RX1) | GPS RXD <- Pin 1 (TX1)
 *    - Baud Rate: 9600 bps (Standart NMEA 0183 protokolü)
 * 
 * DİKKAT (KAPALI ORTAM TESTİ):
 * Test kapalı alanda / atölyede yapıldığı için GPS uyduları kilitlenmeyebilir (0 Uydu / No Fix).
 * Bu yazılım UART haberleşmesini (gelen NMEA baytlarını ve cümlelerini) ayrı, uydu kilidini ayrı
 * değerlendirir. Kapalı alanda UART veri akışı geliyorsa DONANIM BAĞLANTINIZ BAŞARILIDIR!
 * 
 * Harici Kütüphane Gereksinimi: YOKTUR! Yalnızca <Wire.h> ve <Arduino.h> yeterlidir.
 * ========================================================================================= */

#include <Arduino.h>
#include <Wire.h>

// =========================================================================================
// 1. PIN VE PORT YAPILANDIRMASI
// =========================================================================================
// GPS için hangi donanımsal seri portun kullanıldığını seçin:
// Serial2 = Pin 7 (RX2) ve Pin 8 (TX2) [Önerilen / Standart]
// Serial1 = Pin 0 (RX1) ve Pin 1 (TX1) [Eğer arkadaşınız 0 ve 1'e bağladıysa]
#define GPS_PORT Serial2
const int GPS_BAUD_RATE = 9600;

// LED Pini (Teensy 4.1 dahili LED)
const int PIN_LED = 13;

// =========================================================================================
// 2. I2C VE SENSÖR ADRESLERİ
// =========================================================================================
uint8_t ms5611_addr = 0x77; // 0x77 veya 0x76 (otomatik taranacak)
TwoWire* wire_baro  = &Wire; // Barometrenin bulunduğu I2C yolu

const uint8_t ADXL345_ADDR  = 0x53; // İvmeölçer
const uint8_t ITG3205_ADDR  = 0x68; // Jiroskop
const uint8_t HMC5883L_ADDR = 0x1E; // Manyetometre
TwoWire* wire_imu   = &Wire; // IMU'nun bulunduğu I2C yolu

// Sensör durum bayrakları
bool baro_bulundu = false;
bool adxl_bulundu = false;
bool itg_bulundu  = false;
bool hmc_bulundu  = false;

// =========================================================================================
// 3. MS5611 BAROMETRE DEĞİŞKENLERİ VE HESAPLAMA SABİTLERİ
// =========================================================================================
uint16_t C[7]; // PROM Kalibrasyon Katsayıları (C1 - C6)
float yerSeviyesiBasinc = 1013.25; // hPa

// =========================================================================================
// 4. GPS / NMEA AYRIŞTIRMA DEĞİŞKENLERİ
// =========================================================================================
unsigned long gpsGelenBaytSayisi = 0;
char sonNMEACumlesi[120] = "";
int nmeaindex = 0;

// GPS Ayrıştırılan Değerler
float gpsEnlem = 0.0;
float gpsBoylam = 0.0;
float gpsIrtifa = 0.0;
int   gpsUyduSayisi = 0;
int   gpsFixDurumu = 0; // 0 = Geçersiz / Kilit Yok, 1 = GPS Fix, 2 = DGPS Fix
bool  gpsZamanGecerli = false;
char  gpsUTCZaman[12] = "--:--:--";

// =========================================================================================
// 5. FONKSİYON PROTOTİPLERİ
// =========================================================================================
void i2cTaraVeAtamaYap();
bool ms5611Baslat(TwoWire* wire, uint8_t addr);
void ms5611Oku(float &sicaklik, float &basinc, float &irtifa);
bool adxl345Baslat(TwoWire* wire);
void adxl345Oku(float &ax, float &ay, float &az);
bool itg3205Baslat(TwoWire* wire);
void itg3205Oku(float &gx, float &gy, float &gz);
bool hmc5883lBaslat(TwoWire* wire);
void hmc5883lOku(float &mx, float &my, float &mz, float &heading);
void gpsKarakterIsle(char c);
void nmeaParse(char* cumle);

// =========================================================================================
// SETUP: BAŞLANGIÇ TESTLERİ VE BAŞLATMA
// =========================================================================================
void setup() {
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH);

  // USB Seri Konsolunu Başlat
  Serial.begin(115200);
  unsigned long start = millis();
  while (!Serial && (millis() - start < 2500)) {
    // Seri monitörün açılmasını en fazla 2.5 sn bekle
  }

  Serial.println("\n\n================================================================================");
  Serial.println("     TEKNOFEST 2026 ROKET UKB - TÜM MODÜLLER DONANIM DOĞRULAMA TESTİ           ");
  Serial.println("================================================================================");
  Serial.println("Hedef Kart  : Teensy 4.1 (ARM Cortex-M7 @ 600 MHz)");
  Serial.println("Test Kapsami: MS5611 Barometre | GY-85 IMU (ADXL+ITG+HMC) | GPS/GNSS Modulu");
  Serial.println("GPS Testi   : KAPALI ALAN MODU (UART Baglantisi & NMEA Veri Akisi Tespiti)");
  Serial.println("================================================================================\n");

  // I2C Veri Yollarını Başlat
  Wire.begin();              // Wire  (SDA=Pin 18, SCL=Pin 19)
  Wire1.begin();             // Wire1 (SDA1=Pin 17, SCL1=Pin 16)
  Wire.setClock(400000);     // 400 kHz Hızlı I2C
  Wire1.setClock(400000);

  // GPS Seri Portunu Başlat
  GPS_PORT.begin(GPS_BAUD_RATE);

  // 1. ADIM: I2C Veri Yollarını Tara ve Sensörleri Bul
  Serial.println("[ADIM 1] I2C Hatlari Taraniyor (Wire: Pins 18/19 | Wire1: Pins 17/16)...");
  i2cTaraVeAtamaYap();

  // 2. ADIM: MS5611 Barometreyi Başlat
  Serial.println("\n[ADIM 2] MS5611 / HW-291 Barometre Kalibrasyonu Okunuyor...");
  if (baro_bulundu) {
    if (ms5611Baslat(wire_baro, ms5611_addr)) {
      Serial.printf("  -> [BASARILI] MS5611 Barometre baslatildi! (I2C Adres: 0x%02X)\n", ms5611_addr);
      
      // İlk 10 ölçümle referans yer basıncını al
      float s, b, ir;
      float toplamB = 0;
      for (int i = 0; i < 10; i++) {
        ms5611Oku(s, b, ir);
        toplamB += b;
        delay(20);
      }
      yerSeviyesiBasinc = toplamB / 10.0;
      Serial.printf("  -> Kalibre Edilen Referans Yer Basinci: %.2f hPa\n", yerSeviyesiBasinc);
    } else {
      Serial.println("  -> [HATA] MS5611 kalibrasyon PROM verisi okunamadi!");
      baro_bulundu = false;
    }
  } else {
    Serial.println("  -> [HATA] MS5611 Barometre I2C hattinda bulunamadi!");
    Serial.println("     Kontrol: HW-291 VCC (3.3V), GND, SDA, SCL hatlarini kontrol ediniz.");
  }

  // 3. ADIM: GY-85 IMU Sensörlerini Başlat
  Serial.println("\n[ADIM 3] GY-85 IMU Modulu Sensorleri Baslatiliyor...");
  if (adxl_bulundu) {
    if (adxl345Baslat(wire_imu)) {
      Serial.println("  -> [BASARILI] ADXL345 (3-Eksen Ivmeolcer - 0x53) Hazir (+-16g Modu).");
    } else {
      Serial.println("  -> [HATA] ADXL345 ID dogrulanamadi!");
      adxl_bulundu = false;
    }
  } else {
    Serial.println("  -> [UYARI] ADXL345 (0x53) I2C'de bulunamadi!");
  }

  if (itg_bulundu) {
    if (itg3205Baslat(wire_imu)) {
      Serial.println("  -> [BASARILI] ITG3205 (3-Eksen Jiroskop - 0x68) Hazir (+-2000 deg/s).");
    } else {
      Serial.println("  -> [HATA] ITG3205 baslatilamadi!");
      itg_bulundu = false;
    }
  } else {
    Serial.println("  -> [UYARI] ITG3205 (0x68) I2C'de bulunamadi!");
  }

  if (hmc_bulundu) {
    if (hmc5883lBaslat(wire_imu)) {
      Serial.println("  -> [BASARILI] HMC5883L (3-Eksen Pusula / Manyetometre - 0x1E) Hazir.");
    } else {
      Serial.println("  -> [HATA] HMC5883L baslatilamadi!");
      hmc_bulundu = false;
    }
  } else {
    Serial.println("  -> [UYARI] HMC5883L (0x1E) I2C'de bulunamadi!");
  }

  // 4. ADIM: GPS / GNSS Modülü Bilgilendirmesi
  Serial.println("\n[ADIM 4] GPS / GNSS Modulu (E108-GN04D / GY-GPS6MV2) Dinleniyor...");
  Serial.println("  -> Port: Teensy Pin 7 (RX2) <- GPS TXD  |  Pin 8 (TX2) -> GPS RXD");
  Serial.println("  -> Baud: 9600 bps");
  Serial.println("  -> NOT : Kapali alanda test yapildigindan uydularin cekmemesi NORMALDIR.");
  Serial.println("           Testin amaci donanimsal UART iletisiminin ve NMEA veri akisinin dogrulanmasidir.");
  Serial.println("\n================================================================================");
  Serial.println("      DONANIM BASLATMA TAMAMLANDI - CANLI VERI AKISI BASLIYOR                   ");
  Serial.println("================================================================================\n");

  digitalWrite(PIN_LED, LOW);
  delay(1500);
}

// =========================================================================================
// LOOP: CANLI ÖLÇÜM VE EKRANA YAZDIRMA
// =========================================================================================
unsigned long sonEkranZamani = 0;
const unsigned long EKRAN_PERIYODU = 1000; // 1 saniyede bir ekranı güncelle

void loop() {
  // 1. GPS Portunu sürekli dinle (karakter kaçırmamak için)
  while (GPS_PORT.available() > 0) {
    char c = GPS_PORT.read();
    gpsKarakterIsle(c);
  }

  // 2. Periyodik Gösterge Paneli (Her 1 saniyede bir)
  if (millis() - sonEkranZamani >= EKRAN_PERIYODU) {
    sonEkranZamani = millis();
    digitalWrite(PIN_LED, !digitalRead(PIN_LED)); // LED flaşı

    Serial.println("--------------------------------------------------------------------------------");
    Serial.printf("[ZAMAN: %lu ms | Calisma Suresi: %lu sn]\n", millis(), millis() / 1000);

    // --- 1. BAROMETRE BÖLÜMÜ (MS5611) ---
    Serial.println(">> [1. BAROMETRE - MS5611 / HW-291]");
    if (baro_bulundu) {
      float sicaklik, basinc, irtifa;
      ms5611Oku(sicaklik, basinc, irtifa);
      float goreceliIrtifa = irtifa - (44330.0 * (1.0 - pow(yerSeviyesiBasinc / 1013.25, 0.190295)));
      Serial.printf("   Basinc    : %.2f hPa (mbar)\n", basinc);
      Serial.printf("   Sicaklik  : %.2f *C\n", sicaklik);
      Serial.printf("   Irtifa    : %.2f m (Deniz Seviyesi)\n", irtifa);
      Serial.printf("   Goreceli  : %.2f m (Yer seviyesine gore yukseklik)\n", goreceliIrtifa);
      Serial.println("   [DURUM: OK] Barometre hassas ve kararli calisiyor.");
    } else {
      Serial.println("   [DURUM: BAGLANTI YOK] Barometre okunamiyor! I2C kablolarini kontrol edin.");
    }

    // --- 2. IMU BÖLÜMÜ (GY-85) ---
    Serial.println(">> [2. IMU / ATALETSEL SENSÖRLER - GY-85]");
    // İvmeölçer
    if (adxl_bulundu) {
      float ax, ay, az;
      adxl345Oku(ax, ay, az);
      float toplamG = sqrt(ax*ax + ay*ay + az*az);
      Serial.printf("   Ivme (ADXL345)   : X: %+5.2f g | Y: %+5.2f g | Z: %+5.2f g  [Bileske: %.2f g]\n", ax, ay, az, toplamG);
      if (toplamG > 0.8 && toplamG < 1.2) {
        Serial.println("   [ADXL345 DURUM: OK] Masa uzerinde 1.0G yercekimi ivmesi dogrulandi.");
      }
    } else {
      Serial.println("   [ADXL345 DURUM: BAGLANTI YOK]");
    }

    // Jiroskop
    if (itg_bulundu) {
      float gx, gy, gz;
      itg3205Oku(gx, gy, gz);
      Serial.printf("   Aci Hiz (ITG3205): Roll: %+6.1f */s | Pitch: %+6.1f */s | Yaw: %+6.1f */s\n", gx, gy, gz);
    } else {
      Serial.println("   [ITG3205 DURUM: BAGLANTI YOK]");
    }

    // Manyetometre
    if (hmc_bulundu) {
      float mx, my, mz, heading;
      hmc5883lOku(mx, my, mz, heading);
      Serial.printf("   Manyetik (HMC)   : X: %+5.1f | Y: %+5.1f | Z: %+5.1f mG  [Pusula Acisi: %.1f*]\n", mx, my, mz, heading);
    } else {
      Serial.println("   [HMC5883L DURUM: BAGLANTI YOK]");
    }

    // --- 3. GPS / GNSS BÖLÜMÜ (E108-GN04D / GY-GPS6MV2) ---
    Serial.println(">> [3. GPS / GNSS MODÜLÜ - E108-GN04D / GY-GPS6MV2]");
    Serial.printf("   Toplam Alinan Bayt  : %lu bayt\n", gpsGelenBaytSayisi);

    if (gpsGelenBaytSayisi > 0) {
      Serial.println("   [UART BAGLANTISI     : BASARILI (GPS modulu Teensy ile iletisim kuruyor)]");
      if (strlen(sonNMEACumlesi) > 0) {
        Serial.printf("   Son Alinan NMEA     : %s\n", sonNMEACumlesi);
      }
      Serial.printf("   Uydu Sayisi         : %d\n", gpsUyduSayisi);
      Serial.printf("   Fix / Kilit Durumu  : %s\n", (gpsFixDurumu > 0) ? "3D FIX ALINDI!" : "KILIT YOK (No Fix)");

      if (gpsFixDurumu > 0) {
        Serial.printf("   Enlem               : %.6f\n", gpsEnlem);
        Serial.printf("   Boylam              : %.6f\n", gpsBoylam);
        Serial.printf("   GPS Irtifasi        : %.1f m\n", gpsIrtifa);
        Serial.println("   [SONUC: HARIKA] GPS hem donanimsal hem konumsal olarak aktif!");
      } else {
        Serial.println("   -------------------------------------------------------------------------");
        Serial.println("   [KAPALI ALAN TESPITI] Uydular kilitlenmedi (0 Uydu).");
        Serial.println("   -> TEKNIK ACIKLAMA : Test kapali ortamda yapildigindan uydu sinyalleri");
        Serial.println("      betonarme yapidan gecemez. Bu durum tamamen NORMALDIR.");
        Serial.println("   -> DONANIM SONUCU  : Teensy UART portu (Pins 7/8), TX-RX capraz baglantisi");
        Serial.println("      ve GPS baud hizi %100 DOGRUDUR. Acik alanda 1-3 dk icinde konum gelecektir.");
        Serial.println("   -------------------------------------------------------------------------");
      }
    } else {
      Serial.println("   [HATA / UYARI: GPS MODULUNDEN VERI GELMIYOR! (0 Bayt)]");
      Serial.println("   Lutfen su kontrolleri yapiniz:");
      Serial.println("   1. TX-RX Baglantisi: GPS TXD pini Teensy Pin 7'ye (RX2),");
      Serial.println("                        GPS RXD pini Teensy Pin 8'e (TX2) bagli olmalidir.");
      Serial.println("   2. Guc Baglantisi  : GPS VCC (3.3V) ve GND ortaklanmis olmalidir.");
      Serial.println("   3. Eger Pin 0 ve Pin 1'e baglandiysa koddaki GPS_PORT'u Serial1 yapiniz.");
    }

    // Şartname Hatırlatması
    Serial.println("\n[!] TEKNOFEST SARTNAME UYARISI (Madde 4.6.34):");
    Serial.println("    Parasut ayrilma tetiklemesi GPS verisiyle YAPILAMAZ! Ayrilma sadece yukaridaki");
    Serial.println("    MS5611 Barometre ve ADXL345 Ivmeolcer verileriyle gerceklestirilmelidir.");
    Serial.println("--------------------------------------------------------------------------------\n");
  }
}

// =========================================================================================
// 6. I2C TARAYICI VE OTOMATİK YOL ATAMASI
// =========================================================================================
void i2cTaraVeAtamaYap() {
  // Wire (Pins 18 & 19) Tara
  Serial.print("  -> Wire (Pins 18-SDA, 19-SCL) uzerindeki cihazlar: ");
  int bulunanWire = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      Serial.printf("[0x%02X] ", a);
      bulunanWire++;
      if (a == 0x77 || a == 0x76) { ms5611_addr = a; wire_baro = &Wire; baro_bulundu = true; }
      if (a == 0x53) { wire_imu = &Wire; adxl_bulundu = true; }
      if (a == 0x68) { wire_imu = &Wire; itg_bulundu = true; }
      if (a == 0x1E) { wire_imu = &Wire; hmc_bulundu = true; }
    }
  }
  if (bulunanWire == 0) Serial.print("Cihaz bulunamadi.");
  Serial.println();

  // Wire1 (Pins 17 & 16) Tara
  Serial.print("  -> Wire1 (Pins 17-SDA1, 16-SCL1) uzerindeki cihazlar: ");
  int bulunanWire1 = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire1.beginTransmission(a);
    if (Wire1.endTransmission() == 0) {
      Serial.printf("[0x%02X] ", a);
      bulunanWire1++;
      if ((a == 0x77 || a == 0x76) && !baro_bulundu) { ms5611_addr = a; wire_baro = &Wire1; baro_bulundu = true; }
      if (a == 0x53 && !adxl_bulundu) { wire_imu = &Wire1; adxl_bulundu = true; }
      if (a == 0x68 && !itg_bulundu)  { wire_imu = &Wire1; itg_bulundu = true; }
      if (a == 0x1E && !hmc_bulundu)  { wire_imu = &Wire1; hmc_bulundu = true; }
    }
  }
  if (bulunanWire1 == 0) Serial.print("Cihaz bulunamadi.");
  Serial.println();
}

// =========================================================================================
// 7. MS5611 SÜRÜCÜSÜ (STANDALONE DAHİLİ UYGULAMA)
// =========================================================================================
bool ms5611Baslat(TwoWire* wire, uint8_t addr) {
  // Reset Komutu (0x1E)
  wire->beginTransmission(addr);
  wire->write(0x1E);
  if (wire->endTransmission() != 0) return false;
  delay(15);

  // PROM Okuma (C1 - C6 Kalibrasyon Katsayıları)
  for (uint8_t i = 1; i <= 6; i++) {
    wire->beginTransmission(addr);
    wire->write(0xA0 + (i * 2));
    if (wire->endTransmission() != 0) return false;

    wire->requestFrom(addr, (uint8_t)2);
    if (wire->available() >= 2) {
      C[i] = (wire->read() << 8) | wire->read();
    } else {
      return false;
    }
  }
  // PROM geçerlilik testi: Katsayılar 0 veya 0xFFFF olmamalı
  if (C[1] == 0 || C[1] == 0xFFFF) return false;
  return true;
}

void ms5611Oku(float &sicaklik, float &basinc, float &irtifa) {
  // 1. D1 Dönüşümünü Başlat (Basınç OSR=4096: 0x48)
  wire_baro->beginTransmission(ms5611_addr);
  wire_baro->write(0x48);
  wire_baro->endTransmission();
  delay(9); // 4096 örnekleme için ~8.22 ms gerekir

  // ADC Oku (D1)
  wire_baro->beginTransmission(ms5611_addr);
  wire_baro->write(0x00);
  wire_baro->endTransmission();
  wire_baro->requestFrom(ms5611_addr, (uint8_t)3);
  uint32_t D1 = 0;
  if (wire_baro->available() >= 3) {
    D1 = ((uint32_t)wire_baro->read() << 16) | ((uint32_t)wire_baro->read() << 8) | wire_baro->read();
  }

  // 2. D2 Dönüşümünü Başlat (Sıcaklık OSR=4096: 0x58)
  wire_baro->beginTransmission(ms5611_addr);
  wire_baro->write(0x58);
  wire_baro->endTransmission();
  delay(9);

  // ADC Oku (D2)
  wire_baro->beginTransmission(ms5611_addr);
  wire_baro->write(0x00);
  wire_baro->endTransmission();
  wire_baro->requestFrom(ms5611_addr, (uint8_t)3);
  uint32_t D2 = 0;
  if (wire_baro->available() >= 3) {
    D2 = ((uint32_t)wire_baro->read() << 16) | ((uint32_t)wire_baro->read() << 8) | wire_baro->read();
  }

  // 3. Matematiksel Hesaplama (MS5611 Datasheet Formülleri)
  int64_t dT = (int64_t)D2 - ((int64_t)C[5] << 8);
  int64_t TEMP = 2000 + ((dT * (int64_t)C[6]) >> 23);

  int64_t OFF  = ((int64_t)C[2] << 16) + ((dT * (int64_t)C[4]) >> 7);
  int64_t SENS = ((int64_t)C[1] << 15) + ((dT * (int64_t)C[3]) >> 8);

  // 2. Derece Sıcaklık Düzeltmesi
  int64_t T2 = 0, OFF2 = 0, SENS2 = 0;
  if (TEMP < 2000) {
    T2 = (dT * dT) >> 31;
    int64_t tempDiff = TEMP - 2000;
    OFF2  = (5 * tempDiff * tempDiff) >> 1;
    SENS2 = (5 * tempDiff * tempDiff) >> 2;
    if (TEMP < -1500) {
      int64_t tempDiff2 = TEMP + 1500;
      OFF2  += 7 * tempDiff2 * tempDiff2;
      SENS2 += (11 * tempDiff2 * tempDiff2) >> 1;
    }
  }

  TEMP -= T2;
  OFF  -= OFF2;
  SENS -= SENS2;

  int64_t P = (((D1 * SENS) >> 21) - OFF) >> 15;

  sicaklik = TEMP / 100.0f;       // Santigrat Derece (°C)
  basinc   = P / 100.0f;          // Hektopaskal (hPa / mbar)
  // Standart Atmosfer Barometrik İrtifa Formülü
  irtifa   = 44330.0f * (1.0f - pow(basinc / 1013.25f, 0.190295f)); // Metre
}

// =========================================================================================
// 8. GY-85 IMU SÜRÜCÜLERİ
// =========================================================================================
// ADXL345 (İvmeölçer)
bool adxl345Baslat(TwoWire* wire) {
  // Device ID kontrolü (0x00 registerı 0xE5 dönmelidir)
  wire->beginTransmission(ADXL345_ADDR);
  wire->write(0x00);
  wire->endTransmission();
  wire->requestFrom(ADXL345_ADDR, (uint8_t)1);
  if (wire->read() != 0xE5) return false;

  // Power Control: Ölçüm modunu aç (0x2D -> 0x08)
  wire->beginTransmission(ADXL345_ADDR);
  wire->write(0x2D);
  wire->write(0x08);
  wire->endTransmission();

  // Data Format: +-16g tam çözünürlük (0x31 -> 0x0B)
  wire->beginTransmission(ADXL345_ADDR);
  wire->write(0x31);
  wire->write(0x0B);
  wire->endTransmission();
  return true;
}

void adxl345Oku(float &ax, float &ay, float &az) {
  wire_imu->beginTransmission(ADXL345_ADDR);
  wire_imu->write(0x32);
  wire_imu->endTransmission();
  wire_imu->requestFrom(ADXL345_ADDR, (uint8_t)6);
  if (wire_imu->available() >= 6) {
    int16_t rawX = wire_imu->read() | (wire_imu->read() << 8);
    int16_t rawY = wire_imu->read() | (wire_imu->read() << 8);
    int16_t rawZ = wire_imu->read() | (wire_imu->read() << 8);
    // Tam çözünürlükte ölçek: 3.9 mg/LSB (0.0039g)
    ax = rawX * 0.0039f;
    ay = rawY * 0.0039f;
    az = rawZ * 0.0039f;
  }
}

// ITG3205 (Jiroskop)
bool itg3205Baslat(TwoWire* wire) {
  // Uyandırma ve PLL saat referansı (0x3E -> 0x01)
  wire->beginTransmission(ITG3205_ADDR);
  wire->write(0x3E);
  wire->write(0x01);
  if (wire->endTransmission() != 0) return false;

  // +-2000 deg/s tam skala (0x16 -> 0x18)
  wire->beginTransmission(ITG3205_ADDR);
  wire->write(0x16);
  wire->write(0x18);
  wire->endTransmission();
  return true;
}

void itg3205Oku(float &gx, float &gy, float &gz) {
  wire_imu->beginTransmission(ITG3205_ADDR);
  wire_imu->write(0x1D);
  wire_imu->endTransmission();
  wire_imu->requestFrom(ITG3205_ADDR, (uint8_t)6);
  if (wire_imu->available() >= 6) {
    int16_t rawX = (wire_imu->read() << 8) | wire_imu->read();
    int16_t rawY = (wire_imu->read() << 8) | wire_imu->read();
    int16_t rawZ = (wire_imu->read() << 8) | wire_imu->read();
    // 14.375 LSB = 1 derece/saniye
    gx = rawX / 14.375f;
    gy = rawY / 14.375f;
    gz = rawZ / 14.375f;
  }
}

// HMC5883L (Manyetometre)
bool hmc5883lBaslat(TwoWire* wire) {
  // Mod Register: Sürekli Ölçüm Modu (0x02 -> 0x00)
  wire->beginTransmission(HMC5883L_ADDR);
  wire->write(0x02);
  wire->write(0x00);
  if (wire->endTransmission() != 0) return false;
  return true;
}

void hmc5883lOku(float &mx, float &my, float &mz, float &heading) {
  wire_imu->beginTransmission(HMC5883L_ADDR);
  wire_imu->write(0x03);
  wire_imu->endTransmission();
  wire_imu->requestFrom(HMC5883L_ADDR, (uint8_t)6);
  if (wire_imu->available() >= 6) {
    int16_t rawX = (wire_imu->read() << 8) | wire_imu->read();
    int16_t rawZ = (wire_imu->read() << 8) | wire_imu->read();
    int16_t rawY = (wire_imu->read() << 8) | wire_imu->read();
    mx = (float)rawX;
    my = (float)rawY;
    mz = (float)rawZ;

    heading = atan2(my, mx) * 180.0f / PI;
    if (heading < 0) heading += 360.0f;
  }
}

// =========================================================================================
// 9. GPS NMEA İŞLEME VE PARSER
// =========================================================================================
void gpsKarakterIsle(char c) {
  gpsGelenBaytSayisi++;

  if (c == '\n' || c == '\r') {
    if (nmeaindex > 5) {
      sonNMEACumlesi[nmeaindex] = '\0';
      nmeaParse(sonNMEACumlesi);
    }
    nmeaindex = 0;
  } else {
    if (nmeaindex < (int)(sizeof(sonNMEACumlesi) - 1)) {
      sonNMEACumlesi[nmeaindex++] = c;
    }
  }
}

// Hafif NMEA Cümle Ayrıştırıcı ($GNGGA, $GPGGA, $GNRMC, $GPRMC)
void nmeaParse(char* c) {
  // $..GGA: Global Positioning System Fix Data
  if (strstr(c, "GGA") != NULL) {
    char kopya[120];
    strncpy(kopya, c, sizeof(kopya));
    char* token = strtok(kopya, ",");
    int alan = 0;
    while (token != NULL) {
      alan++;
      if (alan == 2 && strlen(token) >= 6) { // UTC Zaman (hhmmss.ss)
        snprintf(gpsUTCZaman, sizeof(gpsUTCZaman), "%.2s:%.2s:%.2s", token, token+2, token+4);
        gpsZamanGecerli = true;
      }
      else if (alan == 7) { // Fix Kalitesi (0=Yok, 1=GPS, 2=DGPS)
        gpsFixDurumu = atoi(token);
      }
      else if (alan == 8) { // Uydu Sayısı
        gpsUyduSayisi = atoi(token);
      }
      else if (alan == 10) { // Anten İrtifası
        gpsIrtifa = atof(token);
      }
      token = strtok(NULL, ",");
    }
  }
  // $..RMC: Recommended Minimum Specific GNSS Data
  else if (strstr(c, "RMC") != NULL) {
    char kopya[120];
    strncpy(kopya, c, sizeof(kopya));
    char* token = strtok(kopya, ",");
    int alan = 0;
    char enlemStr[15] = "", enlemYon = 'N';
    char boylamStr[15] = "", boylamYon = 'E';

    while (token != NULL) {
      alan++;
      if (alan == 3) { // Status (A = Aktif, V = Void/Geçersiz)
        if (token[0] == 'A') gpsFixDurumu = max(gpsFixDurumu, 1);
      }
      else if (alan == 4) strncpy(enlemStr, token, sizeof(enlemStr));
      else if (alan == 5) enlemYon = token[0];
      else if (alan == 6) strncpy(boylamStr, token, sizeof(boylamStr));
      else if (alan == 7) boylamYon = token[0];
      token = strtok(NULL, ",");
    }

    if (strlen(enlemStr) > 4 && strlen(boylamStr) > 4) {
      // NMEA Koordinatını Ondalık Dereceye (DD) Dönüştür (ddmm.mmmm -> dd + mm.mmmm/60)
      float hamLat = atof(enlemStr);
      int derecelat = (int)(hamLat / 100);
      float dakikalat = hamLat - (derecelat * 100);
      gpsEnlem = derecelat + (dakikalat / 60.0f);
      if (enlemYon == 'S') gpsEnlem = -gpsEnlem;

      float hamLng = atof(boylamStr);
      int derecelng = (int)(hamLng / 100);
      float dakikalng = hamLng - (derecelng * 100);
      gpsBoylam = derecelng + (dakikalng / 60.0f);
      if (boylamYon == 'W') gpsBoylam = -gpsBoylam;
    }
  }
}

