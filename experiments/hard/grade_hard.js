/* Behavioural graders for the three hard tasks.
 *
 * Every earlier measurement bug in this study came from a check that could not
 * observe the behaviour it claimed to test. The defence here is a reference
 * implementation of each task, hand-written and known correct: the grader must
 * score it 10/10 before any model output is graded. See reference/.
 *
 * Usage: node grade_hard.js <task> <file.html>
 */
const fs = require("fs");
const { JSDOM } = require("jsdom");

const [, , task, file] = process.argv;
const errors = [];
const dom = new JSDOM(fs.readFileSync(file, "utf8"), {
  runScripts: "dangerously", pretendToBeVisual: true,
  virtualConsole: new (require("jsdom").VirtualConsole)()
    .on("jsdomError", e => errors.push("jsdomError:" + e.message)),
});
const { window } = dom, doc = window.document;
// jsdom lacks these; without stubs correct code throws and we measure jsdom.
window.Element.prototype.scrollIntoView = () => {};
window.scrollTo = () => {}; window.alert = () => {};
window.matchMedia = window.matchMedia || (() => ({ matches: false,
  addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} }));
window.requestAnimationFrame = cb => setTimeout(cb, 0);
window.URL.createObjectURL = () => "blob:stub";

const $ = id => doc.getElementById(id);
const norm = s => (s || "").replace(/\s+/g, " ").trim();
const textOf = id => norm(($(id) || {}).textContent);
const num = id => { const t = textOf(id).replace(/[^0-9.\-]/g, ""); return t === "" ? NaN : +t; };
const set = (id, v) => { const el = $(id); if (!el) return false;
  el.value = v;
  el.dispatchEvent(new window.Event("input", { bubbles: true }));
  el.dispatchEvent(new window.Event("change", { bubbles: true }));
  el.dispatchEvent(new window.Event("keyup", { bubbles: true }));
  return true; };
const click = id => { const el = $(id); if (!el) return false;
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true })); return true; };

const checks = [];
const check = (name, fn) => { let pass = false;
  try { pass = !!fn(); } catch (e) { errors.push(name + ":" + e.message); }
  checks.push({ name, pass }); };

try { doc.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true })); } catch (e) {}

