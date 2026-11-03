import React, { useState, useEffect } from 'react';
import { HospitalAPI } from './api/client';
import { 
  Activity, 
  Bed, 
  AlertTriangle, 
  UserCheck, 
  Send, 
  ShieldAlert, 
  Pill, 
  Calendar, 
  CheckCircle2, 
  Clock 
} from 'lucide-react';

export default function App() {
  // State
  const [beds, setBeds] = useState({});
  const [doctors, setDoctors] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [patientName, setPatientName] = useState('John Doe');
  const [patientPhone, setPatientPhone] = useState('+1-555-0199');
  const [patientEmail, setPatientEmail] = useState('johndoe@example.com');

  // Form input state
  const [patientId, setPatientId] = useState(101);
  const [query, setQuery] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [vitals, setVitals] = useState('Normal');
  const [specialty, setSpecialty] = useState('General Medicine');

  // Agent execution log / results
  const [history, setHistory] = useState([]);

  // Fetch initial hospital telemetry
  const fetchTelemetry = async () => {
    try {
      const [bedRes, docRes, invRes] = await Promise.all([
        HospitalAPI.getBedStatus(),
        HospitalAPI.getDoctors(),
        HospitalAPI.getInventoryShortages()
      ]);
      setBeds(bedRes.beds || {});
      setDoctors(docRes.doctors || []);
      setInventory(invRes.predictions || []);
    } catch (err) {
      console.error("Error fetching telemetry:", err);
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 15000);
    return () => clearInterval(interval);
  }, []);

  // Handle agent dispatch
  const handleDispatch = async (e) => {
    e.preventDefault();
    if (!query) return;

    setLoading(true);
    try {
      const payload = {
        name: patientName,
        phone: patientPhone,
        email: patientEmail,
        query,
        symptoms: symptoms || query,
        vitals,
        specialty
      };

      const result = await HospitalAPI.dispatchQuery(payload);

      setHistory((prev) => [
        {
          timestamp: new Date().toLocaleTimeString(),
          query,
          result
        },
        ...prev
      ]);

      // Reset inputs & refresh live state (e.g. beds booked)
      setQuery('');
      setSymptoms('');
      fetchTelemetry();
    } catch (err) {
      alert("Error dispatching to agents: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-rose-600 rounded-lg text-white shadow-lg shadow-rose-900/40">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              AEGIS <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">HOSPITAL OPS AGENT</span>
            </h1>
            <p className="text-xs text-slate-400">Autonomous Clinical & Resource Orchestrator</p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            Decision Engine Online
          </span>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 p-6 grid grid-cols-1 xl:grid-cols-12 gap-6 max-w-[1800px] w-full mx-auto">
        
        {/* Left Side: Telemetry Metrics & Cards (4 Cols) */}
        <div className="xl:col-span-4 flex flex-col gap-6">
          
          {/* Live Bed Capacity Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Bed className="w-4 h-4 text-cyan-400" /> Bed Resource Allocation
              </h2>
              <span className="text-xs text-slate-400">Live Status</span>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xs text-slate-400">ICU Available</div>
                <div className="text-2xl font-bold text-rose-400">{beds['ICU_AVAILABLE'] || 0}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xs text-slate-400">ER Available</div>
                <div className="text-2xl font-bold text-amber-400">{beds['EMERGENCY_AVAILABLE'] || 0}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xs text-slate-400">General Available</div>
                <div className="text-2xl font-bold text-emerald-400">{beds['GENERAL_AVAILABLE'] || 0}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                <div className="text-xs text-slate-400">Total Occupied</div>
                <div className="text-2xl font-bold text-slate-300">
                  {(beds['ICU_OCCUPIED'] || 0) + (beds['EMERGENCY_OCCUPIED'] || 0) + (beds['GENERAL_OCCUPIED'] || 0)}
                </div>
              </div>
            </div>
          </div>

          {/* On-Duty Physician Schedule */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-emerald-400" /> Physician Roster
              </h2>
              <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">
                {doctors.length} On Duty
              </span>
            </div>
            <div className="divide-y divide-slate-800/60 max-h-48 overflow-y-auto">
              {doctors.map((doc) => (
                <div key={doc.id} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-medium text-slate-200">{doc.name}</div>
                    <div className="text-slate-400">{doc.specialty}</div>
                  </div>
                  <div className="flex items-center gap-1 text-slate-400 font-mono">
                    <Clock className="w-3 h-3 text-slate-500" /> {doc.shift}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Medicine Shortage Predictions */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex-1">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Pill className="w-4 h-4 text-violet-400" /> Predictive Stock Monitor
              </h2>
            </div>
            <div className="space-y-3">
              {inventory.map((item, idx) => (
                <div key={idx} className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium text-slate-200">{item.medicine_name}</span>
                    {item.is_shortage_critical ? (
                      <span className="bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Critical Exhaustion
                      </span>
                    ) : (
                      <span className="text-slate-400">Stable</span>
                    )}
                  </div>
                  <div className="flex justify-between text-slate-400 text-[11px] mt-1">
                    <span>Stock: {item.current_stock} units</span>
                    <span>Depletes in: <b className={item.is_shortage_critical ? "text-rose-400" : "text-emerald-400"}>{item.days_until_stockout} days</b></span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Side: Command Center & Orchestrator Execution Log (8 Cols) */}
        <div className="xl:col-span-8 flex flex-col gap-6">

          {/* Dispatch Input Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Send className="w-4 h-4 text-rose-400" /> Patient Intake & Agent Dispatcher
            </h2>

            <form onSubmit={handleDispatch} className="space-y-4">
              
              {/* Row 1: Patient Identity & Deduplication Keys */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Patient Full Name</label>
                  <input
                    type="text"
                    required
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    placeholder="e.g. John Doe"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Phone Number (Lookup Key)</label>
                  <input
                    type="text"
                    required
                    value={patientPhone}
                    onChange={(e) => setPatientPhone(e.target.value)}
                    placeholder="+1-555-0199"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={patientEmail}
                    onChange={(e) => setPatientEmail(e.target.value)}
                    placeholder="johndoe@example.com"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                  />
                </div>
              </div>

              {/* Row 2: Symptoms & Target Specialty */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div className="md:col-span-3">
                  <label className="text-xs text-slate-400 block mb-1">Observed Symptoms / Case Details</label>
                  <input
                    type="text"
                    placeholder="e.g. Sharp chest pain radiating to jaw, severe sweating"
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Target Specialty</label>
                  <select
                    value={specialty}
                    onChange={(e) => setSpecialty(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                  >
                    <option value="Emergency Medicine">Emergency Medicine</option>
                    <option value="Cardiology">Cardiology</option>
                    <option value="Orthopedics">Orthopedics</option>
                    <option value="General Medicine">General Medicine</option>
                  </select>
                </div>
              </div>

              {/* Row 3: Natural Language Statement & Run Swarm Button */}
              <div>
                <label className="text-xs text-slate-400 block mb-1">Natural Language Request / Patient Statement</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    required
                    placeholder="e.g. 'Emergency triage needed' or 'Book follow-up cardiology visit' or 'Generate invoice'"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-lg flex items-center gap-2 text-sm transition-all shadow-md shadow-rose-950"
                  >
                    {loading ? (
                      <span className="flex items-center gap-2">
                        <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        Evaluating...
                      </span>
                    ) : (
                      <>
                        <Send className="w-4 h-4" /> Run Swarm
                      </>
                    )}
                  </button>
                </div>
              </div>

            </form>
          </div>

          {/* Real-Time Agent Execution & Decision Feed */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" /> Real-Time Decision Engine Log
              </h2>
              <span className="text-xs text-slate-500 font-mono">LangGraph State Stream</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 max-h-[600px] pr-2">
              {history.length === 0 ? (
                <div className="text-center py-16 text-slate-500 text-sm">
                  No requests dispatched yet. Try submitting an emergency case or appointment request above.
                </div>
              ) : (
                history.map((item, index) => {
                  const dec = item.result.decision_engine_evaluation;
                  return (
                    <div key={index} className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-3">
                      {/* Header line */}
                      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-slate-400">[{item.timestamp}]</span>
                          <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-medium">
                            Intent: {item.result.intent_detected}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                            dec?.priority?.includes('LEVEL_1') || dec?.priority?.includes('LEVEL_2')
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-blue-500/20 text-blue-400'
                          }`}>
                            {dec?.priority || 'NORMAL'}
                          </span>
                        </div>
                        <span className="text-xs text-emerald-400 font-medium">Executed by Swarm</span>
                      </div>

                      {/* Decision Details Box */}
                      {dec && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 bg-slate-900/60 p-2.5 rounded border border-slate-800 text-xs">
                          <div>
                            <span className="text-slate-500 block text-[10px] uppercase">Bed Decision</span>
                            <span className="text-slate-300 font-medium">{dec.bed_allocated || "None"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block text-[10px] uppercase">Assigned Staff</span>
                            <span className="text-slate-300 font-medium">{dec.doctor_assigned || "None"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block text-[10px] uppercase">Action Type</span>
                            <span className="text-rose-400 font-medium">{dec.action_type}</span>
                          </div>
                        </div>
                      )}

                      {/* Alerts if any */}
                      {dec?.alerts?.length > 0 && (
                        <div className="bg-amber-950/30 border border-amber-800/50 p-2 rounded text-xs text-amber-300 space-y-1">
                          {dec.alerts.map((alert, i) => (
                            <div key={i} className="flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                              <span>{alert}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Final Agent Response Text */}
                      <div className="text-xs text-slate-300 whitespace-pre-line leading-relaxed bg-slate-900/40 p-3 rounded border border-slate-800/40 font-sans">
                        {item.result.response}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}