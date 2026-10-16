/* 主题：暖橙横向（warm-horizontal）—— themes/暖橙横向.py 的 JS 移植 */
(function (global) {
  "use strict";

  var THEME = {
    name: "warm-horizontal", label: "暖橙横向", version: "1.0", containers: [],
    tokens: {
      BLUE: "#ea8a2e", BLUE_BRIGHT: "#f59e0b", BORDER_BLUE: "#fed7aa",
      INK: "#7c2d12", BOLD_INK: "rgb(124,45,18)", TEXT: "#78350f", MUTED: "#b45309",
      PAGE_BG: "#fffaf3",
      FONT: "-apple-system,system-ui,'PingFang SC','Microsoft YaHei',sans-serif"
    }
  };

  function renderPara(b, c) {
    var t = c.t;
    var text = (b.bullet ? "• " : "") + (b.fields.text || "");
    return '<section style="margin-top:20px;"><p style="margin:0;font-size:15px;line-height:1.95;text-align:justify;color:' +
      t.TEXT + ';letter-spacing:0;">' + c.leaf(text) + "</p></section>";
  }

  function renderCard(b, c) {
    var t = c.t, f = b.fields;
    var title = f.heading || (f.paras[0] || "");
    var paras = f.paras || [];
    var summary = f.heading ? paras : paras.slice(1);
    var sumHtml = summary.map(function (p, j) {
      return '<p style="margin:' + (j < summary.length - 1 ? "0 0 6px" : "0") +
        ';font-size:13.5px;line-height:1.8;color:' + t.TEXT + ';">' + c.leaf(p) + "</p>";
    }).join("");
    return '<section style="margin-top:24px;"><section style="display:flex;align-items:center;gap:14px;background:#fffaf3;border:1px solid ' +
      t.BORDER_BLUE + ';border-radius:12px;padding:15px 16px;">' +
      '<span style="width:40px;height:40px;border-radius:9px;background:#fed7aa;flex-shrink:0;display:flex;align-items:center;justify-content:center;">' +
      '<span style="width:14px;height:14px;border-radius:4px;background:' + t.BLUE +
      ';display:inline-block;"></span></span>' +
      '<span style="flex:1;min-width:0;"><p style="margin:0 0 6px;font-size:16px;font-weight:900;color:' +
      t.INK + ';">' + c.leaf(title) + "</p>" + sumHtml + "</span></section></section>";
  }

  var ROLES = { para: renderPara, card: renderCard };
  global.WX.registerTheme({ THEME: THEME, ROLES: ROLES });
})(window);
