// 招商实时金价 - Egern 小组件 (深色模式适配版)
export default async function(ctx) {
  const API_URL = "https://mbmodule-openapi.paas.cmbchina.com/product/v1/func/market-center";
  const widgetFamily = ctx.widgetFamily || "systemMedium";

  // 🎨 颜色配置：使用 { light, dark } 格式，由 Egern 自动切换
  const theme = {
    bg: { light: "#FFFFFF", dark: "#1C1C1E" },
    card: { light: "#F5F5F7", dark: "#2C2C2E" },
    title: { light: "#000000", dark: "#FFFFFF" },
    label: { light: "#666666", dark: "#AAAAAA" },
    price: { light: "#000000", dark: "#FFFFFF" },
    up: { light: "#00AA00", dark: "#30D158" },
    down: { light: "#FF0000", dark: "#FF453A" },
    time: { light: "#999999", dark: "#888888" }
  };

  let data = null;
  try {
    const resp = await ctx.http.post(API_URL, {
      headers: {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
      },
      body: "params=" + encodeURIComponent(JSON.stringify([{ prdType: "H", prdCode: "" }])),
      timeout: 8000
    });
    data = await resp.json();
  } catch (e) {}

  if (!data || data.code !== "SUC0000") {
    return {
      type: "widget",
      padding: 16,
      backgroundColor: theme.bg,
      children: [{
        type: "text",
        text: "⚠️ 数据获取失败",
        font: { size: "subheadline", weight: "medium" },
        textColor: theme.down,
        textAlign: "center"
      }]
    };
  }

  const gold = data.data.FQAMBPRCZ1 || {};
  const buy = gold.zBuyPrc || "--";
  const sell = gold.zSelPrc || "--";
  const change = gold.zDvlCur || "--";

  // 获取当前时间
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const dateTimeStr = `${year}/${month}/${day} ${hours}:${minutes}`;

  const isUp = change.startsWith("+");

  // 🔹 小尺寸布局
  if (widgetFamily === "systemSmall") {
    return {
      type: "widget",
      padding: [8, 8, 8, 8],
      gap: 4,
      borderRadius: 16,
      refreshAfter: "PT5M",
      backgroundColor: theme.bg,
      children: [
        {
          type: "stack",
          direction: "row",
          alignItems: "center",
          justifyContent: "space-between",
          children: [
            { type: "text", text: "🏦 招商金价", font: { size: "caption1", weight: "bold" }, textColor: theme.title },
            { type: "text", text: `${isUp ? "📈" : "📉"} ${change}`, font: { size: "caption2", weight: "semibold" }, textColor: isUp ? theme.up : theme.down }
          ]
        },
        {
          type: "stack",
          direction: "row",
          gap: 4,
          children: [
            {
              type: "stack", direction: "column", alignItems: "center", flex: 1, padding: [6, 4, 6, 4], backgroundColor: theme.card, borderRadius: 6,
              children: [
                { type: "text", text: "⬇️买入", font: { size: "caption2" }, textColor: theme.label },
                { type: "text", text: buy, font: { size: "headline", weight: "bold" }, textColor: theme.price }
              ]
            },
            {
              type: "stack", direction: "column", alignItems: "center", flex: 1, padding: [6, 4, 6, 4], backgroundColor: theme.card, borderRadius: 6,
              children: [
                { type: "text", text: "⬆️卖出", font: { size: "caption2" }, textColor: theme.label },
                { type: "text", text: sell, font: { size: "headline", weight: "bold" }, textColor: theme.price }
              ]
            }
          ]
        }
      ]
    };
  }

  // 🔹 中尺寸布局
  return {
    type: "widget",
    padding: [12, 12, 12, 12],
    gap: 8,
    borderRadius: 16,
    refreshAfter: "PT5M",
    backgroundColor: theme.bg,
    children: [
      {
        type: "stack",
        direction: "column",
        gap: 4,
        children: [
          {
            type: "stack",
            direction: "row",
            alignItems: "center",
            justifyContent: "space-between",
            children: [
              { type: "text", text: "🏦 招商金价", font: { size: "title3", weight: "bold" }, textColor: theme.title },
              { type: "text", text: `${isUp ? "📈" : "📉"} ${change}`, font: { size: "caption1", weight: "semibold" }, textColor: isUp ? theme.up : theme.down }
            ]
          },
          {
            type: "text",
            text: dateTimeStr,
            font: { size: "caption2" },
            textColor: theme.time
          }
        ]
      },
      {
        type: "stack",
        direction: "row",
        gap: 8,
        children: [
          {
            type: "stack", direction: "column", alignItems: "center", flex: 1, padding: [10, 8, 10, 8], backgroundColor: theme.card, borderRadius: 10,
            children: [
              { type: "text", text: "⬇️ 买入", font: { size: "caption1", weight: "medium" }, textColor: theme.label },
              { type: "text", text: buy, font: { size: "title2", weight: "bold" }, textColor: theme.price },
              { type: "text", text: "元/克", font: { size: "caption2" }, textColor: theme.time }
            ]
          },
          {
            type: "stack", direction: "column", alignItems: "center", flex: 1, padding: [10, 8, 10, 8], backgroundColor: theme.card, borderRadius: 10,
            children: [
              { type: "text", text: "⬆️ 卖出", font: { size: "caption1", weight: "medium" }, textColor: theme.label },
              { type: "text", text: sell, font: { size: "title2", weight: "bold" }, textColor: theme.price },
              { type: "text", text: "元/克", font: { size: "caption2" }, textColor: theme.time }
            ]
          }
        ]
      }
    ]
  };
}

