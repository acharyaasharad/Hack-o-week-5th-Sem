/* charts.js — Plotly chart rendering helpers for Customer Segmentation Dashboard */

const ChartManager = {
  // Chart Color Palette: Distinguishable, Accessible, Distinguishable Noise (-1)
  clusterColors: [
    "#0284c7", // Cluster 0: Sky Blue
    "#059669", // Cluster 1: Emerald Green
    "#d97706", // Cluster 2: Amber
    "#7c3aed", // Cluster 3: Violet
    "#e11d48", // Cluster 4: Rose
    "#0891b2", // Cluster 5: Cyan
    "#4f46e5", // Cluster 6: Indigo
  ],
  noiseColor: "#94a3b8", // Muted Slate for DBSCAN Outliers / Noise (-1)

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

  renderClusterSizeBar(divId, clusterSizes) {
    if (!clusterSizes || Object.keys(clusterSizes).length === 0) {
      document.getElementById(divId).innerHTML = "<div class='text-muted p-4 text-center'>No cluster size data available</div>";
      return;
    }

    const labels = Object.keys(clusterSizes);
    const counts = Object.values(clusterSizes);
    const colors = labels.map(l => l.includes("-1") ? this.noiseColor : this.clusterColors[parseInt(l.replace(/\D/g, "") || 0) % this.clusterColors.length]);

    const trace = {
      x: labels,
      y: counts,
      type: "bar",
      marker: { color: colors, opacity: 0.85, line: { color: "#ffffff", width: 1.5 } },
      text: counts.map(c => `${c} customers`),
      textposition: "auto",
    };

    const layout = this.defaultLayout("Customer Cluster Sizes");
    layout.yaxis = { gridcolor: "#f1f5f9", title: "Number of Customers" };
    Plotly.newPlot(divId, [trace], layout, { responsive: true, displayModeBar: false });
  },

  renderPcaScatter(divId, pcaData) {
    if (!pcaData || !pcaData.available) {
      document.getElementById(divId).innerHTML = "<div class='text-muted p-4 text-center'>PCA projection unavailable</div>";
      return;
    }

    const xVals = pcaData.pca_x;
    const yVals = pcaData.pca_y;
    const labels = pcaData.labels;

    // Separate traces per cluster for clean legend toggling
    const uniqueClusters = Array.from(new Set(labels)).sort((a,b) => a - b);
    const traces = uniqueClusters.map(cid => {
      const isNoise = (cid === -1);
      const idxs = labels.map((l, i) => l === cid ? i : -1).filter(i => i !== -1);
      const name = isNoise ? "Noise Outliers (-1)" : `Cluster ${cid}`;
      const color = isNoise ? this.noiseColor : this.clusterColors[cid % this.clusterColors.length];

      return {
        x: idxs.map(i => xVals[i]),
        y: idxs.map(i => yVals[i]),
        mode: "markers",
        type: "scatter",
        name: name,
        marker: {
          size: isNoise ? 6 : 9,
          color: color,
          opacity: isNoise ? 0.5 : 0.85,
          line: { width: 1, color: isNoise ? "#64748b" : "#ffffff" },
        },
        hoverinfo: "text",
        text: idxs.map(i => `${name}<br>PC1: ${xVals[i]}<br>PC2: ${yVals[i]}`),
      };
    });

    const layout = this.defaultLayout(`PCA 2D Cluster Space (Explained Variance: ${pcaData.total_explained_variance}%)`);
    layout.xaxis = { title: `Principal Component 1 (${pcaData.explained_variance_ratio[0]}%)`, gridcolor: "#f1f5f9" };
    layout.yaxis = { title: `Principal Component 2 (${pcaData.explained_variance_ratio[1]}%)`, gridcolor: "#f1f5f9" };
    layout.legend = { orientation: "h", y: -0.2 };

    Plotly.newPlot(divId, traces, layout, { responsive: true, displayModeBar: true });
  },

  renderSpendingProfileRadar(divId, profiles, numericFeatures) {
    if (!profiles || !profiles.clusters) {
      document.getElementById(divId).innerHTML = "<div class='text-muted p-4 text-center'>No profile data available</div>";
      return;
    }

    const clusters = profiles.clusters;
    const traces = [];

    Object.entries(clusters).forEach(([name, cdata]) => {
      if (cdata.is_noise) return; // Skip noise in general radar
      const cid = cdata.cluster_id;
      const rVals = numericFeatures.map(f => cdata.relative_index[f] || 1.0);
      // Close the loop
      rVals.push(rVals[0]);
      const thetaVals = [...numericFeatures, numericFeatures[0]];

      traces.push({
        type: "scatterpolar",
        r: rVals,
        theta: thetaVals,
        fill: "toself",
        opacity: 0.6,
        name: name,
        marker: { color: this.clusterColors[cid % this.clusterColors.length] },
      });
    });

    const layout = {
      title: { text: "Relative Category Spending Profile (Ratio vs Dataset Mean)", font: { size: 14 } },
      margin: { l: 40, r: 40, t: 40, b: 40 },
      paper_bgcolor: "transparent",
      polar: {
        radialaxis: { visible: true, range: [0, Math.max(3, 4)], gridcolor: "#e2e8f0" },
      },
      showlegend: true,
      legend: { orientation: "h", y: -0.15 },
    };

    Plotly.newPlot(divId, traces, layout, { responsive: true, displayModeBar: false });
  },

  renderElbowCurve(divId, elbowData) {
    if (!elbowData || !elbowData.k_values) {
      document.getElementById(divId).innerHTML = "<div class='text-muted p-4 text-center'>Elbow data unavailable</div>";
      return;
    }

    const traceInertia = {
      x: elbowData.k_values,
      y: elbowData.inertias,
      type: "scatter",
      mode: "lines+markers",
      name: "Inertia (Within-Cluster Sum of Squares)",
      line: { color: "#0284c7", width: 2.5 },
      marker: { size: 7 },
    };

    const traceSil = {
      x: elbowData.k_values,
      y: elbowData.silhouette_scores,
      type: "scatter",
      mode: "lines+markers",
      name: "Silhouette Score",
      yaxis: "y2",
      line: { color: "#059669", width: 2, dash: "dot" },
      marker: { size: 6 },
    };

    const layout = this.defaultLayout("K-Means Elbow Curve & Silhouette Comparison");
    layout.xaxis = { title: "Number of Clusters (k)", gridcolor: "#f1f5f9", dtick: 1 };
    layout.yaxis = { title: "Inertia", gridcolor: "#f1f5f9" };
    layout.yaxis2 = {
      title: "Silhouette Score",
      overlaying: "y",
      side: "right",
      showgrid: false,
      range: [-0.1, 1],
    };
    layout.legend = { orientation: "h", y: -0.2 };

    Plotly.newPlot(divId, [traceInertia, traceSil], layout, { responsive: true, displayModeBar: false });
  },

  renderCorrelationHeatmap(divId, corrData) {
    if (!corrData || !corrData.columns || corrData.columns.length === 0) {
      document.getElementById(divId).innerHTML = "<div class='text-muted p-4 text-center'>No correlation data available</div>";
      return;
    }

    const trace = {
      z: corrData.z,
      x: corrData.columns,
      y: corrData.columns,
      type: "heatmap",
      colorscale: "Blues",
      zmin: -1,
      zmax: 1,
      hoverongaps: false,
    };

    const layout = this.defaultLayout("Pairwise Feature Correlation (Pearson r)");
    layout.margin = { l: 80, r: 40, t: 40, b: 60 };

    Plotly.newPlot(divId, [trace], layout, { responsive: true, displayModeBar: false });
  },

  renderDendrogram(divId, dendroData) {
    if (!dendroData || !dendroData.available) {
      document.getElementById(divId).innerHTML = `<div class='alert alert-warning'>${dendroData ? dendroData.reason : "Dendrogram unavailable"}</div>`;
      return;
    }

    const traces = [];
    for (let i = 0; i < dendroData.icoord.length; i++) {
      traces.push({
        x: dendroData.icoord[i],
        y: dendroData.dcoord[i],
        mode: "lines",
        line: { color: dendroData.color_list[i] || "#0284c7", width: 1.5 },
        hoverinfo: "y",
        showlegend: false,
      });
    }

    const layout = this.defaultLayout(`Hierarchical Dendrogram (${dendroData.linkage_method.toUpperCase()} linkage &bull; ${dendroData.metric})`);
    layout.xaxis = { showticklabels: false, showgrid: false, zeroline: false };
    layout.yaxis = { title: "Distance / Dissimilarity Threshold", gridcolor: "#f1f5f9" };

    Plotly.newPlot(divId, traces, layout, { responsive: true, displayModeBar: false });
  }
};
