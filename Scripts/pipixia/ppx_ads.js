/**
 * 皮皮虾：仅 stream / channel_list
 * 去广告 + 推荐上方四圆/影院入口 + 去水印。
 * check_in「我的」页走 Body Rewrite，避免签到接口刷 Script 日志。
 *
 * 注意：合集 Script 必须 max-size=-1（stream 常 300KB+）。
 */
const url = ($request && $request.url) || "";

const KEEP_CHANNEL = new Set(["feed", "image_text", "follow_feed"]);

const CIRCLE_TITLE_RE =
  /皮皮虾影院|泥巴头像|怀旧\s*809|怪兽的王|怀旧8090/;

const CIRCLE_LIST_KEYS = [
  "user_list",
  "users",
  "circle_list",
  "circle_users",
  "author_list",
  "rec_users",
  "story_users",
  "live_users",
  "header_users",
  "slide_list",
  "hashtag_list",
  "hashtags",
  "icon_list",
  "entrance_list",
  "quick_access",
  "top_list",
];

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

function hasRealPost(cell) {
  const item = cell && cell.item;
  if (!item || typeof item !== "object") return false;
  return !!(item.video || item.content || item.note || item.image_list);
}

/** 推荐上方横滑圆形入口 / 影院 / 热门话题条 */
function isCircleRow(cell) {
  if (!cell || typeof cell !== "object") return false;
  if (cell.banner_info) return true;
  if (cell.hashtag_info || cell.hashtag || cell.topic_info) return true;

  const hasCircleList = CIRCLE_LIST_KEYS.some(
    (k) => Array.isArray(cell[k]) && cell[k].length > 0
  );
  if (hasCircleList && !hasRealPost(cell)) return true;

  for (const k of [
    "cinema_info",
    "story_info",
    "circle_info",
    "header_info",
    "slide_info",
    "icon_info",
    "entrance_info",
    "quick_access_info",
  ]) {
    if (cell[k]) return true;
  }

  // 常见 cell_type / display_type（字节系话题条）
  const t = cell.cell_type ?? cell.display_type ?? cell.style_type ?? cell.card_type;
  if (typeof t === "number" && !hasRealPost(cell)) {
    // 非标准帖子类型且无正文：当作入口条丢掉（保守：仅无 item 时）
    if (cell.item == null && (cell.hashtag_list || cell.icons || cell.icon_list)) return true;
  }

  try {
    const blob = JSON.stringify(cell);
    if (CIRCLE_TITLE_RE.test(blob)) return true;
    if (
      /"event_name"\s*:\s*"(cinema|live|story|circle|header|hashtag|topic|icon)"/.test(blob) &&
      !hasRealPost(cell)
    ) {
      return true;
    }
  } catch (e) {}

  return false;
}

function scrubList(list) {
  if (!Array.isArray(list)) return;
  for (let i = list.length - 1; i >= 0; i--) {
    const cell = list[i];
    if (isAdCell(cell) || isCircleRow(cell)) {
      list.splice(i, 1);
      continue;
    }
    unlockCell(cell);
  }
}

function pickLists(root) {
  const out = [];
  if (!root || typeof root !== "object") return out;
  const data = root.data;
  if (!data || typeof data !== "object") return out;
  for (const key of [
    "data",
    "replies",
    "cell_comments",
    "cell_list",
    "item_list",
    "feed_list",
    "list",
    "hashtag_list",
    "hashtags",
  ]) {
    if (Array.isArray(data[key])) out.push(data[key]);
  }
  if (Array.isArray(data)) out.push(data);
  return out;
}

function filterChannels(data) {
  if (!data || typeof data !== "object") return;

  if (Array.isArray(data.channel_model)) {
    data.channel_model = data.channel_model.filter(
      (item) => item && KEEP_CHANNEL.has(item.event_name)
    );
    fixPos(data.channel_model);
  }

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
    "banner_list",
    "banners",
    "slide_list",
    "icon_list",
    "entrance_list",
    "quick_access",
    "hashtag_list",
    "hashtags",
    "top_hashtag",
    "top_hashtags",
    "god_hashtag",
    "hot_hashtag",
    "hot_hashtags",
  ]) {
    if (key in data) delete data[key];
  }
}

function scrubFeed(body) {
  if (body && body.data) filterChannels(body.data);
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

    if (url.includes("/bds/feed/channel_list") || url.includes("/bds/feed/stream")) {
      scrubFeed(body);
    }

    text = JSON.stringify(body);
    text = text.replace(/id\":\"([0-9]{15,})str\"/g, 'id":$1');
    text = text.replace(/\"can_download\":false/g, '"can_download":true');
    text = text.replace(/tplv-ppx-logo\.image/g, "0x0.gif");
    text = text.replace(/tplv-ppx-logo/g, "0x0");
    text = text.replace(/tplv-ppx-watermark[^\"\\]*/g, "0x0");
    finish(text);
  } catch (e) {
    $done({});
  }
}
