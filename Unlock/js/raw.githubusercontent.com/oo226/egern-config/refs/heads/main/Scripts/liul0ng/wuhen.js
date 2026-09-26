/*
 *
 *
脚本功能：无痕改字
软件版本：1.0.2

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https://meitu\.minecaller\.com/api/users url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/wuhen.js

[mitm]
hostname = meitu.minecaller.com
*
*
*/

let obj = JSON.parse($response.body);

// 开启VIP
obj.vip = true;
obj.trialed = true;
obj.vipPoint = 99999;
obj.recharged = true;
obj.pointRecharged = true;
obj.totalPayAmount = 99999;

// 钻石、点数拉满
obj.diamonds = 999999;
obj.chargePoint = 99999;

// 免费生成次数拉满
obj.freeCount = 9999;

// 各类生成/修改次数拉满
obj.changePhotoCount = 999;
obj.shareDownloadCount = 999;
obj.shareGenerateCount = 999;
obj.changeTemplateGenerate = 999;
obj.paintSameCount = 999;
obj.releaseCount = 999;
obj.raffleCount = 999;

// 勋章满级
obj.medalName = "至尊会员";
obj.allMedalName = "至尊会员";


$done({body: JSON.stringify(obj)});
