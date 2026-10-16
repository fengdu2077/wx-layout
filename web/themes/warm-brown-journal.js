/* 主题：暖棕手记（warm-brown-journal）—— themes/暖棕手记.py 的 JS 移植 */
(function (global) {
  "use strict";
  var WX = global.WX;
  var MARK_RE = /==([^=\n]+)==/g;

  var THEME = {
    name: "warm-brown-journal", label: "暖棕手记", version: "1.0", containers: [],
    tokens: {
      BLUE: "rgb(250,124,33)", BOLD_INK: "rgb(250,124,33)",
      INK: "#383838", TEXT: "#383838", MUTED: "#888888", PAGE_BG: "#ffffff",
      FONT: '"PingFang SC NEW",system-ui,-apple-system,"Helvetica Neue","Hiragino Sans GB","Microsoft YaHei UI","Microsoft YaHei",Arial,sans-serif',
      KHAKI: "#6E6248", SLATE: "#2F3840", MAUVE: "#8F7373", DUSTY: "#A89090",
      PINK: "#E8D5D5", PINK_DEEP: "#CFB7B7", CREAM: "#F4ECD7",
      TAG1_BG: "#F0E4E4", TAG1_FG: "#6E5353",
      TITLE_GRAD: "linear-gradient(90deg,#2d2d2d 0%,#6e6248 58%,#a89090 100%)",
      PART_GRAD: "linear-gradient(90deg,#2f3840 0%,#8f7373 58%,#cfb7b7 100%)",
      BADGE_GRAD: "linear-gradient(135deg,#8f7373 0%,#cfb7b7 100%)",
      HIGHLIGHT: "linear-gradient(transparent 62%,#e8d5d5 62%,#e8d5d5 90%,transparent 90%)"
    }
  };

  /* 行内：先抽 ==卡其高亮==，其余交给内核 inline（**橙 / 链接） */
  function warmInline(text, c) {
    var stash = {};
    var tmp = text.replace(MARK_RE, function (m, inner) {
      var k = "\x01" + Object.keys(stash).length + "\x01";
      stash[k] = inner; return k;
    });
    var out = c.inline(tmp);
    Object.keys(stash).forEach(function (k) {
      var inner = stash[k];
      var frag = '<strong style="margin:0;padding:0 2px;font-weight:700;color:' +
        c.t.KHAKI + ';background-image:' + c.t.HIGHLIGHT +
        ';background-repeat:no-repeat;">' + WX.esc(inner, false) + "</strong>";
      out = out.split(k).join(frag);
    });
    return out;
  }
  function warmLeaf(text, c) {
    return '<span leaf="">' + warmInline(text, c) + "</span>";
  }

  function renderPara(b, c) {
    var text = (b.bullet ? "• " : "") + (b.fields.text || "");
    return '<section style="margin:0 0 20px;"><p style="margin:0;font-size:15px;line-height:1.85;text-align:justify;color:' +
      c.t.INK + ';letter-spacing:0;">' + warmLeaf(text, c) + "</p></section>";
  }

  function pill(txt, bg, fg, margin, c) {
    if (!txt) return "";
    return '<span style="display:inline-block;background:' + bg + ';color:' + fg +
      ';border-radius:980px;padding:4px 10px;font-size:11px;line-height:1.4;margin:' +
      margin + ';">' + c.leaf(txt) + "</span>";
  }

  function renderIssue(b, c) {
    var t = c.t;
    var tag1 = b.get(0), tag2 = b.get(1), title = b.get(2);
    var pills = '<section style="margin:0 0 18px;line-height:1;">' +
      pill(tag1, t.TAG1_BG, t.TAG1_FG, "0 6px 0 0", c) +
      pill(tag2, t.CREAM, t.KHAKI, "0", c) + "</section>";
    var h1 = '<h1 style="margin:0 0 26px;font-size:29px;line-height:1.34;font-weight:780;letter-spacing:-0.02em;color:' +
      t.INK + ';background-image:' + t.TITLE_GRAD + ';background-repeat:no-repeat;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">' +
      c.leaf(title) + "</h1>";
    var dot = '<section style="width:64px;height:4px;margin:0 0 26px;border-radius:980px;background-color:' +
      t.PINK_DEEP + ';"></section>';
    return '<section style="margin:0 10px 34px;padding:26px 10px 4px;">' +
      pills + h1 + dot + "</section>";
  }

  function renderPart(b, c) {
    var t = c.t;
    var num = b.get(0), title = b.get(1), en = b.get(2);
    var badge = '<span style="display:inline-block;background-color:' + t.DUSTY +
      ';background-image:' + t.BADGE_GRAD + ';color:' + t.CREAM +
      ';font-size:18px;font-weight:900;padding:4px 14px;border-radius:6px;margin-right:14px;line-height:1.3;">' +
      c.leaf(num) + "</span>";
    var head = '<span style="min-width:0;">' +
      '<p style="margin:0 0 2px;font-size:10px;font-weight:700;letter-spacing:0;color:' + t.KHAKI + ';">' +
      c.leaf(en.toUpperCase()) + "</p>" +
      '<span style="display:block;font-size:18px;font-weight:800;line-height:1.5;color:' + t.SLATE +
      ';background-image:' + t.PART_GRAD + ';background-repeat:no-repeat;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">' +
      c.leaf(title) + "</span></span>";
    return '<section style="display:flex;align-items:center;margin:18px 0 20px;padding-bottom:14px;border-bottom:3px solid ' +
      t.PINK_DEEP + ';">' + badge + head + "</section>";
  }

  function renderShot(b, c) {
    var t = c.t;
    var src = b.get(0), caption = b.get(1);
    var rounded = ["1", "true", "yes", "圆角"].indexOf(b.kw.round) >= 0;
    var wrapM, imgStyle;
    if (rounded) {
      wrapM = "28px 0 30px";
      imgStyle = "max-width:100%;height:auto;display:block;margin:0 auto;border-radius:12px;";
    } else {
      wrapM = "0 0 8px";
      imgStyle = "max-width:100%;height:auto;display:block;margin:0 auto;";
    }
    var fig = '<section style="text-align:center;margin:' + wrapM + ';"><span leaf="">' +
      '<img src="' + c.escAttr(src) + '" style="' + imgStyle + '" /></span></section>';
    var cap = caption ?
      '<p style="margin:10px 0 20px;font-size:11px;line-height:1.65;text-align:center;color:' +
      t.MUTED + ';">' + c.leaf(caption) + "</p>" : "";
    return fig + cap;
  }

  function renderEnd(b, c) {
    var thanks = b.get(0) || "真诚感谢你的每一个❤️和👍";
    var theEnd = '<section style="text-align:center;margin:28px 0 16px;"><p style="margin:0;font-size:16px;letter-spacing:0;">' +
      c.leaf("—The End—") + "</p></section>";
    var thanksHtml = '<p style="margin:0 0 18px;font-size:14px;line-height:1.85;text-align:center;color:rgb(102,102,102);">' +
      c.leaf(thanks) + "</p>";
    return theEnd + thanksHtml;
  }

  var ROLES = {
    para: renderPara, issue: renderIssue, part: renderPart,
    shot: renderShot, end: renderEnd
  };
  global.WX.registerTheme({ THEME: THEME, ROLES: ROLES });
})(window);
