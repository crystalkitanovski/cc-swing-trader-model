"use strict";

const STORAGE_KEY = "homeworkTracker.assignments.v2";
const SUBJECTS_KEY = "homeworkTracker.subjects.v1";
const DEFAULT_SUBJECTS = ["Math", "Science", "English", "History", "Language", "Elective"];
const CHECK_INTERVAL_MS = 15 * 60 * 1000; // re-check reminders every 15 min while app is open

let assignments = load(STORAGE_KEY, []);
let subjects = load(SUBJECTS_KEY, DEFAULT_SUBJECTS);
let currentFilter = "all";

// ---------- storage helpers ----------

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    console.error("Failed to load", key, e);
    return fallback;
  }
}

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(assignments));
  localStorage.setItem(SUBJECTS_KEY, JSON.stringify(subjects));
}

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

// ---------- date helpers ----------

function todayStr() {
  return toDateStr(new Date());
}

function toDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function daysUntil(dateStr) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(dateStr + "T00:00:00");
  return Math.round((due - today) / 86400000);
}

function formatDue(dateStr) {
  const diff = daysUntil(dateStr);
  const due = new Date(dateStr + "T00:00:00");
  const opts = { weekday: "short", month: "short", day: "numeric" };
  const label = due.toLocaleDateString(undefined, opts);
  if (diff === 0) return `Today · ${label}`;
  if (diff === 1) return `Tomorrow · ${label}`;
  if (diff === -1) return `Yesterday · ${label}`;
  if (diff < 0) return `${Math.abs(diff)} days overdue · ${label}`;
  return `In ${diff} days · ${label}`;
}

function bucketFor(dateStr) {
  const diff = daysUntil(dateStr);
  if (diff < 0) return { key: "overdue", label: "Overdue", color: "red" };
  if (diff === 0) return { key: "today", label: "Due Today", color: "red" };
  if (diff === 1) return { key: "tomorrow", label: "Due Tomorrow", color: "amber" };
  if (diff <= 7) return { key: "week", label: "Due This Week", color: "amber" };
  return { key: "later", label: "Later", color: "green" };
}

// ---------- CRUD ----------

function addAssignment(data) {
  assignments.push({
    id: uid(),
    subject: data.subject.trim(),
    title: data.title.trim(),
    notes: (data.notes || "").trim(),
    dueDate: data.dueDate,
    reminderLead: Number(data.reminderLead),
    completed: false,
    completedAt: null,
    createdAt: Date.now(),
    lastNotifiedDate: null,
  });
  rememberSubject(data.subject.trim());
  save();
  render();
}

function updateAssignment(id, data) {
  const a = assignments.find((x) => x.id === id);
  if (!a) return;
  a.subject = data.subject.trim();
  a.title = data.title.trim();
  a.notes = (data.notes || "").trim();
  a.dueDate = data.dueDate;
  a.reminderLead = Number(data.reminderLead);
  a.lastNotifiedDate = null; // allow re-notify if due date changed
  rememberSubject(data.subject.trim());
  save();
  render();
}

function deleteAssignment(id) {
  assignments = assignments.filter((x) => x.id !== id);
  save();
  render();
}

function toggleComplete(id) {
  const a = assignments.find((x) => x.id === id);
  if (!a) return;
  a.completed = !a.completed;
  a.completedAt = a.completed ? Date.now() : null;
  save();
  render();
}

function rememberSubject(subject) {
  if (subject && !subjects.includes(subject)) {
    subjects.push(subject);
  }
}

// ---------- rendering ----------

const $ = (sel) => document.querySelector(sel);

function render() {
  renderSubjectList();
  renderSummary();
  renderFilters();
  renderLists();
}

function renderSubjectList() {
  const dl = $("#subjectList");
  dl.innerHTML = subjects.map((s) => `<option value="${escapeHtml(s)}"></option>`).join("");
}

function renderSummary() {
  const active = assignments.filter((a) => !a.completed);
  const overdue = active.filter((a) => daysUntil(a.dueDate) < 0).length;
  const dueSoon = active.filter((a) => {
    const d = daysUntil(a.dueDate);
    return d === 0 || d === 1;
  }).length;
  const upcoming = active.length - overdue - dueSoon;

  const pills = [];
  if (overdue > 0) pills.push(`<span class="pill red">⚠️ ${overdue} overdue</span>`);
  pills.push(`<span class="pill amber">⏰ ${dueSoon} due today/tomorrow</span>`);
  pills.push(`<span class="pill green">📅 ${upcoming} upcoming</span>`);
  $("#summary").innerHTML = pills.join("");
}

