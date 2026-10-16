/* web_parity.js · 用 Node 跑浏览器内核，输出各示例×主题的渲染结果供与 Python 对比
 * 用法：node tools/web_parity.js   （在项目根执行；输出 tools/analysis/web_parity.json） */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const ROOT = process.cwd();

global.window = global;
function load(rel) {
  vm.runInThisContext(fs.readFileSync(path.join(ROOT, rel), "utf8"), { filename: rel });
}
load("web/core.js");
load("web/themes/blue-editorial.js");
load("web/themes/warm-horizontal.js");
load("web/themes/warm-brown-journal.js");
load("web/themes/green-tech.js");
load("web/samples.js");

const themeNames = WX.listThemes().map(t => t.name);
const out = {};
WX_SAMPLES.forEach((s, i) => {
  themeNames.forEach(name => {
    const eng = new WX.Engine(WX.getTheme(name));
    out[i + "|" + name] = eng.render(s.md);
  });
});
const dest = path.join(ROOT, "tools", "analysis", "web_parity.json");
fs.writeFileSync(dest, JSON.stringify(out), "utf8");
console.log("JS 侧已输出 " + Object.keys(out).length + " 组 → tools/analysis/web_parity.json");