/* ---------------- cart ---------------- */
function gradeCart() {
  const P = { widget: 24.99, gadget: 79.50, doohickey: 12.25 };
  const r2 = x => Math.round((x + Number.EPSILON) * 100) / 100;
  // Reference pricing, implemented straight from the stated rules.
  function price(q, coupon) {
    const sub = r2(q.widget * P.widget + q.gadget * P.gadget + q.doohickey * P.doohickey);
    const tierPct = sub >= 500 ? 0.15 : sub >= 250 ? 0.10 : sub >= 100 ? 0.05 : 0;
    const c = (coupon || "").toUpperCase();
    let disc = r2(sub * tierPct);
    if (c === "SAVE10") disc = Math.max(disc, r2(sub * 0.10));   // never both
    if (c === "BULK5") disc = r2(disc + 5);                       // stacks
    disc = Math.min(disc, sub);
    const post = r2(sub - disc);
    const ship = (c === "FREESHIP" || post >= 75) ? 0 : 8;
    const tax = r2(post * 0.0825);
    return { sub, disc, ship, tax, total: r2(post + ship + tax) };
  }
  const near = (a, b) => Math.abs(a - b) <= 0.02;
  const setQ = q => { set("qty-widget", q.widget); set("qty-gadget", q.gadget);
                      set("qty-doohickey", q.doohickey); };
  const applyCoupon = c => { set("app-coupon", c); click("app-apply"); };
  // Each scenario asserts all five outputs separately. Checking only subtotal
  // and total lets a wrong split between discount, shipping and tax cancel out
  // and score as correct.
  const scenario = (label, q, coupon) => {
    setQ(q); if (coupon !== undefined) applyCoupon(coupon);
    const e = price(q, coupon);
    check(label + " subtotal", () => near(num("out-subtotal"), e.sub));
    check(label + " discount", () => near(num("out-discount"), e.disc));
    check(label + " shipping", () => near(num("out-shipping"), e.ship));
    check(label + " tax", () => near(num("out-tax"), e.tax));
    check(label + " total", () => near(num("out-total"), e.total));
  };
  check("renders all five outputs", () =>
    ["subtotal", "discount", "shipping", "tax", "total"].every(k => $("out-" + k)));
  scenario("no discount tier", { widget: 1, gadget: 0, doohickey: 0 });
  scenario("5% tier", { widget: 0, gadget: 2, doohickey: 0 });
  scenario("10% tier", { widget: 0, gadget: 4, doohickey: 0 });
  scenario("15% tier", { widget: 0, gadget: 7, doohickey: 0 });
  scenario("SAVE10 beats no tier", { widget: 2, gadget: 0, doohickey: 0 }, "SAVE10");
  scenario("SAVE10 does not stack with a bigger tier",
           { widget: 0, gadget: 7, doohickey: 0 }, "SAVE10");
  scenario("BULK5 stacks with tier", { widget: 0, gadget: 4, doohickey: 0 }, "BULK5");
  // Boundaries, where an off-by-one in a threshold shows up and nowhere else.
  scenario("just below the 5% tier (99.96)", { widget: 4, gadget: 0, doohickey: 0 }, "");
  scenario("just below the 10% tier (238.50)", { widget: 0, gadget: 3, doohickey: 0 }, "");
  scenario("just over the 10% tier (250.75)", { widget: 0, gadget: 3, doohickey: 1 }, "");
  scenario("just below free shipping (74.97)", { widget: 3, gadget: 0, doohickey: 0 }, "");
  scenario("just over free shipping (85.75)", { widget: 0, gadget: 0, doohickey: 7 }, "");
  scenario("BULK5 with no tier", { widget: 2, gadget: 0, doohickey: 0 }, "BULK5");
  scenario("SAVE10 beats a smaller tier", { widget: 0, gadget: 0, doohickey: 9 }, "SAVE10");
  scenario("empty cart", { widget: 0, gadget: 0, doohickey: 0 }, "");
  setQ({ widget: 0, gadget: 4, doohickey: 0 }); applyCoupon("save10");
  check("coupon codes are case-insensitive", () =>
    near(num("out-discount"), price({ widget: 0, gadget: 4, doohickey: 0 }, "SAVE10").disc));
  setQ({ widget: 1, gadget: 0, doohickey: 0 }); applyCoupon("FREESHIP");
  check("FREESHIP zeroes shipping", () => num("out-shipping") === 0);
  setQ({ widget: 1, gadget: 0, doohickey: 0 }); applyCoupon("NOPE123");
  check("invalid coupon reports exactly", () => textOf("out-coupon-error") === "Invalid coupon");
  setQ({ widget: 0, gadget: 0, doohickey: 0 });
  set("qty-widget", "-3"); set("qty-gadget", "abc");
  check("junk quantities clamp to zero without throwing", () => num("out-subtotal") === 0);
}

