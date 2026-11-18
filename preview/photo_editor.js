/* Photo swap and placement mode for the preview.
   An editor of the preview can, for every photo on the site:
     drop a new photo onto it (or pick one),
     drag inside the photo to move it in its frame,
     zoom in or out,
     go back to the original.
   Photos are stored with the artifact (assets); each place is recorded in the shared
   store as photos/<slot> = {asset?, pos, zoom, name?, at}, so choices survive reloads
   and every signed in viewer sees them. Claude reads these records back to put the
   chosen photos and their placement into the real site. */
(function () {
  "use strict";
  if (!window.claude || typeof window.claude.use !== "function") return;

  var SLOTS = [].slice.call(document.querySelectorAll("img[data-slot]"));
  if (!SLOTS.length) return;
  SLOTS.forEach(function (img) {
    img.setAttribute("data-orig-src", img.getAttribute("src"));
    img.setAttribute("data-orig-pos", img.style.objectPosition || "50% 50%");
    img.draggable = false;
  });

  var state = {};          // slot -> stored record
  var db = null, assets = null;
  var ZMIN = 1, ZMAX = 3, ZSTEP = 0.15;

  function imgsFor(slot) { return SLOTS.filter(function (i) { return i.getAttribute("data-slot") === slot; }); }
  function host(img) { return img.closest(".print") || img.closest(".breath") || img.closest(".way-photo") || img.parentElement; }
  function origPos(slot) { var i = imgsFor(slot)[0]; return i ? i.getAttribute("data-orig-pos") : "50% 50%"; }
  function parsePos(p) {
    var m = /(-?[\d.]+)%\s+(-?[\d.]+)%/.exec(p || "");
    return m ? [parseFloat(m[1]), parseFloat(m[2])] : [50, 50];
  }

  function show(slot, rec) {
    var pos = (rec && rec.pos) || origPos(slot);
    var zoom = (rec && rec.zoom) || 1;
    imgsFor(slot).forEach(function (img) {
      var src = rec && rec.asset ? "/_blob/" + rec.asset : img.getAttribute("data-orig-src");
      if (img.getAttribute("src") !== src) img.setAttribute("src", src);
      img.style.objectPosition = pos;
      img.style.transformOrigin = pos;
      img.style.transform = zoom > 1 ? "scale(" + zoom.toFixed(2) + ")" : "";
      host(img).classList.toggle("pe-changed", !!rec);
    });
  }

  var toast, toastTimer;
  function say(text, keep) {
    if (!toast) return;
    toast.textContent = text;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    if (!keep) toastTimer = setTimeout(function () { toast.classList.remove("show"); }, 3600);
  }

  function errorText(err) {
    var code = err && err.code;
    if (code === "too_large") return "התמונה גדולה מדי. אפשר לנסות תמונה קטנה יותר.";
    if (code === "unsupported_type") return "סוג הקובץ לא נתמך. אפשר JPG, PNG או WebP.";
    if (code === "quota_or_state" || code === "quota_exceeded") return "נגמר מקום האחסון של התצוגה.";
    if (code === "rate_limited" || code === "resource_exhausted") return "יותר מדי פעולות ברצף. אפשר לנסות שוב בעוד רגע.";
    return "השמירה לא הצליחה. אפשר לנסות שוב.";
  }

  // Large phone photos are scaled down before upload, so the site stays fast.
  function shrink(file) {
    return new Promise(function (resolve, reject) {
      if (!/^image\/(jpeg|png|webp)$/.test(file.type)) { reject({ code: "unsupported_type" }); return; }
      var url = URL.createObjectURL(file);
      var im = new Image();
      im.onload = function () {
        var max = 2000, w = im.naturalWidth, h = im.naturalHeight;
        URL.revokeObjectURL(url);
        if (Math.max(w, h) <= max && file.size < 3 * 1024 * 1024) { resolve(file); return; }
        var k = Math.min(1, max / Math.max(w, h));
        var c = document.createElement("canvas");
        c.width = Math.round(w * k); c.height = Math.round(h * k);
        c.getContext("2d").drawImage(im, 0, 0, c.width, c.height);
        c.toBlob(function (b) { b ? resolve(b) : resolve(file); }, "image/jpeg", 0.86);
      };
      im.onerror = function () { URL.revokeObjectURL(url); reject({ code: "unsupported_type" }); };
      im.src = url;
    });
  }

  // One write at a time per place, after the hand stops moving.
  var saveTimer = {}, saving = {};
  function save(slot) {
    clearTimeout(saveTimer[slot]);
    saveTimer[slot] = setTimeout(function () {
      saveTimer[slot] = null;
      if (saving[slot]) { save(slot); return; }
      var rec = state[slot];
      if (!rec) return;
      saving[slot] = true;
      db.doc("photos/" + slot).set(rec)
        .catch(function (err) { say(errorText(err)); })
        .then(function () { saving[slot] = false; });
    }, 500);
  }

  function change(slot, patch) {
    var rec = Object.assign({ pos: origPos(slot), zoom: 1 }, state[slot] || {}, patch, { at: new Date().toISOString() });
    state[slot] = rec;
    show(slot, rec);
    save(slot);
  }

  function put(slot, file) {
    say("מעלה את התמונה…", true);
    shrink(file)
      .then(function (blob) { return assets.upload(blob, { type: blob.type || "image/jpeg" }); })
      .then(function (res) {
        imgsFor(slot).forEach(function (i) { i.setAttribute("src", res.url); });
        change(slot, { asset: res.id, pos: "50% 50%", zoom: 1, name: String(file.name || "").slice(0, 120) });
        say("התמונה הוחלפה. גררי בתוך התמונה כדי למקם אותה, ובכפתורי הפלוס והמינוס אפשר להגדיל או להקטין.");
      })
      .catch(function (err) { say(errorText(err)); });
  }

  function reset(slot) {
    clearTimeout(saveTimer[slot]);
    saveTimer[slot] = null;
    delete state[slot];
    show(slot, null);
    db.doc("photos/" + slot).delete()
      .then(function () { say("חזרה לתמונה המקורית ולמיקום המקורי."); })
      .catch(function (err) { say(errorText(err)); });
  }

  function editing() { return document.body.classList.contains("photo-edit"); }

  // Drag inside a photo to move it in its frame (mouse, pen or finger).
  function enablePan(img, slot) {
    var start = null;
    img.addEventListener("pointerdown", function (e) {
      if (!editing() || e.button > 0) return;
      e.preventDefault();
      var frame = img.parentElement.getBoundingClientRect();
      var rec = state[slot] || {};
      start = { x: e.clientX, y: e.clientY, pos: parsePos(rec.pos || origPos(slot)), w: frame.width, h: frame.height, zoom: rec.zoom || 1 };
      img.setPointerCapture(e.pointerId);
      host(img).classList.add("pe-moving");
    });
    img.addEventListener("pointermove", function (e) {
      if (!start) return;
      // Moving the hand right shows more of the left side of the photo.
      var k = 1.4 / start.zoom;
      var x = Math.max(0, Math.min(100, start.pos[0] - (e.clientX - start.x) / start.w * 100 * k));
      var y = Math.max(0, Math.min(100, start.pos[1] - (e.clientY - start.y) / start.h * 100 * k));
      change(slot, { pos: Math.round(x) + "% " + Math.round(y) + "%" });
    });
    function end() { if (start) { start = null; host(img).classList.remove("pe-moving"); } }
    img.addEventListener("pointerup", end);
    img.addEventListener("pointercancel", end);
  }

  function setupEditor() {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pe-toggle";
    btn.setAttribute("aria-pressed", "false");
    btn.textContent = "עריכת תמונות";
    document.body.appendChild(btn);

    toast = document.createElement("div");
    toast.className = "pe-toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);

    var picker = document.createElement("input");
    picker.type = "file";
    picker.accept = "image/jpeg,image/png,image/webp";
    picker.hidden = true;
    document.body.appendChild(picker);
    var pickFor = null;
    picker.addEventListener("change", function () {
      if (picker.files && picker.files[0] && pickFor) put(pickFor, picker.files[0]);
      picker.value = "";
    });

    function setEditing(on) {
      document.body.classList.toggle("photo-edit", on);
      btn.setAttribute("aria-pressed", String(on));
      btn.textContent = on ? "סיום עריכת תמונות" : "עריכת תמונות";
      if (on) say("גררי קובץ אל תמונה כדי להחליף אותה. גררי בתוך תמונה כדי למקם אותה.");
    }
    btn.addEventListener("click", function () { setEditing(!editing()); });
    // while editing, a photo inside a link moves or zooms; it does not follow the link
    document.addEventListener("click", function (e) {
      if (editing() && e.target.closest && e.target.closest(".pe-host") && e.target.closest("a[href]")) e.preventDefault();
    }, true);

    SLOTS.forEach(function (img) {
      var h = host(img);
      var slot = img.getAttribute("data-slot");
      enablePan(img, slot);
      if (h.querySelector(".pe-bar")) return;
      h.classList.add("pe-host");
      var bar = document.createElement("div");
      bar.className = "pe-bar";
      bar.innerHTML =
        '<button type="button" class="pe-pick">החלפה</button>' +
        '<button type="button" class="pe-zoom" data-d="-1" aria-label="הקטנה">−</button>' +
        '<button type="button" class="pe-zoom" data-d="1" aria-label="הגדלה">+</button>' +
        '<button type="button" class="pe-reset">למקור</button>';
      h.appendChild(bar);
      bar.querySelector(".pe-pick").addEventListener("click", function (e) { e.preventDefault(); pickFor = slot; picker.click(); });
      bar.querySelector(".pe-reset").addEventListener("click", function (e) { e.preventDefault(); reset(slot); });
      [].forEach.call(bar.querySelectorAll(".pe-zoom"), function (z) {
        z.addEventListener("click", function (e) {
          e.preventDefault();
          var cur = (state[slot] && state[slot].zoom) || 1;
          var next = Math.max(ZMIN, Math.min(ZMAX, Math.round((cur + ZSTEP * Number(z.getAttribute("data-d"))) * 100) / 100));
          change(slot, { zoom: next });
        });
      });
      h.addEventListener("dragover", function (e) { if (!editing()) return; e.preventDefault(); h.classList.add("pe-over"); });
      h.addEventListener("dragleave", function () { h.classList.remove("pe-over"); });
      h.addEventListener("drop", function (e) {
        if (!editing()) return;
        e.preventDefault();
        h.classList.remove("pe-over");
        var f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
        if (f) put(slot, f);
      });
    });

    // Dragging a file over the page turns the mode on; a file dropped outside
    // a photo is ignored rather than opened by the browser.
    window.addEventListener("dragenter", function (e) {
      var types = e.dataTransfer && e.dataTransfer.types;
      if (types && [].indexOf.call(types, "Files") !== -1 && !editing()) setEditing(true);
    });
    window.addEventListener("dragover", function (e) { if (editing()) e.preventDefault(); });
    window.addEventListener("drop", function (e) { if (editing()) e.preventDefault(); });
  }

  window.claude.use("db").then(function (d) {
    if (!d) return;
    db = d;
    db.collection("photos").onSnapshot(function (snap) {
      var seen = {};
      snap.docs.forEach(function (doc) {
        seen[doc.id] = true;
        if (saveTimer[doc.id] && state[doc.id]) return;   // this view is still saving its own change
        state[doc.id] = Object.assign({}, doc.data());
        show(doc.id, state[doc.id]);
      });
      Object.keys(state).forEach(function (k) { if (!seen[k] && !saveTimer[k]) { delete state[k]; show(k, null); } });
    }, function () { /* the original photos stay */ });
    return window.claude.use("assets").then(function (a) {
      if (!a) return;          // only editors of the preview can change photos
      assets = a;
      setupEditor();
    });
  }).catch(function () { /* the preview works without the editing mode */ });
})();
