/*
 *
 *
脚本功能：英辞
软件版本：5.2.0

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https://api\.mojidict\.com/app/endict/parse/functions/getNPrivileges url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/yingci.js

[mitm]
hostname = api.mojidict.com
*
*
*/
let body = $response.body;
let obj = JSON.parse(body);

let item = obj.result.result.find(v => v);
item.privilegeStatus = "activated";
item.privilege.totalInServiceDays = 99999;

body = JSON.stringify(obj);
$done({body});
