/*
 *
 *
脚本功能：moo
软件版本：3.0.6

使用声明：此脚本仅供学习与交流，请在下载使用24小时内删除！请勿在中国大陆转载与贩卖！
*******************************
[rewrite_local]
^https:\/\/diary\.aiyouaiyou\.cn\/account\/api\/user\/userInfo url script-response-body https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/moo.js

[mitm]
hostname = diary.aiyouaiyou.cn
*
*
*/
$done({
  body: "NSdfrN9PyVWMpSfS7xfH8M9wV5Jf8ANrjKL6zyKt93yUIptW7n1iGnJR0dWUpSaU1d2zMxAcmDsxxX7Zp8mPJSrOqhLAfCTzD2qqRTDpte/i47YXydcxIqu7Z5ZRXN5PdWh4sIUYVGGLGq5n97hnvihF3gKahvhVARK2r8EDKMG76m9x40tneJQblJeZ7LeDLo8V1kuXxi7OPLu4BcAMZIFmYJqpc1ixVvHdWfvZtSyzlKYCLbdiQU21gEJbuNLHGH9Q/+e5oD4Wtz8g4mbkTcFEDPSF8oUMPb8HVz49ttXHNePxrJRwtpePJZ03mPwcQ3fCRxhQgSll6Ca/LKdBPFesRVKzk8kNXaWlrWsLecg1DtlsukOR305N0mYPDZA63Gp4kv+iSEOfWiLqdQupm5mjQ5auMuKZlMaRxT6KXTtQOJWNVt7vXrAAtxZydW8CFaysX2o7u+fp9yGWdJiS8kt950wrsEsLj0e3rfhEfa2EHAcVGbSGbLkbhqUYIBHfLP0whk0p80h5W+dL5Ktsptrfihjron3Otp0+cWVQ2cUek6J8RXgWmCjG45vEgFWw1PKkKDX1WFtkXb/KF/PGsx4wHK1QFlnwuDxmIdswNKdl1VQMcyihPe6s7S4WlnfL76jfQYUiwBP6bAhHuFhKLqGTDrIXk3UBtRNS3WLFYsMzjZX1wFIx2SKeFwLRlZBkeyedB/7YSTzU2d3KheGSYwEnM5B969lM23WD6wNofwJgzm8JY/QHXzumiOf4WfoeMGcm4RDzGjjG/r/OT9ZWWg=="
});
