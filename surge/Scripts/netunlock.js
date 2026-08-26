/**
 * NetUnlock 面板（Surge）
 * 改自 https://github.com/Nullwhy/Egern/blob/main/Scripts/NetUnlock.js
 * 检测：出口地区 / Netflix / Disney+ / ChatGPT / Claude / Gemini
 *
 * argument 示例：
 *   title=解锁检测&icon=antenna.radiowaves.left.and.right&color=#7446D8
 */

function getArgs() {
  const defaults = {
    title: "解锁检测",
    icon: "antenna.radiowaves.left.and.right",
    color: "#7446D8",
  };
  if (typeof $argument === "undefined" || !$argument) return defaults;
  try {
    const parsed = Object.fromEntries(
      String($argument)
        .split("&")
        .filter(Boolean)
        .map((item) => {
          const i = item.indexOf("=");
          if (i < 0) return [item, ""];
          return [
            item.slice(0, i),
            decodeURIComponent(item.slice(i + 1) || ""),
          ];
        })
    );
    return { ...defaults, ...parsed };
  } catch (_) {
    return defaults;
  }
}

const args = getArgs();
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
const headers = { "User-Agent": UA };

function httpGet(url, opts = {}) {
  return new Promise((resolve) => {
    const start = Date.now();
    $httpClient.get(
      {
        url,
        headers: opts.headers || headers,
        timeout: opts.timeout || 4,
      },
      (error, response, body) => {
        resolve({
          error,
          response,
          body: body || "",
          ms: Date.now() - start,
          status: response && response.status,
        });
      }
    );
  });
}

async function fetchProxy() {
  const r = await httpGet("http://ip-api.com/json/?lang=zh-CN", {
    timeout: 4,
  });
  if (r.error || !r.body) return { code: "ERR", cc: "XX", ms: r.ms };
  try {
    const data = JSON.parse(r.body);
    const cc = data.countryCode || "XX";
    return { code: cc === "XX" ? "ERR" : "OK", cc, ms: r.ms };
  } catch (_) {
    return { code: "ERR", cc: "XX", ms: r.ms };
  }
}

async function checkNetflix() {
  const r = await httpGet("https://www.netflix.com/title/70143836", {
    timeout: 4,
  });
  return { code: r.status === 200 ? "OK" : "ERR", ms: r.ms };
}

async function checkDisney() {
  const r = await httpGet("https://www.disneyplus.com", { timeout: 4 });
  return {
    code: !r.error && r.status && r.status !== 403 ? "OK" : "ERR",
    ms: r.ms,
  };
}

async function checkChatGPT() {
  const r = await httpGet("https://chatgpt.com/cdn-cgi/trace", {
    timeout: 3,
  });
  if (r.error || !r.body) return { code: "ERR", ms: r.ms };
  const match = r.body.match(/loc=([A-Z]{2})/);
  return { code: match ? match[1] : "ERR", ms: r.ms };
}

async function checkClaude() {
  const r = await httpGet("https://claude.ai/login", { timeout: 5 });
  return { code: !r.error && r.status ? "OK" : "ERR", ms: r.ms };
}

async function checkGemini() {
  const r = await httpGet("https://gemini.google.com/app", { timeout: 4 });
  return { code: !r.error && r.status ? "OK" : "ERR", ms: r.ms };
}

function line(name, result, fallbackRegion) {
  const ok = result.code !== "ERR";
  const region =
    result.code === "OK" ? fallbackRegion || "OK" : result.code;
  const mark = ok ? "✓" : "✗";
  const regionText = ok ? region : "--";
  return `${mark} ${name}  ${regionText}  ${result.ms}ms`;
}

(async () => {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");

  const [proxy, netflix, disney, chatgpt, claude, gemini] =
    await Promise.all([
      fetchProxy(),
      checkNetflix(),
      checkDisney(),
      checkChatGPT(),
      checkClaude(),
      checkGemini(),
    ]);

  const cc = proxy.cc || "XX";
  const streaming = [
    line(
      "YouTube",
      { code: proxy.code, ms: proxy.ms },
      cc
    ),
    line("Netflix", netflix, cc),
    line("Disney+", disney, cc),
  ];
  const ai = [
    line("ChatGPT", chatgpt, cc),
    line("Claude", claude, cc),
    line("Gemini", gemini, cc),
  ];

  const all = [proxy, netflix, disney, chatgpt, claude, gemini];
  const okCount = all.filter((x) => x.code !== "ERR").length;

  const content = [
    `流媒体 ${streaming.filter((s) => s.startsWith("✓")).length}/3`,
    ...streaming,
    `AI ${ai.filter((s) => s.startsWith("✓")).length}/3`,
    ...ai,
  ].join("\n");

  $done({
    title: `${args.title} · ${okCount}/6 · ${hh}:${mm}`,
    content,
    icon: args.icon,
    "icon-color": okCount === 6 ? "#2F9E58" : args.color,
  });
})().catch((e) => {
  console.log(`NetUnlock error: ${e}`);
  $done({
    title: args.title,
    content: "检测失败，请重试",
    icon: args.icon,
    "icon-color": "#D64545",
  });
});
