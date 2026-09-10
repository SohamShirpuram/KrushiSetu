import os

dashboard_js_path = r"d:\Projects\Gram Chain 2.O\frontend\js\dashboard.js"

with open(dashboard_js_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace old renderTruckTracking with comprehensive Task 7 suite
old_truck_func = """// --- 7. TRUCK GPS TRACKING (MAJOR WH, MINOR WH, FOOD DEPT) ---
async function renderTruckTracking(container) {"""

task7_code = """// =============================================================================
// TASK 7: MAJOR WAREHOUSE -> MINOR WAREHOUSE DISPATCH & TRUCK TRACKING
// =============================================================================

let cachedDispatchesList = [];
let activeDispatchFilter = "ALL";

// --- 1. MAJOR WAREHOUSE DISPATCHES CONSOLE ---
async function renderMajorWHDispatchesConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Loading Major Warehouse Dispatches...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">Connecting to central dispatch and fleet ledger...</p>
    </div>
  `;

  try {
    const res = await ApiClient.getWarehouseDispatches() || {};
    cachedDispatchesList = res.dispatches || (Array.isArray(res) ? res : []);

    const totalCount = cachedDispatchesList.length;
    const inTransitCount = cachedDispatchesList.filter(d => d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT').length;
    const pendingCount = cachedDispatchesList.filter(d => d.status === 'Pending Departure' || d.delivery_status === 'PENDING').length;
    const completedCount = cachedDispatchesList.filter(d => d.status === 'Completed' || d.status === 'Received' || d.delivery_status === 'DELIVERED').length;
    const discrepancyCount = cachedDispatchesList.filter(d => d.status === 'Discrepancy' || d.delivery_status === 'DISCREPANCY').length;

    const filtered = cachedDispatchesList.filter(d => {
      if (activeDispatchFilter === "ALL") return true;
      if (activeDispatchFilter === "IN_TRANSIT") return d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT';
      if (activeDispatchFilter === "PENDING") return d.status === 'Pending Departure' || d.delivery_status === 'PENDING';
      if (activeDispatchFilter === "COMPLETED") return d.status === 'Completed' || d.status === 'Received' || d.delivery_status === 'DELIVERED';
      if (activeDispatchFilter === "DISCREPANCY") return d.status === 'Discrepancy' || d.delivery_status === 'DISCREPANCY';
      return true;
    });

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <!-- Top Toolbar -->
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">🚚 Major Warehouse ➔ Minor Warehouse Dispatches</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Immutable Batch Linkage: Batch ID ➔ Farmer ➔ Crop ➔ Task 5 Certified Grade ➔ Dispatched Stock
            </span>
          </div>
          <div style="display:flex; gap:10px;">
            <button class="btn btn-secondary btn-sm" onclick="renderMajorWHDispatchesConsole()">
              🔄 Refresh
            </button>
            <button class="btn btn-primary btn-sm" onclick="openCreateDispatchModal()" style="background:#1565c0; font-weight:700;">
              ➕ Create New Dispatch
            </button>
          </div>
        </div>

        <!-- Metric KPI Cards -->
        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card" onclick="setDispatchFilter('ALL')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'ALL' ? '3px solid #1565c0' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#1565c0;">${totalCount}</div>
            <div class="metric-label">Total Dispatches</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('IN_TRANSIT')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'IN_TRANSIT' ? '3px solid #0288d1' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#0288d1;">${inTransitCount}</div>
            <div class="metric-label">In Transit (Active GPS)</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('PENDING')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'PENDING' ? '3px solid #f57c00' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#f57c00;">${pendingCount}</div>
            <div class="metric-label">Pending Departure</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('COMPLETED')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'COMPLETED' ? '3px solid #2e7d32' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#2e7d32;">${completedCount}</div>
            <div class="metric-label">Completed & Verified</div>
          </div>
          <div class="metric-card" onclick="setDispatchFilter('DISCREPANCY')" style="cursor:pointer; border-bottom:${activeDispatchFilter === 'DISCREPANCY' ? '3px solid #c62828' : '1px solid var(--border)'};">
            <div class="metric-val" style="color:#c62828;">${discrepancyCount}</div>
            <div class="metric-label">Discrepancies Flagged</div>
          </div>
        </div>

        <!-- Dispatches Table -->
        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Dispatch ID</th>
                <th>Batch ID & Crop</th>
                <th>Certified Grade</th>
                <th>Sent Qty (kg)</th>
                <th>Origin ➔ Destination</th>
                <th>Truck & Driver</th>
                <th>Departure / Arrival</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.length === 0 ? `
                <tr>
                  <td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted);">
                    No dispatches found for filter: <strong>${activeDispatchFilter}</strong>. Click [ Create New Dispatch ] to schedule shipment.
                  </td>
                </tr>
              ` : filtered.map(d => {
                const isPending = d.status === 'Pending Departure' || d.delivery_status === 'PENDING';
                const isInTransit = d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT';
                const isDiscrepancy = d.status === 'Discrepancy' || d.delivery_status === 'DISCREPANCY';
                const isCompleted = d.status === 'Completed' || d.status === 'Received' || d.delivery_status === 'DELIVERED';

                const statusBadge = isCompleted ? 'badge-success' : isInTransit ? 'badge-info' : isDiscrepancy ? 'badge-danger' : 'badge-warning';

                return `
                  <tr>
                    <td><code>${d.dispatch_id}</code></td>
                    <td>
                      <div style="font-weight:700; color:#263238;">${d.crop_name}</div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">Batch: <code>${d.batch_id}</code></div>
                    </td>
                    <td>
                      <span class="badge ${d.final_grade === 'A' ? 'badge-success' : d.final_grade === 'B' ? 'badge-info' : 'badge-warning'}" style="font-size:0.78rem;">
                        Grade ${d.final_grade || 'A'}
                      </span>
                    </td>
                    <td style="font-weight:700; color:#1565c0;">
                      ${Number(d.dispatch_quantity_kg).toLocaleString()} kg
                      <div style="font-size:0.7rem; color:var(--text-muted);">${(d.dispatch_quantity_kg / 1000).toFixed(2)} MT</div>
                    </td>
                    <td>
                      <div style="font-size:0.78rem; font-weight:600;">${d.destination_minor_warehouse}</div>
                      <div style="font-size:0.7rem; color:var(--text-muted);">From: ${d.origin_warehouse}</div>
                    </td>
                    <td>
                      <div style="font-weight:600;">🚚 ${d.truck_number}</div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">${d.driver_name} (${d.driver_phone || ''})</div>
                    </td>
                    <td style="font-size:0.75rem;">
                      <div>Dep: <strong>${d.departure_time || d.dispatch_date || '10:30 AM'}</strong></div>
                      <div>Exp: <strong>${d.expected_arrival || '02:30 PM'}</strong></div>
                      ${d.actual_arrival ? `<div style="color:#2e7d32;">Act: <strong>${d.actual_arrival}</strong></div>` : ''}
                    </td>
                    <td>
                      <span class="badge ${statusBadge}" style="font-size:0.75rem; padding:3px 8px;">
                        ${isInTransit ? '<span class="live-dot" style="display:inline-block; width:6px; height:6px; background:#0288d1; border-radius:50%; margin-right:4px; animation:pulse 1.2s infinite;"></span>' : ''}
                        ${d.status}
                      </span>
                    </td>
                    <td>
                      <div style="display:flex; flex-direction:column; gap:4px;">
                        <button class="btn btn-secondary btn-sm" onclick="openDispatchDetailModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                          👁️ View
                        </button>
                        ${isPending ? `
                          <button class="btn btn-primary btn-sm" onclick="handleStartTransit('${d.dispatch_id}')" style="background:#0288d1; font-size:0.7rem; padding:2px 6px; font-weight:700;">
                            🚚 Start Delivery
                          </button>
                          <button class="btn btn-secondary btn-sm" onclick="openEditDispatchModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                            ✏️ Edit
                          </button>
                        ` : ''}
                        <button class="btn btn-secondary btn-sm" onclick="openDispatchTrackingModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px; background:#e8eaf6; color:#283593;">
                          📍 Track GPS
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load warehouse dispatches: ${err.message}</div>`;
  }
}

function setDispatchFilter(filter) {
  activeDispatchFilter = filter;
  renderMajorWHDispatchesConsole();
}

// --- CREATE DISPATCH MODAL ---
async function openCreateDispatchModal() {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = "➕ Create Major Warehouse ➔ Minor Warehouse Dispatch";
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Create Dispatch Order";

  modalBody.innerHTML = `<div style="padding:24px; text-align:center; color:var(--text-muted);">Loading storage batches and transport fleet...</div>`;
  modal.style.display = "flex";

  try {
    const storageRes = await ApiClient.getWarehouseStorageList() || {};
    const storageList = storageRes.records || (Array.isArray(storageRes) ? storageRes : []);
    const availableBatches = storageList.filter(s => (s.available_quantity_kg || s.current_stock_kg) > 0);

    const trucks = await ApiClient.getTrucksList() || [];

    modalBody.innerHTML = `
      <form id="createDispatchForm" class="form-grid" onsubmit="handleCreateDispatchSubmit(event)">
        <!-- Step 1: Source Batch Selection -->
        <div class="form-group" style="grid-column: span 2; background:#e3f2fd; border:1px solid #90caf9; padding:12px; border-radius:6px;">
          <label class="form-label" style="color:#0d47a1; font-weight:700;">📦 Select Certified Stored Batch *</label>
          <select id="dispBatchSelect" class="form-control" onchange="onDispatchBatchSelected(this.value)" required>
            <option value="">-- Choose Stored Batch --</option>
            ${availableBatches.map(b => `
              <option value="${b.batch_id}" data-crop="${b.crop_name}" data-avail="${b.available_quantity_kg || b.current_stock_kg}" data-grade="${b.quality_grade || 'A'}" data-loc="${b.storage_location}">
                ${b.batch_id} • ${b.crop_name} (Grade ${b.quality_grade || 'A'}) • ${Number(b.available_quantity_kg || b.current_stock_kg).toLocaleString()} kg Available (${b.storage_location})
              </option>
            `).join('')}
          </select>
          <div style="font-size:0.72rem; color:#1565c0; margin-top:4px;">
            Immutable Traceability: Selected batch automatically inherits farmer linkage, crop variety, and Task 5 certified grade.
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Crop Name</label>
          <input type="text" id="dispCropName" class="form-control" placeholder="Auto-filled from batch" readonly style="background:#f5f5f5;">
        </div>

        <div class="form-group">
          <label class="form-label">Certified Quality Grade (Task 5 Certified)</label>
          <input type="text" id="dispFinalGrade" class="form-control" placeholder="Auto-filled (Grade A/B/C)" readonly style="background:#f5f5f5; font-weight:700; color:#2e7d32;">
        </div>

        <div class="form-group">
          <label class="form-label">Available Storage Stock (kg)</label>
          <input type="text" id="dispAvailStock" class="form-control" placeholder="Available kg" readonly style="background:#f5f5f5; font-weight:700; color:#1565c0;">
        </div>

        <div class="form-group">
          <label class="form-label">Dispatch Quantity (kg) *</label>
          <input type="number" step="0.1" id="dispQuantityKg" class="form-control" placeholder="e.g. 15000" min="1" required>
          <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">Strict inventory conservation: Cannot exceed available storage stock.</div>
        </div>

        <!-- Step 2: Logistics & Carrier -->
        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Select Registered Fleet Carrier *</label>
          <select id="dispTruckSelect" class="form-control" onchange="onDispatchTruckSelected(this)">
            <option value="">-- Select Registered Truck --</option>
            ${trucks.map(t => `
              <option value="${t.truck_id}" data-num="${t.vehicle_number}" data-driver="${t.driver_name}" data-phone="${t.driver_phone || ''}" data-driverid="${t.driver_id || ''}">
                ${t.truck_id} • ${t.vehicle_number} (${t.driver_name} - ${t.current_status})
              </option>
            `).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Truck Vehicle Number *</label>
          <input type="text" id="dispTruckNumber" class="form-control" placeholder="e.g. MH-12-Q-4521" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Full Name *</label>
          <input type="text" id="dispDriverName" class="form-control" placeholder="e.g. Ramesh Patil" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Contact Mobile Phone</label>
          <input type="text" id="dispDriverPhone" class="form-control" placeholder="e.g. +91 98220 11223">
        </div>

        <div class="form-group">
          <label class="form-label">Destination Minor Godown *</label>
          <select id="dispDestinationWh" class="form-control" required>
            <option value="Baramati APMC Transit Godown No. 3">Baramati APMC Transit Godown No. 3</option>
            <option value="Indapur Sub-District Godown">Indapur Sub-District Godown</option>
            <option value="Daund PDS Buffer Storage Depot">Daund PDS Buffer Storage Depot</option>
            <option value="Shirur Block Level Depot">Shirur Block Level Depot</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Dispatch Date *</label>
          <input type="text" id="dispDate" class="form-control" value="${new Date().toISOString().split('T')[0]}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Expected Departure Time</label>
          <input type="text" id="dispDepTime" class="form-control" value="10:30 AM">
        </div>

        <div class="form-group">
          <label class="form-label">Expected Arrival Time</label>
          <input type="text" id="dispArrTime" class="form-control" value="02:30 PM">
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Operational Notes & Gate Pass Remarks</label>
          <textarea id="dispNotes" class="form-control" rows="2" placeholder="Standard grain transit protocol under sealed tarpaulin."></textarea>
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("createDispatchForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Failed to initialize dispatch form: ${err.message}</div>`;
  }
}

function onDispatchBatchSelected(batchId) {
  const sel = document.getElementById("dispBatchSelect");
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !batchId) return;

  const crop = opt.getAttribute("data-crop") || "";
  const avail = parseFloat(opt.getAttribute("data-avail")) || 0;
  const grade = opt.getAttribute("data-grade") || "A";

  document.getElementById("dispCropName").value = crop;
  document.getElementById("dispFinalGrade").value = `Grade ${grade}`;
  document.getElementById("dispAvailStock").value = `${avail.toLocaleString()} kg`;
  
  const qtyInput = document.getElementById("dispQuantityKg");
  qtyInput.max = avail;
  if (!qtyInput.value || parseFloat(qtyInput.value) > avail) {
    qtyInput.value = avail;
  }
}

function onDispatchTruckSelected(sel) {
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !sel.value) return;

  document.getElementById("dispTruckNumber").value = opt.getAttribute("data-num") || "";
  document.getElementById("dispDriverName").value = opt.getAttribute("data-driver") || "";
  document.getElementById("dispDriverPhone").value = opt.getAttribute("data-phone") || "";
}

async function handleCreateDispatchSubmit(e) {
  e.preventDefault();
  const batchId = document.getElementById("dispBatchSelect").value;
  const cropName = document.getElementById("dispCropName").value;
  const gradeVal = (document.getElementById("dispFinalGrade").value || "Grade A").replace("Grade ", "").trim();
  const qty = parseFloat(document.getElementById("dispQuantityKg").value);
  const truckNum = document.getElementById("dispTruckNumber").value.trim();
  const driverName = document.getElementById("dispDriverName").value.trim();
  const destWh = document.getElementById("dispDestinationWh").value;

  if (!batchId || !cropName || isNaN(qty) || qty <= 0 || !truckNum || !driverName) {
    alert("Please fill all required fields correctly.");
    return;
  }

  const truckSel = document.getElementById("dispTruckSelect");
  const truckId = truckSel ? truckSel.value : null;

  const payload = {
    batch_id: batchId,
    crop_name: cropName,
    final_grade: gradeVal,
    dispatch_quantity_kg: qty,
    origin_warehouse: "Pune Central Silo Hub",
    origin_warehouse_id: "MWH-PUN-01",
    destination_minor_warehouse: destWh,
    destination_minor_warehouse_id: "MIN-BMT-01",
    truck_id: truckId || undefined,
    truck_number: truckNum,
    driver_name: driverName,
    driver_phone: document.getElementById("dispDriverPhone").value.trim() || undefined,
    dispatch_date: document.getElementById("dispDate").value.trim(),
    departure_time: document.getElementById("dispDepTime").value.trim(),
    expected_arrival: document.getElementById("dispArrTime").value.trim(),
    notes: document.getElementById("dispNotes").value.trim() || undefined
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    btn.textContent = "Creating Dispatch Order...";
    const res = await ApiClient.createWarehouseDispatch(payload);
    closeModal();
    alert(`Dispatch #${res.dispatch_id} created successfully!
${res.dispatch_quantity_kg} kg of ${res.crop_name} (Grade ${res.final_grade}) scheduled for ${res.destination_minor_warehouse}.
Storage stock decremented automatically.`);
    renderMajorWHDispatchesConsole();
  } catch (err) {
    alert("Dispatch creation failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Create Dispatch Order";
    }
  }
}

// --- START DISPATCH TRANSIT ---
async function handleStartTransit(dispatchId) {
  if (!confirm(`Confirm departure and start transit for Dispatch ${dispatchId}? This will activate real-time GPS tracking on the driver's device.`)) {
    return;
  }
  try {
    const res = await ApiClient.startDispatchTransit(dispatchId, {
      departure_time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    alert(`Dispatch ${dispatchId} is now IN TRANSIT! Real-time GPS tracking is ACTIVE.`);
    renderMajorWHDispatchesConsole();
  } catch (err) {
    alert("Failed to start transit: " + err.message);
  }
}

// --- DISPATCH DETAIL MODAL ---
async function openDispatchDetailModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📋 Dispatch Details: ${dispatchId}`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading dispatch record...</div>`;
  modal.style.display = "flex";

  try {
    const d = await ApiClient.getWarehouseDispatch(dispatchId);

    modalBody.innerHTML = `
      <div style="background:#e3f2fd; border:1px solid #90caf9; padding:14px; border-radius:6px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="color:#0d47a1; font-size:1rem;">${d.dispatch_id}</strong>
            <div style="font-size:0.8rem; color:#1565c0; margin-top:2px;">
              Cargo: <strong>${d.crop_name}</strong> • Linked Batch: <code>${d.batch_id}</code>
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge ${d.final_grade === 'A' ? 'badge-success' : 'badge-info'}" style="font-size:0.85rem;">Grade ${d.final_grade}</span>
            <div style="font-size:0.72rem; color:#1976d2; margin-top:2px;">Certified Task 5 Grade</div>
          </div>
        </div>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.82rem; margin-bottom:16px;">
        <div><strong>Dispatched Quantity:</strong> <span style="color:#1565c0; font-weight:700;">${Number(d.dispatch_quantity_kg).toLocaleString()} kg</span></div>
        <div><strong>Current Status:</strong> <span class="badge ${d.status === 'Completed' ? 'badge-success' : d.status === 'In Transit' ? 'badge-info' : 'badge-warning'}">${d.status}</span></div>
        <div><strong>Origin Warehouse:</strong> ${d.origin_warehouse}</div>
        <div><strong>Destination Godown:</strong> ${d.destination_minor_warehouse}</div>
        <div><strong>Assigned Truck:</strong> 🚚 ${d.truck_number} (${d.truck_id || ''})</div>
        <div><strong>Driver:</strong> ${d.driver_name} (${d.driver_phone || 'N/A'})</div>
        <div><strong>Dispatch Date:</strong> ${d.dispatch_date}</div>
        <div><strong>Departure Time:</strong> ${d.departure_time || 'N/A'}</div>
        <div><strong>Expected Arrival:</strong> ${d.expected_arrival || 'N/A'}</div>
        <div><strong>Actual Arrival:</strong> ${d.actual_arrival || 'In Transit / Pending'}</div>
        <div><strong>Live GPS Active:</strong> ${d.is_gps_active ? '🟢 Yes (Duty Active)' : '⚪ No (Inactive / Delivered)'}</div>
        <div><strong>Last Location:</strong> ${d.current_location || 'GPS location unavailable'}</div>
      </div>

      ${d.notes ? `
        <div style="background:#fafafa; border:1px solid #eee; padding:10px; border-radius:4px; font-size:0.8rem; margin-bottom:16px;">
          <strong>Notes:</strong><br>${d.notes}
        </div>
      ` : ''}

      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
        <a href="${d.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${d.latitude || 18.5204},${d.longitude || 73.8567}`}" target="_blank" class="btn btn-maps btn-sm" style="text-decoration:none; padding:6px 14px;">
          🗺️ View on Google Maps
        </a>
        <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading dispatch: ${err.message}</div>`;
  }
}

// --- EDIT DISPATCH MODAL ---
async function openEditDispatchModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `✏️ Edit Dispatch Order: ${dispatchId}`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Save Changes";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading dispatch...</div>`;
  modal.style.display = "flex";

  try {
    const d = await ApiClient.getWarehouseDispatch(dispatchId);

    modalBody.innerHTML = `
      <form id="editDispatchForm" class="form-grid" onsubmit="handleUpdateDispatchSubmit(event, '${d.dispatch_id}')">
        <div class="form-group">
          <label class="form-label">Truck Registration Number</label>
          <input type="text" id="editDispTruckNum" class="form-control" value="${d.truck_number || ''}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Full Name</label>
          <input type="text" id="editDispDriverName" class="form-control" value="${d.driver_name || ''}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Driver Mobile Phone</label>
          <input type="text" id="editDispDriverPhone" class="form-control" value="${d.driver_phone || ''}">
        </div>

        <div class="form-group">
          <label class="form-label">Destination Minor Warehouse</label>
          <input type="text" id="editDispDest" class="form-control" value="${d.destination_minor_warehouse || ''}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Expected Departure Time</label>
          <input type="text" id="editDispDepTime" class="form-control" value="${d.departure_time || ''}">
        </div>

        <div class="form-group">
          <label class="form-label">Expected Arrival Time</label>
          <input type="text" id="editDispArrTime" class="form-control" value="${d.expected_arrival || ''}">
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Notes</label>
          <textarea id="editDispNotes" class="form-control" rows="2">${d.notes || ''}</textarea>
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("editDispatchForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error: ${err.message}</div>`;
  }
}

async function handleUpdateDispatchSubmit(e, dispatchId) {
  e.preventDefault();
  const payload = {
    truck_number: document.getElementById("editDispTruckNum").value.trim(),
    driver_name: document.getElementById("editDispDriverName").value.trim(),
    driver_phone: document.getElementById("editDispDriverPhone").value.trim(),
    destination_minor_warehouse: document.getElementById("editDispDest").value.trim(),
    departure_time: document.getElementById("editDispDepTime").value.trim(),
    expected_arrival: document.getElementById("editDispArrTime").value.trim(),
    notes: document.getElementById("editDispNotes").value.trim()
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    await ApiClient.updateWarehouseDispatch(dispatchId, payload);
    closeModal();
    alert(`Dispatch ${dispatchId} updated successfully!`);
    renderMajorWHDispatchesConsole();
  } catch (err) {
    alert("Update failed: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// --- 2. TRUCK GPS TRACKING CONSOLE ---
async function renderTruckTrackingConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Connecting to Live Fleet GPS Network...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">Acquiring satellite telemetry and transit telemetry...</p>
    </div>
  `;

  try {
    const trucks = await ApiClient.getTrucksList() || [];
    const dispatchesRes = await ApiClient.getWarehouseDispatches() || {};
    const dispatches = dispatchesRes.dispatches || (Array.isArray(dispatchesRes) ? dispatchesRes : []);

    const inTransitDispatches = dispatches.filter(d => d.status === 'In Transit' || d.delivery_status === 'IN_TRANSIT');
    const availableTrucks = trucks.filter(t => t.current_status === 'AVAILABLE');

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">🚛 Live Fleet GPS & Transit Telemetry</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Real-time In-Transit Agricultural Cargo Monitoring • Google Maps Navigation Linkage
            </span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="renderTruckTrackingConsole()" style="background:#1565c0;">
            🔄 Refresh GPS Feed
          </button>
        </div>

        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${trucks.length}</div>
            <div class="metric-label">Registered Fleet Trucks</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#0288d1;">${inTransitDispatches.length}</div>
            <div class="metric-label">Active GPS Transits</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${availableTrucks.length}</div>
            <div class="metric-label">Trucks Ready / Available</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#6a1b9a;">100%</div>
            <div class="metric-label">Privacy Shield Active (Transit-Only)</div>
          </div>
        </div>

        <!-- Active Transit Cards Grid -->
        <h4 style="color:var(--primary-dark); margin:20px 0 12px 0;">Active Vehicle Transits (${inTransitDispatches.length})</h4>
        <div class="truck-grid">
          ${inTransitDispatches.length === 0 ? `
            <div style="grid-column:1/-1; text-align:center; padding:32px; background:white; border-radius:8px; border:1px solid var(--border); color:var(--text-muted);">
              No vehicles currently in transit. Click [ Create New Dispatch ] in Dispatches tab to initiate cargo transit.
            </div>
          ` : inTransitDispatches.map(t => `
            <div class="truck-card" style="background:white; border:1px solid #90caf9; border-radius:8px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
              <div class="truck-header" style="display:flex; justify-content:space-between; align-items:start; border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:12px;">
                <div>
                  <div class="truck-id" style="font-size:1.05rem; font-weight:700; color:#0d47a1;">🚚 ${t.truck_number}</div>
                  <div style="font-size:0.72rem; color:var(--text-muted);">Dispatch ID: <code>${t.dispatch_id}</code></div>
                </div>
                <span class="badge badge-info" style="font-size:0.75rem; padding:4px 8px;">
                  <span class="live-dot" style="display:inline-block; width:6px; height:6px; background:#0288d1; border-radius:50%; margin-right:4px; animation:pulse 1.2s infinite;"></span>
                  IN TRANSIT
                </span>
              </div>

              <div class="truck-route" style="display:flex; align-items:center; justify-content:space-between; background:#f5f7fa; padding:10px; border-radius:6px; margin-bottom:12px;">
                <div class="route-node">
                  <div class="node-label" style="font-size:0.68rem; color:var(--text-muted);">ORIGIN HUB</div>
                  <div class="node-val" style="font-weight:700; font-size:0.8rem; color:#263238;">${t.origin_warehouse}</div>
                </div>
                <div style="color:#0288d1; font-size:1.2rem; font-weight:700;">➔</div>
                <div class="route-node" style="text-align:right;">
                  <div class="node-label" style="font-size:0.68rem; color:var(--text-muted);">DESTINATION GODOWN</div>
                  <div class="node-val" style="font-weight:700; font-size:0.8rem; color:#263238;">${t.destination_minor_warehouse}</div>
                </div>
              </div>

              <div style="font-size:0.8rem; color:#37474f; margin-bottom:12px;">
                <div>🌾 <strong>Cargo:</strong> ${Number(t.dispatch_quantity_kg).toLocaleString()} kg ${t.crop_name} (Grade ${t.final_grade}) • Batch: <code>${t.batch_id}</code></div>
                <div>👤 <strong>Driver:</strong> ${t.driver_name} (${t.driver_phone || 'N/A'})</div>
                <div>🕒 <strong>Departure:</strong> ${t.departure_time || '10:30 AM'} • <strong>Expected:</strong> ${t.expected_arrival || '02:30 PM'}</div>
              </div>

              <div class="gps-strip" style="background:#e8f5e9; border:1px solid #c8e6c9; border-radius:6px; padding:10px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div>
                    <div style="font-size:0.78rem; color:#1b5e20;">📍 Location: <strong>${t.current_location || 'Pune-Solapur Highway (Near Patas)'}</strong></div>
                    <div style="font-size:0.7rem; color:#388e3c; margin-top:2px;">Last GPS Sync: ${t.last_gps_update || 'Just now'}</div>
                  </div>
                  <a href="${t.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${t.latitude || 18.5204},${t.longitude || 73.8567}`}" target="_blank" class="btn btn-maps btn-sm" style="text-decoration:none; padding:4px 10px; font-size:0.72rem; white-space:nowrap;">
                    🗺️ Google Maps
                  </a>
                </div>
              </div>

              <div style="display:flex; gap:8px;">
                <button class="btn btn-outline btn-sm" onclick="openSimulateGPSModal('${t.dispatch_id}')" style="flex:1; font-size:0.75rem;">
                  📍 Update Driver GPS
                </button>
                <button class="btn btn-primary btn-sm" onclick="openMinorWHReceiveModal('${t.dispatch_id}')" style="background:#2e7d32; flex:1; font-size:0.75rem; font-weight:700;">
                  📥 Minor WH Receive
                </button>
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Registered Fleet Registry Table -->
        <h4 style="color:var(--primary-dark); margin:28px 0 12px 0;">Carrier Fleet Registry (${trucks.length})</h4>
        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Truck ID</th>
                <th>Registration No</th>
                <th>Vehicle Type</th>
                <th>Capacity</th>
                <th>Assigned Driver</th>
                <th>Driver Phone</th>
                <th>Fleet Status</th>
                <th>Current Duty / Destination</th>
                <th>Last GPS Update</th>
              </tr>
            </thead>
            <tbody>
              ${trucks.map(t => `
                <tr>
                  <td><code>${t.truck_id}</code></td>
                  <td><strong>${t.vehicle_number}</strong></td>
                  <td>${t.vehicle_type}</td>
                  <td>${t.capacity_mt} MT</td>
                  <td>${t.driver_name}</td>
                  <td>${t.driver_phone || 'N/A'}</td>
                  <td>
                    <span class="badge ${t.current_status === 'AVAILABLE' ? 'badge-success' : t.current_status === 'IN_TRANSIT' ? 'badge-info' : 'badge-warning'}">
                      ${t.current_status}
                    </span>
                  </td>
                  <td>
                    ${t.current_dispatch_id ? `<code>${t.current_dispatch_id}</code> ➔ ${t.destination || 'Minor Godown'}` : '<span style="color:var(--text-muted); font-size:0.75rem;">Idle / Ready at Hub</span>'}
                  </td>
                  <td style="font-size:0.75rem;">${t.last_gps_update || 'N/A'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load truck tracking: ${err.message}</div>`;
  }
}

const renderTruckTracking = renderTruckTrackingConsole;

// --- GPS TRACKING MODAL ---
async function openDispatchTrackingModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📍 Live GPS Telemetry: ${dispatchId}`;
  modalSubmitBtn.style.display = "none";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Fetching live GPS coordinates...</div>`;
  modal.style.display = "flex";

  try {
    const t = await ApiClient.getDispatchTracking(dispatchId);

    modalBody.innerHTML = `
      <div style="background:#e8f5e9; border:1px solid #c8e6c9; border-radius:6px; padding:16px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h4 style="margin:0; color:#1b5e20;">🚚 ${t.truck_number} • ${t.driver_name}</h4>
            <div style="font-size:0.78rem; color:#2e7d32; margin-top:2px;">
              Cargo: <strong>${Number(t.dispatch_quantity_kg).toLocaleString()} kg ${t.crop_name}</strong> (Grade ${t.final_grade})
            </div>
          </div>
          <span class="badge ${t.is_gps_active ? 'badge-success' : 'badge-secondary'}" style="font-size:0.8rem;">
            ${t.is_gps_active ? '🟢 LIVE GPS ACTIVE' : '⚪ GPS INACTIVE'}
          </span>
        </div>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.82rem; margin-bottom:16px;">
        <div><strong>Current Checkpoint:</strong> ${t.current_location || 'GPS location unavailable'}</div>
        <div><strong>Last Coordinate Sync:</strong> ${t.last_gps_update || 'N/A'}</div>
        <div><strong>Latitude:</strong> <code>${t.latitude}</code></div>
        <div><strong>Longitude:</strong> <code>${t.longitude}</code></div>
        <div><strong>Origin:</strong> ${t.origin_warehouse}</div>
        <div><strong>Destination:</strong> ${t.destination_minor_warehouse}</div>
      </div>

      <div style="background:#f5f7fa; border:1px solid #cfd8dc; border-radius:6px; padding:14px; text-align:center; margin-bottom:16px;">
        <div style="font-size:0.85rem; color:#37474f; margin-bottom:10px;">
          🛰️ <strong>Direct Satellite Link:</strong> Open real-time turn-by-turn navigation in Google Maps
        </div>
        <a href="${t.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${t.latitude},${t.longitude}`}" target="_blank" class="btn btn-maps" style="text-decoration:none; display:inline-flex; align-items:center; gap:8px; padding:8px 18px; font-weight:700;">
          🗺️ Launch in Google Maps
        </a>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center;">
        ${t.is_gps_active ? `
          <button class="btn btn-primary btn-sm" onclick="openSimulateGPSModal('${t.dispatch_id}')" style="background:#0288d1;">
            📍 Send Mobile GPS Update
          </button>
        ` : '<div></div>'}
        <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading GPS telemetry: ${err.message}</div>`;
  }
}

// --- SIMULATE DRIVER GPS MODAL ---
function openSimulateGPSModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📍 Send Driver GPS Checkpoint: ${dispatchId}`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Broadcast GPS Location";

  modalBody.innerHTML = `
    <form id="simulateGPSForm" class="form-grid" onsubmit="handleSimulateGPSSubmit(event, '${dispatchId}')">
      <div class="form-group" style="grid-column: span 2;">
        <label class="form-label">Road Checkpoint / Landmark Name *</label>
        <input type="text" id="gpsLocName" class="form-control" value="Near Patas Toll Plaza, Pune-Solapur Expressway (Km 62)" required>
      </div>

      <div class="form-group">
        <label class="form-label">Latitude *</label>
        <input type="number" step="0.0001" id="gpsLat" class="form-control" value="18.4385" required>
      </div>

      <div class="form-group">
        <label class="form-label">Longitude *</label>
        <input type="number" step="0.0001" id="gpsLng" class="form-control" value="74.4172" required>
      </div>

      <div class="form-group" style="grid-column: span 2; font-size:0.75rem; color:var(--text-muted);">
        Notice: In actual deployment, this API receives automated background coordinates directly from the driver mobile device during active transit duty.
      </div>
    </form>
  `;

  modalSubmitBtn.onclick = () => {
    document.getElementById("simulateGPSForm").dispatchEvent(new Event("submit"));
  };
  modal.style.display = "flex";
}

async function handleSimulateGPSSubmit(e, dispatchId) {
  e.preventDefault();
  const locName = document.getElementById("gpsLocName").value.trim();
  const lat = parseFloat(document.getElementById("gpsLat").value);
  const lng = parseFloat(document.getElementById("gpsLng").value);

  const payload = {
    latitude: lat,
    longitude: lng,
    location_name: locName
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    await ApiClient.updateDispatchLocation(dispatchId, payload);
    closeModal();
    alert(`GPS Location broadcasted for Dispatch ${dispatchId}!`);
    renderTruckTrackingConsole();
  } catch (err) {
    alert("GPS update failed: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// --- 3. MINOR WAREHOUSE INWARD & RECEIVING CONSOLE ---
async function renderMinorWHInwardConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `
    <div style="background:white; border-radius:8px; border:1px solid var(--border); padding:32px; text-align:center;">
      <div class="loader-spinner" style="margin:0 auto 16px auto; width:36px; height:36px; border:3px solid #e0e0e0; border-top-color:#1565c0; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <h4 style="margin:0 0 6px 0; color:var(--primary-dark);">Loading Sub-District Inward Dispatches...</h4>
      <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">Checking major warehouse transfers and intake records...</p>
    </div>
  `;

  try {
    const dispatchesRes = await ApiClient.getWarehouseDispatches() || {};
    const dispatches = dispatchesRes.dispatches || (Array.isArray(dispatchesRes) ? dispatchesRes : []);
    const inwardRecords = await ApiClient.getRecords("/minor-wh/inward") || [];

    const totalIncoming = dispatches.length;
    const inTransit = dispatches.filter(d => d.status === 'In Transit').length;
    const received = dispatches.filter(d => d.status === 'Completed' || d.status === 'Received').length;
    const discrepancies = dispatches.filter(d => d.status === 'Discrepancy').length;

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">📥 Minor Warehouse: Incoming Dispatches & Receiving</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">
              Sub-District Transit Godown Inward Verification • Weighbridge Discrepancy Reconciliation
            </span>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="renderMinorWHInwardConsole()">
            🔄 Refresh Inward List
          </button>
        </div>

        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${totalIncoming}</div>
            <div class="metric-label">Total Major Silo Transfers</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#0288d1;">${inTransit}</div>
            <div class="metric-label">Vehicles In Transit</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${received}</div>
            <div class="metric-label">Verified & In Stock</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#c62828;">${discrepancies}</div>
            <div class="metric-label">Discrepancies Flagged</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Dispatch ID</th>
                <th>Batch ID & Crop</th>
                <th>Certified Grade</th>
                <th>Sent Qty (kg)</th>
                <th>Received Qty (kg)</th>
                <th>Difference (kg)</th>
                <th>Carrier & Driver</th>
                <th>Verification Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${dispatches.length === 0 ? `
                <tr>
                  <td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted);">
                    No incoming dispatches found. Dispatches initiated at Major Silo will appear here for intake verification.
                  </td>
                </tr>
              ` : dispatches.map(d => {
                const isCompleted = d.status === 'Completed' || d.status === 'Received';
                const isDiscrepancy = d.status === 'Discrepancy';
                const isInTransit = d.status === 'In Transit';

                const matchingInward = inwardRecords.find(i => i.dispatch_id === d.dispatch_id);
                const recQty = matchingInward ? matchingInward.received_quantity_kg : (isCompleted ? d.dispatch_quantity_kg : '-');
                const diffQty = matchingInward ? matchingInward.difference_kg : (isCompleted ? 0 : '-');

                return `
                  <tr>
                    <td><code>${d.dispatch_id}</code></td>
                    <td>
                      <div style="font-weight:700;">${d.crop_name}</div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">Batch: <code>${d.batch_id}</code></div>
                    </td>
                    <td>
                      <span class="badge ${d.final_grade === 'A' ? 'badge-success' : d.final_grade === 'B' ? 'badge-info' : 'badge-warning'}">
                        Grade ${d.final_grade}
                      </span>
                    </td>
                    <td style="font-weight:700; color:#1565c0;">
                      ${Number(d.dispatch_quantity_kg).toLocaleString()} kg
                    </td>
                    <td style="font-weight:700; color:${isCompleted ? '#2e7d32' : isDiscrepancy ? '#c62828' : 'var(--text-muted)'};">
                      ${recQty !== '-' ? Number(recQty).toLocaleString() + ' kg' : 'Pending Intake'}
                    </td>
                    <td>
                      ${diffQty !== '-' ? (
                        diffQty === 0 ? `<span class="badge badge-success">0 kg (Exact)</span>` : `<span class="badge badge-danger">${diffQty} kg diff</span>`
                      ) : '<span style="color:var(--text-muted); font-size:0.75rem;">-</span>'}
                    </td>
                    <td>
                      <div>🚚 <strong>${d.truck_number}</strong></div>
                      <div style="font-size:0.72rem; color:var(--text-muted);">${d.driver_name}</div>
                    </td>
                    <td>
                      <span class="badge ${isCompleted ? 'badge-success' : isDiscrepancy ? 'badge-danger' : isInTransit ? 'badge-info' : 'badge-warning'}">
                        ${d.status}
                      </span>
                    </td>
                    <td>
                      <div style="display:flex; flex-direction:column; gap:4px;">
                        ${(!isCompleted && !isDiscrepancy) ? `
                          <button class="btn btn-primary btn-sm" onclick="openMinorWHReceiveModal('${d.dispatch_id}')" style="background:#2e7d32; font-size:0.72rem; padding:3px 8px; font-weight:700;">
                            📥 Receive & Verify
                          </button>
                        ` : `
                          <button class="btn btn-secondary btn-sm" onclick="openDispatchDetailModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                            👁️ View Receipt
                          </button>
                        `}
                        <button class="btn btn-secondary btn-sm" onclick="openDispatchTrackingModal('${d.dispatch_id}')" style="font-size:0.7rem; padding:2px 6px;">
                          📍 Track
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load inward dispatches: ${err.message}</div>`;
  }
}

// --- MINOR WAREHOUSE RECEIVE MODAL ---
async function openMinorWHReceiveModal(dispatchId) {
  const modal = document.getElementById("recordModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalSubmitBtn = document.getElementById("modalSubmitBtn");

  modalTitle.textContent = `📥 Minor Warehouse Intake Verification: ${dispatchId}`;
  modalSubmitBtn.style.display = "inline-flex";
  modalSubmitBtn.textContent = "Confirm Inward Receipt & Unload";

  modalBody.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted);">Loading dispatch record...</div>`;
  modal.style.display = "flex";

  try {
    const d = await ApiClient.getWarehouseDispatch(dispatchId);

    modalBody.innerHTML = `
      <div style="background:#e3f2fd; border:1px solid #90caf9; padding:12px; border-radius:6px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="color:#0d47a1; font-size:0.95rem;">${d.dispatch_id} • ${d.crop_name}</strong>
            <div style="font-size:0.78rem; color:#1565c0; margin-top:2px;">
              Linked Batch: <code>${d.batch_id}</code> • Origin: <strong>${d.origin_warehouse}</strong>
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge ${d.final_grade === 'A' ? 'badge-success' : 'badge-info'}" style="font-size:0.85rem;">Grade ${d.final_grade}</span>
            <div style="font-size:0.7rem; color:#1976d2; margin-top:2px;">Certified Task 5 Grade</div>
          </div>
        </div>
      </div>

      <div style="background:#f5f5f5; border:1px solid #e0e0e0; border-radius:6px; padding:10px 14px; margin-bottom:16px; font-size:0.82rem;">
        <div>🚚 <strong>Carrier Truck:</strong> ${d.truck_number} • <strong>Driver:</strong> ${d.driver_name}</div>
        <div style="margin-top:2px;">⚖️ <strong>Major Silo Dispatched Weight:</strong> <span style="font-weight:800; color:#1565c0; font-size:1rem;">${Number(d.dispatch_quantity_kg).toLocaleString()} kg</span></div>
      </div>

      <form id="minorWHReceiveForm" class="form-grid" onsubmit="handleMinorWHReceiveSubmit(event, '${d.dispatch_id}', ${d.dispatch_quantity_kg})">
        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label" style="font-weight:700; color:#2e7d32;">Verified Received Net Weight at Minor Weighbridge (kg) *</label>
          <input type="number" step="0.1" id="mwhRecQty" class="form-control" value="${d.dispatch_quantity_kg}" min="0" oninput="updateMinorWHReceiveDiff(${d.dispatch_quantity_kg})" required style="font-size:1.1rem; font-weight:700;">
        </div>

        <!-- Dynamic Discrepancy Banner -->
        <div id="mwhDiscrepancyBanner" style="grid-column: span 2; padding:12px; border-radius:6px; background:#e8f5e9; border:1px solid #a5d6a7; margin-bottom:10px;">
          <div style="font-weight:700; color:#2e7d32; font-size:0.85rem;">
            ✅ Perfect Weight Verification (0 kg Difference)
          </div>
          <div style="font-size:0.75rem; color:#388e3c; margin-top:2px;">
            Received weight perfectly matches Major Silo dispatched quantity. Status will be marked <strong>COMPLETED / VERIFIED_IN_STOCK</strong>.
          </div>
        </div>

        <div class="form-group" style="grid-column: span 2;">
          <label class="form-label">Discrepancy / Weight Loss Reason</label>
          <input type="text" id="mwhDiscrepancyReason" class="form-control" placeholder="Optional for exact match. Required if difference exists (e.g. moisture loss during transit)">
        </div>

        <div class="form-group">
          <label class="form-label">Receiver / Inspector Name *</label>
          <input type="text" id="mwhReceiverName" class="form-control" value="${(currentUser && currentUser.username) ? currentUser.username : 'Godown Officer'}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Arrival & Unload Time</label>
          <input type="text" id="mwhArrTime" class="form-control" value="${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}">
        </div>
      </form>
    `;

    modalSubmitBtn.onclick = () => {
      document.getElementById("minorWHReceiveForm").dispatchEvent(new Event("submit"));
    };
  } catch (err) {
    modalBody.innerHTML = `<div class="alert-box danger">Error loading dispatch: ${err.message}</div>`;
  }
}

function updateMinorWHReceiveDiff(sentQty) {
  const recInput = document.getElementById("mwhRecQty");
  const banner = document.getElementById("mwhDiscrepancyBanner");
  if (!recInput || !banner) return;

  const recQty = parseFloat(recInput.value) || 0;
  const diff = Math.round((sentQty - recQty) * 100) / 100;

  if (Math.abs(diff) < 0.001) {
    banner.style.background = "#e8f5e9";
    banner.style.borderColor = "#a5d6a7";
    banner.innerHTML = `
      <div style="font-weight:700; color:#2e7d32; font-size:0.85rem;">
        ✅ Perfect Weight Verification (0 kg Difference)
      </div>
      <div style="font-size:0.75rem; color:#388e3c; margin-top:2px;">
        Received weight perfectly matches Major Silo dispatched quantity. Status will be marked <strong>COMPLETED / VERIFIED_IN_STOCK</strong>.
      </div>
    `;
  } else {
    banner.style.background = "#ffebee";
    banner.style.borderColor = "#ef9a9a";
    banner.innerHTML = `
      <div style="font-weight:700; color:#c62828; font-size:0.85rem;">
        ⚠️ Weight Discrepancy Detected: ${diff > 0 ? `${diff} kg Shortage` : `${Math.abs(diff)} kg Excess`}
      </div>
      <div style="font-size:0.75rem; color:#b71c1c; margin-top:2px;">
        Sent: ${Number(sentQty).toLocaleString()} kg ➔ Received: ${Number(recQty).toLocaleString()} kg.
        Status will be flagged as <strong>DISCREPANCY / WEIGHT_MISMATCH</strong>. Major Warehouse sent quantity remains untouched.
      </div>
    `;
    const reasonInput = document.getElementById("mwhDiscrepancyReason");
    if (reasonInput && !reasonInput.value) {
      reasonInput.value = `Transit weight difference of ${diff} kg observed at intake weighbridge`;
    }
  }
}

async function handleMinorWHReceiveSubmit(e, dispatchId, sentQty) {
  e.preventDefault();
  const recQty = parseFloat(document.getElementById("mwhRecQty").value);
  if (isNaN(recQty) || recQty < 0) {
    alert("Please enter a valid non-negative received quantity.");
    return;
  }

  const diff = Math.round((sentQty - recQty) * 100) / 100;
  const reason = document.getElementById("mwhDiscrepancyReason").value.trim();

  if (Math.abs(diff) > 0.001 && (!reason || reason.length < 3)) {
    alert("Please provide a reason for the weight discrepancy.");
    return;
  }

  const payload = {
    received_quantity_kg: recQty,
    arrival_time: document.getElementById("mwhArrTime").value.trim(),
    discrepancy_reason: reason || (diff === 0 ? "Exact Match Verified" : `Weight difference of ${diff} kg`),
    receiver_name: document.getElementById("mwhReceiverName").value.trim()
  };

  const btn = document.getElementById("modalSubmitBtn");
  try {
    btn.disabled = true;
    btn.textContent = "Verifying Intake...";
    const res = await ApiClient.receiveMinorWarehouseDispatch(dispatchId, payload);
    closeModal();
    alert(`Inward receipt processed successfully!
Status: ${res.status}
Received: ${recQty} kg (Difference: ${res.difference_kg} kg)
Minor godown stock updated and truck released.`);
    renderMinorWHInwardConsole();
  } catch (err) {
    alert("Intake verification failed: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Confirm Inward Receipt & Unload";
    }
  }
}

// --- 4. MINOR WAREHOUSE SENT VS RECEIVED (DISCREPANCY AUDIT) ---
async function renderMinorWHSentReceivedConsole(container) {
  if (!container) container = document.getElementById("contentContainer") || document.getElementById("activeTableContainer");
  if (!container) return;

  container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">Loading Sent vs Received Discrepancy Reconciliation...</div>`;

  try {
    const inwardRecords = await ApiClient.getRecords("/minor-wh/inward") || [];

    const totalAudited = inwardRecords.length;
    const exactMatches = inwardRecords.filter(r => (r.difference_kg === 0 || r.verification_status === 'VERIFIED_IN_STOCK')).length;
    const mismatches = inwardRecords.filter(r => (r.difference_kg !== 0 || r.verification_status === 'WEIGHT_MISMATCH')).length;
    const totalShortageKg = inwardRecords.reduce((acc, r) => acc + Math.max(0, (r.difference_kg || 0)), 0);

    container.innerHTML = `
      <div class="table-container" style="border:none; background:transparent;">
        <div class="table-toolbar" style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h3 style="margin:0; color:var(--primary-dark);">⚖️ Sent vs Received Discrepancy & Weight Audit</h3>
            <span style="font-size:0.78rem; color:var(--text-muted);">Reconciles Major Silo Outward Gate Pass with Minor Godown Intake Scales</span>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="renderMinorWHSentReceivedConsole()">
            🔄 Refresh Audit
          </button>
        </div>

        <div class="metric-grid" style="margin:16px 0 20px 0;">
          <div class="metric-card">
            <div class="metric-val" style="color:#1565c0;">${totalAudited}</div>
            <div class="metric-label">Audited Inward Receipts</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#2e7d32;">${exactMatches}</div>
            <div class="metric-label">Exact Weight Matches</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#c62828;">${mismatches}</div>
            <div class="metric-label">Discrepancies Recorded</div>
          </div>
          <div class="metric-card">
            <div class="metric-val" style="color:#e65100;">${totalShortageKg.toFixed(1)} kg</div>
            <div class="metric-label">Total Cumulative Transit Loss</div>
          </div>
        </div>

        <div style="background:white; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
          <table class="record-table">
            <thead>
              <tr>
                <th>Dispatch ID</th>
                <th>Batch ID</th>
                <th>Crop</th>
                <th>Major Silo Sent (kg)</th>
                <th>Minor Received (kg)</th>
                <th>Difference (kg)</th>
                <th>Carrier / Truck</th>
                <th>Arrival Time</th>
                <th>Discrepancy / Audit Justification</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${inwardRecords.length === 0 ? `
                <tr><td colspan="10" style="text-align:center; padding:32px; color:var(--text-muted);">No inward discrepancy records found.</td></tr>
              ` : inwardRecords.map(r => `
                <tr>
                  <td><code>${r.dispatch_id}</code></td>
                  <td><code>${r.batch_id}</code></td>
                  <td><strong>${r.crop_name}</strong></td>
                  <td style="font-weight:700; color:#1565c0;">${Number(r.sent_quantity_kg).toLocaleString()} kg</td>
                  <td style="font-weight:700; color:#2e7d32;">${Number(r.received_quantity_kg).toLocaleString()} kg</td>
                  <td>
                    ${r.difference_kg === 0 ? `
                      <span class="badge badge-success">0 kg</span>
                    ` : `
                      <span class="badge badge-danger">${r.difference_kg > 0 ? `-${r.difference_kg}` : `+${Math.abs(r.difference_kg)}`} kg</span>
                    `}
                  </td>
                  <td>🚚 ${r.truck_number} (${r.driver_name})</td>
                  <td style="font-size:0.75rem;">${r.arrival_time || 'N/A'}</td>
                  <td style="font-size:0.75rem; color:#455a64;">${r.discrepancy_reason || 'Exact Match'}</td>
                  <td>
                    <span class="badge ${r.verification_status === 'VERIFIED_IN_STOCK' ? 'badge-success' : 'badge-danger'}">
                      ${r.verification_status}
                    </span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="alert-box danger">Failed to load discrepancy audit: ${err.message}</div>`;
  }
}
"""

# Replace old renderTruckTracking block
if old_truck_func in content:
    # Find the end of completeTruckDuty block
    idx_start = content.find(old_truck_func)
    idx_end = content.find("// --- 8. BULK BUYER: SINGLE-ID STREAMLINED PROCUREMENT ---", idx_start)
    if idx_end != -1:
        content = content[:idx_start] + task7_code + "\n" + content[idx_end:]
        print("Replaced old truck tracking with Task 7 implementation suite.")
    else:
        print("Could not find end index.")
else:
    print("Could not find old_truck_func.")

# Now update window exports at the end
window_task7_exports = """
// KrushiSetu Task 7: Major Warehouse -> Minor Warehouse Dispatch & Truck Tracking Exports
window.renderMajorWHDispatchesConsole = renderMajorWHDispatchesConsole;
window.setDispatchFilter = setDispatchFilter;
window.openCreateDispatchModal = openCreateDispatchModal;
window.onDispatchBatchSelected = onDispatchBatchSelected;
window.onDispatchTruckSelected = onDispatchTruckSelected;
window.handleCreateDispatchSubmit = handleCreateDispatchSubmit;
window.handleStartTransit = handleStartTransit;
window.openDispatchDetailModal = openDispatchDetailModal;
window.openEditDispatchModal = openEditDispatchModal;
window.handleUpdateDispatchSubmit = handleUpdateDispatchSubmit;
window.renderTruckTrackingConsole = renderTruckTrackingConsole;
window.renderTruckTracking = renderTruckTracking;
window.openDispatchTrackingModal = openDispatchTrackingModal;
window.openSimulateGPSModal = openSimulateGPSModal;
window.handleSimulateGPSSubmit = handleSimulateGPSSubmit;
window.renderMinorWHInwardConsole = renderMinorWHInwardConsole;
window.openMinorWHReceiveModal = openMinorWHReceiveModal;
window.updateMinorWHReceiveDiff = updateMinorWHReceiveDiff;
window.handleMinorWHReceiveSubmit = handleMinorWHReceiveSubmit;
window.renderMinorWHSentReceivedConsole = renderMinorWHSentReceivedConsole;
"""

if "window.renderMajorWHDispatchesConsole" not in content:
    content += window_task7_exports
    print("Appended Task 7 window exports.")

with open(dashboard_js_path, "w", encoding="utf-8") as f:
    f.write(content)

print("dashboard.js updated successfully.")

