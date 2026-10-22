# -*- coding: utf-8 -*-
"""
server.py
---------
KOBİ Hızlı Fiyat Teklifi ve RFQ Portalı - Sıfır Bağımlılıklı Python Sunucusu.
SQLite veritabanı, GİB UBL-TR 2.1 e-Fatura XML üretimi ve Proforma Fatura desteği.
"""

import os
import sys
import json
import sqlite3
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Proje kök dizini ve script importları
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.ubl_invoice_generator import (
    generate_ubl_invoice_xml,
    generate_proforma_html,
    DEFAULT_SUPPLIER
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = int(os.environ.get("PORT", 8081))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(ROOT_DIR, "teklifler.db"))

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_no TEXT UNIQUE,
                company_name TEXT,
                vkn TEXT,
                contact_name TEXT,
                email TEXT,
                phone TEXT,
                city TEXT,
                payment_term TEXT,
                notes TEXT,
                product_name TEXT,
                unit_price REAL,
                qty INTEGER,
                subtotal REAL,
                vat REAL,
                grand_total REAL,
                status TEXT DEFAULT 'Yeni Talep',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()

def get_company_settings():
    settings = dict(DEFAULT_SUPPLIER)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        for key, value in cursor.fetchall():
            if value:
                settings[key] = value
    return settings

def save_company_settings(data):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        for key, val in data.items():
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(key), str(val))
            )
        conn.commit()

class QuoteHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "kobi-teklif"}).encode("utf-8"))
            return

        if parsed.path == "/api/ayarlar":
            settings = get_company_settings()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(settings, ensure_ascii=False).encode("utf-8"))
            return

        if parsed.path == "/api/teklif-listesi":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM quotes ORDER BY created_at DESC")
                rows = [dict(r) for r in cursor.fetchall()]
                self.wfile.write(json.dumps(rows, ensure_ascii=False).encode("utf-8"))
            return

        if parsed.path == "/api/export-ubl-xml":
            quote_no = qs.get("quote_no", [""])[0]
            if not quote_no:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"quote_no parametresi zorunludur.")
                return

            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM quotes WHERE quote_no = ?", (quote_no,))
                row = cursor.fetchone()

            if not row:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(f"'{quote_no}' numarali teklif bulunamadi.".encode("utf-8"))
                return

            quote_data = dict(row)
            supplier = get_company_settings()
            xml_str = generate_ubl_invoice_xml(quote_data, supplier)

            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{quote_no}_ubl.xml"')
            self.end_headers()
            self.wfile.write(xml_str.encode("utf-8"))
            return

        if parsed.path == "/api/proforma-html":
            quote_no = qs.get("quote_no", [""])[0]
            if not quote_no:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"quote_no parametresi zorunludur.")
                return

            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM quotes WHERE quote_no = ?", (quote_no,))
                row = cursor.fetchone()

            if not row:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(f"'{quote_no}' numarali teklif bulunamadi.".encode("utf-8"))
                return

            quote_data = dict(row)
            supplier = get_company_settings()
            html_content = generate_proforma_html(quote_data, supplier)

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/ayarlar":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            save_company_settings(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Ayarlar kaydedildi."}).encode("utf-8"))
            return

        if parsed.path == "/api/export-ubl-xml":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                quote_data = json.loads(body)
            except Exception:
                quote_data = {}

            supplier = get_company_settings()
            xml_str = generate_ubl_invoice_xml(quote_data, supplier)

            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="teklif_taslak_ubl.xml"')
            self.end_headers()
            self.wfile.write(xml_str.encode("utf-8"))
            return

        if parsed.path == "/api/teklif-olustur":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            quote_no = f"TEKLIF-2026-{random.randint(1000, 9999)}"

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
                    data.get("company_name", ""),
                    data.get("vkn", ""),
                    data.get("contact_name", ""),
                    data.get("email", ""),
                    data.get("phone", ""),
                    data.get("city", ""),
                    data.get("payment_term", ""),
                    data.get("notes", ""),
                    data.get("product_name", ""),
                    float(data.get("unit_price", 0)),
                    int(data.get("qty", 1)),
                    float(data.get("subtotal", 0)),
                    float(data.get("vat", 0)),
                    float(data.get("grand_total", 0))
                ))
                conn.commit()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            resp = {
                "success": True,
                "quote_no": quote_no,
                "message": "Fiyat teklifi talebiniz başarıyla oluşturuldu."
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server(port=PORT):
    init_db()
    server_address = ("", port)
    httpd = HTTPServer(server_address, QuoteHandler)
    print(f"💼 KOBİ Teklif Portalı aktif: http://localhost:{port}")
    print(f"📋 Admin Paneli: http://localhost:{port}/admin.html")
    httpd.serve_forever()

if __name__ == "__main__":
    init_db()
    run_server()
