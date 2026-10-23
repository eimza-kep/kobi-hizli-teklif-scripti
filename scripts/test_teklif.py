# -*- coding: utf-8 -*-
"""
test_teklif.py
--------------
KOBİ Fiyat Teklif Portalı entegrasyon ve birim testleri.
KDV hesaplama, iskonto, veritabanı işlemleri, GİB UBL-TR 2.1 XML üretimi
ve kurumsal proforma fatura oluşturucuyu test eder.
"""

import os
import sys
import sqlite3
import unittest
import xml.etree.ElementTree as ET

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import init_db, DB_FILE, get_company_settings, save_company_settings
from scripts.ubl_invoice_generator import (
    generate_ubl_invoice_xml,
    generate_proforma_html,
    calculate_quote_financials,
    TEVKIFAT_RATES,
    DEFAULT_SUPPLIER
)

class TestKobiTeklif(unittest.TestCase):
    def setUp(self):
        init_db()
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM quotes WHERE quote_no LIKE 'TEKLIF-2026-TEST%'")
            conn.commit()

    def test_database_initialization(self):
        self.assertTrue(os.path.exists(DB_FILE), "teklifler.db olusturulamadi.")
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
            self.assertIsNotNone(cursor.fetchone(), "'quotes' tablosu bulunamadi.")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            self.assertIsNotNone(cursor.fetchone(), "'settings' tablosu bulunamadi.")

    def test_quote_calculations_and_insertion(self):
        unit_price = 2450.00
        qty = 3
        subtotal = unit_price * qty # 7350.00
        vat = subtotal * 0.20 # 1470.00
        grand_total = subtotal + vat # 8820.00

        quote_no = "TEKLIF-2026-TEST01"

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quotes (
                    quote_no, company_name, vkn, contact_name, email,
                    phone, city, payment_term, notes, product_name,
                    unit_price, qty, subtotal, vat, grand_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quote_no,
                "Test Sirketi Ltd. Sti.",
                "1234567890",
                "Ali Veli",
                "ali@test.com",
                "05551234567",
                "Ankara",
                "pesin",
                "Hizli teslimat rica ederiz.",
                "E-Imza Paketi",
                unit_price,
                qty,
                subtotal,
                vat,
                grand_total
            ))
            conn.commit()

            cursor.execute("SELECT * FROM quotes WHERE quote_no=?", (quote_no,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], quote_no)
            self.assertEqual(row[2], "Test Sirketi Ltd. Sti.")
            self.assertAlmostEqual(row[13], 7350.00, places=2)
            self.assertAlmostEqual(row[14], 1470.00, places=2)
            self.assertAlmostEqual(row[15], 8820.00, places=2)

    def test_company_settings(self):
        custom_data = {
            "title": "Anadolu Bilişim ve E-İmza Ltd.",
            "vkn": "9876543210",
            "bank_name": "Garanti BBVA",
            "bank_iban": "TR11 0006 2000 1122 3344 5566 77",
            "logo_url": "https://example.com/logo.png"
        }
        save_company_settings(custom_data)
        settings = get_company_settings()
        self.assertEqual(settings["title"], "Anadolu Bilişim ve E-İmza Ltd.")
        self.assertEqual(settings["vkn"], "9876543210")
        self.assertEqual(settings["bank_name"], "Garanti BBVA")
        self.assertEqual(settings["bank_iban"], "TR11 0006 2000 1122 3344 5566 77")
        self.assertEqual(settings["logo_url"], "https://example.com/logo.png")

    def test_generate_ubl_invoice_xml(self):
        sample_quote = {
            "quote_no": "TEKLIF-2026-TEST99",
            "company_name": "Test Ticaret A.Ş.",
            "vkn": "8877665544",
            "contact_name": "Deniz Kara",
            "city": "İzmir",
            "product_name": "3 Yıllık E-İmza USB Token",
            "unit_price": 2500.0,
            "qty": 2,
            "subtotal": 5000.0,
            "vat": 1000.0,
            "grand_total": 6000.0
        }

        xml_output = generate_ubl_invoice_xml(sample_quote)
        self.assertTrue(xml_output.startswith("<?xml"), "Gecerli bir XML basligi olmali.")

        root = ET.fromstring(xml_output)
        self.assertIn("Invoice", root.tag, "Kok etiket Invoice olmalidir.")

        # Namespace kontrolleri
        namespaces = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

        profile_id = root.find('cbc:ProfileID', namespaces)
        self.assertIsNotNone(profile_id)
        self.assertEqual(profile_id.text, "TICARIFATURA")

        doc_id = root.find('cbc:ID', namespaces)
        self.assertEqual(doc_id.text, "TEKLIF-2026-TEST99")

        payable_amount = root.find('cac:LegalMonetaryTotal/cbc:PayableAmount', namespaces)
        self.assertIsNotNone(payable_amount)
        self.assertEqual(payable_amount.text, "6000.00")

    def test_generate_proforma_html(self):
        sample_quote = {
            "quote_no": "TEKLIF-2026-PROFORMA1",
            "company_name": "Erzurum Bilişim San. Tic.",
            "vkn": "1231231234",
            "contact_name": "Hakan Bey",
            "city": "Erzurum",
            "product_name": "Mali Mühür Paketi",
            "unit_price": 4500.0,
            "qty": 1,
            "subtotal": 4500.0,
            "vat": 900.0,
            "grand_total": 5400.0,
            "payment_term": "Peşin / Havale"
        }

        supplier = {
            "title": "Test E-İmza Merkezi",
            "vkn": "9999888877",
            "tax_office": "Aziziye V.D.",
            "address": "Cumhuriyet Cad. No:15",
            "city": "Erzurum",
            "phone": "0442 233 44 55",
            "email": "info@erzurumeimza.com",
            "bank_name": "Vakıfbank",
            "bank_iban": "TR00 0015 0000 0000 1122 3344 55",
            "logo_url": "https://example.com/brand.png"
        }

        html = generate_proforma_html(sample_quote, supplier)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("TEKLIF-2026-PROFORMA1", html)
        self.assertIn("Erzurum Bilişim San. Tic.", html)
        self.assertIn("5,400.00 TL", html)
        self.assertIn("TR00 0015 0000 0000 1122 3344 55", html)
        self.assertIn("Test E-İmza Merkezi", html)
        self.assertIn("brand.png", html)

    def test_calculate_quote_financials_standard(self):
        fin = calculate_quote_financials(unit_price=1000.0, qty=2, discount_rate=0.10, vat_rate=0.20)
        self.assertEqual(fin["gross_total"], 2000.00)
        self.assertEqual(fin["total_discount"], 200.00)
        self.assertEqual(fin["subtotal"], 1800.00)
        self.assertEqual(fin["calculated_vat"], 360.00)
        self.assertFalse(fin["is_withholding"])
        self.assertEqual(fin["payable_vat"], 360.00)
        self.assertEqual(fin["grand_total"], 2160.00)
        self.assertEqual(fin["payable_amount"], 2160.00)

    def test_calculate_quote_financials_withholding_5_10(self):
        # 10.000 TL matrah, %20 KDV = 2.000 TL. 5/10 tevkifat = 1.000 TL kesinti, 1.000 TL ödenecek KDV.
        fin = calculate_quote_financials(unit_price=10000.0, qty=1, withholding_rate="5/10")
        self.assertEqual(fin["subtotal"], 10000.00)
        self.assertEqual(fin["calculated_vat"], 2000.00)
        self.assertTrue(fin["is_withholding"])
        self.assertEqual(fin["withholding_code"], "601")
        self.assertEqual(fin["withholding_amount"], 1000.00)
        self.assertEqual(fin["payable_vat"], 1000.00)
        self.assertEqual(fin["grand_total"], 12000.00)
        self.assertEqual(fin["payable_amount"], 11000.00)

    def test_calculate_quote_financials_withholding_9_10(self):
        # 9/10 tevkifat
        fin = calculate_quote_financials(unit_price=5000.0, qty=2, withholding_rate="9/10")
        # Matrah = 10000 TL, KDV = 2000 TL. 9/10 = 1800 TL tevkifat, 200 TL ödenecek KDV.
        self.assertEqual(fin["subtotal"], 10000.00)
        self.assertEqual(fin["calculated_vat"], 2000.00)
        self.assertEqual(fin["withholding_code"], "602")
        self.assertEqual(fin["withholding_amount"], 1800.00)
        self.assertEqual(fin["payable_vat"], 200.00)
        self.assertEqual(fin["payable_amount"], 10200.00)

    def test_multi_items_calculation(self):
        items = [
            {"name": "E-İmza 3 Yıl", "unit_price": 2450.0, "qty": 2, "discount_rate": 0.0}, # 4900
            {"name": "USB Token", "unit_price": 500.0, "qty": 2, "discount_rate": 0.10}      # 1000 - 100 = 900
        ]
        fin = calculate_quote_financials(items_data=items, withholding_rate="7/10")
        self.assertEqual(fin["line_count"], 2)
        self.assertEqual(fin["gross_total"], 5900.00)
        self.assertEqual(fin["total_discount"], 100.00)
        self.assertEqual(fin["subtotal"], 5800.00)
        self.assertEqual(fin["calculated_vat"], 1160.00) # 5800 * 0.20
        # 7/10 tevkifat = 1160 * 7 / 10 = 812.00
        self.assertEqual(fin["withholding_amount"], 812.00)
        self.assertEqual(fin["payable_vat"], 348.00)
        self.assertEqual(fin["payable_amount"], 6148.00)

    def test_ubl_xml_tevkifat_invoice(self):
        quote_tevkifat = {
            "quote_no": "TEKLIF-2026-TEV01",
            "company_name": "Tevkifatlı Danışmanlık A.Ş.",
            "vkn": "5544332211",
            "city": "İstanbul",
            "unit_price": 20000.0,
            "qty": 1,
            "withholding_rate": "5/10",
            "product_name": "Kurumsal ERP Danışmanlığı"
        }
        xml_output = generate_ubl_invoice_xml(quote_tevkifat)
        root = ET.fromstring(xml_output)

        namespaces = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

        invoice_type = root.find('cbc:InvoiceTypeCode', namespaces)
        self.assertIsNotNone(invoice_type)
        self.assertEqual(invoice_type.text, "TEVKIFAT")

        # WithholdingTaxTotal kontrolü
        withholding_tax = root.find('cac:WithholdingTaxTotal', namespaces)
        self.assertIsNotNone(withholding_tax, "WithholdingTaxTotal etiketi bulunamadi.")
        w_amt = withholding_tax.find('cbc:TaxAmount', namespaces)
        self.assertEqual(w_amt.text, "2000.00") # 20000 * 0.20 * 5/10 = 2000.00

        payable = root.find('cac:LegalMonetaryTotal/cbc:PayableAmount', namespaces)
        self.assertEqual(payable.text, "22000.00") # Matrah(20000) + Tahsil(2000) = 22000.00

    def test_database_migration_columns_and_insertion(self):
        quote_no = "TEKLIF-2026-TEST_MIGRATION"
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM quotes WHERE quote_no = ?", (quote_no,))
            cursor.execute("""
                INSERT INTO quotes (
                    quote_no, company_name, vkn, contact_name,
                    unit_price, qty, subtotal, vat, grand_total,
                    discount_rate, discount_amount, withholding_rate,
                    withholding_code, withholding_amount, payable_amount,
                    items_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quote_no, "Modern A.Ş.", "9988776655", "Ahmet Bey",
                5000.0, 2, 9000.0, 1800.0, 10800.0,
                0.10, 1000.0, "5/10",
                "601", 900.0, 9900.0,
                '[{"name":"Paket","qty":2,"unit_price":5000}]', "Teklif İletildi"
            ))
            conn.commit()

            cursor.execute("SELECT withholding_rate, withholding_code, payable_amount, status FROM quotes WHERE quote_no = ?", (quote_no,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "5/10")
            self.assertEqual(row[1], "601")
            self.assertEqual(row[2], 9900.0)
            self.assertEqual(row[3], "Teklif İletildi")

if __name__ == "__main__":
    print("=" * 60)
    print("  KOBİ FİYAT TEKLİFİ & UBL XML TEST SÜİTİ")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKobiTeklif)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("\n✅ TÜM TESTLER BAŞARIYLA GEÇTİ!")
        sys.exit(0)
    else:
        print("\n❌ TEST BAŞARISIZ!")
        sys.exit(1)
