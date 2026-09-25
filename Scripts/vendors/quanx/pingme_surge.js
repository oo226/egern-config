// PingMe 签到（直连+自动抓取）
// 仅处理 /app/checkIn，视频奖励不管
// by oo226 + chatgpt

const K = {
  UA: 'pingme.ua',
  CK_URL: 'pingme.checkin.url',
  CK_MTD: 'pingme.checkin.method',
  CK_BDY: 'pingme.checkin.body',
};

const isReq = typeof $request !== 'undefined' && $request;
const isResp = typeof $response !== 'undefined' && $response;
const isCron = !isReq && !isResp;

const read  = k => $persistentStore.read(k) || '';
const write = (k, v) => $persistentStore.write(String(v || ''), k);
const now   = () => new Date();

function notify(title, sub = '', body = '') {
  $notification.post(title, sub, body);
}

function done(obj) { typeof $done === 'function' ? $done(obj || {}) : null; }

function encodeDateForQS(d = new Date()) {
  // 2025-10-26 11:58:31 -> URL encoded
  const pad = n => String(n).padStart(2, '0');
  const s = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  return encodeURIComponent(s).replace(/%20/g, '%20').replace(/:/g, '%3A');
}

function patchSignDate(url) {
  // 只更新 signDate=yyyy-MM-dd%20HH%3AMM%3Ass
  if (!url) return url;
  if (/([?&])signDate=/.test(url)) {
    return url.replace(/([?&]signDate=)[^&]*/i, `$1${encodeDateForQS(now())}`);
  } else {
    const sep = url.includes('?') ? '&' : '?';
    return `${url}${sep}signDate=${encodeDateForQS(now())}`;
  }
}

function requestOnce(opt, cb) {
  const o = {
    url: opt.url,
    method: opt.method || 'GET',
    headers: opt.headers || {},
    body: opt.body
  };
  if (!$httpClient) { // Surge 必有
    // 兜底
    cb(new Error('no httpClient in this env'));
    return;
  }
  $httpClient[o.method === 'GET' ? 'get' : 'post'](o, (err, resp, data) => {
    cb(err, resp, data);
  });
}

function parseJSON(s) {
  try { return JSON.parse(s); } catch { return null; }
}

function captureRequest() {
  const u = $request.url || '';
  if (!/\/app\/checkIn\?/i.test(u)) return done({}); // 只要签到

  const ua = ($request.headers && ($request.headers['User-Agent'] || $request.headers['user-agent'])) || '';
  write(K.UA, ua);
  write(K.CK_URL, u);
  write(K.CK_MTD, $request.method || 'GET');
  if ($request.body) write(K.CK_BDY, $request.body);

  notify('PingMe 已捕获【签到】请求', '已保存 URL/UA', u.split('?')[0]);
  done({});
}

function captureResponse() {
  const u = $request.url || '';
  if (!/\/app\/checkIn\?/i.test(u)) return done({});

  const body = typeof $response.body === 'string' ? $response.body : '';
  const j = parseJSON(body) || {};
  if (j && (j.retcode === 0 || /bonus|bonusHint|aftercredit/i.test(body))) {
    // 二次确认
    write(K.CK_URL, u);
    notify('PingMe 已捕获【签到】响应', '接口返回有效，已确认保存', '');
  }
  done({ body });
}

function runCheckin() {
  const ua  = read(K.UA);
  const url = read(K.CK_URL);
  const mtd = read(K.CK_MTD) || 'GET';
  const bdy = read(K.CK_BDY) || '';

  if (!url) {
    notify('PingMe 签到', '缺少“签到”URL', '请先在 App 里手动点一次“签到”。');
    return done();
  }

  const patched = patchSignDate(url);
  const headers = {};
  if (ua) headers['User-Agent'] = ua;

  requestOnce({ url: patched, method: mtd, headers, body: mtd !== 'GET' ? bdy : undefined }, (e, r, d) => {
    if (e) {
      notify('PingMe 签到', '网络错误', String(e));
      return done();
    }
    const ok = r && (r.status || r.statusCode);
    const j = parseJSON(d) || {};
    const msg = j && (j.retmsg || j.retMsg || j.msg || '');
    if (ok >= 200 && ok < 400) {
      // 尝试读奖励提示
      const hint = j.result && (j.result.bonusHint || j.result.hint) || '';
      const bonus = j.result && (j.result.bonus || j.result.addbonus || 0);
      const after = j.result && (j.result.aftercredit || j.result.balance);
      notify('PingMe 签到', '成功', hint || `本次 +${bonus} , 余额≈ ${after}`);
    } else {
      notify('PingMe 签到', '失败', msg || `HTTP ${ok}`);
    }
    done();
  });
}

// 入口
if (isReq) captureRequest();
else if (isResp) captureResponse();
else if (isCron) runCheckin();