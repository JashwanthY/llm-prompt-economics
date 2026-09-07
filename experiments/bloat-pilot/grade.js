// Drive a generated quiz the way a learner would and record what breaks.
// Every check is behavioural: no opinion about appearance.
const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("fs");

const file = process.argv[2];
const errors = [];
const vc = new VirtualConsole()
  .on("jsdomError", e => errors.push("jsdomError: " + e.message))
  .on("error", (...a) => errors.push("console.error: " + String(a[0]).slice(0, 120)));

const dom = new JSDOM(fs.readFileSync(file, "utf8"),
  { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc });

const out = { file, questions: 0, progress_updates: false, submit_gated: false,
  submit_enabled_after: false, score_shown: false, review_shows_correct: false,
  retry_resets: false, js_errors: 0, errors: [] };

const { window } = dom, doc = window.document;
// jsdom lacks these browser APIs; without stubs correct code throws and we
// would be measuring jsdom, not the model.
const noop = () => {};
window.Element.prototype.scrollIntoView = noop;
window.scrollTo = noop; window.scroll = noop; window.alert = noop;
window.matchMedia = window.matchMedia || (q => ({ matches: false, media: q,
  addListener: noop, removeListener: noop, addEventListener: noop,
  removeEventListener: noop, onchange: null }));
window.IntersectionObserver = class { observe(){} unobserve(){} disconnect(){} };
window.ResizeObserver = class { observe(){} unobserve(){} disconnect(){} };
window.requestAnimationFrame = cb => setTimeout(cb, 0);
window.HTMLMediaElement.prototype.play = () => Promise.resolve();

// textContent includes hidden nodes, so a correctly hidden results panel still
// "shows" a score. Read only what a learner could actually see.
const visible = el => {
  if (el.nodeType === 3) return true;
  if (el.hasAttribute && el.hasAttribute("hidden")) return false;
  const st = el.style;
  if (st && (st.display === "none" || st.visibility === "hidden")) return false;
  try {
    const cs = window.getComputedStyle(el);
    if (cs && (cs.display === "none" || cs.visibility === "hidden")) return false;
  } catch (e) {}
  return true;
};
const collect = node => {
  if (node.nodeType === 3) return node.textContent;
  if (node.nodeType !== 1 || !visible(node)) return "";
  return [...node.childNodes].map(collect).join(" ");
};
const txt = () => collect(doc.body).replace(/\s+/g, " ");
const findSubmit = () => [...doc.querySelectorAll("button,input[type=submit]")]
  .find(b => /submit|check|finish|see result|score/i.test(b.textContent || b.value || ""));
const findRetry = () => [...doc.querySelectorAll("button,input[type=button],a")]
  .find(b => /retry|restart|try again|reset|take.*again/i.test(b.textContent || b.value || ""));
const click = el => { try {
  if (el.tagName === "INPUT") { el.checked = true;
    el.dispatchEvent(new window.Event("change", { bubbles: true })); }
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
} catch (e) { errors.push("click: " + e.message); } };

try {
  doc.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true }));

  // one option per question
  const radios = [...doc.querySelectorAll('input[type="radio"]')];
  const groups = {};
  radios.forEach(r => (groups[r.name || "_"] = groups[r.name || "_"] || []).push(r));
  let opts = Object.values(groups).map(g => g[0]);
  if (opts.length < 2) {
    const byQ = {};
    [...doc.querySelectorAll('[data-q],[data-question],[class*="option"]')]
      .filter(e => ["BUTTON","LI","DIV","LABEL"].includes(e.tagName))
      .forEach(e => { const k = e.dataset.q ?? e.dataset.question ??
        e.closest("fieldset,section,[data-q],[data-question]")?.outerHTML?.slice(0,40) ?? "_";
        (byQ[k] = byQ[k] || []).push(e); });
    opts = Object.values(byQ).map(g => g[0]);
  }
  out.questions = opts.length;

  const submit0 = findSubmit();
  out.submit_gated = !!submit0 && (submit0.disabled === true ||
    submit0.getAttribute("aria-disabled") === "true");

  const before = txt();
  if (opts[0]) click(opts[0]);
  out.progress_updates = txt() !== before;          // live progress indicator
  opts.slice(1).forEach(click);

  const submit1 = findSubmit();
  out.submit_enabled_after = !!submit1 && submit1.disabled !== true;
  if (submit1) click(submit1);

  const after = txt();
  const m = after.match(/(?:scored|score[:\s])\s*([0-9]+)\s*(?:\/|out of)\s*([0-9]+)/i);
  out.score_shown = !!m;
  out.review_shows_correct = /correct answer|correct:|the correct|right answer/i.test(after);

  const retry = findRetry();
  if (retry) {
    click(retry);
    const reset = txt();
    const s2 = findSubmit();
    const stillScored = /(?:scored|score[:\s])\s*[0-9]+\s*(?:\/|out of)/i.test(reset);
    const anyChecked = [...doc.querySelectorAll('input[type="radio"]')].some(r => r.checked);
    out.retry_resets = !stillScored && !anyChecked &&
      (!s2 || s2.disabled === true || s2.getAttribute("aria-disabled") === "true");
  }
} catch (e) { errors.push("fatal: " + e.message); }

out.js_errors = errors.length;
out.errors = errors.slice(0, 2);
const checks = ["progress_updates","submit_gated","submit_enabled_after",
                "score_shown","review_shows_correct","retry_resets"];
out.passed = checks.filter(c => out[c]).length;
out.total = checks.length;
out.clean = out.js_errors === 0;
console.log(JSON.stringify(out));
