// SPDX-License-Identifier: Apache-2.0
// Step sequencer for the explain/ animations. No dependencies, no network.
//
// Markup contract, per <figure class="anim" data-steps="N">:
//   - SVG elements with class "st" and data-step="k" appear at step k (1..N) and stay.
//   - data-until="k" on an element hides it again after step k.
//   - <span class="cap"> receives the caption; captions come from data-cap-1 .. data-cap-N
//     on the figure.
//   - buttons with data-act="play" | "step" | "replay".
// Under prefers-reduced-motion the figure renders its final state with no movement;
// the "step" button still walks the stages by hand.
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function setup(fig) {
    var n = parseInt(fig.getAttribute("data-steps"), 10) || 1;
    var els = Array.prototype.slice.call(fig.querySelectorAll(".st"));
    var cap = fig.querySelector(".cap");
    var playBtn = fig.querySelector('[data-act="play"]');
    var step = 0;
    var timer = null;
    var delay = parseInt(fig.getAttribute("data-delay"), 10) || 1900;

    function render(k) {
      step = k;
      els.forEach(function (el) {
        var at = parseInt(el.getAttribute("data-step"), 10) || 1;
        var until = parseInt(el.getAttribute("data-until"), 10) || Infinity;
        var on = k >= at && k <= until;
        el.classList.toggle("on", on);
        el.classList.toggle("off", !on);
      });
      if (cap) {
        cap.textContent = k > 0 ? (fig.getAttribute("data-cap-" + k) || "") : (fig.getAttribute("data-cap-0") || "");
      }
    }
    function stop() {
      if (timer) { clearInterval(timer); timer = null; }
      if (playBtn) playBtn.textContent = "Play";
    }
    function play() {
      if (reduce) { render(n); return; }
      stop();
      if (step >= n) render(0);
      if (playBtn) playBtn.textContent = "Pause";
      timer = setInterval(function () {
        if (step >= n) {
          // Hold the final frame for one extra beat, then loop.
          stop();
          setTimeout(function () { if (!timer) { render(0); play(); } }, delay * 1.5);
          return;
        }
        render(step + 1);
      }, delay);
    }

    fig.addEventListener("click", function (e) {
      var act = e.target && e.target.getAttribute && e.target.getAttribute("data-act");
      if (!act) return;
      if (act === "play") { if (timer) stop(); else play(); }
      if (act === "step") { stop(); render(step >= n ? 1 : step + 1); }
      if (act === "replay") { stop(); render(0); play(); }
    });

    if (reduce) {
      fig.setAttribute("data-static", "");
      render(n);
    } else {
      render(0);
      play();
    }
  }

  Array.prototype.forEach.call(document.querySelectorAll("figure.anim"), setup);
})();
