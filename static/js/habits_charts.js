/*
static/js/habits_charts.js

Objetivo:
- Un solo JS para TODOS los gráficos de hábitos.
- Detecta si está en dashboard o detalle según existan elementos en el DOM.
- Consume endpoints /api/... y renderiza con Chart.js.
*/

/**
 * fetchJson(url)
 * - Llama a una URL
 * - Devuelve JSON si todo sale bien
 * - Devuelve null si hay error (para no romper la UI)
 */
async function fetchJson(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

/**
 * renderLineChart(canvas, labels, values)
 * - Gráfico de línea básico para tendencia.
 */
function renderLineChart(canvas, labels, values) {
  return new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          data: values,
          tension: 0.25,
          fill: true,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
        y: { beginAtZero: true },
      },
    },
  });
}

/**
 * renderBarChart(canvas, labels, values, horizontal=false)
 * - Barras para top hábitos o consistencia por weekday.
 */
function renderBarChart(canvas, labels, values, horizontal = false) {
  return new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{ data: values }],
    },
    options: {
      indexAxis: horizontal ? "y" : "x",
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true },
        x: horizontal ? { beginAtZero: true, max: 100 } : {},
      },
    },
  });
}

/**
 * renderHeatmap(container, fromIso, toIso, completedDates)
 * - Crea cuadritos por día (simple y efectivo).
 * - Usamos DocumentFragment para no hacer 180 appends directos al DOM.
 */
function renderHeatmap(container, fromIso, toIso, completedDates) {
  // Set para lookup O(1)
  const completedSet = new Set(completedDates);

  const from = new Date(`${fromIso}T00:00:00`);
  const to = new Date(`${toIso}T00:00:00`);

  const frag = document.createDocumentFragment();

  for (let d = new Date(from); d <= to; d.setDate(d.getDate() + 1)) {
    const iso = d.toISOString().slice(0, 10);

    const box = document.createElement("div");
    box.className = "habit-heatmap-cell"; // mejor que inline styles
    box.dataset.date = iso;
    box.title = iso;

    // Pintamos según completado
    if (completedSet.has(iso)) {
      box.classList.add("is-completed");
    }

    frag.appendChild(box);
  }

  // Limpiamos y pintamos de una
  container.innerHTML = "";
  container.appendChild(frag);
}

/**
 * initDashboardCharts()
 * - Se ejecuta solo si encuentra los canvas del dashboard
 */
async function initDashboardCharts() {
  const trendCanvas = document.getElementById("globalTrendChart");
  const topCanvas = document.getElementById("topHabitsChart");

  if (!trendCanvas || !topCanvas) return;

  const summary = await fetchJson("/api/habits/summary?range=30");
  if (!summary || !summary.series) return;

  renderLineChart(trendCanvas, summary.series.labels, summary.series.values);

  const topHabits = (summary.habits || []).slice(0, 6);
  renderBarChart(
    topCanvas,
    topHabits.map((item) => item.name),
    topHabits.map((item) => item.value),
    true
  );
}

/**
 * initDetailCharts()
 * - Se ejecuta solo si encuentra elementos del detalle
 */
async function initDetailCharts() {
  const seriesCanvas = document.getElementById("habitSeriesChart");
  const weekdayCanvas = document.getElementById("weekdayChart");
  const heatmapGrid = document.getElementById("heatmapGrid");

  if (!seriesCanvas || !weekdayCanvas || !heatmapGrid) return;

  // Habit id viene desde data-habit-id en el canvas
  const habitId = seriesCanvas.dataset.habitId;
  if (!habitId) return;

  const [seriesData, weekdayData, heatmapData] = await Promise.all([
    fetchJson(`/api/habits/${habitId}/series?range=90`),
    fetchJson("/api/habits/by_weekday?range=90"),
    fetchJson(`/api/habits/${habitId}/heatmap?range=180`),
  ]);

  if (seriesData) {
    renderBarChart(seriesCanvas, seriesData.labels, seriesData.values, false);
  }

  if (weekdayData) {
    renderBarChart(weekdayCanvas, weekdayData.labels, weekdayData.values, false);
  }

  if (heatmapData) {
    renderHeatmap(heatmapGrid, heatmapData.from, heatmapData.to, heatmapData.completed_dates);
  }
}

// Entry point único
(async function initHabitCharts() {
  await initDashboardCharts();
  await initDetailCharts();
})();