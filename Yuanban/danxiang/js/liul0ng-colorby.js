/*
 *
 *
脚本功能：colorby
软件版本：1.6.2

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https://apipro\.colorby\.cn\/api\/user\/me\/membership url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/colorby.js

[mitm]
hostname = apipro.colorby.cn
*
*
*/
let obj = JSON.parse($response.body);

    obj.data.membershipType = "pro";
    

$done({body: JSON.stringify(obj)});
