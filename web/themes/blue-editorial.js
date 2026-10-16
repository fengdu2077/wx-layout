/* 主题：蓝白杂志（blue-editorial）—— themes/蓝白杂志.py 的 JS 移植 */
(function (global) {
  "use strict";

  var THEME = {
    name: "blue-editorial", label: "蓝白杂志", version: "1.0", containers: [],
    tokens: {
      BLUE: "#2563eb", BLUE_BRIGHT: "#3b82f6", BORDER_BLUE: "#dbeafe",
      INK: "#111827", BOLD_INK: "rgb(17,24,39)", TEXT: "#374151", MUTED: "#9ca3af",
      PAGE_BG: "#ffffff",
      FONT: "'IBM Plex Sans',-apple-system,system-ui,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif"
    }
  };

  function renderPara(b, c) {
    var t = c.t;
    var text = (b.bullet ? "• " : "") + (b.fields.text || "");
    return '<section style="margin-top:20px;font-family:' + t.FONT + ';">' +
      '<p style="margin:0;font-size:15px;line-height:1.95;text-align:justify;color:' +
      t.TEXT + ';letter-spacing:0;">' + c.leaf(text) + "</p></section>";
  }

  function renderIssue(b, c) {
    var t = c.t;
    var column = b.get(0), date = b.get(1), cover = b.fields.image || "";
    var texts = b.blocks.filter(function (e) {
      return e.type === "para" || e.type === "heading";
    }).map(function (e) { return e.text; });
    var label = texts[0] || "EDITOR'S NOTE";
    var leads = texts.slice(1);
    var leadHtml = leads.map(function (p, j) {
      return '<p style="margin:' + (j < leads.length - 1 ? "0 0 7px" : "0") +
        ';font-size:15px;font-weight:900;line-height:1.7;color:' + t.INK + ';">' +
        c.leaf(p) + "</p>";
    }).join("");

    return '<section style="background:#ffffff;border:1px solid ' + t.BORDER_BLUE +
      ';border-radius:12px;overflow:hidden;box-shadow:0 4px 14px rgba(37,99,235,0.06);">' +
      '<section style="padding:13px 16px 12px;display:flex;align-items:center;gap:8px;">' +
      '<span style="width:7px;height:7px;background:' + t.BLUE +
      ';border-radius:50%;display:inline-block;overflow:hidden;"><span leaf="">&nbsp;</span></span>' +
      '<span style="font-size:9px;font-weight:800;letter-spacing:0;color:' + t.BLUE + ';">' +
      c.leaf(column) + "</span>" +
      '<span style="height:1px;background:linear-gradient(90deg,#bfdbfe,rgba(191,219,254,0));flex:1;display:inline-block;"><span leaf="">&nbsp;</span></span>' +
      '<span style="font-size:9px;font-weight:700;color:' + t.MUTED + ';">' + c.leaf(date) +
      "</span></section>" +
      '<figure style="margin:0;line-height:0;"><span leaf="">' +
      '<img src="' + c.escAttr(cover) +
      '" style="max-width:100%;height:auto;display:block;margin:0 auto;" /></span></figure>' +
      '<section style="padding:15px 17px 17px;background:linear-gradient(135deg,#eff6ff,#ffffff);border-top:1px solid ' +
      t.BORDER_BLUE + ';">' +
      '<p style="margin:0 0 8px;font-size:9px;font-weight:800;letter-spacing:0;color:' + t.BLUE +
      ';">' + c.leaf(label) + "</p>" + leadHtml + "</section></section>";
  }

  function renderPart(b, c) {
    var t = c.t;
    var num = b.get(0), title = b.get(1), en = b.get(2);
    return '<section style="margin-top:60px;font-family:' + t.FONT + ';">' +
      '<section style="display:flex;align-items:center;gap:16px;">' +
      '<section style="text-align:center;flex-shrink:0;">' +
      '<p style="margin:0;font-size:34px;font-weight:800;color:' + t.BLUE +
      ';line-height:1;letter-spacing:0;">' + c.leaf(num) + "</p>" +
      '<p style="margin:3px 0 0;font-size:8px;font-weight:700;color:' + t.MUTED +
      ';letter-spacing:0;">' + c.leaf("PART") + "</p></section>" +
      '<section style="flex:1;min-width:0;">' +
      '<p style="margin:0 0 3px;font-size:22px;font-weight:800;color:' + t.BLUE +
      ';line-height:1.35;letter-spacing:0;word-break:break-word;">' + c.leaf(title) + "</p>" +
      '<p style="margin:0;font-size:10px;font-weight:700;color:' + t.BLUE_BRIGHT +
      ';letter-spacing:0;">' + c.leaf(en.toUpperCase()) + "</p>" +
      "</section></section></section>";
  }

  function renderSub(b, c) {
    var t = c.t, title = b.get(0);
    return '<section style="margin-top:32px;"><p style="margin:0;font-size:16px;font-weight:800;color:' +
      t.BLUE + ';letter-spacing:0;line-height:1.8;">' +
      '<span style="width:4px;height:14px;background:' + t.BLUE +
      ';border-radius:2px;display:inline-block;vertical-align:-2px;margin-right:9px;"></span>' +
      c.leaf(title) + "</p></section>";
  }

  function renderShot(b, c) {
    var t = c.t, src = b.get(0), caption = b.get(1);
    var cap = caption ?
      '<figcaption style="margin-top:9px;font-size:12px;color:' + t.MUTED +
      ';text-align:center;letter-spacing:0;line-height:1.6;">' + c.leaf(caption) + "</figcaption>" : "";
    return '<section style="margin-top:24px;"><figure style="margin:0;">' +
      '<section style="background:#ffffff;border:1px solid ' + t.BORDER_BLUE +
      ';border-radius:12px;padding:6px;overflow:hidden;box-shadow:0 3px 12px rgba(37,99,235,0.06);">' +
      '<span leaf=""><img src="' + c.escAttr(src) +
      '" style="max-width:100%;height:auto;display:block;margin:0 auto;border-radius:8px;" /></span></section>' +
      cap + "</figure></section>";
  }

  function renderQuote(b, c) {
    var t = c.t, who = b.get(0);
    var tag = who ?
      '<p style="margin:0 0 6px;font-size:11px;font-weight:800;letter-spacing:0;color:' + t.BLUE +
      ';">' + c.leaf(who) + "</p>" : "";
    var paras = b.fields.paras || [];
    var body = paras.map(function (p, j) {
      return '<p style="margin:' + (j < paras.length - 1 ? "0 0 7px" : "0") +
        ';font-size:14px;line-height:1.85;color:' + t.TEXT + ';letter-spacing:0;">' +
        c.leaf(p) + "</p>";
    }).join("");
    return '<section style="margin-top:20px;padding:12px 14px;background:#f8fafc;border-left:3px solid ' +
      t.BLUE + ';border-radius:0 8px 8px 0;">' + tag + body + "</section>";
  }

  function renderVideo(b, c) {
    // 视频只能在后台从素材库引用、是播放框，无法样式化；统一走内核占位块（虚线框 + 替换提示）。
    return c.videoPlaceholder(b);
  }

  function renderEnd(b, c) {
    var t = c.t;
    return '<section style="margin:26px 4px 22px;display:flex;align-items:center;gap:12px;">' +
      '<span style="height:1px;background:linear-gradient(90deg,rgba(37,99,235,0),#93c5fd);flex:1;display:inline-block;"><span leaf="">&nbsp;</span></span>' +
      '<span style="font-size:9px;font-weight:800;letter-spacing:0;color:' + t.BLUE + ';">' +
      c.leaf("END") + "</span>" +
      '<span style="height:1px;background:linear-gradient(90deg,#93c5fd,rgba(37,99,235,0));flex:1;display:inline-block;"><span leaf="">&nbsp;</span></span></section>';
  }

  function renderAuthor(b, c) {
    var t = c.t;
    var name = b.get(0), role = b.get(1);
    var intro = (b.fields.paras || []).join(" ");
    var avatar = name.trim()[0] || "?";
    return '<section style="margin:0 4px 24px;padding:18px;background:linear-gradient(135deg,#f0f7ff,#ffffff);border:1px solid ' +
      t.BORDER_BLUE + ';border-radius:12px;">' +
      '<section style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">' +
      '<section style="width:38px;height:38px;border-radius:50%;background:' + t.BLUE +
      ';text-align:center;line-height:38px;flex-shrink:0;"><span style="font-size:17px;font-weight:900;color:#ffffff;">' +
      avatar + "</span></section>" +
      '<section style="min-width:0;"><p style="margin:0 0 2px;font-size:14px;font-weight:900;color:' +
      t.INK + ';">' + c.leaf(name) + "</p>" +
      '<p style="margin:0;font-size:9px;color:' + t.MUTED + ';letter-spacing:0;">' +
      c.leaf(role.toUpperCase()) + "</p></section></section>" +
      '<p style="margin:0 0 10px;font-size:13px;line-height:1.8;color:' + t.TEXT + ';">' +
      c.leaf(intro.trim()) + "</p>" +
      '<p style="font-size:9px;color:' + t.MUTED + ';letter-spacing:0;margin:14px 0 0;text-align:center;">' +
      c.leaf("THANKS FOR READING") + "</p></section>";
  }

  function renderCard(b, c) {
    var t = c.t, f = b.fields;
    var image = f.image || "";
    var title = f.heading || (f.paras[0] || "");
    var paras = f.paras || [];
    var summary = f.heading ? paras : paras.slice(1);
    var link = f.link || "";
    var action = f.links[0] ? f.links[0].text : "阅读更多";
    var img = image ?
      '<span leaf=""><img src="' + c.escAttr(image) +
      '" style="width:100%;height:160px;object-fit:cover;display:block;" /></span>' : "";
    var sumHtml = summary.map(function (p, j) {
      return '<p style="margin:' + (j < summary.length - 1 ? "0 0 7px" : "0") +
        ';font-size:13.5px;line-height:1.8;color:' + t.TEXT + ';">' + c.leaf(p) + "</p>";
    }).join("");
    var btn = link ?
      '<a href="' + link + '" style="display:inline-block;margin-top:10px;background:' + t.BLUE +
      ';color:#ffffff;font-size:12px;font-weight:700;border-radius:7px;padding:6px 16px;text-decoration:none;">' +
      c.leaf(action) + "</a>" : "";
    return '<section style="margin-top:24px;"><section style="background:#ffffff;border:1px solid ' +
      t.BORDER_BLUE + ';border-radius:12px;overflow:hidden;box-shadow:0 4px 14px rgba(37,99,235,0.06);">' +
      img + '<section style="padding:16px 17px 17px;">' +
      '<p style="margin:0 0 8px;font-size:17px;font-weight:900;color:' + t.INK + ';">' +
      c.leaf(title) + "</p>" + sumHtml + btn + "</section></section></section>";
  }

  var ROLES = {
    para: renderPara, issue: renderIssue, part: renderPart, sub: renderSub,
    shot: renderShot, quote: renderQuote, video: renderVideo, end: renderEnd,
    author: renderAuthor, card: renderCard
  };

  global.WX.registerTheme({ THEME: THEME, ROLES: ROLES });
})(window);
