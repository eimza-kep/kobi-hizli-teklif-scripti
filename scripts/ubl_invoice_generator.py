# -*- coding: utf-8 -*-
"""
scripts/ubl_invoice_generator.py
--------------------------------
KOBİ Tekliflerini GİB UBL-TR 2.1 e-Fatura XML Formatına ve
Kurumsal PDF/Yazdırılabilir Proforma Faturaya Dönüştürücü.
"""

import uuid
import datetime
import xml.etree.ElementTree as ET

DEFAULT_SUPPLIER = {
    "title": "KOBİ Dijital Dönüşüm ve E-İmza Çözümleri A.Ş.",
    "vkn": "5810492810",
    "tax_office": "Büyük Mükellefler V.D.",
    "address": "Bilişim Vadisi, Teknoloji Blokları No:42/A",
    "city": "Kocaeli / İstanbul",
    "phone": "0850 300 40 50",
    "email": "muhasebe@kobieimza.com.tr",
    "bank_name": "Türkiye İş Bankası",
    "bank_iban": "TR68 0006 4000 0011 2233 4455 66",
    "logo_url": "https://raw.githubusercontent.com/eimza-kep/kobi-hizli-teklif-scripti/main/assets/logo.png"
}

def generate_ubl_invoice_xml(quote, supplier=None):
    """
    KOBİ teklif verisini GİB UBL-TR 2.1 standart e-Fatura / e-Arşiv XML'ine dönüştürür.
    """
    sup = supplier or DEFAULT_SUPPLIER
    quote_no = quote.get("quote_no", "TEKLIF-2026-0001")
    doc_uuid = quote.get("uuid") or str(uuid.uuid4())
    issue_date = (quote.get("created_at") or datetime.date.today().isoformat())[:10]

    unit_price = float(quote.get("unit_price", 0.0))
    qty = int(quote.get("qty", 1))
    subtotal = float(quote.get("subtotal", unit_price * qty))
    vat = float(quote.get("vat", subtotal * 0.20))
    grand_total = float(quote.get("grand_total", subtotal + vat))
    prod_name = quote.get("product_name", "Standart Hizmet Paketi")

    cust_title = quote.get("company_name", "Müşteri Firma")
    cust_vkn = quote.get("vkn", "1111111111")
    cust_city = quote.get("city", "İstanbul")

    # XML Namespaces
    ns_ubl = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    ns_cac = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    ns_cbc = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

    ET.register_namespace("", ns_ubl)
    ET.register_namespace("cac", ns_cac)
    ET.register_namespace("cbc", ns_cbc)

    root = ET.Element(f"{{{ns_ubl}}}Invoice")

    # Temel Üst Bilgiler
    ET.SubElement(root, f"{{{ns_cbc}}}UBLVersionID").text = "2.1"
    ET.SubElement(root, f"{{{ns_cbc}}}CustomizationID").text = "TR1.2"
    ET.SubElement(root, f"{{{ns_cbc}}}ProfileID").text = "TICARIFATURA"
    ET.SubElement(root, f"{{{ns_cbc}}}ID").text = quote_no
    ET.SubElement(root, f"{{{ns_cbc}}}CopyIndicator").text = "false"
    ET.SubElement(root, f"{{{ns_cbc}}}UUID").text = doc_uuid
    ET.SubElement(root, f"{{{ns_cbc}}}IssueDate").text = issue_date
    ET.SubElement(root, f"{{{ns_cbc}}}InvoiceTypeCode").text = "SATIS"
    ET.SubElement(root, f"{{{ns_cbc}}}DocumentCurrencyCode").text = "TRY"
    ET.SubElement(root, f"{{{ns_cbc}}}LineCountNumeric").text = "1"

    # Satıcı (Supplier)
    supplier_party = ET.SubElement(root, f"{{{ns_cac}}}AccountingSupplierParty")
    party_sup = ET.SubElement(supplier_party, f"{{{ns_cac}}}Party")
    p_id_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyIdentification")
    ET.SubElement(p_id_sup, f"{{{ns_cbc}}}ID", schemeID="VKN").text = sup["vkn"]
    p_name_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyName")
    ET.SubElement(p_name_sup, f"{{{ns_cbc}}}Name").text = sup["title"]
    p_addr_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PostalAddress")
    ET.SubElement(p_addr_sup, f"{{{ns_cbc}}}CityName").text = sup["city"]
    p_tax_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyTaxScheme")
    tax_sch_sup = ET.SubElement(p_tax_sup, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(tax_sch_sup, f"{{{ns_cbc}}}Name").text = sup["tax_office"]

    # Alıcı (Customer)
    customer_party = ET.SubElement(root, f"{{{ns_cac}}}AccountingCustomerParty")
    party_cust = ET.SubElement(customer_party, f"{{{ns_cac}}}Party")
    p_id_cust = ET.SubElement(party_cust, f"{{{ns_cac}}}PartyIdentification")
    scheme = "VKN" if len(cust_vkn) == 10 else "TCKN"
    ET.SubElement(p_id_cust, f"{{{ns_cbc}}}ID", schemeID=scheme).text = cust_vkn
    p_name_cust = ET.SubElement(party_cust, f"{{{ns_cac}}}PartyName")
    ET.SubElement(p_name_cust, f"{{{ns_cbc}}}Name").text = cust_title
    p_addr_cust = ET.SubElement(party_cust, f"{{{ns_cac}}}PostalAddress")
    ET.SubElement(p_addr_cust, f"{{{ns_cbc}}}CityName").text = cust_city

    # Vergi Toplamı (TaxTotal)
    tax_total = ET.SubElement(root, f"{{{ns_cac}}}TaxTotal")
    ET.SubElement(tax_total, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{vat:.2f}"
    tax_subtotal = ET.SubElement(tax_total, f"{{{ns_cac}}}TaxSubtotal")
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}TaxableAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{vat:.2f}"
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}Percent").text = "20"
    tax_cat = ET.SubElement(tax_subtotal, f"{{{ns_cac}}}TaxCategory")
    tax_sch = ET.SubElement(tax_cat, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(tax_sch, f"{{{ns_cbc}}}Name").text = "KDV"
    ET.SubElement(tax_sch, f"{{{ns_cbc}}}TaxTypeCode").text = "0015"

    # Genel Toplamlar (LegalMonetaryTotal)
    monetary = ET.SubElement(root, f"{{{ns_cac}}}LegalMonetaryTotal")
    ET.SubElement(monetary, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxExclusiveAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxInclusiveAmount", currencyID="TRY").text = f"{grand_total:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}PayableAmount", currencyID="TRY").text = f"{grand_total:.2f}"

    # Fatura Kalemi (InvoiceLine)
    line = ET.SubElement(root, f"{{{ns_cac}}}InvoiceLine")
    ET.SubElement(line, f"{{{ns_cbc}}}ID").text = "1"
    ET.SubElement(line, f"{{{ns_cbc}}}InvoicedQuantity", unitCode="C62").text = str(qty)
    ET.SubElement(line, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    
    item = ET.SubElement(line, f"{{{ns_cac}}}Item")
    ET.SubElement(item, f"{{{ns_cbc}}}Name").text = prod_name
    
    price = ET.SubElement(line, f"{{{ns_cac}}}Price")
    ET.SubElement(price, f"{{{ns_cbc}}}PriceAmount", currencyID="TRY").text = f"{unit_price:.2f}"

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")

def generate_proforma_html(quote, supplier=None):
    """
    Kurumsal A4 boyutunda yazdırılabilir veya PDF olarak saklanabilir
    Proforma Fatura HTML çıktısı üretir.
    """
    sup = supplier or DEFAULT_SUPPLIER
    quote_no = quote.get("quote_no", "TEKLIF-2026-0001")
    issue_date = (quote.get("created_at") or datetime.date.today().isoformat())[:10]

    unit_price = float(quote.get("unit_price", 0.0))
    qty = int(quote.get("qty", 1))
    subtotal = float(quote.get("subtotal", unit_price * qty))
    vat = float(quote.get("vat", subtotal * 0.20))
    grand_total = float(quote.get("grand_total", subtotal + vat))
    prod_name = quote.get("product_name", "Standart Hizmet Paketi")

    cust_title = quote.get("company_name", "Müşteri Firma")
    cust_vkn = quote.get("vkn", "1111111111")
    cust_contact = quote.get("contact_name", "")
    cust_phone = quote.get("phone", "")
    cust_city = quote.get("city", "")

    logo_html = f'<img src="{sup["logo_url"]}" alt="Şirket Logosu" style="max-height: 48px; max-width: 200px; object-fit: contain; margin-bottom: 8px;"><br>' if sup.get("logo_url") else ''

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Proforma Fatura - {quote_no}</title>
<style>
  * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
  body {{ margin: 0; padding: 24px; color: #1e293b; background: #f8fafc; }}
  .toolbar {{ max-width: 800px; margin: 0 auto 16px auto; display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 12px 20px; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
  .invoice-box {{ max-width: 800px; margin: auto; border: 1px solid #e2e8f0; padding: 36px; border-radius: 8px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
  .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0284c7; padding-bottom: 16px; margin-bottom: 20px; }}
  .company-title {{ font-size: 1.25rem; font-weight: 800; color: #0369a1; }}
  .proforma-tag {{ font-size: 1.5rem; font-weight: 800; color: #0284c7; text-align: right; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; font-size: 0.88rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  th {{ background: #f8fafc; padding: 10px; border: 1px solid #e2e8f0; text-align: left; font-size: 0.85rem; }}
  td {{ padding: 12px 10px; border: 1px solid #e2e8f0; font-size: 0.88rem; }}
  .totals {{ display: flex; justify-content: flex-end; margin-bottom: 24px; }}
  .totals-table {{ width: 260px; font-size: 0.9rem; line-height: 1.8; }}
  .bank-box {{ background: #f8fafc; border: 1px dashed #cbd5e1; padding: 14px; border-radius: 6px; font-size: 0.85rem; margin-bottom: 20px; }}
  .footer {{ display: flex; justify-content: space-between; margin-top: 30px; font-size: 0.82rem; color: #64748b; }}
  @media print {{
    body {{ padding: 0; background: #fff; }}
    .toolbar {{ display: none !important; }}
    .invoice-box {{ border: none; padding: 0; box-shadow: none; }}
    .no-print {{ display: none !important; }}
  }}
</style>
</head>
<body>
<div class="toolbar no-print">
  <div style="font-size: 0.92rem; font-weight: 700; color: #0f172a;">💼 Proforma Fatura Belgesi ({quote_no})</div>
  <div style="display: flex; gap: 10px;">
    <button onclick="window.print()" style="background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer;">🖨️ Yazdır / PDF Olarak Kaydet</button>
    <a href="/api/export-ubl-xml?quote_no={quote_no}" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; text-decoration: none; font-size: 0.85rem; display: inline-flex; align-items: center;">📥 UBL XML İndir</a>
  </div>
</div>

<div class="invoice-box">
  <div class="header">
    <div>
      {logo_html}
      <div class="company-title">{sup['title']}</div>
      <div style="font-size:0.82rem; color:#64748b; margin-top:4px; line-height: 1.4;">
        VKN: {sup['vkn']} | {sup['tax_office']}<br>
        {sup['address']} - {sup['city']}<br>
        Tel: {sup['phone']} | E-Posta: {sup['email']}
      </div>
    </div>
    <div class="proforma-tag">
      PROFORMA FATURA<br>
      <span style="font-size:0.9rem; color:#475569; font-weight:600;">No: {quote_no}</span><br>
      <span style="font-size:0.8rem; color:#64748b; font-weight:normal;">Tarih: {issue_date}</span>
    </div>
  </div>

  <div class="meta-grid">
    <div>
      <b>SAYIN (MÜŞTERİ):</b><br>
      {cust_title}<br>
      VKN / TCKN: {cust_vkn}<br>
      Yetkili: {cust_contact}<br>
      İletişim: {cust_phone} | {cust_city}
    </div>
    <div>
      <b>ÖDEME VE TESLİMAT ŞARTLARI:</b><br>
      Ödeme Türü: {quote.get('payment_term', 'Peşin / Havale')}<br>
      Geçerlilik Süresi: 15 Takvim Günü<br>
      Teslimat Şekli: Elektronik Lisans Aktivasyonu
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:40px;">Sıra</th>
        <th>Hizmet / Mal Açıklaması</th>
        <th style="width:80px;">Miktar</th>
        <th style="width:110px;">Birim Fiyat</th>
        <th style="width:70px;">KDV</th>
        <th style="width:120px;">Toplam (TL)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td><b>{prod_name}</b></td>
        <td>{qty} Adet</td>
        <td>{unit_price:,.2f} TL</td>
        <td>%20</td>
        <td><b>{subtotal:,.2f} TL</b></td>
      </tr>
    </tbody>
  </table>

  <div class="totals">
    <div class="totals-table">
      <div style="display:flex; justify-content:space-between;"><span>Ara Toplam:</span> <b>{subtotal:,.2f} TL</b></div>
      <div style="display:flex; justify-content:space-between;"><span>KDV (%20):</span> <b>{vat:,.2f} TL</b></div>
      <div style="display:flex; justify-content:space-between; font-size:1.15rem; color:#0284c7; border-top:2px solid #e2e8f0; padding-top:6px; margin-top:4px;">
        <span>Genel Toplam:</span> <b>{grand_total:,.2f} TL</b>
      </div>
    </div>
  </div>

  <div class="bank-box">
    <b>BANKA HAVALE / EFT BİLGİLERİ:</b><br>
    Banka: {sup['bank_name']}<br>
    IBAN: <b>{sup['bank_iban']}</b><br>
    Hesap Sahibi: {sup['title']}
  </div>

  <div class="footer">
    <div>İşbu belge proforma fatura mahiyetinde olup resmi fatura yerine geçmez.</div>
    <div style="text-align:right;">Yetkili Kaşe & İmza</div>
  </div>
</div>
</body>
</html>"""
