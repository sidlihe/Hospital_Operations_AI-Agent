import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export const HospitalAPI = {
  // Dispatch request to LangGraph Orchestrator
  dispatchQuery: async (data) => {
    const res = await axios.post(`${API_BASE}/dispatch`, data);
    return res.data;
  },

  // Bed status
  getBedStatus: async () => {
    const res = await axios.get(`${API_BASE}/beds/status`);
    return res.data;
  },

  // Doctors on duty
  getDoctors: async () => {
    const res = await axios.get(`${API_BASE}/doctors/on-duty`);
    return res.data;
  },

  // Medicine shortages
  getInventoryShortages: async () => {
    const res = await axios.get(`${API_BASE}/inventory/shortages`);
    return res.data;
  },

  // Emergency triage test
  triagePatient: async (data) => {
    const res = await axios.post(`${API_BASE}/emergency/triage`, data);
    return res.data;
  }
};