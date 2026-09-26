/*
 *
 *
脚本功能：薄荷
软件版本：2.4.5

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https://du\.baicizhan\.com url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/bohe.js

[mitm]
hostname = du.baicizhan.com
*
*
*/
let body = $response.body;
let obj = JSON.parse(body);

if (obj.data) {
 
  obj.data.is_vip = 1;
  obj.data.is_try_vip = 1;
  obj.data.vip_expire = "2099-12-31 23:59:59";
  obj.data.vip_days = 99999;
  obj.data.vipDays = 99999;
  obj.data.expireDate = "2099-12-31 23:59:59";
  obj.data.valid = true;
obj.data.termEndDate = "2099-12-31 23:59:59";



  obj.data.buy_status = 1;
  obj.data.book_package_buy_status = 1;
  obj.data.has_read_service = 1;
  obj.data.is_restricted = 0;
  obj.data.can_read = 1;

  if (obj.data.book) {
    obj.data.book.buy_status = 1;
    obj.data.book.book_package_buy_status = 1;
    obj.data.book.has_read_service = 1;
  }


  obj.data.isVIP = true;
  obj.data.isTrial = false;
  obj.data.expireTime = "2099-12-31 23:59:59";
  obj.data.expireTimestamp = 4102358400;
}

$done({ body: JSON.stringify(obj) });
