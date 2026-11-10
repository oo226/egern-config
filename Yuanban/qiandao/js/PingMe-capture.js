/**
 * PingMe 抓参（精简版，专供 Egern/Surge http-request|response）
 * 存储键: pingme_capture_v3（与 PingMe-signin.js 一致）
 * 勿用 export / $done({})：Egern 上 {} 可能冲掉请求头导致 App 异常。
 *
 * 可选 $argument: CAPTURE=true|false（缺省按 true 抓）
 */

const CK = 'pingme_capture_v3';

function captureEnabled() {
  const arg = typeof $argument !== 'undefined' ? String($argument) : '';
  if (!arg) return true;
  if (/CAPTURE\s*=\s*false/i.test(arg)) return false;
  if (/CAPTURE\s*=\s*true/i.test(arg)) return true;
  return true;
}

function parseRawQuery(url) {
  const query = (String(url).split('?')[1] || '').split('#')[0];
  const rawMap = {};
  query.split('&').forEach(pair => {
    if (!pair) return;
    const idx = pair.indexOf('=');
    if (idx < 0) return;
    rawMap[pair.slice(0, idx)] = pair.slice(idx + 1);
  });
  return rawMap;
}

function headersToMap(headers) {
  const out = {};
  if (!headers) return out;
  if (typeof headers === 'object' && !headers.get && !headers.forEach) {
    Object.keys(headers).forEach(k => {
      const v = headers[k];
      out[k] = Array.isArray(v) ? v.map(String).join(', ') : (v == null ? '' : String(v));
    });
    return out;
  }
  if (typeof headers.forEach === 'function') {
    headers.forEach((v, k) => { out[k] = v; });
  }
  return out;
}

function saveCapture(url, reqHeaders) {
  const capture = {
    url: String(url),
    paramsRaw: parseRawQuery(url),
    headers: headersToMap(reqHeaders),
    capturedAt: Date.now()
  };
  const json = JSON.stringify(capture);
  if (typeof $persistentStore !== 'undefined') {
    $persistentStore.write(json, CK);
    $persistentStore.write(json, `#${CK}`);
  }
  console.log(`【PingMe抓参】已写入 ${CK}\n${url}`);
  if (typeof $notification !== 'undefined' && $notification.post) {
    $notification.post('PingMe 获取成功✅', '抓完把「PingMe 抓参」改成 false，再跑签到', '');
  } else if (typeof $notify === 'function') {
    $notify('PingMe 获取成功✅', '抓完把「PingMe 抓参」改成 false，再跑签到', '');
  }
}

function passThrough() {
  if (typeof $done === 'function') $done();
}

const url = (typeof $request !== 'undefined' && $request && $request.url)
  ? String($request.url)
  : '';

if (!url || !url.includes('queryBalanceAndBonus')) {
  passThrough();
} else if (!captureEnabled()) {
  console.log('【PingMe抓参】CAPTURE=false，跳过写入');
  passThrough();
} else {
  try {
    saveCapture(url, ($request && $request.headers) || {});
  } catch (e) {
    console.log('【PingMe抓参】异常: ' + (e && e.message ? e.message : e));
    if (typeof $notification !== 'undefined' && $notification.post) {
      $notification.post('PingMe 抓参失败❗️', String(e && e.message ? e.message : e), '');
    }
  }
  passThrough();
}
