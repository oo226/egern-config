/*
 *
 *
脚本功能：信易知
软件版本：2.2.47

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https://easycompanyinformation\.keeprisk\.com/user/queryUserInfo url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/xin.js

[mitm]
hostname = easycompanyinformation.keeprisk.com
*
*
*/
let body = $response.body;
try {
  let obj = JSON.parse(body);
  let d = obj.data;


  d.vipuser = 1;
  d.vipStatus = "1";
  d.vipLevel = "9"; 
  d.vipExpireTime = "2099-12-31 23:59:59";
  d.vipExpireTimeStr = "2099-12-31";

  $done({ body: JSON.stringify(obj) });
} catch (e) {
  $done({ body });
}
