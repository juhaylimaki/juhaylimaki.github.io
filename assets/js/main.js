(function () {
  "use strict";

  // Lightbox: enlarges images wrapped in a.lb. Without JS the links open the image directly.
  var box = null;
  var boxImg = null;
  var links = [];
  var current = -1;
  var opener = null;

  function button(cls, label, text, onClick) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = cls;
    b.setAttribute("aria-label", label);
    b.textContent = text;
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      onClick();
    });
    return b;
  }

  function ensureBox() {
    if (box) return;
    box = document.createElement("div");
    box.className = "lightbox";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Image viewer");
    boxImg = document.createElement("img");
    box.appendChild(boxImg);
    box.appendChild(button("lightbox-close", "Close", "×", close));
    box.appendChild(button("lightbox-prev", "Previous image", "‹", function () { step(-1); }));
    box.appendChild(button("lightbox-next", "Next image", "›", function () { step(1); }));
    box.addEventListener("click", function (e) {
      if (e.target === box) close();
    });
    document.body.appendChild(box);
  }

  function show(index) {
    current = (index + links.length) % links.length;
    var link = links[current];
    var thumb = link.querySelector("img");
    boxImg.src = link.getAttribute("href");
    boxImg.alt = thumb ? thumb.alt : "";
  }

  // While the lightbox is open, everything behind it is inert so Tab stays inside the dialog.
  function setBackgroundInert(value) {
    Array.prototype.forEach.call(document.body.children, function (el) {
      if (el !== box) el.inert = value;
    });
  }

  function open(link) {
    ensureBox();
    setBackgroundInert(true);
    links = Array.prototype.slice.call(document.querySelectorAll("a.lb"));
    opener = link;
    show(links.indexOf(link));
    box.hidden = false;
    document.body.style.overflow = "hidden";
    box.querySelector(".lightbox-close").focus();
  }

  function close() {
    if (!box || box.hidden) return;
    box.hidden = true;
    setBackgroundInert(false);
    boxImg.removeAttribute("src");
    document.body.style.overflow = "";
    if (opener) opener.focus();
  }

  function step(delta) {
    if (links.length) show(current + delta);
  }

  // YouTube: swap the thumbnail button for the real player on click.
  function playVideo(btn) {
    var id = btn.getAttribute("data-youtube-id");
    var frame = document.createElement("iframe");
    frame.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) + "?autoplay=1";
    frame.title = "YouTube video";
    frame.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    frame.setAttribute("allowfullscreen", "");
    var wrap = document.createElement("div");
    wrap.className = "yt";
    wrap.appendChild(frame);
    btn.replaceWith(wrap);
    frame.focus();
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var yt = e.target.closest("button.yt[data-youtube-id]");
    if (yt) {
      playVideo(yt);
      return;
    }
    var link = e.target.closest("a.lb");
    if (link) {
      e.preventDefault();
      open(link);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (!box || box.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") step(1);
    else if (e.key === "ArrowLeft") step(-1);
  });
})();
