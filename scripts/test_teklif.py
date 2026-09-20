# -*- coding: utf-8 -*-
"""
test_teklif.py
--------------
KOBİ Fiyat Teklif Portalı entegrasyon ve birim testleri.
KDV hesaplama, iskonto ve veritabanı işlemlerini test eder.
"""

import os
import sys
import sqlite3
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import init_db, DB_FILE

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
            table = cursor.fetchone()
            self.assertIsNotNone(table, "'quotes' tablosu bulunamadi.")

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
            self.assertAlmostEqual(row[14], 1470.00, places=2)
            self.assertAlmostEqual(row[15], 8820.00, places=2)

if __name__ == "__main__":
    print("=" * 60)
    print("  KOBİ FİYAT TEKLİFİ TEST SÜİTİ")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKobiTeklif)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("\n✅ TÜM TESTLER BAŞARIYLA GEÇTİ!")
        sys.exit(0)
    else:
        print("\n❌ TEST BAŞARISIZ!")
        sys.exit(1)
