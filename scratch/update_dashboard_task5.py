import re

target_file = r"frontend/js/dashboard.js"
with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace from `let activeMediaStream = null;` up to `async function renderMajorWHStorage(container) {`
old_pattern = re.compile(
    r"let activeMediaStream = null;.*?async function renderMajorWHStorage\(container\) \{",
    re.DOTALL
)

new_code = r'''let activeMediaStream = null;
let currentGradingSnapshotDataUrl = null;
let cachedActiveIntakes = [];

function toggleWebcamStream() {
  const video = document.getElementById("cameraVideo");
  const btn = document.getElementById("btnToggleWebcam");
  const captureBtn = document.getElementById("btnCaptureSnapshot");
  const statusEl = document.getElementById("cameraStatusIndicator");

  if (activeMediaStream) {
    activeMediaStream.getTracks().forEach(t => t.stop());
    activeMediaStream = null;
    if (video) {
      video.srcObject = null;
      video.style.display = "none";
    }
    if (btn) btn.innerHTML = "📹 Turn On Camera";
    if (captureBtn) captureBtn.style.display = "none";
    if (statusEl) statusEl.textContent = "Camera Standby (Off)";
    return;
  }

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } } })
      .then(stream => {
        activeMediaStream = stream;
        if (video) {
          video.srcObject = stream;
          video.style.display = "block";
        }
        if (btn) btn.innerHTML = "⏹️ Stop Camera";
        if (captureBtn) captureBtn.style.display = "inline-flex";
        if (statusEl) statusEl.innerHTML = '<span style="color:#2e7d32; font-weight:700;">🟢 Camera Streaming Live (Mobile/Desktop)</span>';
      })
      .catch(err => {
        alert("Unable to access camera: " + err.message + "\nYou can use the file upload or existing crop samples.");
      });
  } else {
    alert("Camera API not supported in this browser. Please use file upload.");
  }
}

function captureCameraSnapshot() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("cameraCanvas");
  const preview = document.getElementById("cameraSnapshotPreview");
  if (!video || !canvas || !preview) return;

  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL("image/jpeg", 0.90);
  currentGradingSnapshotDataUrl = dataUrl;
  preview.src = dataUrl;
  preview.style.display = "block";

  // Stop camera stream after snapshot
  toggleWebcamStream();
}

function previewUploadedGrainImage(event) {
  const file = event.target.files[0];
  if (!file) return;
  const preview = document.getElementById("cameraSnapshotPreview");
  if (!preview) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    currentGradingSnapshotDataUrl = e.target.result;
    preview.src = e.target.result;
    preview.style.display = "block";
  };
  reader.readAsDataURL(file);
}

async function renderMajorWHAIGradingConsole(container) {
  container.innerHTML = `
    <div class="table-container" style="border:none; background:transparent;">
      <div class="table-toolbar" style="margin-bottom:18px;">
        <div>
          <h3 style="display:flex; align-items:center; gap:8px;">
            <span>📷</span> Central AI Major Warehouse Crop Quality & Grading Console
          </h3>
          <span style="font-size:0.78rem; color:var(--text-muted);">
            Computer Vision Defect Analysis, 12 Optical Parameters & Dual-Storage Human Certification
          </span>
        </div>
        <div style="display:flex; gap:10px;">
          <button class="btn btn-secondary btn-sm" onclick="loadGradingHistoryTable()">
            📜 View Grading History
          </button>
        </div>
      </div>

      <!-- Prototype AI Model Notice -->
      <div class="alert-box" style="background:#e8f4fd; border:1px solid #90caf9; color:#0d47a1; margin-bottom:20px; font-size:0.82rem; padding:12px 16px; border-radius:6px;">
        <strong>ℹ️ Prototype AI Model Notice:</strong>
        Prototype AI model — requires real crop image training dataset for production accuracy.
        The AI prediction must <strong>NEVER</strong> become the final grade automatically. Human review and explicit confirmation are strictly required.
      </div>

      <div style="display:grid; grid-template-columns:1.2fr 0.8fr; gap:22px; align-items:start;">
        <!-- Left Column: Camera, Sample & Parameter Configuration -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:22px;">
          <h4 style="color:var(--primary-dark); margin-bottom:14px; font-size:0.95rem; border-bottom:1px solid #eee; padding-bottom:8px;">
            1. Select Batch & Capture Sample Frame
          </h4>

          <div class="form-grid" style="grid-template-columns:1fr 1fr; margin-bottom:16px;">
            <div class="form-group">
              <label class="form-label">Select Intake Batch *</label>
              <select id="cvBatchSelect" class="form-control" onchange="onGradingBatchSelected()">
                <option value="KS-BATCH-1001" selected>KS-BATCH-1001 (Wheat - Ramesh Patil)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Batch ID *</label>
              <input type="text" id="cvBatchId" class="form-control" value="KS-BATCH-1001" required>
            </div>
            <div class="form-group">
              <label class="form-label">Crop Variety *</label>
              <input type="text" id="cvCropName" class="form-control" value="Wheat (Lokwan)" required>
            </div>
            <div class="form-group">
              <label class="form-label">Supplying Farmer</label>
              <input type="text" id="cvFarmerName" class="form-control" value="Ramesh Narayan Patil (KS-FMR-1001)" readonly style="background:#f8f9fa;">
            </div>
          </div>

          <!-- Camera Stream & Snapshot Box -->
          <div class="camera-stream-box" style="background:#fdfdfd; border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <div id="cameraStatusIndicator" style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">
                Camera Standby (Laptop, Desktop, Mobile or Tablet)
              </div>
              <div style="display:flex; gap:8px;">
                <button type="button" id="btnToggleWebcam" class="btn btn-primary btn-sm" onclick="toggleWebcamStream()" style="background:#1565c0;">
                  📹 Turn On Camera
                </button>
                <button type="button" id="btnCaptureSnapshot" class="btn btn-primary btn-sm" onclick="captureCameraSnapshot()" style="background:#2e7d32; display:none;">
                  📸 Capture Image
                </button>
              </div>
            </div>

            <video id="cameraVideo" autoplay playsinline style="width:100%; max-height:260px; object-fit:cover; border-radius:6px; background:#111; display:none; margin-bottom:12px;"></video>
            <canvas id="cameraCanvas" style="display:none;"></canvas>
            
            <!-- Snapshot Preview -->
            <div id="snapshotContainer" style="text-align:center;">
              <img id="cameraSnapshotPreview" src="/uploads/grain_samples/KS-BATCH-1001_sample.svg" alt="Captured Grain Sample" style="width:100%; max-height:240px; object-fit:contain; border-radius:6px; border:1px solid #ddd; background:#1e272e; margin-bottom:10px;">
              <div style="font-size:0.75rem; color:var(--text-muted);">Active Inspection Frame: Lokwan Wheat Kernel Tray</div>
            </div>

            <div style="display:flex; align-items:center; gap:10px; font-size:0.8rem; color:var(--text-muted); border-top:1px dashed var(--border); padding-top:12px; margin-top:12px;">
              <span>📁 Or upload sample image file:</span>
              <input type="file" id="cameraUploadInput" accept="image/*" class="form-control" style="font-size:0.75rem; padding:4px 8px;" onchange="previewUploadedGrainImage(event)">
            </div>
          </div>

          <!-- Segregated Physical Measurements -->
          <div style="background:#fff8e1; border:1px solid #ffe082; border-radius:8px; padding:14px; margin-bottom:18px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
              <strong style="color:#b78103; font-size:0.83rem;">
                ⚖️ Physical / Manual Measurements (Segregated from Vision)
              </strong>
              <span class="badge badge-warning" style="font-size:0.68rem;">Physical Probe Required</span>
            </div>
            <p style="font-size:0.74rem; color:#795548; margin-bottom:10px;">
              Notice: Parameters that cannot genuinely be determined from an image alone are physically tested using calibrated hardware probes and weighbridge scales.
            </p>
            <div class="form-grid" style="grid-template-columns:1fr 1fr;">
              <div class="form-group">
                <label class="form-label" style="font-size:0.76rem;">Moisture Content (%) [Electronic Probe]</label>
                <input type="number" id="cvMoisture" class="form-control" value="11.4" step="0.1" min="5" max="30">
              </div>
              <div class="form-group">
                <label class="form-label" style="font-size:0.76rem;">Certified Net Weight (kg) [Weighbridge]</label>
                <input type="number" id="cvNetWeight" class="form-control" value="9150" step="10">
              </div>
            </div>
          </div>

          <!-- Optical Defect Checkboxes & Inspection Flags -->
          <div style="background:#fafafa; border:1px solid var(--border); padding:14px; border-radius:8px; margin-bottom:18px;">
            <label class="form-label" style="margin-bottom:8px; font-weight:700; font-size:0.82rem;">
              🔬 Optical Defect Sensor Flags (12 Quality Parameters):
            </label>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.8rem;">
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkCuts"> Surface / Thresher Cuts
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkCracks"> Kernel Stress Cracks
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkSpots"> Discoloration / Fungal Spots
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkBruises"> Impact Handling Bruises
              </label>
              <label style="display:flex; align-items:center; gap:6px;">
                <input type="checkbox" id="chkPestDamage"> Insect / Pest Boring Damage
              </label>
            </div>
            <div class="form-grid" style="grid-template-columns:1fr 1fr 1fr; margin-top:12px;">
              <div class="form-group">
                <label class="form-label" style="font-size:0.72rem;">Foreign Matter (%)</label>
                <input type="number" id="cvForeign" class="form-control" value="0.8" step="0.1" min="0" max="20">
              </div>
              <div class="form-group">
                <label class="form-label" style="font-size:0.72rem;">Broken Kernel (%)</label>
                <input type="number" id="cvBroken" class="form-control" value="1.5" step="0.1" min="0" max="20">
              </div>
              <div class="form-group">
                <label class="form-label" style="font-size:0.72rem;">Damaged Kernel (%)</label>
                <input type="number" id="cvDamaged" class="form-control" value="0.2" step="0.1" min="0" max="20">
              </div>
            </div>
          </div>

          <button type="button" class="btn btn-primary" onclick="runCameraAIGradingConsole()" style="width:100%; background:#1565c0; font-weight:700; padding:10px;">
            🤖 Run Central AI Crop Quality & Grading Analysis
          </button>
        </div>

        <!-- Right Column: AI Analysis Results & Human Review -->
        <div>
          <div id="cameraGradingResultContainer">
            <div style="background:white; border:1px dashed var(--border); border-radius:8px; padding:36px 20px; text-align:center; color:var(--text-muted);">
              <span style="font-size:2.2rem; display:block; margin-bottom:10px;">🌾</span>
              <h4 style="margin:0 0 6px 0; color:#546e7a;">AI Inference Ready</h4>
              <p style="font-size:0.8rem; max-width:320px; margin:0 auto;">
                Select batch, capture grain sample via camera, and execute Central AI vision evaluation.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Grading History Section -->
      <div id="whGradingHistorySection" style="margin-top:32px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h4 style="margin:0; color:var(--primary-dark); font-size:1.0rem;">
            📜 Major Warehouse AI Grading & Certification Ledger
          </h4>
          <span style="font-size:0.75rem; color:var(--text-muted);">
            Dual-Storage Verified Audit Trail • Batch ID Linked
          </span>
        </div>
        <div id="whGradingHistoryTableContainer">
          <div style="text-align:center; padding:20px; color:var(--text-muted);">Loading certified batch records...</div>
        </div>
      </div>
    </div>
  `;

  // Pre-load batches from database and existing grading history
  loadIntakeBatchesForGrading();
  loadGradingHistoryTable();
}

async function loadIntakeBatchesForGrading() {
  try {
    const intakes = await ApiClient.getRecords("/major-wh/intakes") || [];
    cachedActiveIntakes = intakes;
    const select = document.getElementById("cvBatchSelect");
    if (!select) return;

    if (intakes.length > 0) {
      select.innerHTML = intakes.map(i => `
        <option value="${i.batch_id}" ${i.batch_id === 'KS-BATCH-1001' ? 'selected' : ''}>
          ${i.batch_id} — ${i.crop_name} (${i.farmer_name || i.farmer_id})
        </option>
      `).join("");
      onGradingBatchSelected();
    }
  } catch (err) {
    console.warn("Could not load intakes for grading dropdown:", err);
  }
}

function onGradingBatchSelected() {
  const select = document.getElementById("cvBatchSelect");
  if (!select) return;
  const batchId = select.value;
  const batchIdInput = document.getElementById("cvBatchId");
  const cropInput = document.getElementById("cvCropName");
  const farmerInput = document.getElementById("cvFarmerName");
  const netWeightInput = document.getElementById("cvNetWeight");
  const preview = document.getElementById("cameraSnapshotPreview");

  if (batchIdInput) batchIdInput.value = batchId;

  const found = cachedActiveIntakes.find(i => i.batch_id === batchId);
  if (found) {
    if (cropInput) cropInput.value = found.crop_name || "Wheat (Lokwan)";
    if (farmerInput) farmerInput.value = `${found.farmer_name || 'Farmer'} (${found.farmer_id})`;
    if (netWeightInput && found.net_weight_kg) netWeightInput.value = found.net_weight_kg;
    if (preview && found.crop_image_url) {
      preview.src = found.crop_image_url.startsWith("/") ? found.crop_image_url : `/uploads/grain_samples/${found.crop_image_url}`;
    }
  }
}

async function runCameraAIGradingConsole() {
  const container = document.getElementById("cameraGradingResultContainer");
  if (!container) return;

  const batchId = document.getElementById("cvBatchId").value || "KS-BATCH-1001";
  const cropName = document.getElementById("cvCropName").value || "Wheat (Lokwan)";
  const moisture = parseFloat(document.getElementById("cvMoisture").value) || 11.4;
  const netWeight = parseFloat(document.getElementById("cvNetWeight").value) || 9150;
  const foreign = parseFloat(document.getElementById("cvForeign").value) || 0.8;
  const broken = parseFloat(document.getElementById("cvBroken").value) || 1.5;
  const damaged = parseFloat(document.getElementById("cvDamaged").value) || 0.2;

  const cuts = document.getElementById("chkCuts") ? document.getElementById("chkCuts").checked : false;
  const cracks = document.getElementById("chkCracks") ? document.getElementById("chkCracks").checked : false;
  const spots = document.getElementById("chkSpots") ? document.getElementById("chkSpots").checked : false;
  const bruises = document.getElementById("chkBruises") ? document.getElementById("chkBruises").checked : false;
  const pestDamage = document.getElementById("chkPestDamage") ? document.getElementById("chkPestDamage").checked : false;

  const foundIntake = cachedActiveIntakes.find(i => i.batch_id === batchId);
  const farmerId = foundIntake ? foundIntake.farmer_id : "KS-FMR-1001";
  const farmerName = foundIntake ? foundIntake.farmer_name : "Ramesh Narayan Patil";

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Executing Computer Vision Evaluation...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">
        Scanning optical frame for 12 quality parameters and defect anomalies...
      </p>
    </div>
  `;

  try {
    const payload = {
      batch_id: batchId,
      crop_name: cropName,
      farmer_id: farmerId,
      farmer_name: farmerName,
      warehouse_id: "MWH-PUN-01",
      net_weight_kg: netWeight,
      image_data: currentGradingSnapshotDataUrl,
      manual_moisture_pct: moisture,
      manual_foreign_matter_pct: foreign,
      manual_broken_grain_pct: broken,
      manual_damaged_grain_pct: damaged,
      has_cuts: cuts,
      has_cracks: cracks,
      has_spots: spots,
      has_bruises: bruises,
      has_pest_damage: pestDamage,
    };

    const res = await ApiClient.analyzeCropQuality(payload);
    const score = res.ai_score;
    const grade = res.ai_grade;
    const factors = res.ai_quality_factors || {};
    const warnings = res.ai_warnings || [];

    const gradeClass = grade === 'A' ? 'badge-success' : grade === 'B' ? 'badge-info' : grade === 'C' ? 'badge-warning' : 'badge-danger';
    const scoreColor = score >= 80 ? '#2e7d32' : score >= 60 ? '#1565c0' : score >= 40 ? '#ef6c00' : '#c62828';

    container.innerHTML = `
      <div style="background:white; border:1px solid #a5d6a7; border-radius:8px; padding:22px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
        <!-- Header Banner -->
        <div style="display:flex; justify-content:space-between; align-items:start; border-bottom:1px solid #e0e0e0; padding-bottom:14px; margin-bottom:16px;">
          <div>
            <span style="font-size:0.72rem; text-transform:uppercase; color:#2e7d32; font-weight:700;">
              🤖 Central AI Vision Analysis Result
            </span>
            <h3 style="margin:4px 0; color:#1b5e20;">
              Suggested Grade ${grade} <span style="font-size:1.1rem; color:${scoreColor}; font-weight:600;">(Score: ${score}/100)</span>
            </h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Batch: <strong>${res.batch_id}</strong> • Confidence: <strong>${Math.round(res.ai_confidence * 100)}%</strong>
            </span>
          </div>
          <div style="text-align:right;">
            <span class="badge ${gradeClass}" style="font-size:1.1rem; padding:6px 14px;">
              GRADE ${grade}
            </span>
            <div style="font-size:0.68rem; color:var(--text-muted); margin-top:4px;">
              ${grade === 'A' ? 'A = 80-100 (High Quality)' : grade === 'B' ? 'B = 60-79 (Medium Quality)' : grade === 'C' ? 'C = 40-59 (Fair Quality)' : 'Reject < 40 (Defective)'}
            </div>
          </div>
        </div>

        <!-- Sample Image Thumbnail -->
        ${res.image_url ? `
          <div style="display:flex; align-items:center; gap:12px; background:#f5f7fa; border-radius:6px; padding:8px 12px; margin-bottom:16px;">
            <img src="${res.image_url}" alt="Analyzed Sample" style="width:64px; height:48px; object-fit:cover; border-radius:4px; border:1px solid #ccc;">
            <div style="font-size:0.75rem; color:#37474f;">
              <div><strong>Frame Analyzed:</strong> <code>${res.image_url.split('/').pop()}</code></div>
              <div style="color:var(--text-muted);">Inspection Code: <code>${res.grading_code}</code></div>
            </div>
          </div>
        ` : ''}

        <!-- Anomaly Warnings -->
        ${warnings.length > 0 ? `
          <div style="background:#fff3e0; border:1px solid #ffe0b2; border-radius:6px; padding:10px 14px; margin-bottom:16px;">
            <strong style="color:#e65100; font-size:0.78rem; display:block; margin-bottom:4px;">
              ⚠️ AI Anomaly Warnings Detected:
            </strong>
            <ul style="margin:0; padding-left:18px; font-size:0.75rem; color:#bf360c;">
              ${warnings.map(w => `<li>${w}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        <!-- 12 Visual Parameters Grid -->
        <h4 style="font-size:0.84rem; color:var(--primary-dark); margin-bottom:10px;">
          🔬 12 Optical Defect & Quality Parameters:
        </h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:8px; margin-bottom:16px;">
          ${Object.entries(factors).filter(([k, v]) => v.type === 'VISUAL_OPTICAL').map(([k, v]) => `
            <div class="data-source-card" style="padding:8px; border-radius:6px;">
              <div style="font-size:0.68rem; color:#78909c;">${v.name}</div>
              <strong style="font-size:0.78rem; color:#263238; display:block; margin-top:2px;">${v.value}</strong>
              <span class="badge ${v.status === 'PASS' ? 'badge-success' : v.status === 'MINOR_DEFECT' ? 'badge-warning' : 'badge-danger'}" style="font-size:0.62rem; padding:1px 6px; margin-top:4px;">
                ${v.status}
              </span>
            </div>
          `).join('')}
        </div>

        <!-- Segregated Physical Measurements Display -->
        <div style="background:#f9fbe7; border:1px solid #c0ca33; border-radius:6px; padding:12px; margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <strong style="font-size:0.8rem; color:#827717;">
              ⚖️ Segregated Physical Measurements (Manual Hardware Probes):
            </strong>
            <span class="badge badge-warning" style="font-size:0.65rem;">Manual Probing</span>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.76rem;">
            <div>
              <span style="color:#558b2f;">Moisture Content:</span>
              <strong style="color:#33691e;">${factors.physical_moisture ? factors.physical_moisture.value : moisture + '%'}</strong>
              <div style="font-size:0.66rem; color:#689f38;">Digital probe measurement</div>
            </div>
            <div>
              <span style="color:#558b2f;">Certified Net Weight:</span>
              <strong style="color:#33691e;">${factors.physical_weight ? factors.physical_weight.value : netWeight + ' kg'}</strong>
              <div style="font-size:0.66rem; color:#689f38;">Weighbridge platform scale</div>
            </div>
          </div>
        </div>

        <p style="font-size:0.78rem; color:#455a64; line-height:1.4; margin-bottom:16px; background:#f5f5f5; padding:8px 12px; border-radius:4px;">
          <strong>AI Rationale:</strong> ${res.ai_reasoning}
        </p>

        <!-- HUMAN REVIEW SECTION (MANDATORY) -->
        <div style="background:#f1f8e9; border:1px solid #81c784; border-radius:6px; padding:16px;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
            <h4 style="color:#1b5e20; margin:0; font-size:0.88rem;">
              👤 Mandatory Human Review & Quality Sign-Off
            </h4>
            <span class="badge badge-warning" style="font-size:0.68rem;">Pending Human Stamp</span>
          </div>
          <p style="font-size:0.74rem; color:#33691e; margin-bottom:14px;">
            The AI prediction must NEVER become the final grade automatically. Choose one-click approval or modify with operational justification.
          </p>

          <div style="display:flex; gap:12px; justify-content:flex-end;">
            <button type="button" class="btn btn-secondary btn-sm" onclick="openCorrectWarehouseGradingModal(${res.id})">
              ✏️ Correct Result (Human Override)
            </button>
            <button type="button" class="btn btn-primary btn-sm" onclick="handleApproveWarehouseGrading(${res.id})" style="background:#2e7d32; font-weight:700;">
              ✅ Approve AI Result (Zero Typing)
            </button>
          </div>
        </div>
      </div>
    `;

    // Refresh history table below
    loadGradingHistoryTable();
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Camera AI Grading failed: ${err.message}</div>`;
  }
}

async function handleApproveWarehouseGrading(recordId) {
  if (!confirm("Confirm approval of AI Quality Score and Suggested Grade? This will certify the batch and stamp the final warehouse intake record.")) {
    return;
  }
  try {
    const res = await ApiClient.approveWarehouseGrading(recordId, "Approved without modification by Major Warehouse inspector");
    alert(`Batch ${res.batch_id} officially certified as Grade ${res.effective_final_grade} (Score: ${res.effective_final_score})!`);
    loadGradingHistoryTable();
    // Render approved status card
    const container = document.getElementById("cameraGradingResultContainer");
    if (container) {
      container.innerHTML = `
        <div style="background:#e8f5e9; border:1px solid #81c784; border-radius:8px; padding:24px; text-align:center;">
          <span style="font-size:2.2rem; display:block; margin-bottom:8px;">✅</span>
          <h3 style="color:#1b5e20; margin:0 0 6px 0;">Batch Certified & Stamped</h3>
          <p style="font-size:0.82rem; color:#2e7d32; margin:0 0 12px 0;">
            Batch <strong>${res.batch_id}</strong> certified with <strong>Grade ${res.effective_final_grade}</strong> (Score: ${res.effective_final_score}/100).
          </p>
          <span class="badge badge-success" style="font-size:0.8rem; padding:4px 10px;">APPROVED IN IMMUTABLE LEDGER</span>
        </div>
      `;
    }
  } catch (err) {
    alert("Approval failed: " + err.message);
  }
}

async function openCorrectWarehouseGradingModal(recordId) {
  let rec = null;
  try {
    rec = await ApiClient.getWarehouseGrading(recordId);
  } catch (err) {
    alert("Unable to fetch grading details: " + err.message);
    return;
  }

  const existingModal = document.getElementById("correctGradingModal");
  if (existingModal) existingModal.remove();

  const modalHtml = `
    <div id="correctGradingModal" class="modal-overlay" style="display:flex; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; justify-content:center; align-items:center;">
      <div class="modal-card" style="background:white; border-radius:8px; padding:24px; max-width:540px; width:90%; box-shadow:0 4px 20px rgba(0,0,0,0.2);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:12px; margin-bottom:16px;">
          <h3 style="margin:0; color:var(--primary-dark); font-size:1.05rem;">
            ✏️ Human Inspector Review & Correction
          </h3>
          <button class="btn btn-sm btn-secondary" onclick="document.getElementById('correctGradingModal').remove()">✕</button>
        </div>

        <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:14px;">
          Batch ID: <strong>${rec.batch_id}</strong> • AI Suggested: <strong>Grade ${rec.ai_grade}</strong> (${rec.ai_score}/100)
        </div>

        <form id="correctGradingForm" onsubmit="event.preventDefault(); submitCorrectWarehouseGrading(${rec.id});">
          <div class="form-group" style="margin-bottom:14px;">
            <label class="form-label">Human Final Grade *</label>
            <select id="modalFinalGrade" class="form-control" required>
              <option value="A" ${rec.ai_grade === 'A' ? 'selected' : ''}>Grade A (High Quality: 80 - 100)</option>
              <option value="B" ${rec.ai_grade === 'B' ? 'selected' : ''}>Grade B (Medium Quality: 60 - 79)</option>
              <option value="C" ${rec.ai_grade === 'C' ? 'selected' : ''}>Grade C (Fair Quality: 40 - 59)</option>
              <option value="REJECTED" ${rec.ai_grade === 'REJECTED' ? 'selected' : ''}>REJECTED (Defective / Damaged < 40)</option>
            </select>
          </div>

          <div class="form-group" style="margin-bottom:14px;">
            <label class="form-label">Human Final Quality Score (0 - 100) *</label>
            <input type="number" id="modalFinalScore" class="form-control" value="${rec.human_final_score || rec.ai_score}" step="0.5" min="0" max="100" required>
          </div>

          <div class="form-group" style="margin-bottom:14px;">
            <label class="form-label" style="color:var(--accent);">
              Mandatory Operational Justification (Min 5 Characters) *
            </label>
            <textarea id="modalCorrectionReason" class="form-control" rows="3" placeholder="Explain inspector findings, visual discrepancies, or probe results..." required style="resize:vertical;">${rec.correction_reason || ''}</textarea>
            <span style="font-size:0.7rem; color:var(--text-muted);">Required for official dual-storage audit compliance.</span>
          </div>

          <div class="form-group" style="margin-bottom:18px;">
            <label class="form-label">Inspection & Storage Notes</label>
            <input type="text" id="modalHumanNotes" class="form-control" value="${rec.human_notes || 'Adjusted upon physical inspection'}" placeholder="Storage instructions or silo assignment">
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px;">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('correctGradingModal').remove()">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary" style="background:#e65100;">
              💾 Save Human Correction
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", modalHtml);
}

async function submitCorrectWarehouseGrading(recordId) {
  const grade = document.getElementById("modalFinalGrade").value;
  const score = parseFloat(document.getElementById("modalFinalScore").value);
  const reason = document.getElementById("modalCorrectionReason").value.trim();
  const notes = document.getElementById("modalHumanNotes").value.trim();

  if (reason.length < 5) {
    alert("Mandatory justification must be at least 5 characters.");
    return;
  }

  try {
    const res = await ApiClient.correctWarehouseGrading(recordId, {
      human_final_grade: grade,
      human_final_score: score,
      correction_reason: reason,
      notes: notes,
    });

    const modal = document.getElementById("correctGradingModal");
    if (modal) modal.remove();

    alert(`Human correction recorded! Batch ${res.batch_id} officially certified as Grade ${res.effective_final_grade} (${res.effective_final_score}/100).`);
    loadGradingHistoryTable();

    const container = document.getElementById("cameraGradingResultContainer");
    if (container) {
      container.innerHTML = `
        <div style="background:#fff3e0; border:1px solid #ffb74d; border-radius:8px; padding:24px; text-align:center;">
          <span style="font-size:2.2rem; display:block; margin-bottom:8px;">✏️</span>
          <h3 style="color:#e65100; margin:0 0 6px 0;">Human Correction Certified</h3>
          <p style="font-size:0.82rem; color:#bf360c; margin:0 0 12px 0;">
            Batch <strong>${res.batch_id}</strong> updated from AI Grade ${res.ai_grade} to <strong>Grade ${res.effective_final_grade}</strong> (${res.effective_final_score}/100).
          </p>
          <div style="font-size:0.75rem; color:#5d4037; font-style:italic; margin-bottom:10px;">"${res.correction_reason}"</div>
          <span class="badge badge-warning" style="font-size:0.8rem; padding:4px 10px;">CORRECTED & STAMPED IN LEDGER</span>
        </div>
      `;
    }
  } catch (err) {
    alert("Correction failed: " + err.message);
  }
}

async function loadGradingHistoryTable() {
  const container = document.getElementById("whGradingHistoryTableContainer");
  if (!container) return;

  try {
    const records = await ApiClient.getWarehouseGradings() || [];
    if (records.length === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding:30px; color:var(--text-muted); background:white; border-radius:8px; border:1px solid var(--border);">
          No grading records certified yet. Run AI grading above to create the first record.
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
        <table class="record-table">
          <thead>
            <tr>
              <th>Grading Code</th>
              <th>Batch ID</th>
              <th>Crop & Farmer</th>
              <th>AI Grade (Score)</th>
              <th>Human Final</th>
              <th>Status</th>
              <th>Certified By</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${records.map(r => `
              <tr>
                <td><code>${r.grading_code}</code></td>
                <td><strong>${r.batch_id}</strong></td>
                <td>
                  <div style="font-weight:600;">${r.crop_name}</div>
                  <div style="font-size:0.72rem; color:var(--text-muted);">${r.farmer_name} (${r.farmer_id})</div>
                </td>
                <td>
                  <span class="badge ${r.ai_grade === 'A' ? 'badge-success' : r.ai_grade === 'B' ? 'badge-info' : r.ai_grade === 'C' ? 'badge-warning' : 'badge-danger'}">
                    Grade ${r.ai_grade} (${r.ai_score})
                  </span>
                </td>
                <td>
                  ${r.human_final_grade ? `
                    <span class="badge ${r.human_final_grade === 'A' ? 'badge-success' : r.human_final_grade === 'B' ? 'badge-info' : r.human_final_grade === 'C' ? 'badge-warning' : 'badge-danger'}">
                      Grade ${r.human_final_grade} (${r.human_final_score})
                    </span>
                  ` : `<span style="color:var(--text-muted); font-size:0.75rem;">Pending</span>`}
                </td>
                <td>
                  <span class="badge ${r.review_status === 'APPROVED' ? 'badge-success' : r.review_status === 'CORRECTED' ? 'badge-warning' : 'badge-info'}">
                    ${r.review_status}
                  </span>
                </td>
                <td style="font-size:0.75rem;">
                  <div>${r.reviewed_by || 'AI Standby'}</div>
                  <div style="color:var(--text-muted); font-size:0.7rem;">${r.reviewed_at ? r.reviewed_at.split('T')[0] : (r.created_at ? r.created_at.split('T')[0] : '')}</div>
                </td>
                <td>
                  <div style="display:flex; gap:6px;">
                    <button class="btn btn-sm btn-secondary" onclick="openGradingRecordDetailModal(${r.id})" style="font-size:0.7rem; padding:3px 8px;">
                      👁️ View Sample
                    </button>
                    ${r.review_status === 'PENDING_REVIEW' ? `
                      <button class="btn btn-sm btn-primary" onclick="handleApproveWarehouseGrading(${r.id})" style="background:#2e7d32; font-size:0.7rem; padding:3px 8px;">
                        ✅
                      </button>
                      <button class="btn btn-sm btn-secondary" onclick="openCorrectWarehouseGradingModal(${r.id})" style="font-size:0.7rem; padding:3px 8px;">
                        ✏️
                      </button>
                    ` : ''}
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load grading history: ${err.message}</div>`;
  }
}

async function openGradingRecordDetailModal(recordId) {
  let rec = null;
  try {
    rec = await ApiClient.getWarehouseGrading(recordId);
  } catch (err) {
    alert("Unable to load record: " + err.message);
    return;
  }

  const existingModal = document.getElementById("gradingDetailModal");
  if (existingModal) existingModal.remove();

  const factors = rec.ai_quality_factors || {};
  const warnings = rec.ai_warnings || [];

  const modalHtml = `
    <div id="gradingDetailModal" class="modal-overlay" style="display:flex; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; justify-content:center; align-items:center;">
      <div class="modal-card" style="background:white; border-radius:8px; padding:24px; max-width:680px; width:95%; max-height:90vh; overflow-y:auto; box-shadow:0 4px 24px rgba(0,0,0,0.25);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:12px; margin-bottom:16px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark); font-size:1.1rem;">
              📷 Grain Quality Sample & Defect Certificate
            </h3>
            <span style="font-size:0.75rem; color:var(--text-muted);">
              Grading Code: <code>${rec.grading_code}</code> • Batch: <strong>${rec.batch_id}</strong>
            </span>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="document.getElementById('gradingDetailModal').remove()">✕</button>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
          <!-- Image View -->
          <div style="background:#1e272e; border-radius:6px; padding:10px; text-align:center;">
            <img src="${rec.image_url || '/uploads/grain_samples/KS-BATCH-1001_sample.svg'}" alt="Grain Sample" style="width:100%; max-height:200px; object-fit:contain; border-radius:4px;">
            <div style="font-size:0.7rem; color:#a4b0be; margin-top:6px;">Sample Frame for ${rec.crop_name}</div>
          </div>

          <!-- Metadata & Dual Decision -->
          <div style="font-size:0.8rem; color:#2f3542;">
            <div><strong>Farmer:</strong> ${rec.farmer_name} (<code>${rec.farmer_id}</code>)</div>
            <div style="margin-top:4px;"><strong>Crop:</strong> ${rec.crop_name}</div>
            <div style="margin-top:4px;"><strong>Net Weight:</strong> ${rec.net_weight_kg ? Number(rec.net_weight_kg).toLocaleString() + ' kg' : 'N/A'}</div>
            <div style="margin-top:4px;"><strong>Warehouse:</strong> ${rec.warehouse_name}</div>
            <hr style="margin:10px 0; border:none; border-top:1px solid #eee;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <span>AI Prediction:</span>
              <span class="badge ${rec.ai_grade === 'A' ? 'badge-success' : rec.ai_grade === 'B' ? 'badge-info' : 'badge-warning'}">
                Grade ${rec.ai_grade} (${rec.ai_score})
              </span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <span>Human Certified:</span>
              <span class="badge ${rec.effective_final_grade === 'A' ? 'badge-success' : rec.effective_final_grade === 'B' ? 'badge-info' : 'badge-warning'}">
                Grade ${rec.effective_final_grade} (${rec.effective_final_score})
              </span>
            </div>
            <div style="margin-top:6px; font-size:0.75rem; color:var(--text-muted);">
              Status: <strong>${rec.review_status}</strong> by <strong>${rec.reviewed_by || 'AI Standby'}</strong>
            </div>
            ${rec.correction_reason ? `
              <div style="background:#fff3e0; border:1px solid #ffe0b2; padding:6px 10px; border-radius:4px; margin-top:8px; font-size:0.72rem; color:#bf360c;">
                <strong>Justification:</strong> "${rec.correction_reason}"
              </div>
            ` : ''}
          </div>
        </div>

        <!-- 12 Optical Parameters Breakdown -->
        <h4 style="font-size:0.82rem; color:var(--primary-dark); margin:0 0 8px 0;">
          🔬 12 Optical Defect Parameters:
        </h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:8px; margin-bottom:16px;">
          ${Object.entries(factors).filter(([k, v]) => v.type === 'VISUAL_OPTICAL').map(([k, v]) => `
            <div style="background:#f8f9fa; border:1px solid #e9ecef; border-radius:4px; padding:6px 8px; font-size:0.72rem;">
              <div style="color:#6c757d; font-size:0.65rem;">${v.name}</div>
              <strong style="display:block; margin:2px 0;">${v.value}</strong>
              <span class="badge ${v.status === 'PASS' ? 'badge-success' : 'badge-warning'}" style="font-size:0.6rem; padding:1px 4px;">${v.status}</span>
            </div>
          `).join('')}
        </div>

        <div style="text-align:right;">
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('gradingDetailModal').remove()">
            Close
          </button>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", modalHtml);
}

async function renderMajorWHStorage(container) {'''

if not old_pattern.search(content):
    print("Error: Could not find target pattern in dashboard.js")
    exit(1)

content = old_pattern.sub(new_code, content)

# Also ensure window exports at bottom of dashboard.js include the new helper functions
exports_to_add = [
    "window.onGradingBatchSelected = onGradingBatchSelected;",
    "window.handleApproveWarehouseGrading = handleApproveWarehouseGrading;",
    "window.openCorrectWarehouseGradingModal = openCorrectWarehouseGradingModal;",
    "window.submitCorrectWarehouseGrading = submitCorrectWarehouseGrading;",
    "window.loadGradingHistoryTable = loadGradingHistoryTable;",
    "window.openGradingRecordDetailModal = openGradingRecordDetailModal;",
]

for exp in exports_to_add:
    if exp not in content:
        content += f"\n{exp}"

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully updated dashboard.js for Task 5!")

