/*
 *
 *
脚本功能：语境
软件版本：1.5.5

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https:\/\/api\.contextai\.pro\/api\/v1\/userinfo\/GetUserInfo url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/yujing.js

[mitm]
hostname = api.contextai.pro
*
*
*/
var obj = JSON.parse($response.body);

if(obj.data){
    obj.data.isVip = true;
    obj.data.isForeverVip = true;

    if(obj.data.user){
    
        obj.data.user.startVipAt = "2020-01-01T00:00:00Z";
        obj.data.user.endVipAt = "2099-12-31T23:59:59Z";
        
        
    }
}

$done({body: JSON.stringify(obj)});
