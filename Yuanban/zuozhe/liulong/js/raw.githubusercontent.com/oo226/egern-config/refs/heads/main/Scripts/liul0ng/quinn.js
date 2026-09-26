/*
 *
 *
脚本功能：quinn
软件版本：4.0.1

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https://quinn-prod\.herokuapp\.com/v2/api/user/me url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/quinn.js

[mitm]
hostname = quinn-prod.herokuapp.com
*
*
*/
let body = $response.body;
try {
  let obj = JSON.parse(body);

  // 修改为已订阅 VIP
  obj.isSubscribed = true;

  $done({ body: JSON.stringify(obj) });
} catch (e) {
  $done({});
}
