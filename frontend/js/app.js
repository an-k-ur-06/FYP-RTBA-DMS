import { API } from "./api.js";
import { initWebSocket, subscribeToEvents } from "./websocket.js";

// Global App State
let currentView = "dashboard";
let selectedMatchingRequestId = null;
let cachedHospitals = [];
let cachedPatients = [];
let cachedDoctors = [];
let cachedDonors = [];

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// Modal Helpers
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

// Formatters
function formatDate(str) {
  if (!str) return "N/A";
  return new Date(str).toLocaleDateString();
}

function formatUrgencyBadge(urgency) {
  const map = {
    "Critical": "badge-critical",
    "High": "badge-high",
    "Medium": "badge-medium",
    "Low": "badge-low"
  };
  const cls = map[urgency] || "badge-secondary";
  return `<span class="badge ${cls}">${urgency}</span>`;
}

function formatStatusBadge(status) {
  const map = {
    "Fulfilled": "badge-success",
    "Matching": "badge-high",
    "Pending": "badge-medium",
    "Cancelled": "badge-critical",
    "Partially Fulfilled": "badge-low"
  };
  const cls = map[status] || "badge-secondary";
  return `<span class="badge ${cls}">${status}</span>`;
}

// View Switcher
function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.toggle("active", item.dataset.view === viewName);
  });

  document.querySelectorAll(".view-section").forEach(sec => {
    sec.classList.toggle("active", sec.id === `view-${viewName}`);
  });

  const headerTitles = {
    "dashboard": "Operational Dashboard",
    "donors": "Donor Directory & Management",
    "hospitals": "Hospital & Blood Bank Directory",
    "doctors": "Doctor Registry",
    "patients": "Patient Registry",
    "inventory": "Blood Stock Inventory Management",
    "requests": "Emergency Blood Requests",
    "matching": "Intelligent Donor Matching Pipeline"
  };

  document.getElementById("page-header-title").innerText = headerTitles[viewName] || "Dashboard";

  refreshCurrentView();
}

async function refreshCurrentView() {
  try {
    if (currentView === "dashboard") await loadDashboardView();
    else if (currentView === "donors") await loadDonorsView();
    else if (currentView === "hospitals") await loadHospitalsView();
    else if (currentView === "doctors") await loadDoctorsView();
    else if (currentView === "patients") await loadPatientsView();
    else if (currentView === "inventory") await loadInventoryView();
    else if (currentView === "requests") await loadRequestsView();
    else if (currentView === "matching") await loadMatchingView();
  } catch (err) {
    showToast(err.message || "Failed to load data", "danger");
  }
}

