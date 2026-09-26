/**
 * Spotify：customize 请求前去掉 If-None-Match，减少 304（无 body）日志。
 * 解锁仍靠 spotifyProto 的 http-response；本脚本只改请求头。
 */
(function () {
  const req = typeof $request !== "undefined" ? $request : null;
  if (!req) {
    if (typeof $done === "function") $done({});
    return;
  }
  const headers = req.headers || {};
  for (const key of Object.keys(headers)) {
    const lower = String(key).toLowerCase();
    if (lower === "if-none-match" || lower === "if-modified-since") {
      delete headers[key];
    }
  }
  delete headers["If-None-Match"];
  delete headers["If-Modified-Since"];
  console.log("spotifyProto-nocache: stripped cache validators");
  $done({ headers });
})();
