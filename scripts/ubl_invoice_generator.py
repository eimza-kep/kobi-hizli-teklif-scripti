# -*- coding: utf-8 -*-
"""
scripts/ubl_invoice_generator.py
--------------------------------
KOBİ Tekliflerini GİB UBL-TR 2.1 e-Fatura XML Formatına (Tevkifat & İskonto Uyumlu)
ve Kurumsal PDF/Yazdırılabilir Proforma Faturaya Dönüştürücü Motor.
"""

import uuid
import json
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

# GİB KDV Tevkifat Kodları ve Oranları (KDV Genel Uygulama Tebliği)
TEVKIFAT_RATES = {
    "2/10": (2, 10, "616", "Diğer Hizmetler (2/10)"),
    "3/10": (3, 10, "624", "Fason Tekstil ve Konfeksiyon İşleri (3/10)"),
    "4/10": (4, 10, "608", "Yemek Servis ve Organizasyon Hizmetleri (4/10)"),
    "5/10": (5, 10, "601", "Yapım İşleri ve Danışmanlık Hizmetleri (5/10)"),
    "7/10": (7, 10, "604", "Makine, Teçhizat, Bakım ve Onarım (7/10)"),
    "9/10": (9, 10, "602", "Temizlik, Güvenlik ve Çevre Bakım Hizmetleri (9/10)")
}


def calculate_quote_financials(items_data=None, unit_price=0.0, qty=1, discount_rate=0.0, vat_rate=0.20, withholding_rate=None, product_name="Standart Hizmet Paketi"):
    """
    KOBİ fiyat teklifi ve fatura finansal hesaplama motoru:
    - Çoklu kalem veya tek kalem toplamı
    - İskonto düşümü
    - KDV (%20) hesabı
    - KDV Tevkifatı (2/10, 5/10, 7/10 vb.) ve tahsil edilecek net KDV
    - Ödenecek Toplam Tutar
    """
    items = []
    if isinstance(items_data, str) and items_data.strip().startswith("["):
        try:
            items_data = json.loads(items_data)
        except Exception:
            items_data = []

    if isinstance(items_data, list) and len(items_data) > 0:
        for it in items_data:
            p_name = it.get("name") or it.get("product_name") or "Hizmet/Ürün"
            u_price = float(it.get("unit_price", 0.0) or 0.0)
            q = int(it.get("qty", 1) or 1)
            line_disc = float(it.get("discount_rate", 0.0) or 0.0)
            line_gross = u_price * q
            line_disc_amt = line_gross * line_disc
            line_net = line_gross - line_disc_amt
            items.append({
                "name": p_name,
                "unit_price": round(u_price, 2),
                "qty": q,
                "discount_rate": line_disc,
                "discount_amount": round(line_disc_amt, 2),
                "gross_total": round(line_gross, 2),
                "net_total": round(line_net, 2)
            })
    else:
        u_price = float(unit_price or 0.0)
        q = int(qty or 1)
        gross = u_price * q
        disc_amt = gross * float(discount_rate or 0.0)
        net = gross - disc_amt
        items.append({
            "name": product_name or "Standart Hizmet Paketi",
            "unit_price": round(u_price, 2),
            "qty": q,
            "discount_rate": float(discount_rate or 0.0),
            "discount_amount": round(disc_amt, 2),
            "gross_total": round(gross, 2),
            "net_total": round(net, 2)
        })

    gross_total = sum(i["gross_total"] for i in items)
    total_discount = sum(i["discount_amount"] for i in items)
    if float(discount_rate or 0.0) > 0 and (not items_data or len(items_data) == 0):
        total_discount = gross_total * float(discount_rate)

    matrah = max(0.0, gross_total - total_discount)
    hesaplanan_kdv = round(matrah * float(vat_rate or 0.20), 2)

    # Tevkifat hesabı
    tevkifat_kod = ""
    tevkifat_aciklama = ""
    tevkifat_tutari = 0.0
    withholding_str = str(withholding_rate or "").strip()
    is_tevkifatli = False

    if withholding_str in TEVKIFAT_RATES:
        pay, payda, tevkifat_kod, tevkifat_aciklama = TEVKIFAT_RATES[withholding_str]
        tevkifat_tutari = round(hesaplanan_kdv * pay / payda, 2)
        is_tevkifatli = True
    elif "/" in withholding_str:
        try:
            parts = withholding_str.split("/")
            pay, payda = int(parts[0]), int(parts[1])
            tevkifat_tutari = round(hesaplanan_kdv * pay / payda, 2)
            tevkifat_kod = "601"
            tevkifat_aciklama = f"KDV Tevkifatı ({withholding_str})"
            is_tevkifatli = True
        except Exception:
            pass

    tahsil_edilecek_kdv = hesaplanan_kdv - tevkifat_tutari
    grand_total = matrah + hesaplanan_kdv
    payable_amount = matrah + tahsil_edilecek_kdv

    return {
        "items": items,
        "line_count": len(items),
        "gross_total": round(gross_total, 2),
        "discount_rate": float(discount_rate or 0.0),
        "total_discount": round(total_discount, 2),
        "subtotal": round(matrah, 2),
        "vat_rate": float(vat_rate or 0.20),
        "calculated_vat": round(hesaplanan_kdv, 2),
        "is_withholding": is_tevkifatli,
        "withholding_rate": withholding_str if is_tevkifatli else "YOK",
        "withholding_code": tevkifat_kod,
        "withholding_description": tevkifat_aciklama,
        "withholding_amount": round(tevkifat_tutari, 2),
        "payable_vat": round(tahsil_edilecek_kdv, 2),
        "grand_total": round(grand_total, 2),
        "payable_amount": round(payable_amount, 2)
    }


