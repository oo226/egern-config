/**
 * 皮皮虾信息流去广告 / 去水印
 * 基于 Liquor030 / NobyDa Super.js，补强：
 * - 同时覆盖 *.snssdk.com 与 *.pipix.com
 * - 反向遍历再 splice，避免漏删广告
 * - 空 body / 解析失败时直接放行
 * - 额外剥离 cell 级广告字段
 */
function safeGet(obj, path) {
  let cur = obj;
  for (const key of path) {
    if (cur == null || typeof cur !== "object") return null;
    cur = cur[key];
  }
  return cur;
}

function unlockVideo(item) {
  if (!item || typeof item !== "object") return;
  const download = safeGet(item, ["origin_video_download", "url_list"]);
  if (download && item.video && typeof item.video === "object") {
    item.video.video_download = item.video.video_download || {};
    item.video.video_download.url_list = download;
  }
  const comments = item.comments;
  if (Array.isArray(comments)) {
    for (const c of comments) {
      if (c && c.video && c.video.url_list) {
        c.video_download = c.video_download || {};
        c.video_download.url_list = c.video.url_list;
      }
    }
  }
}

function scrubCell(cell) {
  if (!cell || typeof cell !== "object") return false;
  // 广告卡：有 ad_info / 明确广告类型
  if (cell.ad_info != null) return true;
  if (cell.is_ad === true || cell.is_ads === true) return true;
  if (typeof cell.ad_type === "number" && cell.ad_type > 0) return true;
  if (cell.item) unlockVideo(cell.item);
  if (cell.comment_info && cell.comment_info.video && cell.comment_info.video.url_list) {
    cell.comment_info.video_download = cell.comment_info.video_download || {};
    cell.comment_info.video_download.url_list = cell.comment_info.video.url_list;
  }
  return false;
}

function scrubList(list) {
  if (!Array.isArray(list)) return;
  for (let i = list.length - 1; i >= 0; i--) {
    if (scrubCell(list[i])) list.splice(i, 1);
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
  ]) {
    if (Array.isArray(data[key])) out.push(data[key]);
  }
  // channel_list 等：data 本身是数组
  if (Array.isArray(data)) out.push(data);
  return out;
}

function passThrough() {
  $done({});
}

function finish(text) {
  // 显式带 status，减轻 Egern 日志里 status=0 的显示
  const status = Number(($response && ($response.status || $response.statusCode)) || 200);
  $done({ status: status, body: text });
}

let raw = $response && $response.body;
if (!raw) {
  passThrough();
} else {
  try {
    // 大整数 id 先转字符串，避免 JSON.parse 精度丢失
    let text = String(raw).replace(/id\":([0-9]{15,})/g, 'id":"$1str"');
    const body = JSON.parse(text);
    const lists = pickLists(body);
    if (lists.length) {
      for (const list of lists) scrubList(list);
    } else if (body.data && typeof body.data === "object" && !Array.isArray(body.data)) {
      scrubCell(body.data);
    }
    text = JSON.stringify(body);
    text = text.replace(/id\":\"([0-9]{15,})str\"/g, 'id":$1');
    text = text.replace(/\"can_download\":false/g, '"can_download":true');
    text = text.replace(/tplv-ppx-logo\.image/g, "0x0.gif");
    text = text.replace(/tplv-ppx-logo/g, "0x0");
    finish(text);
  } catch (e) {
    passThrough();
  }
}