function renderFilters() {
  const usedSubjects = [...new Set(assignments.map((a) => a.subject))].sort();
  const buttons = ["all", ...usedSubjects];
  $("#filters").innerHTML = buttons
    .map((s) => {
      const label = s === "all" ? "All" : s;
      const active = s === currentFilter ? "active" : "";
      return `<button data-filter="${escapeHtml(s)}" class="${active}">${escapeHtml(label)}</button>`;
    })
    .join("");
  $("#filters").querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentFilter = btn.dataset.filter;
      render();
    });
  });
}

function renderLists() {
  const groupsOrder = [
    { key: "overdue", label: "Overdue", color: "red" },
    { key: "today", label: "Due Today", color: "red" },
    { key: "tomorrow", label: "Due Tomorrow", color: "amber" },
    { key: "week", label: "Due This Week", color: "amber" },
    { key: "later", label: "Later", color: "green" },
  ];

  const active = assignments
    .filter((a) => !a.completed)
    .filter((a) => currentFilter === "all" || a.subject === currentFilter)
    .sort((a, b) => a.dueDate.localeCompare(b.dueDate));

  const byGroup = {};
  for (const a of active) {
    const b = bucketFor(a.dueDate);
    (byGroup[b.key] = byGroup[b.key] || []).push(a);
  }

  let html = "";
  for (const g of groupsOrder) {
    const items = byGroup[g.key];
    if (!items || items.length === 0) continue;
    html += `<div class="group-title"><span class="dot ${g.color}"></span>${g.label}</div>`;
    html += items.map((a) => cardHtml(a, g.color)).join("");
  }
  $("#lists").innerHTML = html;
  $("#emptyState").classList.toggle("hidden", assignments.length > 0);

  const completed = assignments
    .filter((a) => a.completed)
    .filter((a) => currentFilter === "all" || a.subject === currentFilter)
    .sort((a, b) => (b.completedAt || 0) - (a.completedAt || 0));
  $("#completedCount").textContent = completed.length;
  $("#completedList").innerHTML = completed.map((a) => cardHtml(a, "gray")).join("");

  document.querySelectorAll(".card .check").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleComplete(el.closest(".card").dataset.id);
    });
  });
  document.querySelectorAll(".card .body").forEach((el) => {
    el.addEventListener("click", () => openEditDialog(el.closest(".card").dataset.id));
  });
}

function cardHtml(a, color) {
  const completedClass = a.completed ? "completed" : "";
  return `
    <div class="card ${color} ${completedClass}" data-id="${a.id}">
      <button class="check" aria-label="Mark complete"></button>
      <div class="body">
        <div class="subject">${escapeHtml(a.subject)}</div>
        <div class="title">${escapeHtml(a.title)}</div>
        <div class="meta">${formatDue(a.dueDate)}</div>
        ${a.notes ? `<div class="notes">${escapeHtml(a.notes)}</div>` : ""}
      </div>
    </div>`;
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// ---------- add form ----------

$("#addToggle").addEventListener("click", () => {
  $("#addForm").classList.remove("hidden");
  $("#addToggle").classList.add("hidden");
  $("#dueDate").valueAsDate = new Date();
  $("#subject").focus();
});

$("#cancelAdd").addEventListener("click", () => {
  $("#addForm").reset();
  $("#addForm").classList.add("hidden");
  $("#addToggle").classList.remove("hidden");
});

$("#addForm").addEventListener("submit", (e) => {
  e.preventDefault();
  addAssignment({
    subject: $("#subject").value,
    title: $("#title").value,
    notes: $("#notes").value,
    dueDate: $("#dueDate").value,
    reminderLead: $("#reminderLead").value,
  });
  $("#addForm").reset();
  $("#addForm").classList.add("hidden");
  $("#addToggle").classList.remove("hidden");
  showToast("Assignment added");
});

// ---------- edit dialog ----------

function openEditDialog(id) {
  const a = assignments.find((x) => x.id === id);
  if (!a) return;
  $("#editId").value = a.id;
  $("#editSubject").value = a.subject;
  $("#editDueDate").value = a.dueDate;
  $("#editTitle").value = a.title;
  $("#editNotes").value = a.notes;
  $("#editReminderLead").value = String(a.reminderLead);
  $("#editDialogBackdrop").classList.remove("hidden");
}

function closeEditDialog() {
  $("#editDialogBackdrop").classList.add("hidden");
}

$("#cancelEdit").addEventListener("click", closeEditDialog);
$("#editDialogBackdrop").addEventListener("click", (e) => {
  if (e.target.id === "editDialogBackdrop") closeEditDialog();
});

$("#editForm").addEventListener("submit", (e) => {
  e.preventDefault();
  updateAssignment($("#editId").value, {
    subject: $("#editSubject").value,
    title: $("#editTitle").value,
    notes: $("#editNotes").value,
    dueDate: $("#editDueDate").value,
    reminderLead: $("#editReminderLead").value,
  });
  closeEditDialog();
  showToast("Changes saved");
});

$("#deleteBtn").addEventListener("click", () => {
  const id = $("#editId").value;
  if (confirm("Delete this assignment?")) {
    deleteAssignment(id);
    closeEditDialog();
    showToast("Assignment deleted");
  }
});

// ---------- toast ----------

let toastTimer;
function showToast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 2200);
}