def generate_ubl_invoice_xml(quote, supplier=None):
    """
    KOBİ teklif verisini GİB UBL-TR 2.1 standart e-Fatura / e-Arşiv XML'ine dönüştürür.
    KDV Tevkifatı varsa WithholdingTaxTotal ve InvoiceTypeCode='TEVKIFAT' ekler.
    Çoklu kalem desteği sunar.
    """
    sup = supplier or DEFAULT_SUPPLIER
    quote_no = quote.get("quote_no", "TEKLIF-2026-0001")
    doc_uuid = quote.get("uuid") or str(uuid.uuid4())
    issue_date = (quote.get("created_at") or datetime.date.today().isoformat())[:10]

    # Finansalları hesapla
    fin = calculate_quote_financials(
        items_data=quote.get("items") or quote.get("items_json"),
        unit_price=quote.get("unit_price", 0.0),
        qty=quote.get("qty", 1),
        discount_rate=quote.get("discount_rate", 0.0),
        vat_rate=quote.get("vat_rate", 0.20),
        withholding_rate=quote.get("withholding_rate"),
        product_name=quote.get("product_name", "Standart Hizmet Paketi")
    )

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
    ET.SubElement(root, f"{{{ns_cbc}}}InvoiceTypeCode").text = "TEVKIFAT" if fin["is_withholding"] else "SATIS"
    ET.SubElement(root, f"{{{ns_cbc}}}DocumentCurrencyCode").text = "TRY"
    ET.SubElement(root, f"{{{ns_cbc}}}LineCountNumeric").text = str(fin["line_count"])

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

    # Vergi Toplamı (TaxTotal - KDV)
    tax_total = ET.SubElement(root, f"{{{ns_cac}}}TaxTotal")
    ET.SubElement(tax_total, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{fin['calculated_vat']:.2f}"
    tax_subtotal = ET.SubElement(tax_total, f"{{{ns_cac}}}TaxSubtotal")
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}TaxableAmount", currencyID="TRY").text = f"{fin['subtotal']:.2f}"
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{fin['calculated_vat']:.2f}"
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}Percent").text = "20"
    tax_cat = ET.SubElement(tax_subtotal, f"{{{ns_cac}}}TaxCategory")
    tax_sch = ET.SubElement(tax_cat, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(tax_sch, f"{{{ns_cbc}}}Name").text = "KDV"
    ET.SubElement(tax_sch, f"{{{ns_cbc}}}TaxTypeCode").text = "0015"

    # Tevkifat Toplamı (WithholdingTaxTotal)
    if fin["is_withholding"]:
        withholding_tax = ET.SubElement(root, f"{{{ns_cac}}}WithholdingTaxTotal")
        ET.SubElement(withholding_tax, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{fin['withholding_amount']:.2f}"
        w_subtotal = ET.SubElement(withholding_tax, f"{{{ns_cac}}}TaxSubtotal")
        ET.SubElement(w_subtotal, f"{{{ns_cbc}}}TaxableAmount", currencyID="TRY").text = f"{fin['calculated_vat']:.2f}"
        ET.SubElement(w_subtotal, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{fin['withholding_amount']:.2f}"
        
        w_cat = ET.SubElement(w_subtotal, f"{{{ns_cac}}}TaxCategory")
        w_sch = ET.SubElement(w_cat, f"{{{ns_cac}}}TaxScheme")
        ET.SubElement(w_sch, f"{{{ns_cbc}}}Name").text = "KDV TEVKIFAT"
        ET.SubElement(w_sch, f"{{{ns_cbc}}}TaxTypeCode").text = fin["withholding_code"] or "601"

    # Genel Toplamlar (LegalMonetaryTotal)
    monetary = ET.SubElement(root, f"{{{ns_cac}}}LegalMonetaryTotal")
    ET.SubElement(monetary, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{fin['gross_total']:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxExclusiveAmount", currencyID="TRY").text = f"{fin['subtotal']:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxInclusiveAmount", currencyID="TRY").text = f"{fin['grand_total']:.2f}"
    if fin["total_discount"] > 0:
        ET.SubElement(monetary, f"{{{ns_cbc}}}AllowanceTotalAmount", currencyID="TRY").text = f"{fin['total_discount']:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}PayableAmount", currencyID="TRY").text = f"{fin['payable_amount']:.2f}"

    # Fatura Kalemleri (InvoiceLines)
    for idx, item_data in enumerate(fin["items"], 1):
        line = ET.SubElement(root, f"{{{ns_cac}}}InvoiceLine")
        ET.SubElement(line, f"{{{ns_cbc}}}ID").text = str(idx)
        ET.SubElement(line, f"{{{ns_cbc}}}InvoicedQuantity", unitCode="C62").text = str(item_data["qty"])
        ET.SubElement(line, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{item_data['net_total']:.2f}"

        item = ET.SubElement(line, f"{{{ns_cac}}}Item")
        ET.SubElement(item, f"{{{ns_cbc}}}Name").text = item_data["name"]

        price = ET.SubElement(line, f"{{{ns_cac}}}Price")
        ET.SubElement(price, f"{{{ns_cbc}}}PriceAmount", currencyID="TRY").text = f"{item_data['unit_price']:.2f}"

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def generate_proforma_html(quote, supplier=None):
    """
    Kurumsal A4 boyutunda yazdırılabilir veya PDF olarak saklanabilir
    Proforma Fatura HTML çıktısı üretir (Tevkifat & İskonto Dökümlü).
    """
    sup = supplier or DEFAULT_SUPPLIER
    quote_no = quote.get("quote_no", "TEKLIF-2026-0001")
    issue_date = (quote.get("created_at") or datetime.date.today().isoformat())[:10]

    fin = calculate_quote_financials(
        items_data=quote.get("items") or quote.get("items_json"),
        unit_price=quote.get("unit_price", 0.0),
        qty=quote.get("qty", 1),
        discount_rate=quote.get("discount_rate", 0.0),
        vat_rate=quote.get("vat_rate", 0.20),
        withholding_rate=quote.get("withholding_rate"),
        product_name=quote.get("product_name", "Standart Hizmet Paketi")
    )

    cust_title = quote.get("company_name", "Müşteri Firma")
    cust_vkn = quote.get("vkn", "1111111111")
    cust_contact = quote.get("contact_name", "")
    cust_phone = quote.get("phone", "")
    cust_city = quote.get("city", "")

    logo_html = f'<img src="{sup["logo_url"]}" alt="Şirket Logosu" style="max-height: 48px; max-width: 200px; object-fit: contain; margin-bottom: 8px;"><br>' if sup.get("logo_url") else ''

    # Kalem satırları
    table_rows = []
    for idx, it in enumerate(fin["items"], 1):
        disc_text = f" (%{it['discount_rate']*100:.0f} İsk.)" if it["discount_rate"] > 0 else ""
        table_rows.append(f"""
          <tr>
            <td>{idx}</td>
            <td><b>{it['name']}</b>{disc_text}</td>
            <td>{it['qty']} Adet</td>
            <td>{it['unit_price']:,.2f} TL</td>
            <td>%20</td>
            <td><b>{it['net_total']:,.2f} TL</b></td>
          </tr>
        """)
    table_rows_html = "\n".join(table_rows)

    # Tevkifat dökümü
    tevkifat_rows_html = ""
    if fin["is_withholding"]:
        tevkifat_rows_html = f"""
          <div style="display:flex; justify-content:space-between; color:#b91c1c;">
            <span>Tevkif Edilen KDV ({fin['withholding_rate']}):</span>
            <b>- {fin['withholding_amount']:,.2f} TL</b>
          </div>
          <div style="display:flex; justify-content:space-between; color:#15803d;">
            <span>Tahsil Edilecek KDV:</span>
            <b>+ {fin['payable_vat']:,.2f} TL</b>
          </div>
        """

    discount_row_html = ""
    if fin["total_discount"] > 0:
        discount_row_html = f"""
          <div style="display:flex; justify-content:space-between; color:#dc2626;">
            <span>Toplam İskonto:</span>
            <b>- {fin['total_discount']:,.2f} TL</b>
          </div>
        """

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
  .totals-table {{ width: 320px; font-size: 0.9rem; line-height: 1.8; }}
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
      {f'<br><span style="font-size:0.75rem; color:#b91c1c; font-weight:bold;">TEVKİFATLI FATURA ({fin["withholding_rate"]})</span>' if fin["is_withholding"] else ''}
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
        <th style="width:120px;">Net Toplam (TL)</th>
      </tr>
    </thead>
    <tbody>
      {table_rows_html}
    </tbody>
  </table>

  <div class="totals">
    <div class="totals-table">
      <div style="display:flex; justify-content:space-between;"><span>Brüt Tutar:</span> <b>{fin['gross_total']:,.2f} TL</b></div>
      {discount_row_html}
      <div style="display:flex; justify-content:space-between;"><span>KDV Matrahı:</span> <b>{fin['subtotal']:,.2f} TL</b></div>
      <div style="display:flex; justify-content:space-between;"><span>Hesaplanan KDV (%20):</span> <b>{fin['calculated_vat']:,.2f} TL</b></div>
      {tevkifat_rows_html}
      <div style="display:flex; justify-content:space-between; font-size:1.15rem; color:#0284c7; border-top:2px solid #e2e8f0; padding-top:6px; margin-top:4px;">
        <span>Ödenecek Net Tutar:</span> <b>{fin['payable_amount']:,.2f} TL</b>
      </div>
      {f'<div style="font-size:0.75rem; color:#64748b; text-align:right;">KDV Dahil Toplam: {fin["grand_total"]:,.2f} TL</div>' if fin["is_withholding"] else ''}
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
