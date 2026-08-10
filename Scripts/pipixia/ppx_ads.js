/**
 * 皮皮虾信息流去广告（仅 feed）
 * 基于 Liquor030/NobyDa Super.js：
 * - 大整数 id 保护，避免精度丢失
 * - 只删带 ad_info 的条目（不碰评论接口）
 */
function scrubList(list) {
  if (!Array.isArray(list)) return;
  for (let i = list.length - 1; i >= 0; i--) {
    if (list[i] && list[i].ad_info != null) list.splice(i, 1);
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

let raw = $response && $response.body;
if (!raw) {
  $done({});
} else {
  try {
    let text = String(raw).replace(/id\":([0-9]{15,})/g, 'id":"$1str"');
    const body = JSON.parse(text);
    for (const list of pickLists(body)) scrubList(list);
    text = JSON.stringify(body).replace(/id\":\"([0-9]{15,})str\"/g, 'id":$1');
    $done({ body: text });
  } catch (e) {
    $done({});
  }
}
