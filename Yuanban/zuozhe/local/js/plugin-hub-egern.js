/**
 * kelee/qingrex 插件中心：把 Loon/Surge 安装链改成 Egern。
 * 对应原 ibl3nd-plugin-hub.yaml 的 body_rewrites。
 */
(function () {
  if (typeof $response === "undefined" || $response.body == null) return $done({});
  let body = $response.body;
  if (typeof body !== "string") {
    try {
      body = body.toString();
    } catch (e) {
      return $done({});
    }
  }
  body = body
    .replace(/loon:\/\/import\?plugin=/g, "egern:///modules/new?url=")
    .replace(/surge:\/\/\/install-module\?url=/g, "egern:///modules/new?url=");
  $done({ body });
})();
