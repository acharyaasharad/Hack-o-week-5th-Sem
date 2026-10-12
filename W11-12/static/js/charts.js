/* charts.js — Plotly chart rendering helpers for PCA & t-SNE Studio */

const ChartManager = {
  palette: [
    "#4f46e5", // Indigo
    "#06b6d4", // Cyan
    "#10b981", // Emerald
    "#f59e0b", // Amber
    "#f43f5e", // Rose
    "#8b5cf6", // Purple
    "#3b82f6", // Blue
  ],

  getColorMap(uniqueCategories) {
    const map = {};
    uniqueCategories.forEach((cat, idx) => {
      map[cat] = this.palette[idx % this.palette.length];
    });
    return map;
  },

  defaultLayout(title) {
    return {
      title: { text: title, font: { size: 14, color: "#0f172a", family: "-apple-system, sans-serif" } },
      margin: { l: 45, r: 25, t: 40, b: 40 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: "-apple-system, sans-serif", color: "#475569", size: 12 },
      autosize: true,
      hovermode: "closest",
    };
  },

  renderScatter(divId, coordinates, title, xLabel, yLabel, is3D = false) {
    if (!coordinates || coordinates.length === 0) {
      document.getElementById(divId).innerHTML = "<div class='text-muted p-4 text-center'>No embedding coordinates available</div>";
      return;
    }

    const uniqueColors = Array.from(new Set(coordinates.map(c => c.color_value || "Default"))).sort();
    const colorMap = this.getColorMap(uniqueColors);

    const traces = uniqueColors.map(val => {
      const subset = coordinates.filter(c => (c.color_value || "Default") === val);
      const trace = {
        name: String(val),
        x: subset.map(c => c.x),
        y: subset.map(c => c.y),
        mode: "markers",
        marker: {
          size: is3D ? 4 : 7,
          color: colorMap[val],
          opacity: 0.85,
          line: { width: 0.8, color: "#ffffff" },
        },
        hoverinfo: "text",
        text: subset.map(c => `${c.row_id}<br>${val}<br>(${c.x}, ${c.y}${c.z !== undefined ? ', ' + c.z : ''})`),
        customdata: subset.map(c => c.row_id),
      };

      if (is3D) {
        trace.type = "scatter3d";
        trace.z = subset.map(c => c.z || 0.0);
      } else {
        trace.type = "scatter";
      }
      return trace;
    });

    const layout = this.defaultLayout(title);
    if (is3D) {
      layout.scene = {
        xaxis: { title: xLabel, gridcolor: "#e2e8f0" },
        yaxis: { title: yLabel, gridcolor: "#e2e8f0" },
        zaxis: { title: "Dimension 3", gridcolor: "#e2e8f0" },
      };
    } else {
      layout.xaxis = { title: xLabel, gridcolor: "#f1f5f9" };
      layout.yaxis = { title: yLabel, gridcolor: "#f1f5f9" };
    }
    layout.legend = { orientation: "h", y: -0.2 };

    Plotly.newPlot(divId, traces, layout, { responsive: true, displayModeBar: true });

    // Attach click inspection event
    const graphDiv = document.getElementById(divId);
    graphDiv.on('plotly_click', (data) => {
      if (data.points && data.points[0] && data.points[0].customdata) {
        const rowId = data.points[0].customdata;
        App.inspectPoint(rowId);
      }
    });
  },

  renderScreePlot(divId, expVar, cumVar) {
    if (!expVar || expVar.length === 0) return;

    const compLabels = expVar.map((_, i) => `PC${i+1}`);
    const traceBar = {
      x: compLabels,
      y: expVar,
      type: "bar",
      name: "Individual Variance (%)",
      marker: { color: "#4f46e5", opacity: 0.85 },
      text: expVar.map(v => `${v}%`),
      textposition: "auto",
    };

    const traceLine = {
      x: compLabels,
      y: cumVar,
      type: "scatter",
      mode: "lines+markers",
      name: "Cumulative Variance (%)",
      yaxis: "y2",
      line: { color: "#06b6d4", width: 2.5 },
      marker: { size: 6 },
    };

    const layout = this.defaultLayout("PCA Scree & Cumulative Explained Variance Plot");
    layout.yaxis = { title: "Individual Explained Variance (%)", gridcolor: "#f1f5f9", range: [0, Math.max(...expVar) * 1.2] };
    layout.yaxis2 = {
      title: "Cumulative Variance (%)",
      overlaying: "y",
      side: "right",
      showgrid: false,
      range: [0, 105],
    };
    layout.legend = { orientation: "h", y: -0.2 };

    Plotly.newPlot(divId, [traceBar, traceLine], layout, { responsive: true, displayModeBar: false });
  },

  renderLoadingsBar(divId, loadings, componentName = "PC1") {
    if (!loadings || loadings.length === 0) return;

    const filtered = loadings.filter(l => l.component === componentName)
      .sort((a,b) => Math.abs(b.loading) - Math.abs(a.loading));

    const trace = {
      x: filtered.map(l => l.feature),
      y: filtered.map(l => l.loading),
      type: "bar",
      marker: {
        color: filtered.map(l => l.loading >= 0 ? "#4f46e5" : "#f43f5e"),
        opacity: 0.85,
      },
      text: filtered.map(l => l.loading.toFixed(3)),
      textposition: "auto",
    };

    const layout = this.defaultLayout(`Principal Component Loadings (${componentName})`);
    layout.yaxis = { title: "Component Coefficient (Loading)", gridcolor: "#f1f5f9" };
    layout.xaxis = { tickangle: -35 };

    Plotly.newPlot(divId, [trace], layout, { responsive: true, displayModeBar: false });
  }
};
