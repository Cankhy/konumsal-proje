(function () {
  const fallbackSchools = {
    "Ankara Üniversitesi": [
      "Bilgisayar Programcılığı",
      "Coğrafya",
      "Hukuk",
      "İktisat",
      "İletişim",
      "İşletme",
      "Siyaset Bilimi ve Kamu Yönetimi",
      "Yönetim Bilişim Sistemleri",
    ],
    "Gazi Üniversitesi": [
      "Bilgisayar Mühendisliği",
      "Elektrik-Elektronik Mühendisliği",
      "Endüstri Mühendisliği",
      "Harita Mühendisliği",
      "İnşaat Mühendisliği",
      "Makine Mühendisliği",
      "Mimarlık",
    ],
  };

  const schools = window.KONUMSAL_EDUCATION_OPTIONS || fallbackSchools;
  const schoolNames = Object.keys(schools).sort((a, b) => a.localeCompare(b, "tr"));

  function normalize(value) {
    return String(value || "")
      .toLocaleLowerCase("tr")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function filterValues(values, query) {
    const normalizedQuery = normalize(query);
    if (!normalizedQuery) return values.slice(0, 80);
    const starts = [];
    const includes = [];
    values.forEach((value) => {
      const normalizedValue = normalize(value);
      if (normalizedValue.startsWith(normalizedQuery)) starts.push(value);
      else if (normalizedValue.includes(normalizedQuery)) includes.push(value);
    });
    return starts.concat(includes).slice(0, 80);
  }

  function closeList(list) {
    list.classList.remove("is-open");
    list.innerHTML = "";
  }

  function renderList(list, values, onPick) {
    list.innerHTML = "";
    if (!values.length) {
      const empty = document.createElement("div");
      empty.className = "combo-search-empty";
      empty.textContent = "Sonuç bulunamadı";
      list.appendChild(empty);
      list.classList.add("is-open");
      return;
    }

    values.forEach((value) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = value;
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        onPick(value);
      });
      list.appendChild(button);
    });
    list.classList.add("is-open");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const schoolHidden = document.querySelector("[data-education-school]");
    const departmentHidden = document.querySelector("[data-education-department]");
    const schoolInput = document.querySelector("[data-combo-input='school']");
    const departmentInput = document.querySelector("[data-combo-input='department']");
    const schoolList = document.querySelector("[data-combo-list='school']");
    const departmentList = document.querySelector("[data-combo-list='department']");
    if (!schoolHidden || !departmentHidden || !schoolInput || !departmentInput || !schoolList || !departmentList) return;

    function selectedDepartments() {
      return schools[schoolHidden.value] || [];
    }

    function pickSchool(value) {
      schoolHidden.value = value;
      schoolInput.value = value;
      departmentHidden.value = "";
      departmentInput.value = "";
      departmentInput.placeholder = "Bölüm adı yazın";
      closeList(schoolList);
      closeList(departmentList);
    }

    function pickDepartment(value) {
      departmentHidden.value = value;
      departmentInput.value = value;
      closeList(departmentList);
    }

    if (schoolHidden.value) schoolInput.value = schoolHidden.value;
    if (departmentHidden.value) departmentInput.value = departmentHidden.value;
    if (schoolHidden.value) departmentInput.placeholder = "Bölüm adı yazın";

    schoolInput.addEventListener("input", () => {
      schoolHidden.value = "";
      departmentHidden.value = "";
      departmentInput.value = "";
      departmentInput.placeholder = "Önce okul seçin";
      renderList(schoolList, filterValues(schoolNames, schoolInput.value), pickSchool);
    });

    schoolInput.addEventListener("focus", () => {
      renderList(schoolList, filterValues(schoolNames, schoolInput.value), pickSchool);
    });

    schoolInput.addEventListener("blur", () => setTimeout(() => closeList(schoolList), 120));

    departmentInput.addEventListener("input", () => {
      departmentHidden.value = "";
      renderList(departmentList, filterValues(selectedDepartments(), departmentInput.value), pickDepartment);
    });

    departmentInput.addEventListener("focus", () => {
      renderList(departmentList, filterValues(selectedDepartments(), departmentInput.value), pickDepartment);
    });

    departmentInput.addEventListener("blur", () => setTimeout(() => closeList(departmentList), 120));
  });
})();
