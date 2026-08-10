/**
 * 皮皮虾：信息流去广告 + 去水印 + 「我的」页精简
 *
 * - 去广告/去水印：基于 Liquor030/NobyDa Super.js（大整数 id 保护）
 * - 「我的」页：基于 ZenmoFeiShi PPX.js（check_in / channel_list）
 * - 故意不匹配评论/回复接口，避免精度与字段误伤
 */
const url = ($request && $request.url) || "";

function fixPos(arr) {
  if (!Array.isArray(arr)) return;
  for (let i = 0; i < arr.length; i++) {
    if (arr[i] && typeof arr[i] === "object") arr[i].pos = i + 1;
  }
}

function scrubAds(list) {
  if (!Array.isArray(list)) return;
  for (let i = list.length - 1; i >= 0; i--) {
    if (list[i] && list[i].ad_info != null) list.splice(i, 1);
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

function filterMinePage(body) {
  const data = body && body.data;
  if (!data || typeof data !== "object") return;

  if (url.includes("/bds/user/check_in") && Array.isArray(data.profile_entrances)) {
    const drop = new Set(["放心借", "创作中心", "原创特权", "小黑屋", "我的订单"]);
    data.profile_entrances = data.profile_entrances.filter((e) => e && !drop.has(e.title));
    fixPos(data.profile_entrances);
  }

  if (url.includes("/bds/feed/channel_list") && Array.isArray(data.channel_model)) {
    data.channel_model = data.channel_model.filter(
      (item) => item && ["feed", "image_text"].includes(item.event_name)
    );
    fixPos(data.channel_model);
  }
}

function scrubFeed(body) {
  for (const list of pickLists(body)) {
    scrubAds(list);
    for (const cell of list) unlockCell(cell);
  }
  // cell/detail 等单对象
  if (body && body.data && !Array.isArray(body.data) && body.data.item) {
    unlockCell(body.data);
  }
}

let raw = $response && $response.body;
if (!raw) {
  $done({});
} else {
  try {
    let text = String(raw).replace(/id\":([0-9]{15,})/g, 'id":"$1str"');
    const body = JSON.parse(text);
    filterMinePage(body);
    scrubFeed(body);
    text = JSON.stringify(body);
    text = text.replace(/id\":\"([0-9]{15,})str\"/g, 'id":$1');
    text = text.replace(/\"can_download\":false/g, '"can_download":true');
    text = text.replace(/tplv-ppx-logo\.image/g, "0x0.gif");
    text = text.replace(/tplv-ppx-logo/g, "0x0");
    $done({ body: text });
  } catch (e) {
    $done({});
  }
}
