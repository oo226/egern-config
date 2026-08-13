/**
 * 起点 App 去广告（基于 app2smile/rules qidian.js）
 *
 * 上游把「当前有活动图标」(ActivityIcon.Type !== 0) 当成错误弹通知，
 * 起点一改活动配置就会刷「起点 App 脚本错误」。这里改为静默清掉广告字段。
 */
let url = $request.url;
let method = $request.method;
if (!$response.body) {
  $done({});
}

let body = JSON.parse($response.body);
const getMethod = "GET";
const postMethod = "POST";

if (!body.Data) {
  $done({ body: $response.body });
} else if (url.includes("v4/client/getsplashscreen") && method === getMethod) {
  if (body.Data.List) body.Data.List = null;
  if (body.Data.EnableGDT === 1) body.Data.EnableGDT = 0;
} else if (url.includes("v2/deeplink/geturl") && method === getMethod) {
  if (body.Data.ActionUrl) body.Data.ActionUrl = "";
} else if (url.includes("v1/adv/getadvlistbatch?positions=iOS_tab") && method === getMethod) {
  if (body.Data.iOS_tab) body.Data.iOS_tab = [];
} else if (url.includes("v2/dailyrecommend/getdailyrecommend") && method === getMethod) {
  if (body.Data.Items?.length) body.Data.Items = [];
} else if (url.includes("v1/bookshelf/getHoverAdv") && method === getMethod) {
  if (body.Data.ItemList?.length) body.Data.ItemList = [];
} else if (url.includes("v1/client/getconf") && method === postMethod) {
  if (body.Data.ActivityPopup) body.Data.ActivityPopup = null;
  if (body.Data.WolfEye === 1) body.Data.WolfEye = 0;
  if (body.Data.CloudSetting?.TeenShowFreq === "1") {
    body.Data.CloudSetting.TeenShowFreq = "0";
  }
  // 书架右下角活动图标：有 Type/Icon 就清掉，不再当错误通知
  if (body.Data.ActivityIcon && typeof body.Data.ActivityIcon === "object") {
    body.Data.ActivityIcon.Type = 0;
    body.Data.ActivityIcon.StartTime = 0;
    body.Data.ActivityIcon.EndTime = 0;
    delete body.Data.ActivityIcon.Actionurl;
    delete body.Data.ActivityIcon.Icon;
  }
  if (body.Data.EnableSearchUser !== "1") {
    body.Data.EnableSearchUser = "1";
  }
}

$done({ body: JSON.stringify(body) });