// 1. Dashboard View
async function loadDashboardView() {
  try {
    const stats = await API.getDashboardStats();
    if (!stats) return;

    document.getElementById("stat-total-donors").innerText = stats.total_donors ?? 0;
    document.getElementById("stat-available-donors").innerText = `${stats.available_donors ?? 0} Currently Available`;
    document.getElementById("stat-total-hospitals").innerText = stats.total_hospitals ?? 0;
    document.getElementById("stat-pending-requests").innerText = stats.pending_requests ?? 0;
    document.getElementById("stat-critical-requests").innerText = `${stats.critical_requests ?? 0} Critical Urgency`;
    document.getElementById("stat-total-inventory").innerText = stats.total_inventory_units ?? 0;
    document.getElementById("stat-low-inventory").innerText = `${stats.low_inventory_count ?? 0} Low Stock Alerts`;

    // Render regional blood stock grid
    const grid = document.getElementById("dashboard-inventory-grid");
    if (grid) {
      grid.innerHTML = "";
      const allGroups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
      const invMap = stats.inventory_by_group || {};
      allGroups.forEach(grp => {
        const units = invMap[grp] ?? 0;
        const isLow = units < 5;
        const card = document.createElement("div");
        card.className = `inventory-card ${isLow ? "low-stock" : ""}`;
        card.innerHTML = `
          <div class="blood-group">${grp}</div>
          <div class="units">${units}</div>
          <div class="unit-label">${isLow ? "Low Stock" : "Units Available"}</div>
        `;
        grid.appendChild(card);
      });
    }

    // Render recent requests
    const reqTable = document.getElementById("dashboard-recent-requests-table");
    if (reqTable) {
      reqTable.innerHTML = "";
      const recentReqs = stats.recent_requests || [];
      if (recentReqs.length === 0) {
        reqTable.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No recent requests</td></tr>`;
      } else {
        recentReqs.forEach(r => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><strong>${r.hospital_name || "N/A"}</strong></td>
            <td>${r.patient_name || "N/A"}</td>
            <td><strong>${r.blood_group}${r.rh_factor}</strong></td>
            <td>${r.units_required}</td>
            <td>${formatUrgencyBadge(r.urgency)}</td>
            <td>${formatStatusBadge(r.status)}</td>
          `;
          reqTable.appendChild(tr);
        });
      }
    }

    // Render recent matches
    const matchTable = document.getElementById("dashboard-recent-matches-table");
    if (matchTable) {
      matchTable.innerHTML = "";
      const recentMatches = stats.recent_matches || [];
      if (recentMatches.length === 0) {
        matchTable.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No recent matching runs</td></tr>`;
      } else {
        recentMatches.forEach(m => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><strong>${m.donor_name}</strong></td>
            <td>${m.blood_group}${m.rh_factor}</td>
            <td>${m.rf_suitability_score}</td>
            <td>${m.fuzzy_priority_score}</td>
            <td>${formatUrgencyBadge(m.fuzzy_priority_rank)}</td>
          `;
          matchTable.appendChild(tr);
        });
      }
    }
  } catch (err) {
    console.error("Failed to load dashboard view:", err);
    throw err;
  }
}

