/**
 * 实时油价面板（Surge）
 * 数据源：http://m.qiyoujiage.com/
 * 改自 getsomecat/youjia.js、IBL3ND Oil_Widget
 *
 * argument 示例：
 *   region=guangdong/guangzhou&title=广东油价&icon=fuelpump.fill&color=#FF9F0A
 *
 * 地区拼音：省/市，如 beijing、shanghai、guangdong/guangzhou、shanxi-3/xian
 * 也可在 Surge 持久化写入 key=yj 覆盖地区（脚本编辑器齿轮 → $persistentStore）
 */

function getArgs() {
  const defaults = {
    region: "guangdong/guangzhou",
    title: "实时油价",
    icon: "fuelpump.fill",
    color: "#FF9F0A",
  };
  if (typeof $argument === "undefined" || !$argument) return defaults;
  try {
    const parsed = Object.fromEntries(
      String($argument)
        .split("&")
        .filter(Boolean)
        .map((item) => {
          const i = item.indexOf("=");
          if (i < 0) return [item, ""];
          return [
            item.slice(0, i),
            decodeURIComponent(item.slice(i + 1) || ""),
          ];
        })
    );
    return { ...defaults, ...parsed };
  } catch (_) {
    return defaults;
  }
}

const args = getArgs();
let region = args.region;

try {
  const pref = $persistentStore.read("yj");
  if (pref) region = pref;
} catch (_) {}

const queryAddr = `http://m.qiyoujiage.com/${region}.shtml`;

$httpClient.get(
  {
    url: queryAddr,
    headers: {
      referer: "http://m.qiyoujiage.com/",
      "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
  },
  (error, _response, data) => {
    if (error || !data) {
      console.log(`油价请求失败: ${error || "empty"} URL=${queryAddr}`);
      $done({
        title: args.title,
        content: `获取失败\n${region}`,
        icon: args.icon,
        "icon-color": "#D64545",
      });
      return;
    }

    let regionName = "";
    const titleMatch = String(data).match(/<title>([^_<]+)/);
    if (titleMatch) {
      regionName = titleMatch[1]
        .replace(/(油价|实时|今日|最新|查询|价格)/g, "")
        .trim();
    }

    const regPrice =
      /<dl>[\s\S]+?<dt>(.*油)<\/dt>[\s\S]+?<dd>(.*)\(元\)<\/dd>/gm;
    const prices = [];
    let m;
    while ((m = regPrice.exec(data)) !== null) {
      if (m.index === regPrice.lastIndex) regPrice.lastIndex++;
      prices.push({ name: m[1].trim(), value: `${m[2].trim()} 元/L` });
    }

    let adjustDate = "";
    let adjustTrend = "";
    let adjustValue = "";
    const tipsMatch = data.match(
      /<div class="tishi">\s*<span>(.*)<\/span><br\/>([\s\S]+?)<br\/>/
    );
    if (tipsMatch && tipsMatch.length === 3) {
      const rawDate = tipsMatch[1].split("价")[1] || "";
      adjustDate = rawDate.slice(0, -2);
      adjustValue = tipsMatch[2];
      adjustTrend =
        /下调|下跌/.test(adjustValue) ? "↓" : "↑";
      const range = adjustValue.match(
        /([\d.]+)元\/升-([\d.]+)元\/升/
      );
      if (range) {
        adjustValue = `${range[1]}-${range[2]}元/L`;
      } else {
        const ton = adjustValue.match(/[\d.]+元\/吨/);
        if (ton) adjustValue = ton[0];
      }
    }

    if (prices.length < 3) {
      console.log(`油价解析失败 count=${prices.length} URL=${queryAddr}`);
      $done({
        title: args.title,
        content: `解析失败\n${region}`,
        icon: args.icon,
        "icon-color": "#D64545",
      });
      return;
    }

    const lines = prices
      .slice(0, 4)
      .map((p) => `${p.name}  ${p.value}`)
      .join("\n");
    const tip =
      adjustDate || adjustValue
        ? `\n${adjustDate} ${adjustTrend} ${adjustValue}`.trimEnd()
        : "";
    const title = regionName
      ? `${args.title} · ${regionName}`
      : args.title;

    $done({
      title,
      content: `${lines}${tip}`,
      icon: args.icon,
      "icon-color": args.color,
    });
  }
);
