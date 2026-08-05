/**
 * Spotify：请求前去掉缓存校验头，避免 304 无 body，解锁脚本改不了 protobuf。
 * 配合 spotifyProto（Eevee）使用。
 */
function stripCacheHeaders(headers) {
  if (!headers || typeof headers !== "object") return headers || {};
  const out = { ...headers };
  for (const key of Object.keys(out)) {
    const lower = String(key).toLowerCase();
    if (lower === "if-none-match" || lower === "if-modified-since") {
      delete out[key];
    }
  }
  return out;
}

function run($req) {
  if (!$req) {
    if (typeof $done === "function") $done({});
    return;
  }
  const headers = stripCacheHeaders($req.headers);
  if (typeof $done === "function") {
    $done({ headers });
  }
}

if (typeof $request !== "undefined") {
  run($request);
}

export default async function (ctx) {
  const req = ctx?.request;
  if (!req) return;
  const headers = stripCacheHeaders(req.headers || {});
  if (typeof ctx.resolve === "function") {
    ctx.resolve({ headers });
    return;
  }
  if (typeof $done === "function") $done({ headers });
}
