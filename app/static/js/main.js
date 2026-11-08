// SR All Service Hub — frontend
document.addEventListener('DOMContentLoaded', function () {
  // Mobile menu
  const toggle = document.getElementById('menuToggle');
  const nav = document.getElementById('mainNav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => nav.classList.toggle('open'));
  }

  // Persist language preference
  const lang = document.documentElement.lang || 'ne';
  try {
    localStorage.setItem('sr_lang', lang);
  } catch (e) {}

  // Simple form unsaved warning (optional)
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    let dirty = false;
    form.addEventListener('change', () => { dirty = true; });
    form.addEventListener('submit', () => { dirty = false; });
    window.addEventListener('beforeunload', (e) => {
      if (dirty) { e.preventDefault(); e.returnValue = ''; }
    });
  });
});


// Scroll reveal animations site-wide
(function(){
  var nodes = document.querySelectorAll('.reveal, .card, .section-title');
  if (!('IntersectionObserver' in window)) {
    nodes.forEach(function(n){ n.classList.add('visible'); });
    return;
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        e.target.style.opacity = '1';
        e.target.style.transform = 'none';
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  nodes.forEach(function(n){
    if (!n.classList.contains('reveal')) {
      n.style.opacity = '0';
      n.style.transform = 'translateY(16px)';
      n.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    }
    io.observe(n);
  });
})();








// Loading overlay only while page is loading; typewriter once
(function(){
  var CHAR_DELAY = 12;
  var WORD_GAP = 28;
  var TYPE_KEY = "sr_typewriter_done_v1";

  function hideWait() {
    var wait = document.getElementById("srWritingWait");
    if (!wait) return;
    wait.classList.add("is-hidden");
    setTimeout(function(){ if (wait.parentNode) wait.remove(); }, 400);
  }

  if (document.body.classList.contains("admin-body") || location.pathname.indexOf("/admin") === 0) {
    hideWait();
    return;
  }

  // Hide loading as soon as page is ready (real load time only)
  if (document.readyState === "complete") {
    hideWait();
  } else {
    window.addEventListener("load", hideWait);
    // safety: never block more than 8s if something hangs
    setTimeout(hideWait, 8000);
  }

  var alreadyTyped = false;
  try { alreadyTyped = localStorage.getItem(TYPE_KEY) === "1"; } catch(e) {}

  function typeEl(el, onDone) {
    if (!el || el.dataset.typed === "1") { if (onDone) onDone(); return; }
    el.dataset.typed = "1";
    var html = el.innerHTML;
    var text = (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim();
    if (text.length < 3) { if (onDone) onDone(); return; }
    el.classList.add("is-typing", "page-typing");
    el.textContent = "";
    var words = text.split(" "), wi = 0, shown = "";
    function typeWord() {
      if (wi >= words.length) {
        el.innerHTML = html;
        el.classList.remove("is-typing", "page-typing");
        if (onDone) onDone();
        return;
      }
      var word = words[wi++], ci = 0;
      function typeChar() {
        if (ci <= word.length) {
          el.textContent = shown + word.slice(0, ci);
          ci++;
          setTimeout(typeChar, CHAR_DELAY);
        } else {
          shown += word + (wi < words.length ? " " : "");
          el.textContent = shown;
          setTimeout(typeWord, WORD_GAP);
        }
      }
      typeChar();
    }
    typeWord();
  }

  function queue(list, i) {
    if (i >= list.length) {
      try { localStorage.setItem(TYPE_KEY, "1"); } catch(e) {}
      return;
    }
    typeEl(list[i], function(){ queue(list, i + 1); });
  }

  function targets() {
    var sels = [".hero-content h1", ".hero-content p", ".section-title", ".section-subtitle", "#aboutTyping", ".policy-content", ".page-type-body", ".collab-type"];
    var out = [], seen = new Set();
    sels.forEach(function(s){
      document.querySelectorAll(s).forEach(function(n){
        if (seen.has(n)) return;
        if (n.closest(".site-header, .bottom-nav, .site-footer, .admin-sidebar")) return;
        seen.add(n);
        if ((n.innerText || "").trim().length >= 3) out.push(n);
      });
    });
    return out.slice(0, 10);
  }

  function go() {
    document.body.classList.remove("sr-blank");
    if (alreadyTyped) return;
    queue(targets(), 0);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", go);
  else go();
})();


// Web Push — registered users only
(function () {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;
  var isCustomer = document.body && document.body.dataset.customer === "1";
  if (!isCustomer) return;

  function urlBase64ToUint8Array(base64String) {
    var padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    var base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(base64);
    var out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }

  navigator.serviceWorker.register("/static/sw.js").then(function (reg) {
    return fetch("/auth/push-public-key")
      .then(function (r) { return r.json(); })
      .then(function (cfg) {
        if (!cfg.enabled || !cfg.publicKey) return;
        return reg.pushManager.getSubscription().then(function (sub) {
          if (sub) {
            return fetch("/auth/push-subscribe", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(sub.toJSON()),
            });
          }
          // Ask permission once
          return Notification.requestPermission().then(function (perm) {
            if (perm !== "granted") return;
            return reg.pushManager.subscribe({
              userVisibleOnly: true,
              applicationServerKey: urlBase64ToUint8Array(cfg.publicKey),
            }).then(function (subscription) {
              return fetch("/auth/push-subscribe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(subscription.toJSON()),
              });
            });
          });
        });
      });
  }).catch(function (e) { console.warn("SW/push", e); });
})();
