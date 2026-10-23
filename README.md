# 💼 KOBİ & B2B Hızlı Fiyat Teklifi ve Talep Toplama Scripti

[![CI](https://github.com/eimza-kep/kobi-hizli-teklif-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-hizli-teklif-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-hizli-teklif-scripti/)
[![Lisans: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![UBL-TR](https://img.shields.io/badge/e--Fatura%20UBL--TR-2.1%20Uyumlu-blue)](#)
[![Kurulum Süresi](https://img.shields.io/badge/Kurulum-1%20Dakika-brightgreen)](#)
[![Bağımlılık](https://img.shields.io/badge/ba%C4%9F%C4%B1ml%C4%B1l%C4%B1k-0%20(S%C4%B1f%C4%B1r)-blue)](#)

KOBİ'lerin, B2B ticaret yapan firmaların, ajansların, toptancıların ve bilişim/yazılım şirketlerinin web sitelerine **1 dakikada kurabileceği**, dinamik sepet/miktar hesaplayıcılı, **KDV Tevkifatı (2/10 - 9/10 oranları & GİB kodları)**, **özel iskonto yönetimi**, **GİB UBL-TR 2.1 e-Fatura XML taslak ihracı**, **kurumsal logo & IBAN destekli A4 Proforma Fatura çıktısı**, CRM yönetim paneli ve tek tıkla WhatsApp satış entegrasyonu sunan **Kurumsal Fiyat Teklifi (RFQ) Scripti**.

---

## 🌟 Temel Yetenekler & Özellikler

1. **GİB UBL-TR 2.1 e-Fatura & Tevkifatlı Fatura XML Dışa Aktarımı:**
   - Onaylanan veya talep edilen teklifleri uluslararası ve Gelir İdaresi Başkanlığı (GİB) standardı olan **UBL-TR 2.1 TICARIFATURA / SATIS / TEVKIFAT** XML formatına dönüştürür.
   - Tevkifat uygulandığında otomatik `<cac:WithholdingTaxTotal>` ve resmi tevkifat kodunu (601, 602, 604, 608, 616, 624 vb.) üretir.
   - Doğrudan özel entegratörlere veya [e-fatura-xml-goruntuleyici](https://github.com/eimza-kep/e-fatura-xml-goruntuleyici) sistemine aktarılabilir.
2. **KDV Tevkifatı ve Gelişmiş İskonto Motoru:**
   - KDV Genel Uygulama Tebliği uyumlu 2/10, 3/10, 4/10, 5/10, 7/10 ve 9/10 oranlarında tevkifat hesaplama.
   - Hesaplanan KDV, Tevkif Edilen KDV, Tahsil Edilecek KDV ve Net Ödenecek Tutar ayrımı.
   - Peşin ödeme iskontosu (%5) ve özel iskonto oranları ile dinamik matrah hesaplama.
3. **Kurumsal Proforma Fatura & Yazdır / PDF İndirme:**
   - Şirket logosu, resmi unvan, VKN/vergi dairesi, banka adı, IBAN ve tevkifat dökümünü içeren A4 formatında profesyonel proforma fatura oluşturur.
   - Yazdırma modu (`@media print`) optimize edilmiştir; tek tıkla doğrudan PDF olarak kaydedilebilir.
4. **CRM & Talep Yönetim Paneli (`admin.html`):**
   - Teklif taleplerini listeleme, tevkifatlı teklif rozetleri, arama ve durum güncelleme (`Yeni Talep` ➔ `Teklif İletildi` ➔ `Satışa Döndü` ➔ `İptal`).
   - Şirket ve fatura ayarları modalı (`⚙️ Şirket & Fatura Ayarları`) ile unvan, VKN, IBAN ve logo URL dinamik olarak yönetilir.
   - Toplam potansiyel ciro takibi ve tek tıkla CSV/Excel dökümü.
5. **WhatsApp Kurumsal Satış Hattı Entegrasyonu:**
   - Teklif özeti ve net tutarı formatlanarak tek tıkla kurumsal WhatsApp hattına iletilir.
6. **Esnek Çoklu Dağıtım Mimarisi:**
   - **Python (Önerilen):** Sıfır ek paket bağımlılığı ile yerleşik SQLite ve dahili HTTP sunucu (`python server.py`).
   - **Docker:** `docker compose up -d` ile izole ve üretime hazır konteyner.
   - **cPanel / Paylaşımlı Hosting:** Apache ve PHP (`api.php`) ile JSON tabanlı depolama.
   - **Statik / GitHub Pages:** Sunucu olmaksızın tarayıcı yerel depolaması (`localStorage`) ile bağımsız çalışma.

---

## 🚀 Kurulum ve Çalıştırma Rehberi

### Yöntem 1: Python Sunucusu ile Çalıştırma (Sıfır Bağımlılık)

Ek kütüphane (`pip install`) gerektirmez; standart Python 3.8+ kütüphaneleriyle çalışır:

```bash
# Depoyu klonlayın
git clone https://github.com/eimza-kep/kobi-hizli-teklif-scripti.git
cd kobi-hizli-teklif-scripti

# Sunucuyu başlatın
python server.py
```

- **Müşteri Teklif Portalı:** [http://localhost:8081/index.html](http://localhost:8081/index.html)
- **Yönetici Paneli:** [http://localhost:8081/admin.html](http://localhost:8081/admin.html)
- **Sağlık Kontrolü:** [http://localhost:8081/health](http://localhost:8081/health)

*(Windows kullanıcıları doğrudan klasördeki **`Baslat.bat`**, Linux/macOS kullanıcıları **`./baslat.sh`** çalıştırabilir).*

---

### Yöntem 2: Docker ile Çalıştırma

```bash
# Docker imajını oluşturup çalıştırın
docker build -t kobi-teklif .
docker run -d -p 8081:8081 -v $(pwd)/data:/app/data --name kobi-teklif-app kobi-teklif
```

---

### Yöntem 3: cPanel / Paylaşımlı Hosting (PHP & Apache)

1. Depo dosyalarını zip olarak indirin.
2. cPanel Dosya Yöneticisi ile `public_html/teklif` klasörüne yükleyin ve çıkartın.
3. `api.php` dosyasının bulunduğu dizine yazma izni (CHMOD 755 / 775) verin.
4. `https://siteniz.com/teklif/` adresinden doğrudan kullanın.

---

## 🔌 REST API Uç Noktaları

| Metot | Uç Nokta | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/api/teklif-olustur` | Yeni müşteri teklif talebini SQLite'a kaydeder, tevkifat/iskonto hesaplar ve `quote_no` döner. |
| `POST` | `/api/calculate-quote` | Kalemler, miktar, iskonto ve tevkifat oranlarına göre canlı finansal döküm hesaplar. |
| `POST` | `/api/durum-guncelle` | Teklif durumunu günceller (`Yeni Talep`, `Teklif İletildi`, `Satışa Döndü`, `İptal`). |
| `GET` | `/api/tevkifat-oranlari` | Resmi GİB KDV Tevkifat kodları ve pay/payda oranlarını JSON döner. |
| `GET` | `/api/teklif-listesi` | Tüm gelen teklif kayıtlarını JSON dizisi olarak listeler. |
| `GET` | `/api/export-ubl-xml?quote_no=...` | Belirtilen teklifi GİB UBL-TR 2.1 (Tevkifatlı/Standart) `.xml` dosyası olarak indirir. |
| `POST` | `/api/export-ubl-xml` | Gönderilen teklif JSON gövdesini doğrudan UBL-TR XML'e dönüştürür. |
| `GET` | `/api/proforma-html?quote_no=...` | Yazdırılabilir A4 Proforma Fatura HTML sayfasını üretir. |
| `GET` | `/api/ayarlar` | Mevcut şirket unvanı, VKN, IBAN ve logo ayarlarını döner. |
| `POST` | `/api/ayarlar` | Şirket unvanı, VKN, IBAN ve logo ayarlarını SQLite'a kaydeder. |
| `GET` | `/health` | Servis sağlık durumunu (`status: healthy`) döner. |

---

## 🧪 Birim ve Entegrasyon Testleri

Tüm veritabanı CRUD işlemleri, KDV hesaplamaları, iskonto, KDV tevkifat oranları (2/10, 5/10, 7/10, 9/10), UBL-TR XML şema doğrulaması ve HTML proforma şablonu birim testlerle korunmaktadır:

```bash
python scripts/test_teklif.py
```

Çıktı Örneği:
```text
============================================================
  KOBİ FİYAT TEKLİFİ & UBL XML TEST SÜİTİ
============================================================
test_calculate_quote_financials_standard ... ok
test_calculate_quote_financials_withholding_5_10 ... ok
test_calculate_quote_financials_withholding_9_10 ... ok
test_company_settings ... ok
test_database_initialization ... ok
test_database_migration_columns_and_insertion ... ok
test_generate_proforma_html ... ok
test_generate_ubl_invoice_xml ... ok
test_multi_items_calculation ... ok
test_quote_calculations_and_insertion ... ok
test_ubl_xml_tevkifat_invoice ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.031s

OK
✅ TÜM TESTLER BAŞARIYLA GEÇTİ!
```

---

## 🌐 KOBİ & E-Dönüşüm Açık Kaynak Ekosistemi

Bu teklif motoru, [@eimza-kep](https://github.com/eimza-kep) açık kaynak ekosisteminin satış ve teklif otomasyon modülüdür. İlgili diğer araçlar:

* 🏢 [kobi-finans-yonetim-excel-sablonlari](https://github.com/eimza-kep/kobi-finans-yonetim-excel-sablonlari) - Proforma fatura, nakit akışı ve başabaş analizi Excel şablonları.
* 📄 [e-fatura-xml-goruntuleyici](https://github.com/eimza-kep/e-fatura-xml-goruntuleyici) - Onaylanan tekliflerin e-Fatura/e-Arşiv UBL-TR XML çıktısını görüntüleme ve doğrulama.
* 📦 [kobi-tedarikci-teklif-toplama-scripti](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti) - Satın alma ve tedarikçilerden karşılaştırmalı teklif toplama portalı.
* 🌟 [awesome-turkiye-e-donusum](https://github.com/eimza-kep/awesome-turkiye-e-donusum) - Türkiye e-Dönüşüm açık kaynak araçları ve kütüphaneleri kürasyonu.

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Kurumsal ve ticari amaçlarla tamamen serbestçe kullanılabilir.
