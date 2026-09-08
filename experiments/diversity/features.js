/* Render a generated page in jsdom and dump the raw material the diversity
 * metric is computed from. No judgement here -- just the tag sequence, the
 * CSS text and a few element counts. analyze.py does the rest.
 * Usage: node features.js <file.html>   -> one JSON line */
const fs = require("fs");
const { JSDOM, VirtualConsole } = require("jsdom");
const file = process.argv[2];
const dom = new JSDOM(fs.readFileSync(file, "utf8"), {
  runScripts: "dangerously", pretendToBeVisual: true,
  virtualConsole: new VirtualConsole(),
});
const { window } = dom, doc = window.document;
window.Element.prototype.scrollIntoView = () => {};
window.scrollTo = () => {}; window.alert = () => {};
window.matchMedia = window.matchMedia || (() => ({ matches: false, addListener(){},
  removeListener(){}, addEventListener(){}, removeEventListener(){} }));
window.requestAnimationFrame = cb => setTimeout(cb, 0);
window.ResizeObserver = window.ResizeObserver || class { observe(){} disconnect(){} };
window.IntersectionObserver = window.IntersectionObserver || class { observe(){} disconnect(){} };
// canvas charts: give getContext a no-op 2d context so drawing code does not throw
window.HTMLCanvasElement.prototype.getContext = () => new Proxy({}, {
  get: (_, k) => (k === "canvas" ? null : () => ({})) });
try { doc.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true })); } catch (e) {}
try { window.dispatchEvent(new window.Event("load")); } catch (e) {}

const tags = [];
(function walk(n, d) {
  for (const c of n.children) { tags.push(c.tagName.toLowerCase() + ":" + d); walk(c, d + 1); }
})(doc.body, 0);
const css = [...doc.querySelectorAll("style")].map(s => s.textContent).join("\n")
  + "\n" + [...doc.querySelectorAll("[style]")].map(e => e.getAttribute("style")).join(";\n");
const count = t => doc.querySelectorAll(t).length;
console.log(JSON.stringify({
  file, tags, css,
  counts: Object.fromEntries(["svg","canvas","table","aside","nav","header","footer",
    "section","article","ul","ol","h1","h2","h3","button"].map(t => [t, count(t)])),
  text_chars: (doc.body.textContent || "").replace(/\s+/g, " ").trim().length,
}));
