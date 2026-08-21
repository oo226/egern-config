/**
 * ByteDance / Pangolin app_log & toblog fake success.
 * Empty reject-200 bodies cause SDK retry storms (phone heat).
 * Return a body the SDK accepts so it stops.
 */
const url = $request.url || "";
const now = Math.floor(Date.now() / 1000);
let body;

if (/device_register/i.test(url)) {
  body = JSON.stringify({
    message: "success",
    code: 0,
    device_id: 1,
    install_id: 1,
    ssid: "0",
    server_time: now,
  });
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
