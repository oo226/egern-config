/**
 * Spotify：请求前去掉缓存校验头，避免 304 无 body（对齐 app2smile/spotify-qx-header.js）
 */
(function () {
  const req = typeof $request !== "undefined" ? $request : null;
  if (!req) {
    if (typeof $done === "function") $done({});
    return;
  }
  const headers = req.headers || {};
  const drop = new Set(["if-none-match", "if-modified-since"]);
  for (const key of Object.keys(headers)) {
    if (drop.has(String(key).toLowerCase())) {
      delete headers[key];
    }
  }
  // 常见大小写再删一次
  delete headers["If-None-Match"];
  delete headers["If-Modified-Since"];
  delete headers["if-none-match"];
  delete headers["if-modified-since"];
  console.log("spotifyProto-nocache: stripped If-None-Match / If-Modified-Since");
  $done({ headers });
})();
