const fmt = new Intl.NumberFormat("uz-UZ", { maximumFractionDigits: 0 });

function money(x) {
  if (x === null || x === undefined || x === "") return "0";
  return fmt.format(Number(x)) + " so‘m";
}

function todayISO() {
  const d = new Date();
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function thisMonth() {
  const d = new Date();
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = body && body.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
        ? detail.map(d => d.msg || JSON.stringify(d)).join("; ")
        : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body;
}

const $ = id => document.getElementById(id);

async function loadDebtors() {
  const month = $("month").value;
  const state = $("debtors-state");
  const table = $("debtors-table");
  const tbody = $("debtors-body");
  state.textContent = "Yuklanmoqda…";
  state.className = "muted";
  table.hidden = true;

  try {
    const [debtors, students] = await Promise.all([
      api(`/api/debtors?month=${month}`),
      api("/api/students"),
    ]);

    $("stat-total").textContent = students.length;
    $("stat-debtors").textContent = debtors.length;
    const total = debtors.reduce((s, d) => s + Number(d.debt), 0);
    $("stat-debt").textContent = money(total);

    if (debtors.length === 0) {
      state.textContent = "Qarzdorlar yo‘q.";
      return;
    }

    tbody.innerHTML = "";
    for (const d of debtors) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td data-label="O‘quvchi">${escapeHtml(d.name)}<br><small class="muted">${escapeHtml(d.phone)}</small></td>
        <td data-label="Guruh">${escapeHtml(d.group)}</td>
        <td data-label="Oylik">${money(d.monthly_fee)}</td>
        <td data-label="To‘langan">${money(d.paid)}</td>
        <td data-label="Qarz" class="debt">${money(d.debt)}</td>`;
      tbody.appendChild(tr);
    }
    state.textContent = "";
    table.hidden = false;
  } catch (err) {
    state.textContent = "Xatolik: " + err.message;
    state.className = "feedback error";
  }
}

async function loadStudentsForSelect() {
  const sel = $("pay-student");
  try {
    const students = await api("/api/students");
    sel.innerHTML = "";
    if (students.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "— avval o‘quvchi qo‘shing —";
      opt.disabled = true;
      opt.selected = true;
      sel.appendChild(opt);
      return;
    }
    for (const s of students) {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.name} (${s.group})`;
      sel.appendChild(opt);
    }
  } catch (err) {
    sel.innerHTML = `<option disabled selected>Xatolik: ${err.message}</option>`;
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function submitPayment(ev) {
  ev.preventDefault();
  const feedback = $("pay-feedback");
  feedback.textContent = "";
  feedback.className = "feedback";

  const student_id = Number($("pay-student").value);
  const amount = $("pay-amount").value;
  const payment_date = $("pay-date").value;

  if (!student_id) { feedback.textContent = "O‘quvchini tanlang."; feedback.classList.add("error"); return; }

  try {
    await api("/api/payments", {
      method: "POST",
      body: JSON.stringify({ student_id, amount, payment_date }),
    });
    feedback.textContent = "To‘lov saqlandi ✓";
    feedback.classList.add("success");
    $("pay-amount").value = "";
    await loadDebtors();
  } catch (err) {
    feedback.textContent = "Xatolik: " + err.message;
    feedback.classList.add("error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("month").value = thisMonth();
  $("pay-date").value = todayISO();
  $("refresh").addEventListener("click", loadDebtors);
  $("month").addEventListener("change", loadDebtors);
  $("payment-form").addEventListener("submit", submitPayment);
  loadStudentsForSelect();
  loadDebtors();
});
