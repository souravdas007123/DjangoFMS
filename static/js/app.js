(function () {
  "use strict";

  // ---- Light / dark theme ----------------------------------------------
  var root = document.documentElement;
  document.addEventListener("click", function (e) {
    var toggle = e.target.closest("[data-theme-toggle]");
    if (!toggle) { return; }
    var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-bs-theme", next);
    try { localStorage.setItem("fms-theme", next); } catch (err) { /* storage blocked */ }
  });

  // ---- Inline formset rows (add / remove) ------------------------------
  document.addEventListener("click", function (e) {
    var addBtn = e.target.closest("[data-add-row]");
    if (addBtn) {
      var prefix = addBtn.getAttribute("data-add-row");
      var total = document.getElementById("id_" + prefix + "-TOTAL_FORMS");
      var tpl = document.getElementById("tpl-" + prefix);
      var body = document.getElementById("rows-" + prefix);
      if (!total || !tpl || !body) { return; }
      body.insertAdjacentHTML("beforeend", tpl.innerHTML.replace(/__prefix__/g, total.value));
      total.value = parseInt(total.value, 10) + 1;
      var firstField = body.lastElementChild && body.lastElementChild.querySelector("input:not([type=hidden]), select");
      if (firstField) { firstField.focus(); }
      return;
    }

    var removeBtn = e.target.closest(".js-remove-row");
    if (removeBtn) {
      var row = removeBtn.closest("tr.inline-row");
      if (!row) { return; }
      var del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (del) { del.checked = true; }
      row.querySelectorAll("[required]").forEach(function (el) { el.removeAttribute("required"); });
      row.classList.add("d-none");
    }
  });
})();
