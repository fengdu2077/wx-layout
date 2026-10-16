/* ============================================================
 * wx-layout 浏览器内核 core.js（wx_core.py 的忠实 JS 移植）
 * 纯标准浏览器环境、离线、无依赖。负责：
 *   解析 md/:::模块 → IR；leaf/inline 微信适配；主题路由与 fallback；渲染。
 * 主题通过 window.WX_THEMES 注册（见 themes/*.js）。
 * ============================================================ */
(function (global) {
  "use strict";

  var DEFAULT_CONTAINERS = ["issue", "quote", "author", "card", "gallery", "callout",
    "faq", "timeline", "compare", "steps", "highlights", "profile", "toc", "stats",
    "keyvalue", "note", "tip", "warning", "code", "table", "cta", "audio"];
  var SINGLETON_ROLES = ["part", "sub", "shot", "video", "end", "divider", "image"];

  /* ---------- HTML 转义（对应 Python html.escape） ---------- */
  function esc(s, quote) {
    s = String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    if (quote) s = s.replace(/"/g, "&quot;");
    return s;
  }

  /* ---------- IR Block ---------- */
  function Block(role, pos, kw, bodyLines, bullet) {
    this.role = role;
    this.pos = pos || [];
    this.kw = kw || {};
    this.bodyLines = bodyLines || [];
    this.bullet = !!bullet;
    this.blocks = [];
    this.fields = {};
  }
  Block.prototype.get = function (i, d) {
    return i < this.pos.length ? this.pos[i] : (d === undefined ? "" : d);
  };

  /* ---------- 正则 ---------- */
  var IMG_RE = /^!\[([^\]]*)\]\(([^)\s]+)\)\s*$/;
  var HEADING_RE = /^(#{1,6})\s+(.*)$/;
  var URL_RE = /^(https?:\/\/\S+|[\w\-./\\]+\.(?:png|jpe?g|gif|webp|bmp))\s*$/i;
  var LINK_RE_G = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)/g;
  var LINK_ONLY_RE = /^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)\s*$/;
  var LIST_LINE_RE = /^\s*[-*]\s+/;

  /* ---------- body 元素解析 ---------- */
  function parseBodyElements(lines) {
    var elements = [];
    var paras = [], buf = [];
    lines.concat([""]).forEach(function (ln) {
      if (ln.trim() === "") {
        if (buf.length) { paras.push(buf); buf = []; }
      } else buf.push(ln);
    });
    if (buf.length) paras.push(buf);

    paras.forEach(function (plines) {
      if (plines.every(function (x) { return LIST_LINE_RE.test(x); })) {
        var items = plines.map(function (x) {
          return x.replace(LIST_LINE_RE, "").trim();
        });
        elements.push({ type: "list", items: items });
        return;
      }
      plines.forEach(function (x) {
        var s = x.trim(), m;
        m = s.match(IMG_RE);
        if (m) { elements.push({ type: "image", alt: m[1], src: m[2] }); return; }
        m = s.match(HEADING_RE);
        if (m) { elements.push({ type: "heading", level: m[1].length, text: m[2].trim() }); return; }
        if (URL_RE.test(s)) { elements.push({ type: "image", alt: "", src: s }); return; }
        m = s.match(LINK_ONLY_RE);
        if (m) { elements.push({ type: "link", text: m[1], href: m[2] }); return; }
        elements.push({ type: "para", text: s });
      });
    });

    var links = [];
    elements.forEach(function (e) {
      if (e.type === "link") links.push({ text: e.text, href: e.href });
      if (e.type === "para") {
        var g, re = new RegExp(LINK_RE_G.source, "g");
        while ((g = re.exec(e.text)) !== null)
          links.push({ text: g[1], href: g[2] });
      }
    });
    var fields = {
      images: elements.filter(function (e) { return e.type === "image"; }).map(function (e) { return e.src; }),
      paras: elements.filter(function (e) { return e.type === "para"; }).map(function (e) { return e.text; }),
      headings: elements.filter(function (e) { return e.type === "heading"; }).map(function (e) { return e.text; }),
      lists: elements.filter(function (e) { return e.type === "list"; }).map(function (e) { return e.items; }),
      links: links
    };
    fields.image = fields.images[0] || "";
    fields.link = fields.links[0] ? fields.links[0].href : "";
    fields.heading = fields.headings[0] || "";
    return [elements, fields];
  }

  /* ---------- 指令头解析 ---------- */
  function parseHead(head) {
    var pos = [], kw = {};
    head.split("|").map(function (x) { return x.trim(); }).forEach(function (part) {
      if (!part) return;
      var m = part.match(/^([A-Za-z_][\w\-]*)\s*=\s*(.+)$/);
      if (m) kw[m[1]] = m[2].trim();
      else pos.push(part);
    });
    return [pos, kw];
  }

  /* ---------- 顶层解析 ---------- */
  function parse(mdText, containers) {
    mdText = mdText.replace(/<!--[\s\S]*?-->/g, "");  // 剥离 HTML 注释
    var lines = mdText.split(/\r?\n/);
    var out = [], i = 0;
    while (i < lines.length) {
      var s = lines[i].trim();
      if (!s) { i++; continue; }

      if (s.indexOf(":::") !== 0) {
        var buf = [];
        while (i < lines.length && lines[i].trim().indexOf(":::") !== 0) {
          buf.push(lines[i]); i++;
        }
        var text = buf.join("\n");
        var chunks = text.split(/\n\s*\n/).map(function (p) { return p.trim(); })
          .filter(function (p) { return p; });
        chunks.forEach(function (chunk) {
          var clines = chunk.split("\n").filter(function (ln) { return ln.trim(); });
          var items = clines.filter(function (ln) { return LIST_LINE_RE.test(ln); });
          if (items.length && items.length === clines.length) {
            items.forEach(function (it) {
              var b = new Block("para", null, null, null, true);
              var pf = parseBodyElements([it]);
              b.blocks = pf[0]; b.fields = pf[1];
              b.fields.text = it.replace(LIST_LINE_RE, "").trim();
              out.push(b);
            });
          } else {
            var b = new Block("para");
            var pf = parseBodyElements(clines);
            b.blocks = pf[0]; b.fields = pf[1];
            b.fields.text = clines.map(function (x) { return x.trim(); }).join(" ");
            out.push(b);
          }
        });
        continue;
      }

      var m = s.match(/^:::([A-Za-z_][\w\-]*)\s*(.*)$/);
      if (!m) { i++; continue; }
      var role = m[1], head = m[2];
      var ph = parseHead(head), pos = ph[0], kw = ph[1];

      if (containers.indexOf(role) >= 0) {
        var body = [], j = i + 1;
        while (j < lines.length && lines[j].trim() !== ":::") {
          body.push(lines[j]); j++;
        }
        var b = new Block(role, pos, kw, body);
        var pf = parseBodyElements(body);
        b.blocks = pf[0]; b.fields = pf[1];
        out.push(b);
        i = j + 1;
      } else {
        out.push(new Block(role, pos, kw));
        i++;
      }
    }
    return out;
  }

  /* ---------- 渲染引擎 ---------- */
  function Engine(theme) {
    this.theme = theme;
    this.t = (theme.THEME.tokens) || {};
  }
  Engine.prototype.inline = function (text) {
    text = esc(text, false);
    var stash = {};
    function keep(frag) {
      var k = "\x00" + Object.keys(stash).length + "\x00";
      stash[k] = frag; return k;
    }
    var self = this;
    text = text.replace(/\*\*([^*]+)\*\*/g, function (mm, p1) {
      return keep('<span textstyle="" style="color:' +
        (self.t.BOLD_INK || "rgb(17,24,39)") + ';font-weight:600;">' + p1 + "</span>");
    });
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, function (mm, p1, p2) {
      return keep('<a href="' + p2 + '" style="color:' +
        (self.t.BLUE || "#2563eb") + ';text-decoration:underline;">' + p1 + "</a>");
    });
    Object.keys(stash).forEach(function (k) { text = text.split(k).join(stash[k]); });
    return text;
  };
  Engine.prototype.leaf = function (text) {
    return '<span leaf="">' + this.inline(text) + "</span>";
  };
  Engine.prototype.escAttr = function (text) { return esc(text, true); };
  Engine.prototype.containers = function () {
    var extra = this.theme.THEME.containers || [];
    var set = {};
    DEFAULT_CONTAINERS.concat(extra).forEach(function (r) {
      if (SINGLETON_ROLES.indexOf(r) < 0) set[r] = 1;
    });
    return Object.keys(set);
  };
  Engine.prototype.render = function (mdText) {
    var blocks = parse(mdText, this.containers());
    var roles = this.theme.ROLES || {};
    var pieces = [];
    for (var i = 0; i < blocks.length; i++) {
      var b = blocks[i], fn = roles[b.role];
      if (fn) pieces.push(fn(b, this));
      else if (this.theme.fallback) pieces.push(this.theme.fallback(b, this));
      else pieces.push(this.defaultFallback(b));
    }
    var t = this.t;
    return '<section style="max-width:677px;margin:0 auto;padding:8px 16px;box-sizing:border-box;' +
      'background:' + (t.PAGE_BG || "#ffffff") + ';color:' + (t.TEXT || "#374151") +
      ';font-family:' + (t.FONT || "") + ';line-height:1.75;">' + pieces.join("") + "</section>";
  };
  Engine.prototype.videoPlaceholder = function (b) {
    // 视频本身是素材库引用的播放框、无法用网页样式生成；但可放进卡片框：上方视频位（后台插入视频），
    // 下方保留标题/说明。粘贴后视频留在框内、下方文字不丢失。
    var title = (b.get && b.get(0)) || b.pos[0] || "";
    var desc = (b.get && b.get(1)) || b.pos[1];
    var slot = '<section style="width:100%;aspect-ratio:16/9;min-height:180px;background:#0f172a;' +
      'display:flex;flex-direction:column;align-items:center;justify-content:center;' +
      'text-align:center;padding:16px;box-sizing:border-box;">' +
      '<p style="margin:0;font-size:14px;font-weight:800;color:#e2e8f0;letter-spacing:0;">' +
      "▶ 视频位置｜在此插入视频</p>" +
      '<p style="margin:8px 0 0;font-size:11px;line-height:1.7;color:#94a3b8;letter-spacing:0;">' +
      "将光标放本框，点后台工具栏「视频」，从素材库上传/选择对应视频，替换本提示。</p></section>";
    var cap = "";
    if (title) cap += '<p style="margin:12px 14px 0;font-size:14px;font-weight:800;color:#1e293b;' +
      'letter-spacing:0;">' + this.leaf(title) + "</p>";
    if (desc) cap += '<p style="margin:5px 14px 13px;font-size:12px;line-height:1.7;color:#64748b;' +
      'letter-spacing:0;">' + this.leaf(desc) + "</p>";
    return '<section style="margin:24px 0;"><section style="border:1px solid #e2e8f0;' +
      'border-radius:12px;overflow:hidden;background:#ffffff;">' + slot + cap + "</section></section>";
  };
  Engine.prototype.defaultFallback = function (b) {
    if (b.role === "video") {
      return this.videoPlaceholder(b);
    }
    if (b.role === "para") {
      var text = (b.bullet ? "• " : "") + (b.fields.text || "");
      return '<section style="margin-top:20px;"><p style="margin:0;font-size:15px;' +
        'line-height:1.95;text-align:justify;color:' + (this.t.TEXT || "#374151") +
        ';letter-spacing:0;">' + this.leaf(text) + "</p></section>";
    }
    var txt = (b.fields.paras || []).join(" ") || b.pos.join(" ");
    return '<section style="margin-top:16px;padding:10px 12px;background:#f8fafc;' +
      'border-radius:8px;"><p style="margin:0;font-size:14px;color:' + (this.t.TEXT || "#374151") +
      ';">' + (txt ? "" : "[" + b.role + "] ") + this.leaf(txt) + "</p></section>";
  };

  /* ---------- 主题注册与解析 ---------- */
  var THEMES = {};
  function registerTheme(theme) { THEMES[theme.THEME.name] = theme; }
  function listThemes() {
    return Object.keys(THEMES).map(function (name) {
      return { name: name, label: THEMES[name].THEME.label || name };
    });
  }
  function getTheme(name) {
    if (THEMES[name]) return THEMES[name];
    var keys = Object.keys(THEMES);
    for (var i = 0; i < keys.length; i++) {
      var th = THEMES[keys[i]];
      if (th.THEME.label === name) return th;
    }
    throw new Error("主题不存在：" + name);
  }

  global.WX = {
    Block: Block, Engine: Engine, parse: parse,
    esc: esc, registerTheme: registerTheme,
    listThemes: listThemes, getTheme: getTheme
  };
})(window);
