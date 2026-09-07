// Drive the data table the way a user would. Behavioural checks only.
const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("fs");
const file = process.argv[2];
const errors = [];
const vc = new VirtualConsole()
  .on("jsdomError", e => errors.push("jsdomError: " + e.message))
  .on("error", (...a) => errors.push("err: " + String(a[0]).slice(0, 100)));
const dom = new JSDOM(fs.readFileSync(file, "utf8"),
  { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc });
const { window } = dom, doc = window.document;
const noop = () => {};
window.Element.prototype.scrollIntoView = noop;
window.scrollTo = noop; window.alert = noop;
window.URL.createObjectURL = window.URL.createObjectURL || (() => "blob:stub");
window.URL.revokeObjectURL = noop;
window.matchMedia = window.matchMedia || (q => ({ matches:false, media:q,
  addListener:noop, removeListener:noop, addEventListener:noop, removeEventListener:noop }));
window.requestAnimationFrame = cb => setTimeout(cb, 0);
window.HTMLAnchorElement.prototype.click = function(){ this.__clicked = true; };

const out = { file, renders:false, sorts:false, sort_indicator:false, filters:false,
  active_filter:false, paginates:false, prev_disabled_p1:false, count_line:false,
  export_present:false, export_fires:false, js_errors:0, errors:[] };
const rows = () => [...doc.querySelectorAll("tbody tr")].filter(r => r.offsetParent !== null || true);
const cells = () => rows().map(r => (r.cells[0]||{}).textContent?.trim() || "");
const txt = () => (doc.body.textContent||"").replace(/\s+/g," ");
const click = el => { try { el.dispatchEvent(new window.MouseEvent("click",{bubbles:true})); }
                      catch(e){ errors.push("click:"+e.message); } };

try {
  doc.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles:true }));
  const before = cells();
  out.renders = before.length > 0;
  out.paginates = before.length <= 10 && before.length > 0;

  // Click the sort CONTROL, not the <th>. Every generated file puts the click
  // handler on a <button data-column> inside the header cell; clicking the <th>
  // does not reach it, because events propagate up, not down. The first version
  // of this check clicked ths[0] and so scored sorting as broken in 24/24 runs
  // -- a grader artifact, not a model failure.
  const ths = [...doc.querySelectorAll("th")];
  const sortCtl = doc.querySelector("th button, th [data-column], th [data-sort], th [data-key]")
                  || ths[0];
  if (sortCtl) { click(sortCtl); const after = cells();
    out.sorts = after.length > 0 && after.join("|") !== before.join("|"); }
  out.sort_indicator = /[▲▼↑↓]|aria-sort|sort-(asc|desc)/i.test(doc.body.innerHTML);

  const box = doc.querySelector('input[type="text"],input[type="search"],input:not([type])');
  if (box) { const n0 = rows().length; box.value = "Engineering";
    box.dispatchEvent(new window.Event("input",{bubbles:true}));
    box.dispatchEvent(new window.Event("keyup",{bubbles:true}));
    out.filters = rows().length !== n0 || /Engineering/.test(txt());
    box.value = ""; box.dispatchEvent(new window.Event("input",{bubbles:true})); }

  // Compare the RESULT-SET SIZE, not the rows visible on page 1. The table
  // paginates at 10/page, so filtering 24 records down to 19 leaves page 1
  // showing 10 rows either way: a row-count comparison can never observe a
  // working filter. The "of N" total in the count line does move, so read that,
  // and fall back to comparing row identity when no count line exists.
  const totalOf = () => { const m = /of\s+(\d+)/i.exec(txt()); return m ? +m[1] : null; };
  const cb = doc.querySelector('input[type="checkbox"]');
  if (cb) { const t0 = totalOf(), k0 = cells().join("|"), n0 = rows().length;
    cb.checked = true;
    cb.dispatchEvent(new window.Event("change",{bubbles:true}));
    const t1 = totalOf();
    out.active_filter = (t0 !== null && t1 !== null) ? t1 !== t0
                      : (rows().length !== n0 || cells().join("|") !== k0);
    cb.checked = false; cb.dispatchEvent(new window.Event("change",{bubbles:true})); }

  const prev = [...doc.querySelectorAll("button")].find(b => /prev/i.test(b.textContent));
  out.prev_disabled_p1 = !!prev && prev.disabled === true;
  out.count_line = /showing\s+\d+\s*[-–—to]+\s*\d+\s+of\s+\d+/i.test(txt());

  const exp = [...doc.querySelectorAll("button,a")].find(b => /export|download|csv/i.test(b.textContent));
  out.export_present = !!exp;
  if (exp) { const n = errors.length; click(exp); out.export_fires = errors.length === n; }
} catch(e){ errors.push("fatal:"+e.message); }

out.js_errors = errors.length; out.errors = errors.slice(0,2);
const C = ["renders","sorts","sort_indicator","filters","active_filter","paginates",
           "prev_disabled_p1","count_line","export_present","export_fires"];
out.passed = C.filter(c => out[c]).length; out.total = C.length;
console.log(JSON.stringify(out));
