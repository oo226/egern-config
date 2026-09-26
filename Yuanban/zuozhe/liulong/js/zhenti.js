/*
 *
 *
脚本功能：真题伴侣
软件版本：3.5.9

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https?://newtest\.zoooy111\.com/mobilev4\.php/User/index url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/zhenti.js

[mitm]
hostname = newtest.zoooy111.com
*
*
*/
let body = $response.body;
try {
  let obj = JSON.parse(body);
  // 直接替换data为你指定的新密文
  obj.data = "cc4def8ec21cc628e22bd23b75fd88a611763fdc758a15814b6b016d77ec4832ddf1e39e2fde9d00ccc7d9a4f2978b290ba9fdee56d6dde254d62a52fb0ef10cb079c214fc9fa74b339bbf081bb7d2c7611560d6c76b253eb1dfd6112b6b55349b79f642aa37c4ec93e087ff3db526a3882eb20974bba65ff45190654bd0a0bbd35deaecc86d6847c1034c72ab6a9d7e1166f9e1ee539d3f7b17d36c54b6417f5fd58d5b2fe2fa100d198fe789e45f9273fb3f1760290ae8c3eb55addb29cd9bb7455d8e20b488eb1c72da5a1b143ab53a71d5c9cd8b673e6e8f4893dc179535c851ecb956327d8b2407dccd43fb3e066fcf2b291541472b5dd5e169506afebf";
  $done({ body: JSON.stringify(obj) });
} catch (e) {
  // 解析失败时原样返回，避免APP崩溃
  $done({ body });
}