// 2. Donors View
async function loadDonorsView() {
  const bgFilter = document.getElementById("donor-blood-filter").value;
  const availFilter = document.getElementById("donor-status-filter").value;
  const search = document.getElementById("donor-search-input").value.toLowerCase();

  const donors = await API.getDonors(bgFilter, availFilter === "true");
  cachedDonors = donors;

  const tbody = document.getElementById("donors-table-body");
  tbody.innerHTML = "";

  const filtered = donors.filter(d => {
    if (!search) return true;
    return d.name.toLowerCase().includes(search) || d.email.toLowerCase().includes(search) || d.phone.includes(search);
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted);">No donors found</td></tr>`;
    return;
  }

  filtered.forEach(d => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${d.name}</strong><br><small style="color:var(--text-muted);">${d.email}</small></td>
      <td><strong style="color:var(--primary-red);">${d.blood_group}${d.rh_factor}</strong></td>
      <td>${d.age} / ${d.gender}</td>
      <td>${d.phone}</td>
      <td>${formatDate(d.last_donation_date)}</td>
      <td>${d.total_donations} Units</td>
      <td>
        <button class="btn btn-sm ${d.is_available ? "btn-secondary" : "btn-outline"}" data-toggle-donor="${d.id}" data-current="${d.is_available}">
          ${d.is_available ? "Available" : "Unavailable"}
        </button>
      </td>
      <td>
        <button class="btn btn-secondary btn-sm" data-edit-donor="${d.id}">Edit</button>
        <button class="btn btn-secondary btn-sm" style="color:var(--primary-red);" data-delete-donor="${d.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 3. Hospitals View
async function loadHospitalsView() {
  const hospitals = await API.getHospitals();
  cachedHospitals = hospitals;

  const tbody = document.getElementById("hospitals-table-body");
  tbody.innerHTML = "";

  if (hospitals.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No hospitals registered</td></tr>`;
    return;
  }

  hospitals.forEach(h => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${h.name}</strong></td>
      <td><code>${h.code}</code></td>
      <td>${h.city}<br><small style="color:var(--text-muted);">${h.address}</small></td>
      <td>${h.latitude}, ${h.longitude}</td>
      <td>${h.phone}</td>
      <td>${h.emergency_contact}</td>
      <td>
        <button class="btn btn-secondary btn-sm" data-edit-hospital="${h.id}">Edit</button>
        <button class="btn btn-secondary btn-sm" style="color:var(--primary-red);" data-delete-hospital="${h.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 4. Doctors View
async function loadDoctorsView() {
  const doctors = await API.getDoctors();
  cachedDoctors = doctors;

  const tbody = document.getElementById("doctors-table-body");
  tbody.innerHTML = "";

  if (doctors.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No doctors registered</td></tr>`;
    return;
  }

  doctors.forEach(d => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${d.name}</strong></td>
      <td><code>${d.license_number}</code></td>
      <td>${d.specialization}</td>
      <td>${d.hospital_name || "N/A"}</td>
      <td>${d.email}</td>
      <td>${d.phone}</td>
      <td>
        <button class="btn btn-secondary btn-sm" style="color:var(--primary-red);" data-delete-doctor="${d.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 5. Patients View
async function loadPatientsView() {
  const patients = await API.getPatients();
  cachedPatients = patients;

  const tbody = document.getElementById("patients-table-body");
  tbody.innerHTML = "";

  if (patients.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No patients registered</td></tr>`;
    return;
  }

  patients.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${p.name}</strong></td>
      <td><code>${p.medical_record_number}</code></td>
      <td>${p.age} / ${p.gender}</td>
      <td><strong style="color:var(--primary-red);">${p.blood_group}${p.rh_factor}</strong></td>
      <td>${p.hospital_name || "N/A"}</td>
      <td>${p.condition_summary || "None"}</td>
      <td>
        <button class="btn btn-secondary btn-sm" style="color:var(--primary-red);" data-delete-patient="${p.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 6. Inventory View
async function loadInventoryView() {
  await populateHospitalDropdowns();
  const hospFilter = document.getElementById("inventory-hospital-filter").value;
  const bgFilter = document.getElementById("inventory-blood-filter").value;

  const inventory = await API.getInventory(hospFilter, bgFilter);
  const tbody = document.getElementById("inventory-table-body");
  tbody.innerHTML = "";

  if (inventory.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No inventory records found</td></tr>`;
    return;
  }

  inventory.forEach(inv => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${inv.hospital_name || "N/A"}</strong></td>
      <td><strong style="color:var(--primary-red);">${inv.blood_group}${inv.rh_factor}</strong></td>
      <td><strong style="font-size:15px;">${inv.available_units}</strong></td>
      <td>${inv.reserved_units}</td>
      <td>${inv.minimum_threshold}</td>
      <td>
        ${inv.is_low_stock ? '<span class="badge badge-critical">Low Stock Alert</span>' : '<span class="badge badge-success">Sufficient</span>'}
      </td>
      <td>${new Date(inv.updated_at).toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
}

// 7. Requests View
async function loadRequestsView() {
  const urgencyFilter = document.getElementById("request-urgency-filter").value;
  const statusFilter = document.getElementById("request-status-filter").value;

  const requests = await API.getBloodRequests(urgencyFilter, statusFilter);
  const tbody = document.getElementById("requests-table-body");
  tbody.innerHTML = "";

  if (requests.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--text-muted);">No blood requests found</td></tr>`;
    return;
  }

  requests.forEach(req => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${req.hospital_name || "N/A"}</strong></td>
      <td>${req.patient_name || "N/A"}</td>
      <td><strong style="color:var(--primary-red); font-size:15px;">${req.blood_group}${req.rh_factor}</strong></td>
      <td>${req.units_required}</td>
      <td>${formatUrgencyBadge(req.urgency)}</td>
      <td>${req.clinical_severity} / 10</td>
      <td>
        <select class="form-control" style="padding:2px 4px; font-size:12px;" data-change-status="${req.id}">
          <option value="Pending" ${req.status === "Pending" ? "selected" : ""}>Pending</option>
          <option value="Matching" ${req.status === "Matching" ? "selected" : ""}>Matching</option>
          <option value="Partially Fulfilled" ${req.status === "Partially Fulfilled" ? "selected" : ""}>Partially Fulfilled</option>
          <option value="Fulfilled" ${req.status === "Fulfilled" ? "selected" : ""}>Fulfilled</option>
          <option value="Cancelled" ${req.status === "Cancelled" ? "selected" : ""}>Cancelled</option>
        </select>
      </td>
      <td>
        <button class="btn btn-primary btn-sm" data-run-matching="${req.id}">Run Intelligent Matching</button>
      </td>
      <td>
        <button class="btn btn-secondary btn-sm" style="color:var(--primary-red);" data-delete-request="${req.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 8. Matching View
async function loadMatchingView() {
  const detailsDiv = document.getElementById("matching-request-details");
  const resultsCard = document.getElementById("matching-results-card");

  if (!selectedMatchingRequestId) {
    detailsDiv.innerHTML = `<p style="color: var(--text-muted);">No blood request selected. Go to <a href="#" id="link-go-to-requests">Blood Requests</a> and click <strong>Run Intelligent Matching</strong> on a request.</p>`;
    resultsCard.style.display = "none";
    return;
  }

  const req = await API.getBloodRequest(selectedMatchingRequestId);
  detailsDiv.innerHTML = `
    <div class="form-grid" style="grid-template-columns: repeat(4, 1fr);">
      <div>
        <small style="color:var(--text-muted);">Hospital</small>
        <div style="font-weight:700;">${req.hospital_name}</div>
      </div>
      <div>
        <small style="color:var(--text-muted);">Patient</small>
        <div style="font-weight:700;">${req.patient_name}</div>
      </div>
      <div>
        <small style="color:var(--text-muted);">Required Blood Group</small>
        <div style="font-weight:800; color:var(--primary-red); font-size:18px;">${req.blood_group}${req.rh_factor} (${req.units_required} Units)</div>
      </div>
      <div>
        <small style="color:var(--text-muted);">Urgency & Status</small>
        <div>${formatUrgencyBadge(req.urgency)} ${formatStatusBadge(req.status)}</div>
      </div>
    </div>
  `;

  // Fetch or Run matching results
  let results = await API.getMatchingResults(selectedMatchingRequestId);
  if (results.length === 0) {
    results = await API.runMatching(selectedMatchingRequestId);
  }

  resultsCard.style.display = "block";
  if (results.length > 0) {
    document.getElementById("matching-exec-time").innerText = `Execution Time: ${results[0].execution_time_ms}ms`;
  }

  const tbody = document.getElementById("matching-results-table-body");
  tbody.innerHTML = "";

  if (results.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:var(--text-muted);">No compatible donors found for this request.</td></tr>`;
    return;
  }

  results.forEach(m => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong style="font-size:16px;">#${m.final_rank}</strong></td>
      <td><strong>${m.donor_name}</strong></td>
      <td><strong style="color:var(--primary-red);">${m.blood_group}${m.rh_factor}</strong></td>
      <td><span class="badge badge-success">ABO Compatible</span></td>
      <td>${m.distance_km} km</td>
      <td><strong>${m.rf_suitability_score}</strong></td>
      <td><strong>${m.fuzzy_priority_score} / 100</strong></td>
      <td>${formatUrgencyBadge(m.fuzzy_priority_rank)}</td>
      <td>${m.donor_phone}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Populate Dropdowns
async function populateHospitalDropdowns() {
  if (cachedHospitals.length === 0) {
    cachedHospitals = await API.getHospitals();
  }

  const optionsHtml = cachedHospitals.map(h => `<option value="${h.id}">${h.name} (${h.code})</option>`).join("");
  
  ["doctor-hospital-id", "patient-hospital-id", "inventory-update-hospital", "allocate-hospital", "request-hospital-id", "donation-hospital-id"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = optionsHtml;
  });

  const filterEl = document.getElementById("inventory-hospital-filter");
  if (filterEl && filterEl.options.length <= 1) {
    filterEl.innerHTML = `<option value="">All Hospitals</option>` + optionsHtml;
  }
}

async function populatePatientAndDoctorDropdowns() {
  if (cachedPatients.length === 0) cachedPatients = await API.getPatients();
  if (cachedDoctors.length === 0) cachedDoctors = await API.getDoctors();

  const patientOpts = cachedPatients.map(p => `<option value="${p.id}">${p.name} (MRN: ${p.medical_record_number} - Group: ${p.blood_group}${p.rh_factor})</option>`).join("");
  const pEl = document.getElementById("request-patient-id");
  if (pEl) pEl.innerHTML = patientOpts;

  const docOpts = `<option value="">None</option>` + cachedDoctors.map(d => `<option value="${d.id}">${d.name} (${d.specialization})</option>`).join("");
  const dEl = document.getElementById("request-doctor-id");
  if (dEl) dEl.innerHTML = docOpts;
}

async function populateDonorDropdown() {
  if (cachedDonors.length === 0) cachedDonors = await API.getDonors();
  const opts = cachedDonors.map(d => `<option value="${d.id}">${d.name} (${d.blood_group}${d.rh_factor} - ${d.phone})</option>`).join("");
  const el = document.getElementById("donation-donor-id");
  if (el) el.innerHTML = opts;
}

// Global Event Delegation & Event Handlers
function setupEventListeners() {
  // Sidebar navigation
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      switchView(item.dataset.view);
    });
  });

  // Quick Action Buttons
  document.getElementById("btn-quick-request").addEventListener("click", async () => {
    await populateHospitalDropdowns();
    await populatePatientAndDoctorDropdowns();
    openModal("modal-request");
  });

  document.getElementById("btn-quick-donor").addEventListener("click", () => {
    document.getElementById("form-donor").reset();
    document.getElementById("donor-id").value = "";
    document.getElementById("modal-donor-title").innerText = "Register New Donor";
    openModal("modal-donor");
  });

  document.getElementById("btn-quick-donation").addEventListener("click", async () => {
    await populateHospitalDropdowns();
    await populateDonorDropdown();
    openModal("modal-donation");
  });

  document.getElementById("btn-view-all-inventory").addEventListener("click", () => {
    switchView("inventory");
  });

  // Modal Close Buttons
  document.querySelectorAll("[data-close]").forEach(btn => {
    btn.addEventListener("click", () => {
      closeModal(btn.dataset.close);
    });
  });

  // Donors Page Actions
  document.getElementById("btn-add-donor").addEventListener("click", () => {
    document.getElementById("form-donor").reset();
    document.getElementById("donor-id").value = "";
    document.getElementById("modal-donor-title").innerText = "Register New Donor";
    openModal("modal-donor");
  });

  document.getElementById("btn-save-donor").addEventListener("click", async () => {
    const dId = document.getElementById("donor-id").value;
    const payload = {
      name: document.getElementById("donor-name").value,
      email: document.getElementById("donor-email").value,
      phone: document.getElementById("donor-phone").value,
      blood_group: document.getElementById("donor-blood-group").value,
      rh_factor: document.getElementById("donor-rh-factor").value,
      age: parseInt(document.getElementById("donor-age").value),
      gender: document.getElementById("donor-gender").value,
      latitude: parseFloat(document.getElementById("donor-lat").value),
      longitude: parseFloat(document.getElementById("donor-lng").value),
      is_available: document.getElementById("donor-is-available").value === "true"
    };

    try {
      if (dId) {
        await API.updateDonor(dId, payload);
        showToast("Donor updated successfully!", "success");
      } else {
        await API.createDonor(payload);
        showToast("Donor registered successfully!", "success");
      }
      closeModal("modal-donor");
      refreshCurrentView();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("donor-search-input").addEventListener("input", () => loadDonorsView());
  document.getElementById("donor-blood-filter").addEventListener("change", () => loadDonorsView());
  document.getElementById("donor-status-filter").addEventListener("change", () => loadDonorsView());

  document.getElementById("donors-table-body").addEventListener("click", async (e) => {
    const toggleBtn = e.target.closest("[data-toggle-donor]");
    if (toggleBtn) {
      const id = toggleBtn.dataset.toggleDonor;
      const current = toggleBtn.dataset.current === "true";
      await API.updateDonorAvailability(id, !current);
      showToast(`Donor availability updated to ${!current ? 'Available' : 'Unavailable'}`, "success");
      loadDonorsView();
      return;
    }

    const editBtn = e.target.closest("[data-edit-donor]");
    if (editBtn) {
      const id = editBtn.dataset.editDonor;
      const donor = cachedDonors.find(d => d.id === id);
      if (donor) {
        document.getElementById("donor-id").value = donor.id;
        document.getElementById("donor-name").value = donor.name;
        document.getElementById("donor-email").value = donor.email;
        document.getElementById("donor-phone").value = donor.phone;
        document.getElementById("donor-blood-group").value = donor.blood_group;
        document.getElementById("donor-rh-factor").value = donor.rh_factor;
        document.getElementById("donor-age").value = donor.age;
        document.getElementById("donor-gender").value = donor.gender;
        document.getElementById("donor-lat").value = donor.latitude;
        document.getElementById("donor-lng").value = donor.longitude;
        document.getElementById("donor-is-available").value = donor.is_available ? "true" : "false";
        document.getElementById("modal-donor-title").innerText = "Edit Donor Details";
        openModal("modal-donor");
      }
      return;
    }

    const delBtn = e.target.closest("[data-delete-donor]");
    if (delBtn) {
      if (confirm("Are you sure you want to delete this donor?")) {
        await API.deleteDonor(delBtn.dataset.deleteDonor);
        showToast("Donor record deleted", "warning");
        loadDonorsView();
      }
    }
  });

  // Hospitals Page Actions
  document.getElementById("btn-add-hospital").addEventListener("click", () => {
    document.getElementById("form-hospital").reset();
    document.getElementById("hospital-id").value = "";
    document.getElementById("modal-hospital-title").innerText = "Add New Hospital";
    openModal("modal-hospital");
  });

  document.getElementById("btn-save-hospital").addEventListener("click", async () => {
    const hId = document.getElementById("hospital-id").value;
    const payload = {
      name: document.getElementById("hospital-name").value,
      code: document.getElementById("hospital-code").value,
      city: document.getElementById("hospital-city").value,
      address: document.getElementById("hospital-address").value,
      latitude: parseFloat(document.getElementById("hospital-lat").value),
      longitude: parseFloat(document.getElementById("hospital-lng").value),
      phone: document.getElementById("hospital-phone").value,
      emergency_contact: document.getElementById("hospital-emergency").value
    };

    try {
      if (hId) {
        await API.updateHospital(hId, payload);
        showToast("Hospital details updated!", "success");
      } else {
        await API.createHospital(payload);
        showToast("Hospital created successfully!", "success");
      }
      closeModal("modal-hospital");
      cachedHospitals = [];
      refreshCurrentView();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("hospitals-table-body").addEventListener("click", async (e) => {
    const editBtn = e.target.closest("[data-edit-hospital]");
    if (editBtn) {
      const id = editBtn.dataset.editHospital;
      const h = cachedHospitals.find(item => item.id === id);
      if (h) {
        document.getElementById("hospital-id").value = h.id;
        document.getElementById("hospital-name").value = h.name;
        document.getElementById("hospital-code").value = h.code;
        document.getElementById("hospital-city").value = h.city;
        document.getElementById("hospital-address").value = h.address;
        document.getElementById("hospital-lat").value = h.latitude;
        document.getElementById("hospital-lng").value = h.longitude;
        document.getElementById("hospital-phone").value = h.phone;
        document.getElementById("hospital-emergency").value = h.emergency_contact;
        document.getElementById("modal-hospital-title").innerText = "Edit Hospital Details";
        openModal("modal-hospital");
      }
      return;
    }

    const delBtn = e.target.closest("[data-delete-hospital]");
    if (delBtn) {
      if (confirm("Delete this hospital and associated inventory/requests?")) {
        await API.deleteHospital(delBtn.dataset.deleteHospital);
        showToast("Hospital deleted", "warning");
        cachedHospitals = [];
        loadHospitalsView();
      }
    }
  });

  // Doctors Page Actions
  document.getElementById("btn-add-doctor").addEventListener("click", async () => {
    await populateHospitalDropdowns();
    document.getElementById("form-doctor").reset();
    openModal("modal-doctor");
  });

  document.getElementById("btn-save-doctor").addEventListener("click", async () => {
    const payload = {
      hospital_id: document.getElementById("doctor-hospital-id").value,
      name: document.getElementById("doctor-name").value,
      license_number: document.getElementById("doctor-license").value,
      specialization: document.getElementById("doctor-spec").value,
      phone: document.getElementById("doctor-phone").value,
      email: document.getElementById("doctor-email").value
    };

    try {
      await API.createDoctor(payload);
      showToast("Doctor registered successfully!", "success");
      closeModal("modal-doctor");
      cachedDoctors = [];
      loadDoctorsView();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("doctors-table-body").addEventListener("click", async (e) => {
    const delBtn = e.target.closest("[data-delete-doctor]");
    if (delBtn) {
      if (confirm("Delete doctor record?")) {
        await API.deleteDoctor(delBtn.dataset.deleteDoctor);
        showToast("Doctor record deleted", "warning");
        cachedDoctors = [];
        loadDoctorsView();
      }
    }
  });

  // Patients Page Actions
  document.getElementById("btn-add-patient").addEventListener("click", async () => {
    await populateHospitalDropdowns();
    document.getElementById("form-patient").reset();
    openModal("modal-patient");
  });

  document.getElementById("btn-save-patient").addEventListener("click", async () => {
    const payload = {
      hospital_id: document.getElementById("patient-hospital-id").value,
      name: document.getElementById("patient-name").value,
      medical_record_number: document.getElementById("patient-mrn").value,
      age: parseInt(document.getElementById("patient-age").value),
      gender: document.getElementById("patient-gender").value,
      blood_group: document.getElementById("patient-blood-group").value,
      rh_factor: document.getElementById("patient-rh-factor").value,
      condition_summary: document.getElementById("patient-condition").value
    };

    try {
      await API.createPatient(payload);
      showToast("Patient registered successfully!", "success");
      closeModal("modal-patient");
      cachedPatients = [];
      loadPatientsView();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("patients-table-body").addEventListener("click", async (e) => {
    const delBtn = e.target.closest("[data-delete-patient]");
    if (delBtn) {
      if (confirm("Delete patient record?")) {
        await API.deletePatient(delBtn.dataset.deletePatient);
        showToast("Patient record deleted", "warning");
        cachedPatients = [];
        loadPatientsView();
      }
    }
  });

  // Inventory Page Actions
  document.getElementById("btn-update-inventory-units").addEventListener("click", async () => {
    await populateHospitalDropdowns();
    openModal("modal-inventory");
  });

  document.getElementById("btn-save-inventory").addEventListener("click", async () => {
    const payload = {
      hospital_id: document.getElementById("inventory-update-hospital").value,
      blood_group: document.getElementById("inventory-update-group").value,
      rh_factor: document.getElementById("inventory-update-rh").value,
      available_units: parseInt(document.getElementById("inventory-update-units").value),
      minimum_threshold: parseInt(document.getElementById("inventory-update-threshold").value)
    };

    try {
      await API.updateInventory(payload);
      showToast("Inventory stock updated!", "success");
      closeModal("modal-inventory");
      loadInventoryView();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("btn-allocate-units").addEventListener("click", async () => {
    await populateHospitalDropdowns();
    openModal("modal-allocate");
  });

  document.getElementById("btn-confirm-allocate").addEventListener("click", async () => {
    const payload = {
      hospital_id: document.getElementById("allocate-hospital").value,
      blood_group: document.getElementById("allocate-group").value,
      rh_factor: document.getElementById("allocate-rh").value,
      units_to_allocate: parseInt(document.getElementById("allocate-units").value)
    };

    try {
      await API.allocateInventory(payload);
      showToast("Units allocated successfully!", "success");
      closeModal("modal-allocate");
      loadInventoryView();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("inventory-hospital-filter").addEventListener("change", () => loadInventoryView());
  document.getElementById("inventory-blood-filter").addEventListener("change", () => loadInventoryView());

  // Blood Requests Actions
  document.getElementById("btn-create-request").addEventListener("click", async () => {
    await populateHospitalDropdowns();
    await populatePatientAndDoctorDropdowns();
    openModal("modal-request");
  });

  document.getElementById("btn-save-request").addEventListener("click", async () => {
    const payload = {
      hospital_id: document.getElementById("request-hospital-id").value,
      patient_id: document.getElementById("request-patient-id").value,
      doctor_id: document.getElementById("request-doctor-id").value || null,
      blood_group: document.getElementById("request-group").value,
      rh_factor: document.getElementById("request-rh").value,
      units_required: parseInt(document.getElementById("request-units").value),
      urgency: document.getElementById("request-urgency").value,
      clinical_severity: parseFloat(document.getElementById("request-severity").value)
    };

    try {
      const created = await API.createBloodRequest(payload);
      showToast("Emergency blood request created!", "success");
      closeModal("modal-request");
      
      // Auto-trigger matching view
      selectedMatchingRequestId = created.id;
      switchView("matching");
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("request-urgency-filter").addEventListener("change", () => loadRequestsView());
  document.getElementById("request-status-filter").addEventListener("change", () => loadRequestsView());

  document.getElementById("requests-table-body").addEventListener("change", async (e) => {
    const selectEl = e.target.closest("[data-change-status]");
    if (selectEl) {
      const id = selectEl.dataset.changeStatus;
      const newStatus = selectEl.value;
      await API.updateRequestStatus(id, newStatus);
      showToast(`Request status updated to ${newStatus}`, "success");
    }
  });

  document.getElementById("requests-table-body").addEventListener("click", async (e) => {
    const matchBtn = e.target.closest("[data-run-matching]");
    if (matchBtn) {
      selectedMatchingRequestId = matchBtn.dataset.runMatching;
      switchView("matching");
      return;
    }

    const delBtn = e.target.closest("[data-delete-request]");
    if (delBtn) {
      if (confirm("Delete this blood request?")) {
        await API.deleteBloodRequest(delBtn.dataset.deleteRequest);
        showToast("Request deleted", "warning");
        loadRequestsView();
      }
    }
  });

  // Donation Recording Actions
  document.getElementById("btn-save-donation").addEventListener("click", async () => {
    const payload = {
      donor_id: document.getElementById("donation-donor-id").value,
      hospital_id: document.getElementById("donation-hospital-id").value,
      blood_group: document.getElementById("donation-group").value,
      rh_factor: document.getElementById("donation-rh").value,
      units: parseInt(document.getElementById("donation-units").value)
    };

    try {
      await API.createDonation(payload);
      showToast("Donation recorded and blood inventory increased!", "success");
      closeModal("modal-donation");
      cachedDonors = [];
      refreshCurrentView();
    } catch (err) {
      showToast(err.message, "danger");
    }
  });

  document.getElementById("btn-back-to-requests").addEventListener("click", () => switchView("requests"));
  
  document.addEventListener("click", (e) => {
    if (e.target.id === "link-go-to-requests") {
      e.preventDefault();
      switchView("requests");
    }
  });
}

// Real-Time WebSocket Event Subscriber
function setupWebSocketHandler() {
  const dot = document.getElementById("ws-dot");
  const txt = document.getElementById("ws-status-text");

  initWebSocket((connected) => {
    if (connected) {
      dot.className = "ws-dot connected";
      txt.innerText = "Live Real-Time";
    } else {
      dot.className = "ws-dot";
      txt.innerText = "Connecting...";
    }
  });

  subscribeToEvents((event, data) => {
    console.log("WebSocket event handler triggered:", event, data);
    
    if (event === "inventory_updated") {
      showToast(`Blood stock update: ${data.hospital_name} - ${data.blood_group} (${data.available_units} Units available)`, "info");
    } else if (event === "blood_request_created") {
      showToast(`New Emergency Request: ${data.hospital_name} - ${data.blood_group} (${data.urgency})`, "danger");
    } else if (event === "donor_availability_updated") {
      showToast(`Donor status change: ${data.name} is now ${data.is_available ? 'Available' : 'Unavailable'}`, "info");
    } else if (event === "matching_completed") {
      showToast(`Donor Matching completed! ${data.total_matches} donors ranked in ${data.execution_time_ms}ms`, "success");
    }

    // Auto-refresh active view without manual reload
    refreshCurrentView();
  });
}

// App Initialization
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  setupWebSocketHandler();
  switchView("dashboard");
});
