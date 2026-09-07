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
  const scenario = (label, q, coupon) => {
    setQ(q); if (coupon !== undefined) applyCoupon(coupon);
    const e = price(q, coupon);
    check(label, () => near(num("out-subtotal"), e.sub) && near(num("out-total"), e.total));
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
  put("A1", "99");
  const undone = click("app-undo");
  check("undo reverts the last edit", () => undone && out("A1") === "10.00");
}

/* ---------------- form ---------------- */
function gradeForm() {
  const F = { u: "app-username", e: "app-email", p: "app-password",
              c: "app-confirm", d: "app-dob", h: "app-phone" };
  const err = k => textOf("err-" + k);
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
  check("all errors show simultaneously", () =>
    err("username") !== "" && err("email") !== "" && err("phone") !== "");
  check("submit disabled while invalid", () => $("app-submit") && $("app-submit").disabled === true);
  fill({});
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
