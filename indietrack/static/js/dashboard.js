/**
 * IndieTrack — Dashboard Visualizations with Chart.js
 */

document.addEventListener("DOMContentLoaded", () => {
  // Common chart styling tokens
  const colors = {
    purple: "#8b5cf6",
    blue: "#3b82f6",
    cyan: "#06b6d4",
    green: "#10b981",
    amber: "#f59e0b",
    grid: "rgba(255, 255, 255, 0.08)",
    text: "#94a3b8"
  };

  // 1. Performance Over Time Chart (Line Chart)
  const trendsCtx = document.getElementById("performanceTrendsChart");
  if (trendsCtx && window.dashboardData && window.dashboardData.timeSeries) {
    const ts = window.dashboardData.timeSeries;

    if (ts.labels && ts.labels.length > 0) {
      new Chart(trendsCtx, {
        type: "line",
        data: {
          labels: ts.labels,
          datasets: [
            {
              label: "Recorded Clicks",
              data: ts.clicks,
              borderColor: colors.cyan,
              backgroundColor: "rgba(6, 182, 212, 0.1)",
              tension: 0.3,
              fill: true,
              yAxisID: "y"
            },
            {
              label: "Reported Streams",
              data: ts.streams,
              borderColor: colors.purple,
              backgroundColor: "rgba(139, 92, 246, 0.1)",
              tension: 0.3,
              fill: true,
              yAxisID: "y"
            },
            {
              label: "Spend ($)",
              data: ts.spend,
              borderColor: colors.amber,
              backgroundColor: "rgba(245, 158, 11, 0.1)",
              borderDash: [4, 4],
              tension: 0.2,
              yAxisID: "y1"
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: {
            legend: {
              labels: { color: colors.text, font: { family: "system-ui", size: 12 } }
            },
            tooltip: {
              padding: 10,
              boxPadding: 4
            }
          },
          scales: {
            x: {
              grid: { color: colors.grid },
              ticks: { color: colors.text, font: { size: 11 } }
            },
            y: {
              type: "linear",
              position: "left",
              grid: { color: colors.grid },
              ticks: { color: colors.text, font: { size: 11 } },
              title: { display: true, text: "Clicks / Streams", color: colors.text }
            },
            y1: {
              type: "linear",
              position: "right",
              grid: { drawOnChartArea: false },
              ticks: { color: colors.amber, font: { size: 11 } },
              title: { display: true, text: "Spend ($)", color: colors.amber }
            }
          }
        }
      });
    } else {
      // Empty state placeholder
      const parent = trendsCtx.parentElement;
      parent.innerHTML = `
        <div class="text-center py-5 text-muted">
          <i class="bi bi-graph-up display-5 mb-2 opacity-50 d-block"></i>
          <p class="mb-0">No time-series metrics recorded yet.</p>
          <small class="text-secondary">Add daily metrics to your campaigns to view trends.</small>
        </div>
      `;
    }
  }

  // 2. Platform Distribution Chart (Doughnut Chart)
  const platformCtx = document.getElementById("platformDistributionChart");
  if (platformCtx && window.dashboardData && window.dashboardData.platforms) {
    const pData = window.dashboardData.platforms;

    if (pData.platforms && pData.platforms.length > 0) {
      new Chart(platformCtx, {
        type: "doughnut",
        data: {
          labels: pData.platforms,
          datasets: [
            {
              data: pData.spend,
              backgroundColor: [
                "#8b5cf6",
                "#3b82f6",
                "#06b6d4",
                "#10b981",
                "#f59e0b",
                "#ec4899",
                "#64748b"
              ],
              borderColor: "transparent",
              borderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: { color: colors.text, boxWidth: 12, padding: 14 }
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  return ` ${context.label}: $${context.raw.toFixed(2)} spend`;
                }
              }
            }
          },
          cutout: "70%"
        }
      });
    } else {
      const parent = platformCtx.parentElement;
      parent.innerHTML = `
        <div class="text-center py-5 text-muted">
          <i class="bi bi-pie-chart display-5 mb-2 opacity-50 d-block"></i>
          <p class="mb-0">No platform spend data available.</p>
        </div>
      `;
    }
  }
});
