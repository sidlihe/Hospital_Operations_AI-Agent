import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const HospitalAPI = {
  // Patient Registration & Check
  registerPatient: async (patientData) => {
    const res = await axios.post(`${API_BASE}/patients/register`, patientData);
    return res.data;
  },

  getPatientHistory: async (identifier) => {
    const res = await axios.get(`${API_BASE}/patients/${identifier}/history`);
    return res.data;
  },

  // Multi-Agent Dispatcher
  dispatchQuery: async (data) => {
    const res = await axios.post(`${API_BASE}/dispatch`, data);
    return res.data;
  },

  // Bed Management
  getBedStatus: async () => {
    const res = await axios.get(`${API_BASE}/beds/breakdown`);
    return res.data;
  },

  getAllBedsDetailed: async () => {
    const res = await axios.get(`${API_BASE}/admin/beds`);
    return res.data;
  },

  releaseBed: async (bedId) => {
    const res = await axios.post(`${API_BASE}/beds/release/${bedId}`);
    return res.data;
  },

  // Doctors
  getDoctors: async () => {
    const res = await axios.get(`${API_BASE}/doctors/roster`);
    return res.data;
  },

  setDoctorAvailability: async (doctorId, isOnDuty) => {
    const res = await axios.patch(`${API_BASE}/admin/doctors/${doctorId}/availability`, {
      is_on_duty: isOnDuty
    });
    return res.data;
  },

  // Pharmacy & Inventory
  getInventoryShortages: async () => {
    const res = await axios.get(`${API_BASE}/inventory/predict-shortages`);
    return res.data;
  },

  restockMedicine: async (data) => {
    const res = await axios.post(`${API_BASE}/inventory/restock`, data);
    return res.data;
  },

  adjustInventoryStock: async (data) => {
    const res = await axios.post(`${API_BASE}/inventory/adjustments`, data);
    return res.data;
  },

  getInventoryTransactions: async () => {
    const res = await axios.get(`${API_BASE}/admin/inventory/transactions`);
    return res.data;
  }
};