/* ---------------- sheet ---------------- */
function gradeSheet() {
  const out = a => textOf("out-" + a);
  const put = (a, v) => set("cell-" + a, v);
  check("renders a 4x4 grid", () =>
    ["A1", "B2", "C3", "D4"].every(a => $("cell-" + a) && $("out-" + a)));
  put("A1", "5");
  check("literal formats to 2dp", () => out("A1") === "5.00");
  put("B1", "=A1*2");
  check("reference and multiply", () => out("B1") === "10.00");
  put("C1", "=1+2*3");
  check("* binds tighter than +", () => out("C1") === "7.00");
  put("C2", "=(1+2)*3");
  check("parentheses", () => out("C2") === "9.00");
  put("A2", "3"); put("A3", "2"); put("A4", "1"); put("D1", "=SUM(A1:A4)");
  check("SUM over a range", () => out("D1") === "11.00");
  put("A1", "10");
  check("transitive recompute", () => out("B1") === "20.00" && out("D1") === "16.00");
  put("B4", "=1/3");
  check("rounds to 2dp", () => out("B4") === "0.33");
  put("C4", "=1/0");
  check("division by zero", () => out("C4") === "#DIV/0");
  put("D2", "=Z9");
  check("out-of-range reference", () => out("D2") === "#REF");
  put("D3", "=D4"); put("D4", "=D3");
  check("cycle detected, no hang", () => out("D3") === "#CYCLE" && out("D4") === "#CYCLE");
  put("B2", "=SUM(A1:B2)");
  check("SUM over a 2D range self-referencing is a cycle", () => out("B2") === "#CYCLE");
  put("B2", "");
  put("C3", "=A1+A2*2");
  check("precedence across a reference", () => out("C3") === "16.00");
  put("A1", "10");
  put("B3", "=((1+2)*(3+4))");
  check("nested parentheses", () => out("B3") === "21.00");
  put("D1", "");
  put("D1", "=A1 + A2");
  check("spaces inside a formula", () => out("D1") === "13.00");
  put("C1", "=-4+1");
  check("unary minus", () => out("C1") === "-3.00");
  put("A4", "notanumber");
  check("non-numeric literal reads as 0", () => out("A4") === "0.00");
  put("A4", "1");
  put("B1", "=C4+1");
  check("#DIV/0 propagates through arithmetic", () => out("B1") === "#DIV/0");
  put("B1", "=D2+1");
  check("#REF propagates through arithmetic", () => out("B1") === "#REF");
  put("B1", "=A1*2");
  put("C2", "=C2");
  check("self-reference is a cycle", () => out("C2") === "#CYCLE");
  put("C2", "=(1+2)*3");
  put("A1", "99");
  const undone = click("app-undo");
  check("undo reverts the last edit", () => undone && out("A1") === "10.00");
  put("A1", "7"); put("A2", "8");
  click("app-undo"); click("app-undo");
  check("repeated undo walks further back", () => out("A1") === "10.00" && out("A2") === "3.00");
}

