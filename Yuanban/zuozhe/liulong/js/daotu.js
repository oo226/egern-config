/*
 *
 *
脚本功能：思维导图
软件版本：10.0.9

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https://api\.mindline\.cn/userSync\?ios url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/daotu.js

[mitm]
hostname = api.mindline.cn
*
*
*/
let body = $response.body;
let obj = JSON.parse(body);

obj.data.paid = true;
obj.data.vipPeriod = 999999999;
obj.data.purchasedDate = 1735689600;

body = JSON.stringify(obj);
$done({body});
