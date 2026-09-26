/*
 *
 *
脚本功能：取证
软件版本：1.2.8

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^http:\/\/ys\.qquanyun\.top\/api\/user\/my url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/quzheng.js

[mitm]
hostname = ys.qquanyun.top
*
*
*/
let obj = JSON.parse($response.body);
obj.data.free_num = 99999;
obj.data.type = 2;
obj.data.finish_time = "2099-12-31到期";
$done({body: JSON.stringify(obj)});
