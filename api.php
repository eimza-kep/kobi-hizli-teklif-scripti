<?php
/**
 * api.php
 * -------
 * KOBİ B2B Fiyat Teklifi ve Talep PHP Uç Noktası (cPanel / Apache / Nginx uyumlu).
 * Verileri 'teklifler.json' dosyasında saklar.
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$dataFile = __DIR__ . '/teklifler.json';

if (!file_exists($dataFile)) {
    file_put_contents($dataFile, json_encode([], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $content = file_get_contents($dataFile);
    echo $content ?: '[]';
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    if (!$input) {
        http_response_code(400);
        echo json_encode(['error' => 'Geçersiz veri.']);
        exit;
    }

    $currentData = json_decode(file_get_contents($dataFile), true) ?: [];
    $quoteNo = 'TEKLIF-2026-' . rand(1000, 9999);

    $entry = [
        'id' => count($currentData) + 1,
        'quote_no' => $quoteNo,
        'company_name' => htmlspecialchars($input['company_name'] ?? ''),
        'vkn' => htmlspecialchars($input['vkn'] ?? ''),
        'contact_name' => htmlspecialchars($input['contact_name'] ?? ''),
        'email' => htmlspecialchars($input['email'] ?? ''),
        'phone' => htmlspecialchars($input['phone'] ?? ''),
        'city' => htmlspecialchars($input['city'] ?? ''),
        'payment_term' => htmlspecialchars($input['payment_term'] ?? ''),
        'notes' => htmlspecialchars($input['notes'] ?? ''),
        'product_name' => htmlspecialchars($input['product_name'] ?? ''),
        'unit_price' => floatval($input['unit_price'] ?? 0),
        'qty' => intval($input['qty'] ?? 1),
        'subtotal' => floatval($input['subtotal'] ?? 0),
        'vat' => floatval($input['vat'] ?? 0),
        'grand_total' => floatval($input['grand_total'] ?? 0),
        'status' => 'Yeni Talep',
        'created_at' => date('c')
    ];

    $currentData[] = $entry;
    file_put_contents($dataFile, json_encode($currentData, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

    echo json_encode([
        'success' => true,
        'quote_no' => $quoteNo,
        'message' => 'Fiyat teklifi talebiniz kaydedildi.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}
?>
