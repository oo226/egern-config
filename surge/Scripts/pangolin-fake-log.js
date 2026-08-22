/**
 * ByteDance / Pangolin / JPush telemetry fake success.
 * Empty reject-200 bodies cause SDK retry storms (phone heat).
 */
const url = $request.url || "";
const host = ($request.hostname || "").toLowerCase();
const now = Math.floor(Date.now() / 1000);
let body;

if (/jpush\.cn|jiguang\.cn/.test(host)) {
  body = JSON.stringify({ code: 0, message: "success" });
} else if (/device_register/i.test(url)) {
  body = JSON.stringify({
    message: "success",
    code: 0,
    device_id: 1,
    install_id: 1,
    ssid: "0",
    server_time: now,
  });
} else if (/api-access\.pangolin.*\/stats/i.test(url) || /\/stats\/batch/i.test(url)) {
  body = JSON.stringify({ code: 0, message: "success", data: {} });
} else {
  body = JSON.stringify({
    code: 0,
    message: "success",
    magic_tag: "ss_app_log",
    server_time: now,
    data: {},
  });
}

$done({
  response: {
    status: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
    },
    body,
  },
});
