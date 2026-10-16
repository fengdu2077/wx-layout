/* 主题：翠绿科技（green-tech）—— themes/翠绿科技.py 的 JS 移植 */
(function (global) {
  "use strict";
  var WX = global.WX;

  var THEME = {
    name: "green-tech", label: "翠绿科技", version: "1.0", containers: ["step"],
    tokens: {
      BLUE: "#059669", BOLD_INK: "#059669",
      INK: "#111827", TEXT: "#374151", MUTED: "#9ca3af", LIGHT: "#d1d5db",
      PAGE_BG: "#ffffff",
      FONT: '-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif',
      MONO: '"SF Mono",Consolas,Monaco,monospace',
      AMBER: "#f59e0b", GREEN_BG: "#ecfdf5", GREEN_BG2: "#f0fdf4",
      AMBER_BG: "#fffbeb", CODE_BG: "#f3f4f6",
      TERM_BG: "#1e293b", TERM_HEAD: "#0f172a", TERM_FG: "#e2e8f0",
      HL_GREEN: "#a7f3d0", HL_YELLOW: "#fde68a", HL_PINK: "#fecaca",
      BORDER_GRAY: "#e5e7eb"
    }
  };

  /* 行内（主题本地扩展） */
  function chip(inner, bg, weight, c) {
    return '<code style="font-family:' + c.t.MONO + ';font-size:13px;color:#1f2937;background:' +
      bg + ';font-weight:' + weight + ';border-radius:4px;padding:2px 6px;">' + inner + '</code>';
  }

  function greenInline(text, c) {
    text = WX.esc(text, false);
    var stash = {};
    function keep(frag) {
      var k = "\x01" + Object.keys(stash).length + "\x01";
      stash[k] = frag; return k;
    }
    text = text.replace(/`([^`\n]+)`/g, function (m, inner) {
      return keep(chip(inner, "#f3f4f6", "600", c));
    });
    text = text.replace(/@@([^@\n]+)@@/g, function (m, inner) {
      return keep(chip(inner, "#fde68a", "700", c));
    });
    text = text.replace(/==([^=\n]+)==/g, function (m, inner) {
      return keep('<strong style="color:' + c.t.BLUE + ';font-weight:bold;border-bottom:3px solid ' +
        c.t.HL_YELLOW + ';">' + inner + '</strong>');
    });
    text = text.replace(/~~([^~\n]+)~~/g, function (m, inner) {
      return keep('<span style="border-bottom:2px solid ' + c.t.HL_PINK + ';">' + inner + '</span>');
    });
    text = text.replace(/\+\+([^+\n]+)\+\+/g, function (m, inner) {
      return keep('<span style="font-weight:600;border-bottom:2px solid ' + c.t.HL_GREEN + ';">' +
        inner + '</span>');
    });
    text = text.replace(/\*\*([^*]+)\*\*/g, function (m, inner) {
      return keep('<strong style="color:' + c.t.BLUE + ';">' + inner + '</strong>');
    });
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, function (m, inner, href) {
      return keep('<a href="' + href + '" style="color:' + c.t.BLUE +
        ';text-decoration:underline;">' + inner + '</a>');
    });
    Object.keys(stash).forEach(function (k) {
      text = text.split(k).join(stash[k]);
    });
    return text;
  }

  function greenLeaf(text, c) {
    return '<span leaf="">' + greenInline(text, c) + "</span>";
  }

  function renderPara(b, c) {
    var text = (b.bullet ? "• " : "") + (b.fields.text || "");
    return '<section style="margin:0 0 8px;"><p style="margin:0;font-size:14px;line-height:1.9;text-align:justify;color:' +
      c.t.TEXT + ';letter-spacing:0;">' + greenLeaf(text, c) + "</p></section>";
  }

  function renderIssue(b, c) {
    var t = c.t;
    var tag = b.get(0), date = b.get(1), small = b.get(2);
    var line1 = b.get(3), line2 = b.get(4), subtitle = b.get(5);
    var banner = b.get(6), pill1 = b.get(7), pill2 = b.get(8);

    var top =
      '<section style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">' +
      '<span style="font-size:11px;color:' + t.BLUE + ';font-weight:700;">' + greenLeaf(tag, c) + '</span>' +
      '<span style="height:1px;flex:1;background:linear-gradient(to right,rgba(5,150,105,0.6),rgba(5,150,105,0));"></span>' +
      '<span style="font-size:10px;color:' + t.LIGHT + ';font-weight:600;">' + greenLeaf(date, c) + '</span></section>';
    var eyebrow = small ?
      '<p style="margin:0 0 6px;font-size:15px;color:' + t.LIGHT + ';">' + greenLeaf(small, c) + '</p>' : "";
    var h =
      '<p style="margin:0;font-size:24px;color:' + t.INK + ';font-weight:900;line-height:1.05;">' +
      greenInline(line1, c) + '</p>' +
      '<p style="margin:0 0 16px;font-size:24px;color:' + t.BLUE + ';font-weight:900;line-height:1.05;">' +
      greenInline(line2, c) + '</p>';
    var bar = '<section style="width:48px;height:3px;border-radius:2px;margin-bottom:16px;background:linear-gradient(to right,rgb(5,150,105),rgba(5,150,105,0));"></section>';
    var sub = subtitle ?
      '<p style="margin:0 0 18px;font-size:13px;color:' + t.MUTED + ';line-height:1.7;">' +
      greenLeaf(subtitle, c) + '</p>' : "";
    function modelPill(x) {
      return '<span style="font-size:8px;color:#ffffff;background:rgba(255,255,255,0.2);font-weight:600;border-radius:3px;padding:1px 6px;margin-right:6px;">' +
        greenLeaf(x, c) + '</span>';
    }
    var bannerH =
      '<section style="display:flex;align-items:center;gap:8px;padding:12px 0;margin-top:4px;">' +
      '<span style="font-size:12px;color:rgba(255,255,255,0.9);font-weight:600;margin-right:6px;">' +
      greenLeaf(banner, c) + '</span>' + modelPill(pill1) + modelPill(pill2) + '</section>';
    var bannerWrap = '<section style="background:linear-gradient(135deg,#059669,#10b981);border-radius:10px;padding:0 20px;">' +
      bannerH + '</section>';

    return '<section style="width:677px;max-width:100%;box-sizing:border-box;background:#ffffff;border-radius:20px;margin:0 0 32px;padding:32px 28px 28px;">' +
      top + eyebrow + h + bar + sub + bannerWrap + '</section>';
  }

  function tocCard(num, title, sub, active) {
    if (active) {
      return '<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:linear-gradient(135deg,#059669,#10b981);border-radius:12px;padding:12px;margin-right:8px;">' +
        '<p style="margin:0 0 5px;font-size:9px;color:rgba(255,255,255,0.7);font-weight:700;letter-spacing:1px;">PART ' + num + '</p>' +
        '<p style="margin:0 0 3px;font-size:13px;color:#ffffff;font-weight:800;">' + title + '</p>' +
        '<p style="margin:0;font-size:10px;color:rgba(255,255,255,0.7);">' + sub + '</p></section>';
    }
    return '<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:#ffffff;border-radius:12px;padding:12px;margin-right:8px;">' +
      '<p style="margin:0 0 5px;font-size:9px;color:#9ca3af;font-weight:700;letter-spacing:1px;">PART ' + num + '</p>' +
      '<p style="margin:0 0 3px;font-size:13px;color:#111827;font-weight:800;">' + title + '</p>' +
      '<p style="margin:0;font-size:10px;color:#9ca3af;">' + sub + '</p></section>';
  }
  function renderToc(b, c) {
    var entries = [];
    b.bodyLines.forEach(function (ln) {
      if (!ln.trim()) return;
      var cells = ln.split("|").map(function (x) { return x.trim(); });
      if (cells.length >= 2) entries.push([cells[0], cells[1], cells[2] || ""]);
    });
    var nParts = entries.filter(function (e) { return e[0] !== "///"; }).length;
    var head = '<section style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">' +
      '<p style="margin:0;font-size:10px;color:#9ca3af;font-weight:600;text-transform:uppercase;letter-spacing:2px;">📦 ' + nParts + ' Parts + Conclusion</p>' +
      '<p style="margin:0;font-size:10px;color:#9ca3af;">👉 滑动</p></section>';
    var cards = "";
    entries.forEach(function (e, i) {
      cards += tocCard(e[0], e[1], e[2], i === 0);
    });
    return '<section style="margin:0 20px 32px;">' + head +
      '<section style="overflow-x:auto;white-space:nowrap;padding-bottom:8px;">' + cards + '</section></section>';
  }

  function renderPart(b, c) {
    var t = c.t;
    var num = b.get(0), title = b.get(1), en = b.get(2);
    var small = num === "///" ? "LAST" : "PART";
    return '<section style="padding:0 20px;margin:24px 0 12px;">' +
      '<section style="display:flex;align-items:center;gap:16px;">' +
      '<section style="text-align:center;flex-shrink:0;">' +
      '<p style="margin:0;font-size:28px;color:' + t.BLUE + ';font-weight:900;line-height:1;">' +
      greenLeaf(num, c) + '</p>' +
      '<p style="margin:2px 0 0;font-size:8px;color:' + t.LIGHT + ';font-weight:700;">' + small + '</p></section>' +
      '<span style="width:1px;height:36px;background:' + t.BORDER_GRAY + ';"></span>' +
      '<section style="min-width:0;">' +
      '<p style="margin:0 0 1px;font-size:17px;color:' + t.INK + ';font-weight:900;">' +
      greenLeaf(title, c) + '</p>' +
      '<p style="margin:0;font-size:11px;color:' + t.MUTED + ';font-weight:600;">' +
      greenLeaf(en.toUpperCase(), c) + '</p>' +
      '</section></section></section>';
  }

  function renderSub(b, c) {
    return '<section style="margin:28px 0 14px;"><p style="margin:0;font-size:16px;color:#1c1917;font-weight:800;line-height:1.5;padding-left:10px;border-left:4px solid ' +
      c.t.BLUE + ';">' + greenLeaf(b.get(0), c) + '</p></section>';
  }

  function renderShot(b, c) {
    var t = c.t;
    var src = b.get(0), caption = b.get(1);
    var img = '<section style="text-align:center;margin:8px 0;"><span leaf="">' +
      '<img src="' + c.escAttr(src) +
      '" style="max-width:100%;height:auto;border-radius:8px;display:block;margin:0 auto;" /></span></section>';
    var cap = caption ?
      '<p style="margin:6px 0 12px;font-size:12px;color:' + t.MUTED +
      ';text-align:center;line-height:1.6;">' + greenLeaf(caption, c) + '</p>' : "";
    return img + cap;
  }

  function callout(b, c, bg, border, labelBg, labelFg) {
    var t = c.t;
    var title = b.get(0);
    var paras = b.fields.paras || [];
    var head = title ?
      '<p style="margin:0 0 8px;"><span style="display:inline-block;font-size:11px;color:' + labelFg +
      ';background:' + labelBg + ';font-weight:700;border-radius:4px;padding:2px 10px;">' +
      greenLeaf(title, c) + '</span></p>' : "";
    var body = "";
    paras.forEach(function (p) {
      body += '<p style="margin:0 0 6px;font-size:14px;color:' + t.TEXT + ';line-height:1.8;">' +
        greenLeaf(p, c) + '</p>';
    });
    return '<section style="background:' + bg + ';border-radius:0 8px 8px 0;padding:14px 18px;margin:14px 0;border-left:4px solid ' +
      border + ';">' + head + body + '</section>';
  }
  function renderNote(b, c) {
    return callout(b, c, c.t.GREEN_BG, c.t.BLUE, c.t.BLUE, "#ffffff");
  }
  function renderTip(b, c) { return renderNote(b, c); }
  function renderWarning(b, c) {
    return callout(b, c, c.t.AMBER_BG, c.t.AMBER, c.t.AMBER, "#ffffff");
  }

  function renderStep(b, c) {
    var t = c.t;
    var num = b.get(0), title = b.get(1);
    var paras = b.fields.paras || [];
    var body = "";
    paras.forEach(function (p) {
      body += '<p style="margin:6px 0 0;font-size:14px;color:' + t.TEXT + ';line-height:1.8;">' +
        greenLeaf(p, c) + '</p>';
    });
    return '<section style="margin:18px 0 6px;"><section style="display:flex;align-items:center;gap:10px;">' +
      '<span style="display:inline-block;font-size:10px;color:#ffffff;background:' + t.INK +
      ';font-weight:700;border-radius:12px;padding:2px 8px;">STEP ' + greenLeaf(num, c) + '</span>' +
      '<h4 style="margin:0;font-size:15px;color:' + t.INK + ';font-weight:800;">' +
      greenLeaf(title, c) + '</h4></section>' + body + '</section>';
  }

  function renderCode(b, c) {
    var t = c.t;
    var lang = b.kw.lang || ((b.pos.length) ? b.get(0) : "") || "bash";
    var lines = b.bodyLines;
    function dot(color, mr) {
      return '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' +
        color + ';margin-right:' + mr + ';"></span>';
    }
    var dots = dot("#ff5f56", "6px") + dot("#ffbd2e", "6px") + dot("#27c93f", "8px");
    var head = '<section style="display:flex;align-items:center;background:' + t.TERM_HEAD +
      ';padding:9px 14px;">' + dots + '<span style="font-size:12px;color:#64748b;letter-spacing:1px;">' +
      greenLeaf(lang, c) + '</span></section>';
    var code = "";
    lines.forEach(function (ln) {
      code += '<p style="margin:0;font-size:13px;color:' + t.TERM_FG +
        ';line-height:1.6;font-family:' + t.MONO + ';white-space:pre;">' + WX.esc(ln, false) + '</p>';
    });
    return '<section style="background:' + t.TERM_BG + ';border-radius:8px;margin:0 0 24px;overflow:hidden;">' +
      head + '<section style="padding:11px 14px;overflow-x:auto;">' + code + '</section></section>';
  }

  function splitRow(line) {
    return line.trim().replace(/^\|+/, "").replace(/\|+$/, "").split("|").map(function (x) {
      return x.trim();
    });
  }
  function renderTable(b, c) {
    var t = c.t;
    var rows = b.bodyLines.filter(function (ln) { return ln.trim(); });
    if (!rows.length) return "";
    var header = splitRow(rows[0]);
    var bodyRows = rows.slice(1).filter(function (r) { return !/^[\s|:\-]+$/.test(r); });
    var th = "";
    header.forEach(function (h) {
      th += '<th style="color:#ffffff;background:' + t.BLUE + ';font-weight:700;text-align:left;padding:8px 10px;border-bottom:1px solid ' +
        t.BLUE + ';">' + greenLeaf(h, c) + '</th>';
    });
    var trs = "";
    bodyRows.forEach(function (r) {
      var cells = splitRow(r), tds = "";
      cells.forEach(function (cell, ci) {
        var firstBg = ci === 0 ? ('background:' + t.GREEN_BG2 + ';') : "";
        tds += '<td style="padding:8px 10px;border-bottom:1px solid ' + t.BORDER_GRAY + ';' + firstBg + '">' +
          greenLeaf(cell, c) + '</td>';
      });
      trs += "<tr>" + tds + "</tr>";
    });
    return '<section style="margin:14px 0;"><table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr>' +
      th + '</tr></thead><tbody>' + trs + '</tbody></table></section>';
  }

  function renderCta(b, c) {
    var t = c.t;
    var lead = (b.fields.paras || [""])[0];
    var items = [["👍", "点赞", "#ffffff", "#4b5563"],
                 ["👀", "在看", "#ffffff", "#4b5563"],
                 ["➦", "转发", t.GREEN_BG, t.BLUE]];
    var cols = "";
    items.forEach(function (it) {
      var icon = it[0], label = it[1], bg = it[2], fg = it[3];
      cols += '<section style="flex:1;text-align:center;"><section style="display:flex;width:40px;height:40px;background:' +
        bg + ';border-radius:12px;margin:0 auto 6px;align-items:center;justify-content:center;font-size:18px;color:' +
        fg + ';">' + icon + '</section><span style="font-size:10px;font-weight:600;color:' + fg + ';">' +
        label + '</span></section>';
    });
    var leadH = lead ?
      '<p style="margin:0 0 18px;font-size:13px;color:' + t.INK + ';font-weight:bold;line-height:1.6;">' +
      greenLeaf(lead, c) + '</p>' : "";
    return '<section style="background:radial-gradient(circle,#f9fafb 0%,#f1f5f9 100%);text-align:center;border-radius:16px;margin:24px 0;padding:32px 20px;">' +
      leadH + '<section style="display:flex;gap:12px;">' + cols + '</section>' +
      '<p style="margin:18px 0 0;font-size:10px;color:' + t.MUTED + ';">' +
      greenLeaf("THANKS FOR READING", c) + '</p></section>';
  }

  var ROLES = {
    para: renderPara, issue: renderIssue, toc: renderToc, part: renderPart, sub: renderSub,
    shot: renderShot, note: renderNote, tip: renderTip, warning: renderWarning,
    step: renderStep, code: renderCode, table: renderTable, cta: renderCta
  };
  global.WX.registerTheme({ THEME: THEME, ROLES: ROLES });
})(window);
