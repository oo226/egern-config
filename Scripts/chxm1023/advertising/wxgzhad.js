/*************************************

项目名称：微信公众号广告（getappmsgad / getappmsgext）
脚本作者：chxm1023
电报频道：https://t.me/chxm1023
使用声明：⚠️仅供参考，🈲转载与售卖！
说明：只清空 advertisement_*，保留 getappmsgext 阅读/赞评等字段

**************************************

[rewrite_local]
^http[s]?:\/\/mp\.weixin\.qq\.com(:\d+)?\/mp\/(getappmsgad|getappmsgext) url script-response-body https://raw.githubusercontent.com/chxm1023/Advertising/main/wxgzhad.js

[mitm]
hostname = mp.weixin.qq.com

*************************************/


var body = $response.body;
try {
  var chxm1023 = JSON.parse(body);
  chxm1023.advertisement_num = 0;
  chxm1023.advertisement_info = [];
  delete chxm1023.appid;
  body = JSON.stringify(chxm1023);
} catch (e) {
  // ignore non-JSON
}

$done({body: body});
 
