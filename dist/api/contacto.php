<?php
/**
 * C&K Ingenieros — envío del formulario de contacto a GoHighLevel.
 *
 * El formulario del sitio (Inicio y Contacto) envía aquí sus datos. Este script
 * valida la solicitud, aplica protección anti-spam y la reenvía como JSON al
 * webhook entrante de GoHighLevel. La URL del webhook queda en el servidor
 * (api/config.php) y nunca se expone en el navegador.
 *
 * Instalación: copiar api/config.example.php a api/config.php y pegar la URL
 * del webhook (GoHighLevel → Automation → Workflow → trigger "Inbound Webhook").
 */

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

function reply(int $code, bool $ok, string $error = ''): void {
    http_response_code($code);
    echo json_encode($ok ? ['ok' => true] : ['ok' => false, 'error' => $error]);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    reply(405, false, 'method_not_allowed');
}

$configFile = __DIR__ . '/config.php';
if (!is_file($configFile)) {
    error_log('C&K contacto: falta api/config.php');
    reply(500, false, 'not_configured');
}
$config = require $configFile;
$webhook = trim($config['ghl_webhook_url'] ?? '');
if (!preg_match('#^https://#', $webhook)) {
    error_log('C&K contacto: ghl_webhook_url no válida');
    reply(500, false, 'not_configured');
}

// Anti-spam: campo trampa y tiempo mínimo en la página. Respondemos "ok" para no
// dar pistas a los bots, pero no reenviamos nada.
$honeypot = trim($_POST['website'] ?? '');
$elapsedMs = (int)($_POST['ms'] ?? 0);
if ($honeypot !== '' || $elapsedMs < 2500) {
    reply(200, true);
}

// Límite simple por IP: 5 envíos cada 10 minutos.
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$bucket = sys_get_temp_dir() . '/ck_contacto_' . hash('sha256', $ip);
$now = time();
$hits = [];
if (is_file($bucket)) {
    $hits = array_filter(
        array_map('intval', explode(',', (string)file_get_contents($bucket))),
        fn($t) => $t > $now - 600
    );
}
if (count($hits) >= 5) {
    reply(429, false, 'too_many_requests');
}
$hits[] = $now;
@file_put_contents($bucket, implode(',', $hits), LOCK_EX);

function field(string $key, int $max): string {
    $v = trim((string)($_POST[$key] ?? ''));
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v) ?? '';
    return mb_substr($v, 0, $max);
}

$nombre       = field('nombre', 120);
$empresa      = field('empresa', 160);
$email        = field('email', 160);
$especialidad = field('especialidad', 120);
$mensaje      = field('mensaje', 5000);
$pagina       = field('pagina', 120);

$allowed = [
    'Asesoría técnica y representación', 'Ingeniería de diseño', 'Construcción eléctrica',
    'Mantención especializada', 'Instalación de equipos de alta complejidad',
    'Equipos y diagnóstico técnico', 'Asesoría tarifaria y cliente libre', 'Otro',
];

if ($nombre === '' || $empresa === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)
    || !in_array($especialidad, $allowed, true) || mb_strlen($mensaje) < 10) {
    reply(422, false, 'invalid');
}

// Separar nombre y apellido para los campos estándar de GoHighLevel.
$parts = preg_split('/\s+/', $nombre, 2);

$payload = [
    'first_name'   => $parts[0] ?? $nombre,
    'last_name'    => $parts[1] ?? '',
    'full_name'    => $nombre,
    'email'        => $email,
    'company_name' => $empresa,
    'especialidad' => $especialidad,
    'mensaje'      => $mensaje,
    'source'       => 'Sitio web cykingenieros.cl',
    'pagina'       => $pagina,
    'fecha'        => gmdate('c'),
];

$ch = curl_init($webhook);
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE),
    CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Accept: application/json'],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 5,
    CURLOPT_TIMEOUT        => 12,
]);
$response = curl_exec($ch);
$status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError = curl_error($ch);
curl_close($ch);

if ($response === false || $status < 200 || $status >= 300) {
    error_log("C&K contacto: webhook respondió $status $curlError");
    reply(502, false, 'upstream_error');
}

reply(200, true);
