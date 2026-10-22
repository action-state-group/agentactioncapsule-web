// SPDX-License-Identifier: Apache-2.0
// The map page: a layer panel and one action walking up the stack. No dependencies, no network.
//
// Each layer node is an <a href="#L-<id>"> in the SVG, so without this script a click still
// jumps to that layer's section below the map. With it, a click shows the section in the side
// panel instead. The walk reads its stops from <script id="map-stops">; under
// prefers-reduced-motion it does not play, and Step walks the stops by hand.
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var svg = document.getElementById("mapsvg");
  var panel = document.getElementById("panel");
  var body = document.getElementById("panel-body");
  var nodes = Array.prototype.slice.call(svg.querySelectorAll(".node"));
  var stops = JSON.parse(document.getElementById("map-stops").textContent);
  var dot = document.getElementById("dot");
  var cap = document.getElementById("mapcap");
  var fig = document.querySelector(".mapfig");
  var playBtn = fig.querySelector('[data-act="play"]');
  var cap0 = cap.textContent;
  var delay = 1900;
  var step = -1;
  var timer = null;

  function nodeFor(id) {
    for (var i = 0; i < nodes.length; i++) if (nodes[i].getAttribute("data-layer") === id) return nodes[i];
    return null;
  }

  function show(id) {
    var src = document.getElementById("L-" + id);
    if (!src) return;
    var copy = src.cloneNode(true);
    copy.removeAttribute("id");
    body.innerHTML = "";
    Array.prototype.forEach.call(copy.childNodes, function (c) { body.appendChild(c.cloneNode(true)); });
    nodes.forEach(function (n) { n.classList.toggle("sel", n.getAttribute("data-layer") === id); });
    // Below the map on narrow screens: bring the panel into view.
    if (panel.getBoundingClientRect().top > window.innerHeight) {
      panel.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    }
  }

  nodes.forEach(function (n) {
    n.addEventListener("click", function (e) {
      e.preventDefault();
      show(n.getAttribute("data-layer"));
    });
  });

  function render(k) {
    step = k;
    nodes.forEach(function (n) { n.classList.remove("hot"); });
    if (k < 0) {
      dot.classList.remove("on");
      cap.textContent = cap0;
      return;
    }
    var s = stops[k];
    dot.setAttribute("transform", "translate(" + s.x + " " + s.y + ")");
    dot.classList.add("on");
    if (s.layer) {
      var n = nodeFor(s.layer);
      if (n) n.classList.add("hot");
    }
    cap.textContent = s.cap;
  }
  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
    playBtn.textContent = "Play";
  }
  function play() {
    stop();
    if (step >= stops.length - 1) render(-1);
    playBtn.textContent = "Pause";
    timer = setInterval(function () {
      if (step >= stops.length - 1) { stop(); return; }
      render(step + 1);
    }, delay);
  }

  fig.addEventListener("click", function (e) {
    var act = e.target && e.target.getAttribute && e.target.getAttribute("data-act");
    if (!act) return;
    if (act === "play") { if (timer) stop(); else play(); }
    if (act === "step") { stop(); render(step >= stops.length - 1 ? 0 : step + 1); }
    if (act === "replay") { stop(); render(-1); if (!reduce) play(); else render(0); }
  });

  if (location.hash.indexOf("#L-") === 0) show(location.hash.slice(3));
  render(-1);
  if (!reduce) play();
})();
