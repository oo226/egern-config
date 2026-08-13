/**
 * 皮皮虾去广告 + 去水印（合集 Script，Surge / Egern 通用）
 *
 * 参考：
 * - NobyDa/Liquor030 Super.js — 信息流 ad_info 剔除 + origin_video_download 去水印
 * - QingRex/可莉 hub.kelee.one — check_in 精简、api/ad Map Local
 * - 本仓扩展 — 四圆/影院入口、底部「福利」Tab、原生广告（红果/关闭广告）
 */
const url = ($request && $request.url) || "";

const DROP_PROFILE = new Set([
  "放心借",
  "洋钱罐借款",
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

const CIRCLE_TITLE_RE =
  /皮皮虾影院|泥巴头像|怀旧\s*809|怪兽的王|怀旧8090/;

const NATIVE_AD_RE =
  /关闭广告|点击观看|红果|hongguo|免费看剧|playable-component|ad_label|ad_tag|is_promotion|splash_ad|穿山甲|pangle/i;

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

function isNativeAdCell(cell) {
  if (!cell || typeof cell !== "object") return false;
  try {
    const blob = JSON.stringify(cell);
    if (NATIVE_AD_RE.test(blob)) return true;
  } catch (e) {}
  const item = cell.item;
  if (item && typeof item === "object") {
    if (item.ad_info != null || item.is_ad === true) return true;
    const text = [item.content, item.note, item.title, item.share_info && item.share_info.share_title]
      .filter(Boolean)
      .join(" ");
    if (NATIVE_AD_RE.test(text)) return true;
  }
  return false;
}

function isAdCell(cell) {
  if (!cell || typeof cell !== "object") return false;
  if (cell.ad_info != null) return true;
  if (cell.is_ad === true || cell.is_ads === true) return true;
  if (typeof cell.ad_type === "number" && cell.ad_type > 0) return true;
  if (isNativeAdCell(cell)) return true;
  return false;
}

function hasRealPost(cell) {
  const item = cell && cell.item;
  if (!item || typeof item !== "object") return false;
  return !!(item.video || item.content || item.note || item.image_list);
}

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
  ]) {
    if (cell[k]) return true;
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
    if (cell && cell.banner_info) delete cell.banner_info;
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

function dropWelfareTitle(s) {
  const t = String(s || "").trim();
  return t === "福利" || t === "金币" || t === "赚钱" || /福利|金币任务|luckycat/i.test(t);
}

function scrubTabArray(arr) {
  if (!Array.isArray(arr)) return;
  for (let i = arr.length - 1; i >= 0; i--) {
    const e = arr[i];
    if (!e || typeof e !== "object") continue;
    const title = e.title || e.name || e.text || e.tab_name || e.channel_name;
    const en = e.event_name || e.type || e.tab_type || e.key || e.schema;
    if (dropWelfareTitle(title) || dropWelfareTitle(en) || /lucky|welfare|gold|coin/i.test(String(en || ""))) {
      arr.splice(i, 1);
    }
  }
  fixPos(arr);
}

function walkDropWelfare(node, depth) {
  if (!node || depth > 6) return;
  if (Array.isArray(node)) {
    scrubTabArray(node);
    for (const x of node) walkDropWelfare(x, depth + 1);
    return;
  }
  if (typeof node !== "object") return;
  for (const k of Object.keys(node)) {
    const v = node[k];
    if (
      /tab|bottom|nav|channel_model|entrance|bar_list|menu/i.test(k) &&
      Array.isArray(v)
    ) {
      scrubTabArray(v);
    }
    walkDropWelfare(v, depth + 1);
  }
}

function filterProfile(data) {
  if (!data || typeof data !== "object") return;

  if (Array.isArray(data.profile_entrances)) {
    data.profile_entrances = data.profile_entrances.filter(
      (e) => e && !DROP_PROFILE.has(String(e.title || "").trim())
    );
    fixPos(data.profile_entrances);
  }

  for (const key of [
    "pet_interface_message",
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

function run() {
  const raw = $response && $response.body;
  if (!raw) {
    $done({});
    return;
  }
  try {
    let text = String(raw).replace(/id\":([0-9]{15,})/g, 'id":"$1str"');
    const body = JSON.parse(text);
    const data = body && body.data;

    if (url.includes("/bds/user/check_in")) filterProfile(data);
    if (url.includes("/bds/feed/channel_list") || url.includes("/bds/feed/stream")) {
      scrubFeed(body);
    }
    if (
      url.includes("/bds/cell/detail") ||
      url.includes("/bds/comment/") ||
      url.includes("/bds/cell/cell_comment") ||
      url.includes("/bds/ward/") ||
      url.includes("/bds/user/favorite") ||
      url.includes("/bds/user/cell_") ||
      url.includes("/bds/user/publish_list")
    ) {
      scrubFeed(body);
    }
    if (
      url.includes("/bds/settings/") ||
      url.includes("/service/settings/") ||
      url.includes("/bds/feed/channel_list") ||
      url.includes("/bds/user/check_in")
    ) {
      walkDropWelfare(body, 0);
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

run();
