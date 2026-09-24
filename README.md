# 💼 KOBİ & B2B Hızlı Fiyat Teklifi ve Talep Toplama Scripti

[![CI](https://github.com/eimza-kep/kobi-hizli-teklif-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-hizli-teklif-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-hizli-teklif-scripti/)
[![Lisans: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Kurulum Süresi](https://img.shields.io/badge/Kurulum-1%20Dakika-brightgreen)](#)
[![Bağımlılık](https://img.shields.io/badge/ba%C4%9F%C4%B1ml%C4%B1l%C4%B1k-0%20(S%C4%B1f%C4%B1r)-blue)](#)

KOBİ'lerin, B2B ticaret yapan firmaların, ajansların, toptancıların ve yazılım şirketlerinin web sitelerine **1 dakikada kurabileceği**, dinamik sepet/miktar hesaplayıcılı, yazdırılabilir proforma çıktılı ve WhatsApp entegrasyonlu **Kurumsal Fiyat Teklifi (RFQ) Scripti**.

---

## 🌟 Temel Özellikler

1. **Dinamik Fiyat ve KDV Hesaplama:**
   - Ürün/hizmet seçimi, miktar artırma/azaltma, peşin havale iskontosu (%5) ve yasal %20 KDV hesabı anlık olarak çalışır.
2. **Resmi Proforma Fatura / Teklif Çıktısı:**
   - Form gönderildiğinde teklif numarası (Örn: `TEKLIF-2026-4819`) atanır ve müşteri anında profesyonel, yazdırılabilir veya PDF olarak kaydedilebilir proforma teklif belgesine ulaşır.
3. **Tek Tıkla WhatsApp Satış Hattı Entegrasyonu:**
   - Müşteri oluşturulan teklifi doğrudan tek tuşla şirketinizin WhatsApp kurumsal hattına gönderebilir.
4. **CRM Yönetim Paneli (`admin.html`):**
   - Gelen teklif taleplerini listeleme, arama ve durum güncelleme (`Yeni Talep` -> `Teklif İletildi` -> `Satışa Döndü` -> `İptal`).
   - Toplam potansiyel ciro takibi ve tek tıkla Excel/CSV dökümü alma.
5. **Çift Arka Uç Desteği:**
   - **cPanel / Paylaşımlı Hosting:** Doğrudan `api.php` üzerinden JSON depolama.
   - **VPS / Yerel:** Python `server.py` ve yerleşik SQLite veritabanı.
   - **Statik:** Sunucusuz doğrudan tarayıcı hafızasıyla (`localStorage`) çalışabilir.

---

## 🚀 1 Dakikada Hızlı Kurulum

### 1. Windows'ta Tek Tıkla Çalıştırma (Test & Demo)
Klasördeki **`Baslat.bat`** dosyasına çift tıklayın! Yerel sunucu otomatik başlar ve tarayıcınızda form açılır.

### 2. Paylaşımlı Hosting / cPanel (Apache & PHP)
1. Dosyaları zip olarak indirin.
2. Sitenizin `public_html/teklif` dizinine yükleyin.
3. `https://siteniz.com/teklif/` adresinden doğrudan kullanın!

### 3. Python Sunucusu ile Çalıştırma
```bash
python server.py
```
- Müşteri Teklif Formu: `http://localhost:8081/index.html`
- CRM Yönetim Paneli: `http://localhost:8081/admin.html`

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Kurumsal ve ticari amaçlarla tamamen serbestçe kullanılabilir.
