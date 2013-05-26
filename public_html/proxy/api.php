<?php
$url = 'http://commons.wikimedia.org/w/api.php';
$method   = (!empty($_POST)) ? 'post' : 'get';

$ch = curl_init();
curl_setopt($ch, CURLOPT_USERAGENT, 'Oslobilder2commons helper tool @ toolserver (alpha)');

if ($method == 'get') {
  if ($_SERVER['QUERY_STRING']) $url .= '?' . $_SERVER['QUERY_STRING'];
  
  curl_setopt($ch, CURLOPT_HEADER, 0);
  curl_setopt($ch, CURLOPT_URL, $url);
} else {
  curl_setopt($ch, CURLOPT_POST, true);
  curl_setopt($ch, CURLOPT_POSTFIELDS, $_POST);
  curl_setopt($ch, CURLOPT_URL, $url);
}

$data = curl_exec($ch);
curl_close($ch);

?>
