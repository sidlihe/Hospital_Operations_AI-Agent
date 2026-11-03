import React, { useCallback, useState, useEffect } from 'react';
import { HospitalAPI } from './api/client';
import {
  Activity,
  Bed,
  UserCheck,
  Send,
  Pill,
  ShieldCheck,
  AlertCircle,
  Settings,
  User,
  PlusCircle,
  RefreshCw,
  Info,
  Calendar,
  CreditCard,
  HeartPulse
} from 'lucide-react';

export default function App() {
  // Navigation: 'portal' | 'admin'
  const [activeTab, setActiveTab] = useState('portal');

  // Telemetry state
  const [beds, setBeds] = useState({});
  const [adminBeds, setAdminBeds] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [stockAdjustment, setStockAdjustment] = useState(10);
  const [stockAdjustmentReason, setStockAdjustmentReason] = useState('Routine pharmacy adjustment');
  const [inventoryTransactions, setInventoryTransactions] = useState([]);
  const [telemetryError, setTelemetryError] = useState('');

  // Patient Intake Form & Regex State
  const [form, setForm] = useState({
    name: '',
    phone: '',
    email: '',
    age: 30,
    gender: 'Male'
  });
  const [errors, setErrors] = useState({});
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifiedPatient, setVerifiedPatient] = useState(null);
  const [verificationError, setVerificationError] = useState('');

  // Agent Dispatch State
  const [query, setQuery] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [specialty, setSpecialty] = useState('Emergency Medicine');
  const [loadingAgent, setLoadingAgent] = useState(false);
  const [history, setHistory] = useState([]);

  // Keep each operational panel current while reporting failures per API.
  const loadHospitalData = useCallback(async () => {
    const requests = [
      ['Bed capacity', HospitalAPI.getBedStatus()],
      ['Bed roster', HospitalAPI.getAllBedsDetailed()],
      ['Doctor roster', HospitalAPI.getDoctors()],
      ['Inventory forecast', HospitalAPI.getInventoryShortages()],
      ['Inventory audit', HospitalAPI.getInventoryTransactions()]
    ];
    const results = await Promise.allSettled(requests.map(([, request]) => request));
    const failures = [];

    results.forEach((result, index) => {
      const label = requests[index][0];
      if (result.status === 'rejected') {
        const error = result.reason;
        failures.push(`${label}: ${error?.response?.data?.detail || error?.message || error || 'Unexpected error'}`);
        return;
      }

      const data = result.value;
      if (index === 0) setBeds(data.beds || {});
      if (index === 1) setAdminBeds(data || []);
      if (index === 2) setDoctors(data.doctors || []);
      if (index === 3) setInventory(data.predictions || []);
      if (index === 4) setInventoryTransactions(data || []);
    });

    setTelemetryError(failures.join(' · '));
  }, []);

  useEffect(() => {
    loadHospitalData();
    const timer = setInterval(loadHospitalData, 10000);
    return () => clearInterval(timer);
  }, [loadHospitalData]);

  // Strict Regex Validation
  const validateIntake = () => {
    const errs = {};
    const nameRegex = /^[\p{L}][\p{L}\s.'-]{1,98}$/u;
    const phoneRegex = /^\+?[\d\s().-]{7,20}$/;
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    if (!nameRegex.test(form.name.trim())) {
      errs.name = 'Enter a name with 2-100 letters, spaces, apostrophes, or hyphens';
    }
    if (!phoneRegex.test(form.phone.trim())) {
      errs.phone = 'Enter a valid phone number, including country code when available';
    } else if (form.phone.replace(/\D/g, '').length < 7 || form.phone.replace(/\D/g, '').length > 15) {
      errs.phone = 'Phone number must contain 7-15 digits';
    }
    if (!emailRegex.test(form.email.trim())) {
      errs.email = 'Valid email address required (e.g. name@domain.com)';
    }
    if (!Number.isInteger(Number(form.age)) || Number(form.age) < 1 || Number(form.age) > 120) {
      errs.age = 'Age must be between 1 and 120';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // Step 1: Submit Patient Identity Verification
  const handlePatientVerify = async (e) => {
    e.preventDefault();
    if (!validateIntake()) return;

    setIsVerifying(true);
    setVerificationError('');
    try {
      const res = await HospitalAPI.registerPatient({
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
        age: Number(form.age),
        gender: form.gender
      });

      setVerifiedPatient({ ...res.patient, is_new_patient: res.is_new_patient });
      // Pre-fill query hint if first visit
      if (res.is_new_patient) {
        setQuery('I am feeling unwell and need immediate medical consultation');
      }
    } catch (err) {
      setVerificationError(err.response?.data?.detail || err.message);
    } finally {
      setIsVerifying(false);
    }
  };

  // Step 2: Dispatch Query to AI Multi-Agent Swarm
  const handleDispatchAgent = async (e) => {
    e.preventDefault();
    if (!query || !verifiedPatient) return;

    setLoadingAgent(true);
    try {
      const payload = {
        name: verifiedPatient.name,
        phone: verifiedPatient.phone,
        email: verifiedPatient.email,
        age: verifiedPatient.age || 30,
        gender: verifiedPatient.gender || 'Not Specified',
        query,
        symptoms: symptoms || query,
        vitals: 'Normal',
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

      setQuery('');
      setSymptoms('');
      loadHospitalData();
    } catch (err) {
      alert('Agent Execution Error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingAgent(false);
    }
  };

  // Admin Actions
  const handleReleaseBed = async (bedId) => {
    try {
      await HospitalAPI.releaseBed(bedId);
      loadHospitalData();
    } catch (err) {
      alert('Failed to release bed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleToggleDoctor = async (doctor) => {
    try {
      await HospitalAPI.setDoctorAvailability(doctor.id, !doctor.is_on_duty);
      await loadHospitalData();
    } catch (err) {
      setTelemetryError(`Doctor availability: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleAdjustStock = async (medicineName, quantityChange) => {
    try {
      await HospitalAPI.adjustInventoryStock({
        medicine_name: medicineName,
        quantity_change: quantityChange,
        reason: stockAdjustmentReason
      });
      await loadHospitalData();
    } catch (err) {
      setTelemetryError(`Inventory adjustment: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur px-6 py-3.5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-rose-600 rounded-lg text-white shadow-lg shadow-rose-900/40">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white flex items-center gap-2">
              AEGIS <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">HOSPITAL OPS</span>
            </h1>
            <p className="text-[11px] text-slate-400">Clinical Autonomous Orchestrator</p>
          </div>
        </div>

        {/* Portal Navigation Toggle */}
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('portal')}
            className={`px-4 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
              activeTab === 'portal' ? 'bg-rose-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <User className="w-3.5 h-3.5" /> Patient Intake & Agents
          </button>
          <button
            onClick={() => setActiveTab('admin')}
            className={`px-4 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
              activeTab === 'admin' ? 'bg-rose-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings className="w-3.5 h-3.5" /> Hospital Admin Console
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 p-6 max-w-[1750px] w-full mx-auto">
        {telemetryError && (
          <div role="alert" className="mb-5 rounded-lg border border-amber-500/40 bg-amber-950/40 px-4 py-3 text-xs text-amber-200">
            <div className="font-semibold">Some operational data could not be refreshed.</div>
            <div className="mt-1 text-amber-200/80">{telemetryError}</div>
          </div>
        )}
        {activeTab === 'portal' ? (
          /* ==============================================================
             PORTAL 1: PATIENT REGISTRATION + DISCLAIMER + AI SWARM
             ============================================================== */
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">

            {/* Left 4 Cols: Patient Verification & Telemetry Summary */}
            <div className="xl:col-span-4 flex flex-col gap-6">

              {/* Step 1: Patient Identity Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-3">
                  <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" /> 1. Patient Registration & Verification
                  </h2>
                  {verifiedPatient && (
                    <span className={`text-[11px] px-2 py-0.5 rounded font-mono ${
                      verifiedPatient.is_new_patient
                        ? 'bg-blue-500/20 text-blue-300'
                        : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {verifiedPatient.is_new_patient ? 'NEW REGISTRATION' : 'REGISTRY MATCH'}
                    </span>
                  )}
                </div>

                {!verifiedPatient ? (
                  <form onSubmit={handlePatientVerify} className="space-y-3 text-xs">
                    <div>
                      <label className="text-slate-400 block mb-1">Full Legal Name</label>
                      <input
                        type="text"
                        placeholder="e.g. John Doe"
                        autoComplete="name"
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-rose-500"
                      />
                      {errors.name && <p className="text-rose-400 text-[10px] mt-1">{errors.name}</p>}
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-slate-400 block mb-1">Phone Number (Lookup Key)</label>
                        <input
                          type="text"
                          inputMode="tel"
                          placeholder="+15551234567"
                          autoComplete="tel"
                          value={form.phone}
                          onChange={(e) => setForm({ ...form, phone: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-rose-500"
                        />
                        {errors.phone && <p className="text-rose-400 text-[10px] mt-1">{errors.phone}</p>}
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Email Address</label>
                        <input
                          type="email"
                          placeholder="john@example.com"
                          autoComplete="email"
                          value={form.email}
                          onChange={(e) => setForm({ ...form, email: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-rose-500"
                        />
                        {errors.email && <p className="text-rose-400 text-[10px] mt-1">{errors.email}</p>}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-slate-400 block mb-1">Age</label>
                        <input
                          type="number"
                          value={form.age}
                          onChange={(e) => setForm({ ...form, age: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-rose-500"
                        />
                      </div>
                      <div>
                        <label className="text-slate-400 block mb-1">Gender</label>
                        <select
                          value={form.gender}
                          onChange={(e) => setForm({ ...form, gender: e.target.value })}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-rose-500"
                        >
                          <option>Male</option>
                          <option>Female</option>
                          <option>Other</option>
                        </select>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isVerifying}
                      className="w-full mt-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2.5 rounded-lg transition text-xs shadow-md shadow-emerald-950 flex items-center justify-center gap-2"
                    >
                      {isVerifying ? 'Checking Hospital Registry...' : 'Check Registry & Continue'}
                    </button>
                    {verificationError && (
                      <p role="alert" className="rounded border border-rose-500/30 bg-rose-950/30 p-2 text-rose-300">
                        {verificationError}
                      </p>
                    )}
                    <p className="text-[10px] leading-relaxed text-slate-500">
                      Returning patients are matched against registered name, mobile, and email. This registry check is not SMS/OTP identity proof.
                    </p>
                  </form>
                ) : (
                  <div className="space-y-3 text-xs bg-slate-950 p-3.5 rounded-lg border border-emerald-500/30">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Patient MRN:</span>
                      <span className="font-mono font-bold text-emerald-400">{verifiedPatient.mrn}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Name:</span>
                      <span className="font-semibold text-slate-200">{verifiedPatient.name}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Email:</span>
                      <span className="text-slate-300">{verifiedPatient.email}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Phone:</span>
                      <span className="text-slate-300 font-mono">{verifiedPatient.phone}</span>
                    </div>
                    <p className="text-[10px] leading-relaxed text-slate-500">
                      {verifiedPatient.is_new_patient
                        ? 'New patient registration completed. Staff validation may still be required.'
                        : 'Existing registry record matched. This does not replace OTP verification or staff validation.'}
                    </p>
                    <button
                      onClick={() => {
                        setVerifiedPatient(null);
                        setVerificationError('');
                      }}
                      className="w-full mt-2 border border-slate-700 hover:border-slate-500 text-slate-300 py-1.5 rounded transition text-[11px]"
                    >
                      Switch / Verify Another Patient
                    </button>
                  </div>
                )}
              </div>

              {/* Live Resource Overview */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-4 h-4 text-rose-400" /> Operational Capacity
                </h3>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">ICU Free</span>
                    <span className="text-lg font-bold text-rose-400">{beds['ICU_AVAILABLE'] || 0}</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">ER Free</span>
                    <span className="text-lg font-bold text-amber-400">{beds['EMERGENCY_AVAILABLE'] || 0}</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">General Free</span>
                    <span className="text-lg font-bold text-emerald-400">{beds['GENERAL_AVAILABLE'] || 0}</span>
                  </div>
                </div>
              </div>

            </div>

            {/* Right 8 Cols: AI Scope Disclaimer + Dispatcher + Stream Log */}
            <div className="xl:col-span-8 flex flex-col gap-6">
              
              {/* Mandatory AI Clinical Scope Disclaimer */}
              <div className="bg-blue-950/20 border border-blue-500/30 rounded-xl p-4 text-xs text-blue-200">
                <div className="flex items-center gap-2 font-semibold text-blue-400 mb-1.5">
                  <Info className="w-4 h-4" /> AI Operations Scope & Capabilities Guide
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-2 text-[11px] text-blue-200/80">
                  <div className="bg-slate-900/60 p-2 rounded border border-blue-500/20">
                    <b className="text-rose-400 block mb-0.5 flex items-center gap-1"><HeartPulse className="w-3 h-3"/> Emergency Triage:</b>
                    Severe chest pain, collapse, trauma. Auto-reserves ICU/ER bays.
                  </div>
                  <div className="bg-slate-900/60 p-2 rounded border border-blue-500/20">
                    <b className="text-emerald-400 block mb-0.5 flex items-center gap-1"><Calendar className="w-3 h-3"/> Consult Scheduling:</b>
                    Routine appointments with on-duty Cardiologists or Surgeons.
                  </div>
                  <div className="bg-slate-900/60 p-2 rounded border border-blue-500/20">
                    <b className="text-amber-400 block mb-0.5 flex items-center gap-1"><CreditCard className="w-3 h-3"/> Inpatient Billing:</b>
                    Itemized cost breakdown with 80% insurance estimation.
                  </div>
                  <div className="bg-slate-900/60 p-2 rounded border border-blue-500/20">
                    <b className="text-violet-400 block mb-0.5 flex items-center gap-1"><Pill className="w-3 h-3"/> Pharmacy Queries:</b>
                    Predicted burn-rate and drug stockout timelines.
                  </div>
                </div>
              </div>

              {/* Step 2: Agent Dispatch Console */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Send className="w-4 h-4 text-rose-400" /> 2. AI Multi-Agent Clinical Dispatcher
                </h2>

                {!verifiedPatient ? (
                  <div className="bg-slate-950/80 border border-amber-500/20 p-6 rounded-lg text-center text-slate-400 text-xs">
                    <AlertCircle className="w-6 h-6 text-amber-400 mx-auto mb-2" />
                    Please complete Step 1 (Validate & Authenticate Patient) on the left panel to unlock the AI agent console.
                  </div>
                ) : (
                  <form onSubmit={handleDispatchAgent} className="space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div className="md:col-span-3">
                        <label className="text-xs text-slate-400 block mb-1">Observed Symptoms / Vital Signs Context</label>
                        <input
                          type="text"
                          placeholder="e.g. Sudden severe chest tightness radiating to left arm, sweating heavily"
                          value={symptoms}
                          onChange={(e) => setSymptoms(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-400 block mb-1">Target Specialty</label>
                        <select
                          value={specialty}
                          onChange={(e) => setSpecialty(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
                        >
                          <option>Emergency Medicine</option>
                          <option>Cardiology</option>
                          <option>Orthopedics</option>
                          <option>General Medicine</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Natural Language Clinical Statement / Patient Query</label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          required
                          placeholder="e.g., 'Emergency triage needed immediately' or 'Book a routine cardiology consult'"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
                        />
                        <button
                          type="submit"
                          disabled={loadingAgent}
                          className="bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg flex items-center gap-2 text-sm transition shadow-md shadow-rose-950"
                        >
                          {loadingAgent ? 'Swarm Evaluating...' : 'Dispatch Swarm'}
                        </button>
                      </div>
                    </div>
                  </form>
                )}
              </div>

              {/* Feed of Agent Decisions */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex-1 flex flex-col">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" /> Real-Time Decision Stream
                  </h3>
                  <span className="text-[10px] text-slate-500 font-mono">LangGraph Orchestrated</span>
                </div>

                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                  {history.length === 0 ? (
                    <div className="text-center py-12 text-slate-500 text-xs">
                      No decisions executed yet. Dispatch a statement above to observe multi-agent orchestration.
                    </div>
                  ) : (
                    history.map((item, idx) => {
                      const dec = item.result.decision_engine_evaluation;
                      return (
                        <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-3 text-xs">
                          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-slate-500 font-mono">[{item.timestamp}]</span>
                              <span className="bg-slate-800 text-slate-200 px-2 py-0.5 rounded font-medium">
                                Intent: {item.result.intent_detected}
                              </span>
                              <span className={`px-2 py-0.5 rounded font-semibold ${
                                dec?.priority?.includes('LEVEL_1') || dec?.priority?.includes('LEVEL_2')
                                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                  : 'bg-blue-500/20 text-blue-400'
                              }`}>
                                {dec?.priority || 'NORMAL'}
                              </span>
                            </div>
                            <span className="text-[11px] text-emerald-400 font-mono">MRN: {item.result.patient_info?.mrn}</span>
                          </div>

                          {dec && (
                            <div className="grid grid-cols-3 gap-2 bg-slate-900/80 p-2.5 rounded border border-slate-800/80 text-[11px]">
                              <div>
                                <span className="text-slate-500 block text-[9px] uppercase">Bed Allocation</span>
                                <span className="text-slate-200 font-medium">{dec.bed_allocated}</span>
                              </div>
                              <div>
                                <span className="text-slate-500 block text-[9px] uppercase">Attending Lead</span>
                                <span className="text-slate-200 font-medium">{dec.doctor_assigned}</span>
                              </div>
                              <div>
                                <span className="text-slate-500 block text-[9px] uppercase">Action Strategy</span>
                                <span className="text-rose-400 font-medium">{dec.action_type}</span>
                              </div>
                            </div>
                          )}

                          <div className="p-3 bg-slate-900/50 rounded border border-slate-800/50 text-slate-300 whitespace-pre-line leading-relaxed">
                            {item.result.patient_friendly_response || item.result.response}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

            </div>

          </div>
        ) : (
          /* ==============================================================
             PORTAL 2: ADMIN OPERATIONS CONSOLE (BEDS, DOCTORS, INVENTORY)
             ============================================================== */
          <div className="space-y-5">
            <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              {[
                ['Beds available', Object.entries(beds).filter(([key]) => key.endsWith('_AVAILABLE')).reduce((total, [, count]) => total + count, 0), 'text-cyan-300'],
                ['Doctors on duty', doctors.filter((doctor) => doctor.is_on_duty).length, 'text-emerald-300'],
                ['Critical stock alerts', inventory.filter((item) => item.is_shortage_critical).length, 'text-rose-300'],
                ['Tracked medicines', inventory.length, 'text-violet-300']
              ].map(([label, value, color]) => (
                <div key={label} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                  <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
                  <div className={`mt-1 text-2xl font-semibold ${color}`}>{value}</div>
                </div>
              ))}
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* 1. Bed Management Console */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Bed className="w-4 h-4 text-cyan-400" /> Ward & Bed Management
                </h2>
                <button onClick={loadHospitalData} className="text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1">
                  <RefreshCw className="w-3 h-3" /> Refresh
                </button>
              </div>

              <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
                {adminBeds.length === 0 && <p className="text-xs text-slate-500">No bed records are available.</p>}
                {adminBeds.map((b) => (
                  <div key={b.id} className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-bold text-slate-200">{b.room_number} <span className="text-[10px] text-slate-400 font-normal">({b.bed_type})</span></div>
                      <div className="text-[11px] mt-0.5">
                        Status:{' '}
                        <span className={b.status === 'AVAILABLE' ? 'text-emerald-400 font-medium' : 'text-rose-400 font-medium'}>
                          {b.status}
                        </span>
                        {b.assigned_patient_id && (
                          <span className="text-slate-500 ml-2 font-mono">Patient ID: #{b.assigned_patient_id}</span>
                        )}
                      </div>
                    </div>
                    {b.status === 'OCCUPIED' && (
                      <button
                        onClick={() => handleReleaseBed(b.id)}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded text-[11px] font-medium border border-slate-700"
                      >
                        Discharge & Free
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* 2. Physician Shift & Duty Roster */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-emerald-400" /> Physician Roster Control
                </h2>
              </div>

              <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
                {doctors.length === 0 && <p className="text-xs text-slate-500">No physician records are available.</p>}
                {doctors.map((doc) => (
                  <div key={doc.id} className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-semibold text-slate-200">{doc.name}</div>
                      <div className="text-[11px] text-slate-400">{doc.specialty} • Shift: {doc.shift}</div>
                    </div>
                    <button
                      type="button"
                      aria-pressed={doc.is_on_duty}
                      onClick={() => handleToggleDoctor(doc)}
                      className={`px-3 py-1.5 rounded text-[11px] font-medium border ${
                        doc.is_on_duty
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-rose-500/20 hover:text-rose-300 hover:border-rose-500/30'
                          : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-emerald-500/20 hover:text-emerald-300 hover:border-emerald-500/30'
                      }`}
                    >
                      {doc.is_on_duty ? 'On duty · Set off duty' : 'Off duty · Set on duty'}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* 3. Pharmacy Inventory & Restocking */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Pill className="w-4 h-4 text-violet-400" /> Pharmacy Inventory Control
                </h2>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span>Units:</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={stockAdjustment}
                    onChange={(e) => setStockAdjustment(e.target.value)}
                    className="w-14 bg-slate-950 border border-slate-800 rounded p-1 text-center text-xs"
                  />
                </div>
              </div>

              <label className="mb-3 text-[11px] text-slate-400">
                Adjustment reason
                <input
                  type="text"
                  maxLength="200"
                  value={stockAdjustmentReason}
                  onChange={(e) => setStockAdjustmentReason(e.target.value)}
                  className="mt-1 w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-slate-200"
                />
              </label>

              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                {inventory.length === 0 && <p className="text-xs text-slate-500">No medicine inventory records are available.</p>}
                {inventory.map((item) => (
                  <div key={item.medicine_name} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-slate-200">{item.medicine_name}</span>
                      <span className={item.is_shortage_critical ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                        {item.days_until_stockout} days left
                      </span>
                    </div>
                    <div className="flex flex-wrap justify-between items-center gap-2 text-slate-400 text-[11px]">
                      <span>On hand: <strong className="text-slate-200">{item.current_stock} units</strong> · Burn rate: {item.burn_rate_per_day}/day</span>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={!Number.isInteger(Number(stockAdjustment)) || !Number(stockAdjustment) || Number(stockAdjustment) > item.current_stock || !stockAdjustmentReason.trim()}
                          onClick={() => handleAdjustStock(item.medicine_name, -Number(stockAdjustment))}
                          className="rounded border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-amber-200 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Record usage −{stockAdjustment}
                        </button>
                        <button
                          type="button"
                          disabled={!Number.isInteger(Number(stockAdjustment)) || !Number(stockAdjustment) || !stockAdjustmentReason.trim()}
                          onClick={() => handleAdjustStock(item.medicine_name, Number(stockAdjustment))}
                          className="flex items-center gap-1 rounded border border-violet-500/40 bg-violet-600/30 px-2.5 py-1 text-violet-200 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          <PlusCircle className="w-3 h-3" /> Receive +{stockAdjustment}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 border-t border-slate-800 pt-3">
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Recent stock movements</h3>
                <div className="space-y-1.5 text-[10px] text-slate-400">
                  {inventoryTransactions.length === 0 ? (
                    <p>No stock movements recorded yet.</p>
                  ) : inventoryTransactions.slice(0, 5).map((transaction) => (
                    <div key={transaction.id} className="flex justify-between gap-3">
                      <span className="truncate">{transaction.medicine} · {transaction.reason}</span>
                      <span className={transaction.quantity_change < 0 ? 'shrink-0 text-amber-300' : 'shrink-0 text-emerald-300'}>
                        {transaction.quantity_change > 0 ? '+' : ''}{transaction.quantity_change}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

          </div>
          </div>
        )}
      </main>
    </div>
  );
}