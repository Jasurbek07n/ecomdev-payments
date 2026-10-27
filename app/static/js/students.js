const fmt = new Intl.NumberFormat("uz-UZ", { maximumFractionDigits: 0 });
const money = x => (x === null || x === undefined ? "0" : fmt.format(Number(x)) + " so‘m");
const $ = id => document.getElementById(id);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = body && body.detail;
    const msg = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
      ? detail.map(d => d.msg || JSON.stringify(d)).join("; ")
      : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function loadStudents() {
  const state = $("students-state");
  const table = $("students-table");
  const tbody = $("students-body");
  state.textContent = "Yuklanmoqda…";
  state.className = "muted";
  table.hidden = true;

  try {
    const items = await api("/api/students");
    if (items.length === 0) {
      state.textContent = "O‘quvchilar yo‘q.";
      return;
    }
    tbody.innerHTML = "";
    for (const s of items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td data-label="Ism">${escapeHtml(s.name)}</td>
        <td data-label="Telefon">${escapeHtml(s.phone)}</td>
        <td data-label="Guruh">${escapeHtml(s.group)}</td>
        <td data-label="Oylik">${money(s.monthly_fee)}</td>
        <td><button class="btn danger" data-id="${s.id}">O‘chirish</button></td>`;
      tbody.appendChild(tr);
    }
    tbody.querySelectorAll("button[data-id]").forEach(b =>
      b.addEventListener("click", () => deleteStudent(Number(b.dataset.id)))
    );
    state.textContent = "";
    table.hidden = false;
  } catch (err) {
    state.textContent = "Xatolik: " + err.message;
    state.className = "feedback error";
  }
}

async function deleteStudent(id) {
  if (!confirm("O‘quvchini o‘chirishni tasdiqlaysizmi?")) return;
  try {
    const res = await fetch(`/api/students/${id}`, { method: "DELETE" });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    await loadStudents();
  } catch (err) {
    alert("Xatolik: " + err.message);
  }
}

async function createStudent(ev) {
  ev.preventDefault();
  const feedback = $("s-feedback");
  feedback.textContent = "";
  feedback.className = "feedback";
  try {
    await api("/api/students", {
      method: "POST",
      body: JSON.stringify({
        name: $("s-name").value,
        phone: $("s-phone").value,
        group: $("s-group").value,
        monthly_fee: $("s-fee").value,
      }),
    });
    feedback.textContent = "Qo‘shildi ✓";
    feedback.classList.add("success");
    ["s-name", "s-phone", "s-group", "s-fee"].forEach(id => ($(id).value = ""));
    await loadStudents();
  } catch (err) {
    feedback.textContent = "Xatolik: " + err.message;
    feedback.classList.add("error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("student-form").addEventListener("submit", createStudent);
  loadStudents();
});
