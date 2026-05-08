(function () {
  const shell = document.body;
  const sidebarToggles = document.querySelectorAll("[data-sidebar-toggle]");
  const overlay = document.querySelector("[data-panel-overlay]");
  const userMenu = document.querySelector("[data-user-menu]");
  const userToggle = document.querySelector("[data-user-toggle]");
  const topMenus = document.querySelectorAll("[data-panel-menu]");
  const avatarInputs = document.querySelectorAll("[data-avatar-input]");
  const mobileSidebar = window.matchMedia("(max-width: 900px)");
  const searchForm = document.querySelector("[data-panel-search]");
  const searchInput = document.querySelector("[data-panel-search-input]");
  const searchResults = document.querySelector("[data-panel-search-results]");

  const closeTopMenus = (exceptMenu) => {
    topMenus.forEach((menu) => {
      if (menu !== exceptMenu) menu.classList.remove("is-open");
    });
  };

  sidebarToggles.forEach((button) => {
    button.addEventListener("click", () => {
      if (mobileSidebar.matches) {
        shell.classList.toggle("sidebar-open");
        return;
      }

      const collapsed = shell.classList.toggle("sidebar-collapsed");
      window.localStorage.setItem("panelSidebarCollapsed", collapsed ? "1" : "0");
    });
  });

  if (overlay) {
    overlay.addEventListener("click", () => {
      shell.classList.remove("sidebar-open");
    });
  }

  if (!mobileSidebar.matches && window.localStorage.getItem("panelSidebarCollapsed") === "1") {
    shell.classList.add("sidebar-collapsed");
  }

  mobileSidebar.addEventListener("change", (event) => {
    shell.classList.remove("sidebar-open");
    if (event.matches) {
      shell.classList.remove("sidebar-collapsed");
    } else if (window.localStorage.getItem("panelSidebarCollapsed") === "1") {
      shell.classList.add("sidebar-collapsed");
    }
  });

  if (userMenu && userToggle) {
    userToggle.addEventListener("click", (event) => {
      event.stopPropagation();
      closeTopMenus();
      const isOpen = userMenu.classList.toggle("is-open");
      userToggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", (event) => {
      if (!userMenu.contains(event.target)) {
        userMenu.classList.remove("is-open");
        userToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  topMenus.forEach((menu) => {
    const toggle = menu.querySelector("[data-panel-menu-toggle]");
    if (!toggle) return;

    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      if (userMenu && userToggle) {
        userMenu.classList.remove("is-open");
        userToggle.setAttribute("aria-expanded", "false");
      }
      const willOpen = !menu.classList.contains("is-open");
      closeTopMenus(menu);
      menu.classList.toggle("is-open", willOpen);
    });
  });

  document.addEventListener("click", (event) => {
    const clickedInsideTopMenu = Array.from(topMenus).some((menu) => menu.contains(event.target));
    if (!clickedInsideTopMenu) closeTopMenus();
  });

  avatarInputs.forEach((input) => {
    input.addEventListener("change", () => {
      if (input.files && input.files.length && input.form) {
        input.form.submit();
      }
    });
  });

  if (searchForm && searchInput && searchResults) {
    const navItems = Array.from(document.querySelectorAll(".panel-nav a[href]")).map((link) => ({
      type: "Sayfa",
      label: link.textContent.replace(/\s+/g, " ").trim(),
      href: link.href,
    }));

    const pageItems = Array.from(
      document.querySelectorAll(".portal-hero, .portal-panel, .portal-stat-card, .dashboard-card, .log-detail-card, .intern-track-card, .document-status-card, .portal-table tbody tr")
    ).map((element, index) => {
      if (!element.id) element.id = `panel-search-hit-${index}`;
      return {
        type: "Bu sayfada",
        label: element.textContent.replace(/\s+/g, " ").trim().slice(0, 90),
        href: `#${element.id}`,
        element,
      };
    });

    const normalize = (value) => value.toLocaleLowerCase("tr-TR").trim();

    const renderResults = (query) => {
      const normalizedQuery = normalize(query);
      searchResults.innerHTML = "";

      if (normalizedQuery.length < 2) {
        searchForm.classList.remove("has-results");
        pageItems.forEach((item) => item.element?.classList.remove("panel-search-hidden"));
        return [];
      }

      const navMatches = navItems.filter((item) => normalize(item.label).includes(normalizedQuery)).slice(0, 5);
      const pageMatches = pageItems.filter((item) => normalize(item.label).includes(normalizedQuery)).slice(0, 5);
      const matches = [...navMatches, ...pageMatches].slice(0, 8);

      pageItems.forEach((item) => {
        if (!item.element) return;
        const isMatch = normalize(item.label).includes(normalizedQuery);
        item.element.classList.toggle("panel-search-hidden", !isMatch);
      });

      if (!matches.length) {
        searchResults.innerHTML = '<div class="panel-search-empty">Sonuç bulunamadı.</div>';
        searchForm.classList.add("has-results");
        return [];
      }

      matches.forEach((item) => {
        const result = document.createElement("a");
        result.href = item.href;
        result.innerHTML = `<strong>${item.label || "Sonuç"}</strong><small>${item.type}</small>`;
        result.addEventListener("click", () => {
          searchForm.classList.remove("has-results");
          if (item.element) {
            item.element.classList.remove("panel-search-hidden");
            item.element.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        });
        searchResults.appendChild(result);
      });

      searchForm.classList.add("has-results");
      return matches;
    };

    searchInput.addEventListener("input", () => renderResults(searchInput.value));

    searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const matches = renderResults(searchInput.value);
      if (!matches.length) return;
      window.location.href = matches[0].href;
    });

    document.addEventListener("click", (event) => {
      if (!searchForm.contains(event.target)) {
        searchForm.classList.remove("has-results");
      }
    });
  }

  const chartCanvas = document.getElementById("applicationStatusChart");
  if (chartCanvas && window.Chart) {
    const labels = JSON.parse(chartCanvas.dataset.labels || "[]");
    const approved = JSON.parse(chartCanvas.dataset.approved || "[]");
    const pending = JSON.parse(chartCanvas.dataset.pending || "[]");
    const rejected = JSON.parse(chartCanvas.dataset.rejected || "[]");

    new Chart(chartCanvas, {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Onaylanan", data: approved, backgroundColor: "#32c391", borderRadius: 5 },
          { label: "Bekleyen", data: pending, backgroundColor: "#ff9f43", borderRadius: 5 },
          { label: "Reddedilen", data: rejected, backgroundColor: "#f5577b", borderRadius: 5 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#cbd5e1", boxWidth: 12 } },
        },
        scales: {
          x: {
            ticks: { color: "#9aa8bd" },
            grid: { color: "rgba(148, 163, 184, 0.10)" },
          },
          y: {
            beginAtZero: true,
            ticks: { color: "#9aa8bd", precision: 0 },
            grid: { color: "rgba(148, 163, 184, 0.14)" },
          },
        },
      },
    });
  }
})();
