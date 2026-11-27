(function () {
  "use strict";

  // Mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector("#site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    // choosing a page closes the menu
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Scroll reveal, skipped when the user prefers reduced motion
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var reveals = document.querySelectorAll(".reveal");
  if (!reduce && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  // Lead forms
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  var PHONE = /^[0-9+\-\s()]{7,20}$/;

  document.querySelectorAll("form[data-lead-form]").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var msg = form.querySelector(".form-msg");
      var data = new FormData(form);
      var name = (data.get("name") || "").toString().trim();
      var phone = (data.get("phone") || "").toString().trim();
      var email = (data.get("email") || "").toString().trim();
      var problem = "";
      if (name.length < 2) problem = "נא להזין שם.";
      else if (!phone && !email) problem = "נא להזין טלפון או מייל, כדי שנוכל לחזור אלייך.";
      else if (phone && !PHONE.test(phone)) problem = "מספר הטלפון אינו נראה תקין.";
      else if (email && !EMAIL.test(email)) problem = "כתובת המייל אינה נראית תקינה.";
      if (problem) { msg.className = "form-msg err"; msg.textContent = problem; return; }

      var body = {
        name: name,
        phone: phone,
        email: email,
        service: data.get("service") || "general",
        item: (data.get("item") || "").toString(),
        message: (data.get("message") || "").toString().trim(),
        marketing_consent: data.get("marketing") === "on",
        source: form.getAttribute("data-source") || location.pathname,
        website: (data.get("website") || "").toString()
      };
      var btn = form.querySelector("button[type=submit]");
      btn.disabled = true;
      msg.className = "form-msg";
      msg.textContent = "שולחים...";
      fetch("https://forms.annalee-milstein.com/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      }).then(function (r) {
        return r.json().then(function (j) { return { ok: r.ok, j: j }; });
      }).then(function (res) {
        if (res.ok) {
          var download = form.getAttribute("data-download");
          var chosen = form.querySelector("select[name=item] option:checked");
          var next = (chosen && chosen.getAttribute("data-next")) || form.getAttribute("data-next");
          form.reset();
          msg.className = "form-msg ok";
          msg.textContent = form.getAttribute("data-success") || res.j.message || "התקבל. נחזור אלייך בתוך 48 שעות.";
          if (download) {
            var link = document.createElement("a");
            link.href = download;
            link.download = "";
            document.body.appendChild(link);
            link.click();
            link.remove();
          }
          if (next) setTimeout(function () { location.href = next; }, 700);
        } else {
          msg.className = "form-msg err";
          msg.textContent = res.j.error || "אירעה תקלה. אפשר לנסות שוב בעוד רגע.";
        }
      }).catch(function () {
        msg.className = "form-msg ok"; var wa = "https://wa.me/972506651451?text=" + encodeURIComponent("שלום, אני " + body.name + ". " + (body.message || "אשמח שתחזרי אליי") + " טלפון: " + body.phone + " מייל: " + body.email); msg.innerHTML = 'לשליחת הפרטים לאנה, <a target="_blank" rel="noopener" href="' + wa + '">לחצי כאן לוואטסאפ</a>.'; window.open(wa, "_blank");
      }).finally(function () { btn.disabled = false; });
    });
  });

  // The article list: from the server when it runs (admin), otherwise from the static file the build writes
  function loadArticles(query) {
    return fetch("/api/articles" + (query || "")).then(function (r) {
      if (!r.ok) throw new Error("no api");
      return r.json();
    }).catch(function () {
      return fetch("/static/articles.json").then(function (r) { return r.json(); }).then(function (j) {
        var items = j.articles || [];
        if (query && query.indexOf("featured=1") !== -1) items = items.filter(function (a) { return a.featured; }).slice(0, 3);
        return { articles: items };
      });
    });
  }

  // Article index: search, category filter, load more
  var list = document.querySelector("[data-article-list]");
  if (list) {
    var PAGE = 9;
    var state = { category: "", q: "", shown: PAGE, items: [] };
    var grid = list.querySelector(".grid");
    var empty = list.querySelector(".empty");
    var more = list.querySelector("[data-more]");
    var search = list.querySelector("input[type=search]");
    var filters = list.querySelector(".filters");

    function card(a) {
      var el = document.createElement("article");
      el.className = "card";
      var tag = a.category ? '<span class="tag"></span>' : "";
      el.innerHTML = tag + '<h3><a href="/articles/' + encodeURIComponent(a.slug) + '"></a></h3><p></p><a class="more" href="/articles/' + encodeURIComponent(a.slug) + '">לקריאה</a>';
      if (a.category) el.querySelector(".tag").textContent = a.category;
      el.querySelector("h3 a").textContent = a.title;
      el.querySelector("p").textContent = a.excerpt || "";
      return el;
    }

    function render() {
      var filtered = state.items.filter(function (a) {
        var okCat = !state.category || a.category === state.category;
        var okQ = !state.q || (a.title + " " + (a.excerpt || "")).indexOf(state.q) !== -1;
        return okCat && okQ;
      });
      grid.innerHTML = "";
      filtered.slice(0, state.shown).forEach(function (a) { grid.appendChild(card(a)); });
      empty.hidden = filtered.length > 0;
      more.hidden = filtered.length <= state.shown;
    }

    function buildFilters(categories) {
      filters.innerHTML = "";
      ["הכול"].concat(categories).forEach(function (c) {
        var b = document.createElement("button");
        b.type = "button";
        b.textContent = c;
        var active = (c === "הכול" && !state.category) || c === state.category;
        b.setAttribute("aria-pressed", String(active));
        b.addEventListener("click", function () {
          state.category = c === "הכול" ? "" : c;
          state.shown = PAGE;
          buildFilters(categories);
          render();
        });
        filters.appendChild(b);
      });
    }

    loadArticles("").then(function (j) {
      state.items = j.articles || [];
      var cats = [];
      state.items.forEach(function (a) { if (a.category && cats.indexOf(a.category) === -1) cats.push(a.category); });
      if (cats.length) { filters.hidden = false; buildFilters(cats); } else { filters.hidden = true; }
      render();
    }).catch(function () { empty.hidden = false; empty.textContent = "לא הצלחנו לטעון את המאמרים כרגע."; });

    search.addEventListener("input", function () {
      state.q = search.value.trim();
      state.shown = PAGE;
      render();
    });
    more.addEventListener("click", function () { state.shown += PAGE; render(); });
  }

  // Featured articles on the home page
  var featured = document.querySelector("[data-featured]");
  if (featured) {
    loadArticles("?featured=1&limit=3").then(function (j) {
      var items = j.articles || [];
      if (!items.length) { featured.closest("section").hidden = true; return; }
      items.forEach(function (a) {
        var el = document.createElement("article");
        el.className = "card sage";
        el.innerHTML = '<h3><a href="/articles/' + encodeURIComponent(a.slug) + '"></a></h3><p></p><a class="more" href="/articles/' + encodeURIComponent(a.slug) + '">לקריאה</a>';
        el.querySelector("h3 a").textContent = a.title;
        el.querySelector("p").textContent = a.excerpt || "";
        featured.appendChild(el);
      });
    }).catch(function () { featured.closest("section").hidden = true; });
  }

  // Single article page
  var art = document.querySelector("[data-article-slug]");
  if (art && art.querySelector("[data-body]")) {   // only the dynamic template; the static article pages already hold the text
    var slug = art.getAttribute("data-article-slug") || decodeURIComponent(location.pathname.split("/").pop());
    fetch("/api/articles/" + encodeURIComponent(slug)).then(function (r) {
      if (!r.ok) throw new Error("not found");
      return r.json();
    }).then(function (a) {
      document.title = (a.seo_title || a.title) + " | אנה לי מילשטיין";
      var h = art.querySelector("h1");
      h.textContent = a.title;
      art.querySelector("[data-byline]").textContent = "מאת " + a.author + " · עודכן " + a.updated_date;
      var body = art.querySelector("[data-body]");
      body.innerHTML = "";
      a.blocks.forEach(function (b) {
        var el = document.createElement(b.type === "h2" ? "h2" : "p");
        el.textContent = b.text;
        body.appendChild(el);
      });
      if (a.sources && a.sources.length) {
        var s = art.querySelector("[data-sources]");
        s.hidden = false;
        s.querySelector("ul").innerHTML = "";
        a.sources.forEach(function (src) {
          var li = document.createElement("li");
          li.textContent = src;
          s.querySelector("ul").appendChild(li);
        });
      }
      var rel = art.querySelector("[data-related]");
      if (a.related && a.related.length) {
        rel.hidden = false;
        var ul = rel.querySelector("ul");
        a.related.forEach(function (r) {
          var li = document.createElement("li");
          var link = document.createElement("a");
          link.href = "/articles/" + encodeURIComponent(r.slug);
          link.textContent = r.title;
          li.appendChild(link);
          ul.appendChild(li);
        });
      }
    }).catch(function () {
      art.querySelector("h1").textContent = "המאמר לא נמצא";
      art.querySelector("[data-body]").innerHTML = "<p>אפשר לחזור לכל המאמרים.</p>";
    });
  }
})();