/* ---------------- form ---------------- */
function gradeForm() {
  const F = { u: "app-username", e: "app-email", p: "app-password",
              c: "app-confirm", d: "app-dob", h: "app-phone" };
  // Returns null, not "", when the span is absent. textOf() cannot distinguish
  // "this field is valid" from "this element does not exist", so an empty stub
  // page scored 6/31 by having no error spans at all.
  const err = k => $("err-" + k) ? norm($("err-" + k).textContent) : null;
  const fill = o => { set(F.u, o.u ?? "goodname"); set(F.e, o.e ?? "a@b.com");
    set(F.p, o.p ?? "Abcdefg1!x"); set(F.c, o.c ?? (o.p ?? "Abcdefg1!x"));
    set(F.d, o.d ?? "1990-01-01"); set(F.h, o.h ?? "5551234567"); };
  check("renders all six error spans", () =>
    ["username", "email", "password", "confirm", "dob", "phone"].every(k => $("err-" + k)));
  fill({ u: "" });
  check("empty username", () => err("username") === "Username is required");
  fill({ u: "ab" });
  check("short username", () => err("username") === "Username must be 3-16 characters");
  fill({ u: "bad user!" });
  check("username charset", () =>
    err("username") === "Username may only contain letters, digits and underscore");
  fill({ u: "admin" });
  check("taken username", () => err("username") === "Username is already taken");
  fill({ e: "not-an-email" });
  check("invalid email", () => err("email") === "Enter a valid email address");
  fill({ p: "Ab1!", c: "Ab1!" });
  check("short password reports length only", () =>
    err("password") === "Password must be at least 10 characters");
  fill({ p: "abcdefghij!", c: "abcdefghij!" });
  check("password lists only missing classes", () =>
    err("password") === "Password needs: uppercase, digit");
  fill({ p: "Abcdefg1!x", c: "different1X!" });
  check("confirm mismatch", () => err("confirm") === "Passwords do not match");
  fill({ d: "2015-01-01" });
  check("under 18", () => err("dob") === "You must be at least 18");
  fill({ h: "12345" });
  check("bad phone", () => err("phone") === "Enter a 10-digit phone number");
  fill({ u: "", e: "bad", h: "1" });
  // Must be a non-empty string. `!== ""` alone is satisfied by null, so a page
  // with no error spans passed this by having nothing at all.
  check("all errors show simultaneously", () =>
    ["username", "email", "phone"].every(k => typeof err(k) === "string" && err(k) !== ""));
  check("submit disabled while invalid", () => $("app-submit") && $("app-submit").disabled === true);
  fill({ u: "abc" });
  check("username of exactly 3 is valid", () => err("username") === "");
  fill({ u: "a".repeat(16) });
  check("username of exactly 16 is valid", () => err("username") === "");
  fill({ u: "a".repeat(17) });
  check("username of 17 is too long", () => err("username") === "Username must be 3-16 characters");
  fill({ u: "Admin" });
  check("taken check is case-insensitive", () => err("username") === "Username is already taken");
  fill({ e: "a@@b.com" });
  check("email with two at-signs", () => err("email") === "Enter a valid email address");
  fill({ e: "a@bcom" });
  check("email domain without a dot", () => err("email") === "Enter a valid email address");
  fill({ e: "@b.com" });
  check("email with empty local part", () => err("email") === "Enter a valid email address");
  fill({ p: "Abcdefg1!x", c: "Abcdefg1!x" });
  check("password of exactly 10 is valid", () => err("password") === "");
  fill({ p: "Abcdefghij1", c: "Abcdefghij1" });
  check("password missing only a symbol", () => err("password") === "Password needs: symbol");
  fill({ p: "ABCDEFGHIJ1!", c: "ABCDEFGHIJ1!" });
  check("password missing only lowercase", () => err("password") === "Password needs: lowercase");
  fill({ p: "abcdefghijkl", c: "abcdefghijkl" });
  check("password missing uppercase, digit and symbol", () =>
    err("password") === "Password needs: uppercase, digit, symbol");
  fill({ c: "" });
  check("empty confirm mismatches", () => err("confirm") === "Passwords do not match");
  const d18 = new Date(); d18.setFullYear(d18.getFullYear() - 18);
  fill({ d: d18.toISOString().slice(0, 10) });
  check("exactly 18 today is allowed", () => err("dob") === "");
  const d18m = new Date(); d18m.setFullYear(d18m.getFullYear() - 18); d18m.setDate(d18m.getDate() + 1);
  fill({ d: d18m.toISOString().slice(0, 10) });
  check("one day short of 18 is rejected", () => err("dob") === "You must be at least 18");
  fill({ h: "(555) 123-4567" });
  check("phone with punctuation is accepted", () => err("phone") === "");
  fill({ h: "55512345678" });
  check("eleven digits is rejected", () => err("phone") === "Enter a 10-digit phone number");
  fill({});
  check("all error spans are empty when valid", () =>
    ["username", "email", "password", "confirm", "dob", "phone"].every(k => err(k) === ""));
  check("submit enabled when all valid", () => $("app-submit") && $("app-submit").disabled === false);
}

try { ({ cart: gradeCart, sheet: gradeSheet, form: gradeForm })[task](); }
catch (e) { errors.push("fatal:" + e.message); }

const passed = checks.filter(c => c.pass).length;
console.log(JSON.stringify({
  file, task, passed, total: checks.length,
  failed: checks.filter(c => !c.pass).map(c => c.name),
  js_errors: errors.length, errors: errors.slice(0, 2),
}));