// ---------- export / import ----------

$("#exportBtn").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify({ assignments, subjects }, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `homework-backup-${todayStr()}.json`;
  link.click();
  URL.revokeObjectURL(url);
});

$("#importInput").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    if (!Array.isArray(data.assignments)) throw new Error("Invalid file");
    assignments = data.assignments;
    subjects = Array.isArray(data.subjects) ? data.subjects : subjects;
    save();
    render();
    showToast("Backup imported");
  } catch (err) {
    alert("Couldn't import that file: " + err.message);
  }
  e.target.value = "";
});

// ---------- notifications ----------

function updateNotifyBtn() {
  const btn = $("#notifyBtn");
  if (!("Notification" in window)) {
    btn.textContent = "🔔 Not supported";
    btn.disabled = true;
    return;
  }
  if (Notification.permission === "granted") {
    btn.textContent = "🔔 Reminders: on";
  } else if (Notification.permission === "denied") {
    btn.textContent = "🔕 Reminders blocked";
  } else {
    btn.textContent = "🔔 Reminders: off";
  }
}

$("#notifyBtn").addEventListener("click", async () => {
  if (!("Notification" in window)) return;
  if (Notification.permission === "default") {
    const perm = await Notification.requestPermission();
    updateNotifyBtn();
    if (perm === "granted") {
      new Notification("Reminders on! 🎉", {
        body: "I'll remind you here when homework is due soon. Keep this app open or check back daily.",
      });
      checkReminders();
    }
  } else if (Notification.permission === "denied") {
    alert(
      "Notifications are blocked in your browser settings. To turn reminders on, allow notifications for this site in your browser's site settings."
    );
  } else {
    updateNotifyBtn();
  }
});

function checkReminders() {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  const today = todayStr();
  let changed = false;
  for (const a of assignments) {
    if (a.completed) continue;
    const remindDate = addDays(a.dueDate, -a.reminderLead);
    const shouldRemind = today >= remindDate && a.lastNotifiedDate !== today;
    if (shouldRemind) {
      const diff = daysUntil(a.dueDate);
      let body;
      if (diff < 0) body = `Overdue by ${Math.abs(diff)} day(s)!`;
      else if (diff === 0) body = "Due today!";
      else if (diff === 1) body = "Due tomorrow.";
      else body = `Due in ${diff} days.`;
      try {
        new Notification(`${a.subject}: ${a.title}`, { body, tag: a.id });
      } catch (e) {
        console.error("Notification failed", e);
      }
      a.lastNotifiedDate = today;
      changed = true;
    }
  }
  if (changed) save();
}

function addDays(dateStr, days) {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + days);
  return toDateStr(d);
}

// ---------- init ----------

updateNotifyBtn();
render();
checkReminders();
setInterval(checkReminders, CHECK_INTERVAL_MS);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") checkReminders();
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch((e) => console.error("SW registration failed", e));
  });
}
