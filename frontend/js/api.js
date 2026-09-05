// API Client module for Real-Time Blood Availability System
const API_BASE = "/api";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  if (config.body && typeof config.body === "object") {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    if (response.status === 204) {
      return null;
    }
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "API request failed");
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const API = {
  // Dashboard
  getDashboardStats: () => request("/dashboard/stats"),

  // Hospitals
  getHospitals: () => request("/hospitals"),
  createHospital: (data) => request("/hospitals", { method: "POST", body: data }),
  updateHospital: (id, data) => request(`/hospitals/${id}`, { method: "PUT", body: data }),
  deleteHospital: (id) => request(`/hospitals/${id}`, { method: "DELETE" }),

  // Doctors
  getDoctors: () => request("/doctors"),
  createDoctor: (data) => request("/doctors", { method: "POST", body: data }),
  updateDoctor: (id, data) => request(`/doctors/${id}`, { method: "PUT", body: data }),
  deleteDoctor: (id) => request(`/doctors/${id}`, { method: "DELETE" }),

  // Patients
  getPatients: () => request("/patients"),
  createPatient: (data) => request("/patients", { method: "POST", body: data }),
  updatePatient: (id, data) => request(`/patients/${id}`, { method: "PUT", body: data }),
  deletePatient: (id) => request(`/patients/${id}`, { method: "DELETE" }),

  // Donors
  getDonors: (bloodGroup, availableOnly) => {
    let query = [];
    if (bloodGroup) query.push(`blood_group=${encodeURIComponent(bloodGroup)}`);
    if (availableOnly) query.push(`available_only=true`);
    const qStr = query.length > 0 ? `?${query.join("&")}` : "";
    return request(`/donors${qStr}`);
  },
  createDonor: (data) => request("/donors", { method: "POST", body: data }),
  updateDonor: (id, data) => request(`/donors/${id}`, { method: "PUT", body: data }),
  updateDonorAvailability: (id, isAvailable) => request(`/donors/${id}/availability`, { method: "PATCH", body: { is_available: isAvailable } }),
  deleteDonor: (id) => request(`/donors/${id}`, { method: "DELETE" }),

  // Inventory
  getInventory: (hospitalId, bloodGroup) => {
    let query = [];
    if (hospitalId) query.push(`hospital_id=${hospitalId}`);
    if (bloodGroup) query.push(`blood_group=${encodeURIComponent(bloodGroup)}`);
    const qStr = query.length > 0 ? `?${query.join("&")}` : "";
    return request(`/inventory${qStr}`);
  },
  updateInventory: (data) => request("/inventory/update", { method: "PUT", body: data }),
  allocateInventory: (data) => request("/inventory/allocate", { method: "POST", body: data }),

  // Blood Requests
  getBloodRequests: (urgency, statusFilter) => {
    let query = [];
    if (urgency) query.push(`urgency=${encodeURIComponent(urgency)}`);
    if (statusFilter) query.push(`status_filter=${encodeURIComponent(statusFilter)}`);
    const qStr = query.length > 0 ? `?${query.join("&")}` : "";
    return request(`/blood-requests${qStr}`);
  },
  getBloodRequest: (id) => request(`/blood-requests/${id}`),
  createBloodRequest: (data) => request("/blood-requests", { method: "POST", body: data }),
  updateRequestStatus: (id, status) => request(`/blood-requests/${id}/status`, { method: "PATCH", body: { status } }),
  deleteBloodRequest: (id) => request(`/blood-requests/${id}`, { method: "DELETE" }),

  // Donations
  getDonations: () => request("/donations"),
  createDonation: (data) => request("/donations", { method: "POST", body: data }),

  // Matching Engine
  runMatching: (requestId) => request(`/matching/run/${requestId}`, { method: "POST" }),
  getMatchingResults: (requestId) => request(`/matching/results/${requestId}`),
};