// "on thorns": with reduced motion, the line rests in its calm state, the wave with its flowers
(function () {
  if (!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
  [].forEach.call(document.querySelectorAll("svg.kotzim-line"), function (s) {
    if (s.pauseAnimations) { s.pauseAnimations(); s.setCurrentTime(6.5); }
  });
})();


// Accessibility menu: a fixed button on every page, opening a small panel of display adjustments.
// The choices are kept in this browser (localStorage) so they stay on the next page and visit.
(function () {
  var KEY = "a11y-prefs";
  var OPTIONS = [
    ["contrast", "ניגודיות גבוהה"],
    ["gray", "גווני אפור"],
    ["links", "הדגשת קישורים"],
    ["focus", "הדגשת פוקוס מקלדת"],
    ["font", "גופן קריא"],
    ["spacing", "ריווח שורות"],
    ["still", "עצירת אנימציות"]
  ];
  var root = document.documentElement;
  var prefs = {};
  try { prefs = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { prefs = {}; }

  function save() { try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) {} }
  function stillSvgs(on) {
    [].forEach.call(document.querySelectorAll("svg"), function (s) {
      if (!s.pauseAnimations) return;
      if (on) s.pauseAnimations(); else s.unpauseAnimations();
    });
  }
  function apply() {
    root.classList.remove("a11y-fs1", "a11y-fs2", "a11y-fs3");
    if (prefs.size) root.classList.add("a11y-fs" + prefs.size);
    OPTIONS.forEach(function (o) { root.classList.toggle("a11y-" + o[0], !!prefs[o[0]]); });
    stillSvgs(!!prefs.still);
  }
  apply();

  var icon = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="4" r="2" fill="currentColor"/>' +
    '<path d="M4.5 8.2l7.5 1.3 7.5-1.3M12 9.5v5m0 0l-3.5 7m3.5-7l3.5 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var wrap = document.createElement("div");
  wrap.className = "a11y-widget";
  wrap.innerHTML =
    '<button type="button" class="a11y-toggle" aria-expanded="false" aria-controls="a11y-panel" aria-label="תפריט נגישות">' + icon + '</button>' +
    '<div class="a11y-panel" id="a11y-panel" role="dialog" aria-label="תפריט נגישות" hidden>' +
      '<div class="a11y-head"><h2>נגישות</h2><button type="button" class="a11y-close" aria-label="סגירת תפריט הנגישות">×</button></div>' +
      '<div class="a11y-size" role="group" aria-label="גודל טקסט">' +
        '<span>גודל טקסט</span>' +
        '<button type="button" data-size="-1" aria-label="הקטנת טקסט">א-</button>' +
        '<button type="button" data-size="1" aria-label="הגדלת טקסט">א+</button>' +
      '</div>' +
      '<div class="a11y-grid">' + OPTIONS.map(function (o) {
        return '<button type="button" data-opt="' + o[0] + '" aria-pressed="false">' + o[1] + '</button>';
      }).join("") + '</div>' +
      '<div class="a11y-foot"><button type="button" class="a11y-reset">איפוס הגדרות</button>' +
      '<a href="/accessibility">הצהרת נגישות</a></div>' +
    '</div>';
  document.body.appendChild(wrap);

  var toggle = wrap.querySelector(".a11y-toggle"), panel = wrap.querySelector(".a11y-panel");
  function sync() {
    [].forEach.call(wrap.querySelectorAll("[data-opt]"), function (b) {
      b.setAttribute("aria-pressed", prefs[b.getAttribute("data-opt")] ? "true" : "false");
    });
  }
  function open(on) {
    panel.hidden = !on;
    toggle.setAttribute("aria-expanded", on ? "true" : "false");
    if (on) panel.querySelector("button").focus(); else toggle.focus();
  }
  sync();
  toggle.addEventListener("click", function () { open(panel.hidden); });
  wrap.querySelector(".a11y-close").addEventListener("click", function () { open(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) open(false); });
  document.addEventListener("click", function (e) { if (!panel.hidden && !wrap.contains(e.target)) { panel.hidden = true; toggle.setAttribute("aria-expanded", "false"); } });
  wrap.addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b) return;
    if (b.hasAttribute("data-size")) {
      prefs.size = Math.max(0, Math.min(3, (prefs.size || 0) + Number(b.getAttribute("data-size"))));
    } else if (b.hasAttribute("data-opt")) {
      var k = b.getAttribute("data-opt"); prefs[k] = !prefs[k];
    } else if (b.classList.contains("a11y-reset")) {
      prefs = {};
    } else { return; }
    save(); apply(); sync();
  });
})();
