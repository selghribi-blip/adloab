/* لوحة التحكم — كل الطلبات نسبية (نفس الأصل)، بلا أي نظام خارجي. */

const REFRESH_MS = 15000;
let sparklines = {};

const fmtMs = (v) => (v == null ? "—" : `${Math.round(v)} ms`);
const fmtTime = (ts) => (ts ? new Date(ts * 1000).toLocaleTimeString("ar-MA") : "—");
const fmtDateTime = (ts) => (ts ? new Date(ts * 1000).toLocaleString("ar-MA") : "—");
const duration = (a, b) => {
  if (!a) return "—";
  const secs = Math.round(((b || Date.now() / 1000) - a));
  if (secs < 60) return `${secs} ثانية`;
  if (secs < 3600) return `${Math.round(secs / 60)} دقيقة`;
  return `${(secs / 3600).toFixed(1)} ساعة`;
};

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function statusBadge(latest) {
  if (!latest) return { cls: "unknown", text: "بانتظار أول فحص" };
  if (latest.ok) return { cls: "ok", text: "سليم" };
  return { cls: "bad", text: `متوقف (${latest.status_code || "بلا رد"})` };
}

function drawSparkline(canvas, checks) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * dpr; canvas.height = h * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  if (!checks.length) return;

  const values = checks.map((c) => (c.ok ? c.total_ms || 0 : null));
  const known = values.filter((v) => v != null);
  const max = Math.max(...known, 1);
  const stepX = checks.length > 1 ? w / (checks.length - 1) : w;

  // خط الصفر
  ctx.strokeStyle = "rgba(139,150,184,.25)";
  ctx.beginPath(); ctx.moveTo(0, h - 1); ctx.lineTo(w, h - 1); ctx.stroke();

  ctx.lineWidth = 2;
  ctx.strokeStyle = "#4f7cff";
  ctx.beginPath();
  let started = false;
  checks.forEach((c, i) => {
    const x = i * stepX;
    if (c.total_ms == null) { started = false; return; }
    const y = h - 4 - (c.total_ms / max) * (h - 10);
    if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
  });
  ctx.stroke();

  // نقاط الإخفاق
  ctx.fillStyle = "#ef4444";
  checks.forEach((c, i) => {
    if (c.ok) return;
    ctx.beginPath();
    ctx.arc(i * stepX, h - 4, 3, 0, Math.PI * 2);
    ctx.fill();
  });

  // الخطوة قبل الأخيرة: خط أفقي خفيف لأقصى قيمة
  ctx.fillStyle = "rgba(139,150,184,.7)";
  ctx.font = "10px sans-serif";
  ctx.fillText(`${Math.round(max)} ms`, 4, 10);
}

function renderCard(target) {
  const latest = target.latest;
  const stats = target.stats || {};
  const badge = statusBadge(latest);
  const card = document.createElement("article");
  card.className = "card";
  card.innerHTML = `
    <div class="card-head">
      <div>
        <h3>${target.name}</h3>
        <div class="url">${target.url}</div>
      </div>
      <span class="badge ${badge.cls}">${badge.text}</span>
    </div>
    <div class="metrics">
      <div class="metric"><span>زمن الاستجابة</span><b>${fmtMs(latest?.total_ms)}</b></div>
      <div class="metric"><span>أول بايت (TTFB)</span><b>${fmtMs(latest?.ttfb_ms)}</b></div>
      <div class="metric"><span>توفّر 24س</span><b>${stats.uptime_pct != null ? stats.uptime_pct + "%" : "—"}</b></div>
      <div class="metric"><span>p95</span><b>${fmtMs(stats.p95_ms)}</b></div>
      <div class="metric"><span>SSL متبقٍ</span><b>${stats.tls_days_left != null ? Math.round(stats.tls_days_left) + " يوم" : "—"}</b></div>
      <div class="metric"><span>آخر فحص</span><b>${fmtTime(latest?.ts)}</b></div>
    </div>
    <canvas data-target="${target.id}"></canvas>
    <div class="reason">${latest?.reason || ""}</div>
    <div class="card-foot">
      <span class="muted small">كل ${target.interval_seconds} ثانية${target.browser_check ? " · فحص متصفح" : ""}</span>
      <button class="btn ghost" data-check="${target.id}">افحص الآن</button>
    </div>`;
  card.querySelector("[data-check]").addEventListener("click", async (e) => {
    e.target.disabled = true;
    e.target.textContent = "جارٍ الفحص…";
    try {
      await api(`/api/targets/${target.id}/check`, { method: "POST" });
      await refresh();
    } catch (err) {
      alert("تعذّر تنفيذ الفحص: " + err.message);
    }
  });
  return card;
}

async function renderSparklines(targets) {
  await Promise.all(
    targets.map(async (t) => {
      try {
        const data = await api(`/api/targets/${t.id}/checks?limit=60`);
        const canvas = document.querySelector(`canvas[data-target="${t.id}"]`);
        if (canvas) drawSparkline(canvas, data.checks);
      } catch { /* تجاهل */ }
    })
  );
}

function renderIncidents(rows, targets) {
  const names = Object.fromEntries(targets.map((t) => [t.id, t.name]));
  const tbody = document.querySelector("#incidents tbody");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="muted">لا توجد حوادث مسجّلة.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows
    .map(
      (i) => `<tr>
        <td>${names[i.target_id] || i.target_id}</td>
        <td>${fmtDateTime(i.started_at)}</td>
        <td>${i.resolved_at ? fmtDateTime(i.resolved_at) : '<span style="color:var(--bad)">مستمرة</span>'}</td>
        <td>${duration(i.started_at, i.resolved_at)}</td>
        <td class="muted">${(i.reason || "").slice(0, 120)}</td>
      </tr>`
    )
    .join("");
}

async function refresh() {
  const data = await api("/api/status");
  const targets = data.targets;

  document.querySelector("#t-targets").textContent = targets.length;
  const up = targets.map((t) => t.stats?.uptime_pct).filter((v) => v != null);
  document.querySelector("#t-uptime").textContent = up.length
    ? (up.reduce((a, b) => a + b, 0) / up.length).toFixed(2) + "%"
    : "—";
  const lat = targets.map((t) => t.stats?.avg_ms).filter((v) => v != null);
  document.querySelector("#t-latency").textContent = lat.length
    ? Math.round(lat.reduce((a, b) => a + b, 0) / lat.length) + " ms"
    : "—";
  document.querySelector("#t-incidents").textContent = data.incidents_open.length;
  document.querySelector("#last-update").textContent = "آخر تحديث: " + new Date().toLocaleTimeString("ar-MA");

  const cards = document.querySelector("#cards");
  cards.innerHTML = "";
  targets.forEach((t) => cards.appendChild(renderCard(t)));

  renderSparklines(targets);
  renderIncidents(await api("/api/incidents?limit=30").then((d) => d.incidents), targets);
}

async function loadDomains() {
  try {
    const { owned_domains } = await api("/api/config/domains");
    document.querySelector("#domains").innerHTML = owned_domains
      .map((d) => `<span class="chip">${d}</span>`)
      .join("");
  } catch { /* تجاهل */ }
}

document.querySelector("#check-all").addEventListener("click", async (e) => {
  e.target.disabled = true;
  e.target.textContent = "جارٍ فحص كل الأهداف…";
  try {
    await api("/api/check-all", { method: "POST" });
    await refresh();
  } finally {
    e.target.disabled = false;
    e.target.textContent = "افحص كل الأهداف الآن";
  }
});

refresh().catch((e) => console.error(e));
loadDomains();
setInterval(() => refresh().catch(() => {}), REFRESH_MS);
