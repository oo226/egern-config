//小红书笔记时间显化
let body = $response.body;
if (!body) {
  $done({});
}

let obj;
try {
  obj = JSON.parse(body);
} catch (e) {
  $done({ body });
}

let isEnglish = false;

if (typeof $request !== "undefined" && $request.headers) {
  const headers = $request.headers;
  const acceptLang =
    (headers["Accept-Language"] ||
      headers["accept-language"] ||
      "").toLowerCase();

  const zhIndex = acceptLang.indexOf("zh");
  const enIndex = acceptLang.indexOf("en");

  if (
    enIndex !== -1 &&
    (zhIndex === -1 || enIndex < zhIndex)
  ) {
    isEnglish = true;
  }
}

const i18n = {
  zh: {
    justNow: "刚刚",
    m: "分钟",
    h: "小时",
    d: "天"
  },
  en: {
    justNow: "Now",
    m: "m",
    h: "h",
    d: "d"
  }
};

const lang = isEnglish ? i18n.en : i18n.zh;

function decodeTimestamp(noteId) {
  const hex = noteId.slice(0, 8);
  const ts = parseInt(hex, 16);
  return new Date(ts * 1000);
}

function formatTwitterStyleTime(date) {
  const now = new Date();

  const diffMins = Math.floor(
    (now - date) / 60000
  );

  if (diffMins < 5) {
    return lang.justNow;
  }

  if (diffMins < 60) {
    return `${diffMins}${lang.m}`;
  }

  const diffHours = Math.floor(diffMins / 60);

  if (diffHours < 24) {
    return `${diffHours}${lang.h}`;
  }

  const diffDays = Math.floor(diffHours / 24);

  if (diffDays < 7) {
    return `${diffDays}${lang.d}`;
  }

  const pad = (n) =>
    String(n).padStart(2, "0");

  return `${pad(date.getMonth() + 1)}-${pad(
    date.getDate()
  )}`;
}

function processItem(item) {
  if (!item) return;

  if (item.model_type !== "note") return;

  if (
    !item.id ||
    !/^[a-f0-9]{24}$/i.test(item.id)
  ) {
    return;
  }

  try {
    const d = decodeTimestamp(item.id);

    if (isNaN(d.getTime())) {
      return;
    }

    const timeStr =
      formatTwitterStyleTime(d);

    const timePattern =
      /^(?:刚刚|Now|\d+(?:分钟|小时|天|m|h|d)|\d{2}-\d{2}) · /i;

    if (
      item.user &&
      item.user.nickname &&
      !timePattern.test(item.user.nickname)
    ) {
      item.user.nickname =
        `${timeStr} · ${item.user.nickname}`;
    }
  } catch (e) {}
}

if (Array.isArray(obj?.data)) {
  for (const item of obj.data) {
    processItem(item);
  }
}

$done({
  body: JSON.stringify(obj)
});
