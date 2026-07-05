/*
 *
 *
脚本功能：语球
软件版本：1.3.4

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https?:\/\/api\.kotobaheworld\.com\.cn\/api\/user url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/yuqiu.js

[mitm]
hostname = api.kotobaheworld.com
*
*
*/
let body = $response.body;
let obj = JSON.parse(body);


    obj.result.isVip = 1;
    obj.result.vipStartTime = "2025-01-01 00:00:00";
    obj.result.vipEndTime = "2099-12-31 23:59:59";


body = JSON.stringify(obj);
$done({body});
