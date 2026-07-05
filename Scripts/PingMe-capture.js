/**
 * PingMe 抓参 — 对齐 oo226/quanx cook.js 写法
 * Egern: http_request + export default(ctx)
 * 存储键: #pingme_capture_v3（与签到脚本一致）
 */

const CK = 'pingme_capture_v3';

function normalizeHeaderNameMap(headers) {
  const out = {};
  Object.keys(headers || {}).forEach(k => { out[k] = headers[k]; });
  return out;
}

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

function headersToMap(headers) {
  const out = {};
  if (!headers) return out;
  if (typeof headers === 'object' && !headers.get && !headers.forEach) {
    Object.keys(headers).forEach(k => { out[k] = headers[k]; });
    return out;
  }
  if (typeof headers.forEach === 'function') {
    headers.forEach((v, k) => { out[k] = v; });
    return out;
  }
  if (typeof headers.entries === 'function') {
    for (const [k, v] of headers.entries()) out[k] = v;
    return out;
  }
  if (typeof headers.get === 'function') {
    if (typeof headers.forEach === 'function') {
      headers.forEach((v, k) => { out[k] = v; });
    }
  }
  return out;
}

function saveCapture(url, reqHeaders) {
  const capture = {
    url,
    paramsRaw: parseRawQuery(url),
    headers: normalizeHeaderNameMap(headersToMap(reqHeaders))
  };
  const json = JSON.stringify(capture);

  if (typeof $persistentStore !== 'undefined') {
    $persistentStore.write(json, `#${CK}`);
    return;
  }
  if (typeof globalThis.__pingmeStorage !== 'undefined' && globalThis.__pingmeStorage) {
    const s = globalThis.__pingmeStorage;
    if (typeof s.setJSON === 'function') s.setJSON(CK, capture);
    else if (typeof s.set === 'function') s.set(CK, json);
    return;
  }
  console.log(`【PingMe抓参】无可用存储，capture=${json.slice(0, 120)}...`);
}

function notifyOk(url) {
  const msg = '现在可以关闭「PingMe参数」，再开「PingMe签到」';
  console.log(`【PingMe抓参】成功\n${url}`);
  if (typeof $notification !== 'undefined' && $notification.post) {
    $notification.post('PingMe 获取成功✅', msg, '');
  } else if (typeof $notify === 'function') {
    $notify('PingMe 获取成功✅', msg, '');
  }
}

function captureFromRequest(req) {
  if (!req?.url || !req.url.includes('/app/queryBalanceAndBonus')) return;
  saveCapture(req.url, req.headers || {});
  notifyOk(req.url);
}

export default async function (ctx) {
  globalThis.__pingmeStorage = ctx?.storage || null;
  if (ctx?.request?.url) {
    captureFromRequest({ url: String(ctx.request.url), headers: ctx.request.headers });
  }
}

if (typeof $request !== 'undefined' && $request?.url?.includes('queryBalanceAndBonus')) {
  captureFromRequest($request);
  if (typeof $done === 'function') $done({});
}
