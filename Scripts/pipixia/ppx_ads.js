/**
 * 皮皮虾：信息流去广告 + 去水印 +「我的」页 / 频道栏精简
 *
 * - 去广告/去水印：Liquor030/NobyDa Super.js（大整数 id 保护）
 * - 「我的」/频道：ZenmoFeiShi PPX.js（check_in / channel_list / stream banner）
 * - 不匹配评论/回复接口，避免精度与字段误伤
 * - 显式带回 status，减轻 Egern 日志里 status=0
 */
const url = ($request && $request.url) || "";

const DROP_PROFILE = new Set([
  "放心借",
  "创作中心",
  "原创特权",
  "小黑屋",
  "我的订单",
  "银行卡管理",
  "神评鉴定",
  "宠物乐园",
  "进入宠物乐园",
]);

const KEEP_CHANNEL = new Set(["feed", "image_text", "follow_feed"]);

function fixPos(arr) {
  if (!Array.isArray(arr)) return;
  for (let i = 0; i < arr.length; i++) {
    if (arr[i] && typeof arr[i] === "object") arr[i].pos = i + 1;
  }
}

function unlockVideo(item) {
  if (!item || typeof item !== "object") return;
  try {
    if (item.video && item.origin_video_download && item.origin_video_download.url_list) {
      if (!item.video.video_download) item.video.video_download = {};
      item.video.video_download.url_list = item.origin_video_download.url_list;
    }
  } catch (e) {}
  if (Array.isArray(item.comments)) {
    for (const c of item.comments) {
      try {
        if (c && c.video && c.video.url_list) {
          if (!c.video_download) c.video_download = {};
          c.video_download.url_list = c.video.url_list;
        }
      } catch (e) {}
    }
  }
}

function unlockCell(cell) {
  if (!cell || typeof cell !== "object") return;
  if (cell.item) unlockVideo(cell.item);
  if (cell.comment_info && cell.comment_info.video && cell.comment_info.video.url_list) {
    try {
      if (!cell.comment_info.video_download) cell.comment_info.video_download = {};
      cell.comment_info.video_download.url_list = cell.comment_info.video.url_list;
    } catch (e) {}
  }
}

function isAdCell(cell) {
  if (!cell || typeof cell !== "object") return false;
  if (cell.ad_info != null) return true;
  if (cell.is_ad === true || cell.is_ads === true) return true;
  if (typeof cell.ad_type === "number" && cell.ad_type > 0) return true;
  return false;
}

function scrubList(list) {
  if (!Array.isArray(list)) return;
  for (let i = list.length - 1; i >= 0; i--) {
    const cell = list[i];
    if (isAdCell(cell)) {
      list.splice(i, 1);
      continue;
    }
    if (cell && cell.banner_info) delete cell.banner_info;
    unlockCell(cell);
  }
}

function pickLists(root) {
  const out = [];
  if (!root || typeof root !== "object") return out;
  const data = root.data;
  if (!data || typeof data !== "object") return out;
  for (const key of ["data", "replies", "cell_comments", "cell_list", "item_list", "feed_list", "list"]) {
    if (Array.isArray(data[key])) out.push(data[key]);
  }
  if (Array.isArray(data)) out.push(data);
  return out;
}

function filterProfile(data) {
  if (!data || typeof data !== "object") return;

  if (Array.isArray(data.profile_entrances)) {
    data.profile_entrances = data.profile_entrances.filter(
      (e) => e && !DROP_PROFILE.has(String(e.title || "").trim())
    );
    fixPos(data.profile_entrances);
  }

  // 常见促销 / 入口字段：有则清掉
  for (const key of [
    "pet_entrance",
    "pet_paradise",
    "activity_banner",
    "profile_banner",
    "banner",
    "banners",
    "loan_entrance",
    "credit_entrance",
  ]) {
    if (key in data) delete data[key];
  }
}

function filterChannels(data) {
  if (!data || typeof data !== "object") return;

  if (Array.isArray(data.channel_model)) {
    data.channel_model = data.channel_model.filter(
      (item) => item && KEEP_CHANNEL.has(item.event_name)
    );
    fixPos(data.channel_model);
  }

  // 推荐上方圆形入口 / 影院 / 直播条等（字段名随版本变化，有则清）
  for (const key of [
    "story_list",
    "stories",
    "circle_list",
    "live_list",
    "live_cells",
    "top_list",
    "top_channels",
    "square_list",
    "square_items",
    "cinema_list",
    "header_list",
    "recommend_users",
    "user_story",
  ]) {
    if (key in data) delete data[key];
  }
}

function scrubFeed(body) {
  for (const list of pickLists(body)) scrubList(list);
  if (body && body.data && !Array.isArray(body.data) && body.data.item) {
    unlockCell(body.data);
  }
}

function finish(text) {
  const status = Number(($response && ($response.status || $response.statusCode)) || 200);
  $done({ status: status, body: text });
}

let raw = $response && $response.body;
if (!raw) {
  $done({});
} else {
  try {
    let text = String(raw).replace(/id\":([0-9]{15,})/g, 'id":"$1str"');
    const body = JSON.parse(text);
    const data = body && body.data;

    if (url.includes("/bds/user/check_in")) filterProfile(data);
    if (url.includes("/bds/feed/channel_list")) filterChannels(data);
    if (
      url.includes("/bds/feed/stream") ||
      url.includes("/bds/feed/channel_list") ||
      url.includes("/bds/cell/detail")
    ) {
      scrubFeed(body);
    }

    text = JSON.stringify(body);
    text = text.replace(/id\":\"([0-9]{15,})str\"/g, 'id":$1');
    text = text.replace(/\"can_download\":false/g, '"can_download":true');
    text = text.replace(/tplv-ppx-logo\.image/g, "0x0.gif");
    text = text.replace(/tplv-ppx-logo/g, "0x0");
    // 其它常见水印切片
    text = text.replace(/tplv-ppx-watermark[^\"\\]*/g, "0x0");
    finish(text);
  } catch (e) {
    $done({});
  }
}
