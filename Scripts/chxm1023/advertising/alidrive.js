/****************************************

[rewrite_local]

# 阿里云盘-优化首页display
^https?:\/\/api\.(aliyundrive|alipan)\.com\/apps\/v\d\/users\/apps\/widgets$ url script-response-body https://raw.githubusercontent.com/chxm1023/Advertising/main/alidrive.js

[mitm]

hostname = api.aliyundrive.com, api.alipan.com

****************************************/

const url = $request.url;
if (!/\/apps\/v\d+\/users\/apps\/widgets/.test(url)) {
  $done({});
} else {
  let chxm1023 = JSON.parse($response.body);
  if (chxm1023.result) {
    chxm1023.result = Object.values(chxm1023.result).filter(
      (item) => item["appCode"] == "file" || item["appCode"] == "video"
    );
  }
  $done({ body: JSON.stringify(chxm1023) });
}
