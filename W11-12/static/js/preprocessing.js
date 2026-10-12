/* preprocessing.js — Preprocessing validation and pipeline architecture helpers */

const PreprocessingManager = {
  getSelectedFeatures() {
    const checkboxes = document.querySelectorAll("input[name='pca_feature']:checked");
    return Array.from(checkboxes).map(cb => cb.value);
  },

  getPreprocessingConfig() {
    const scaler = document.getElementById("select-scaler").value;
    const logTransform = document.getElementById("checkbox-log-transform").checked;
    return { scaler, logTransform };
  }
};
