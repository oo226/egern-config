/**
 * PingMe 抓参（Surge）
 * 参考：fmz200/wool_scripts Scripts/cookie/get_cookie.js（PingMe 段）
 * 存储键：#pingme_capture_v3（与 PingMeSignin 一致）
 */
const CK = '#pingme_capture_v3';

function parseRawQuery(url) {
  const query = (url.split('?')[1] || '').split('#')[0];
  const rawMap = {};
  query.split('&').forEach(pair => {
    if (!pair) return;
    const idx = pair.indexOf('=');
    if (idx < 0) return;
    rawMap[pair.slice(0, idx)] = pair.slice(idx + 1);
  });
  return rawMap;
}

function normalizeHeaderNameMap(headers) {
  const out = {};
  Object.keys(headers || {}).forEach(k => { out[k] = headers[k]; });
  return out;
}

if (typeof $request !== 'undefined' && $request.url && $request.url.includes('/app/queryBalanceAndBonus')) {
  const capture = {
    url: $request.url,
    paramsRaw: parseRawQuery($request.url),
    headers: normalizeHeaderNameMap($request.headers || {}),
    capturedAt: Date.now()
  };
  const json = JSON.stringify(capture);
  if (typeof $persistentStore !== 'undefined') {
    $persistentStore.write(json, CK);
    $persistentStore.write(json, 'pingme_capture_v3');
  }
  if (typeof $notification !== 'undefined') {
    $notification.post('PingMe 获取成功✅', '现在可以把模块里抓参关掉（改成 #）', '');
  }
  console.log('PingMe 抓参成功: ' + $request.url);
}
$done({});
