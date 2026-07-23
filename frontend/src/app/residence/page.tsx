"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { complaintsApi, incidentsApi } from "@/lib/api";
import {
  FileText, Plus, CheckCircle2, AlertTriangle, AlertCircle, Info, Home, ShieldAlert, Clock
} from "lucide-react";

interface Complaint {
  id: string;
  resident_id: string;
  title: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  linked_incident_id?: string;
  ai_confidence_score?: number;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

const CATEGORIES = [
  { value: "lift", label: "Lift / Elevator" },
  { value: "smell", label: "Odor / Smell" },
  { value: "plumbing", label: "Plumbing / Leakage" },
  { value: "electrical", label: "Electrical / Power" },
  { value: "noise", label: "Noise Disturbance" },
  { value: "structural", label: "Structural Damage" },
  { value: "parking", label: "Parking Issue" },
  { value: "security", label: "Security Concern" },
  { value: "other", label: "Other Issues" },
];

const PRIORITIES = [
  { value: "low", label: "Low (General)" },
  { value: "medium", label: "Medium (Standard)" },
  { value: "high", label: "High (Urgent Attention)" },
  { value: "urgent", label: "Urgent (Immediate Danger)" },
];

const STATUS_BADGES: Record<string, string> = {
  submitted: "bg-amber-100 text-amber-900 border-amber-300 font-bold",
  under_review: "bg-indigo-100 text-indigo-900 border-indigo-300 font-bold",
  converted_to_incident: "bg-blue-100 text-blue-900 border-blue-300 font-bold",
  assigned: "bg-cyan-100 text-cyan-900 border-cyan-300 font-bold",
  resolved: "bg-emerald-100 text-emerald-900 border-emerald-300 font-bold",
  rejected: "bg-rose-100 text-rose-900 border-rose-300 font-bold",
};

export default function ResidencePage() {
  const { token, user } = useAuth();
  
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [incidents, setIncidents] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("plumbing");
  const [priority, setPriority] = useState("medium");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  const fetchComplaints = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await complaintsApi.listMine(token);
      const items = res.items || [];
      setComplaints(items);
      setError(null);

      // Async fetch linked incidents
      const linkedIds = items
        .map((c: any) => c.linked_incident_id)
        .filter((id: any) => !!id) as string[];

      if (linkedIds.length > 0) {
        const uniqueIds = Array.from(new Set(linkedIds));
        const fetchedMap: Record<string, any> = {};
        await Promise.all(
          uniqueIds.map(async (id) => {
            try {
              const incident = await incidentsApi.get(token, id);
              fetchedMap[id] = incident;
            } catch {
              // ignore fetch failure for individual incident
            }
          })
        );
        setIncidents((prev) => ({ ...prev, ...fetchedMap }));
      }
    } catch (err: any) {
      setError(err.message || "Failed to load complaints.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
    // Poll every 15s so the stepper timeline reflects admin/manager incident updates automatically
    const interval = setInterval(fetchComplaints, 15000);
    return () => clearInterval(interval);
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setFormSubmitting(true);
    setSuccessMsg(null);
    setError(null);
    
    try {
      await complaintsApi.create(token, { title, description, category, priority });
      setSuccessMsg("Complaint submitted successfully! Our operators will review it shortly.");
      setTitle("");
      setDescription("");
      fetchComplaints();
    } catch (err: any) {
      setError(err.message || "Failed to submit complaint.");
    } finally {
      setFormSubmitting(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Welcome header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-gradient-to-r from-amber-500/10 to-yellow-500/5 border border-amber-300 rounded-3xl p-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center shadow-inner">
            <Home className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-stone-800 tracking-tight">Resident Portal</h1>
            <p className="text-xs text-stone-500 mt-1">
              Logged in as <span className="text-stone-800 font-medium">{user?.full_name || "Resident"}</span> &bull; Flat 302, Tower A
            </p>
          </div>
        </div>
        <div className="px-4 py-2 bg-stone-100 border border-stone-200 rounded-xl text-center">
          <p className="text-[10px] text-stone-500 uppercase tracking-wider">Apartment Status</p>
          <p className="text-xs font-semibold text-emerald-600 mt-0.5">Occupied &bull; Active</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Side: Create Complaint Form */}
        <div className="lg:col-span-1 bg-white border border-stone-200 rounded-3xl p-6 space-y-6 shadow-xl">
          <div>
            <div className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-amber-600" />
              <h2 className="text-lg font-bold text-stone-800 tracking-tight">File a Complaint</h2>
            </div>
            <p className="text-xs text-stone-500 mt-1">Submit maintenance or amenity issues to society operators.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Issue Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-stone-100 border border-stone-200 text-sm text-stone-800 focus:outline-none focus:border-amber-500 focus:bg-stone-100 transition"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value} className="bg-white text-stone-800">
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Priority Level
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-stone-100 border border-stone-200 text-sm text-stone-800 focus:outline-none focus:border-amber-500 focus:bg-stone-100 transition"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value} className="bg-white text-stone-800">
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Complaint Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Pipe leakage in kitchen"
                className="w-full px-4 py-3 rounded-xl bg-stone-100 border border-stone-200 text-sm text-stone-800 focus:outline-none focus:border-amber-500 focus:bg-stone-100 transition"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Detailed Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="Describe the issue in detail (location, when it started, etc.)..."
                className="w-full px-4 py-3 rounded-xl bg-stone-100 border border-stone-200 text-sm text-stone-800 focus:outline-none focus:border-amber-500 focus:bg-stone-100 transition"
                required
              />
            </div>

            {successMsg && (
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-2 text-xs text-emerald-600 leading-snug">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>{successMsg}</span>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2 text-xs text-rose-600 leading-snug">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={formSubmitting}
              className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:bg-amber-300 text-stone-800 text-sm font-semibold transition shadow-lg shadow-amber-200/40"
            >
              {formSubmitting ? "Submitting..." : "Submit Complaint"}
            </button>
          </form>
        </div>

        {/* Right Side: Track Complaints */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="text-lg font-bold text-stone-800 tracking-tight">Complaint History</h2>
            <p className="text-xs text-stone-500 mt-1">Track progress, review conversions, and view resolution details.</p>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-amber-600"></div>
            </div>
          ) : complaints.length === 0 ? (
            <div className="border border-dashed border-stone-200 rounded-3xl p-12 text-center text-stone-400">
              <FileText className="mx-auto h-12 w-12 text-stone-400 mb-3 animate-pulse" />
              <p className="text-sm font-medium">No complaints found</p>
              <p className="text-xs mt-1">You haven't filed any complaints yet. Use the form on the left to file your first issue.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {complaints.map((c) => (
                <div key={c.id} className="bg-white border border-stone-200 rounded-3xl p-6 space-y-4 shadow-lg">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-amber-600 font-mono tracking-wider">
                        {c.category} &bull; {c.priority} Priority
                      </span>
                      <h3 className="text-base font-bold text-stone-800 tracking-tight mt-1">{c.title}</h3>
                    </div>
                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_BADGES[c.status] || "bg-stone-400/20 text-stone-400"}`}>
                      {c.status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <p className="text-sm text-stone-600 leading-relaxed bg-stone-100 p-3 rounded-2xl border border-stone-200">
                    {c.description}
                  </p>

                  {/* If linked to an incident, display Ops details and timeline progress */}
                  {c.linked_incident_id && (() => {
                    const inc = incidents[c.linked_incident_id];
                    if (!inc) {
                      return (
                        <div className="p-4 bg-stone-100 border border-stone-200 rounded-2xl flex items-center justify-between">
                          <div className="flex items-center gap-2 text-xs text-stone-500">
                            <Clock className="h-4 w-4 animate-spin text-orange-600" />
                            <span>Loading dispatch timeline details...</span>
                          </div>
                        </div>
                      );
                    }

                    // Map status to stepper active index: 1, 2, 3, 4
                    const statusStr = (inc.status || "").toLowerCase();
                    let step = 1;
                    if (statusStr === "investigating" || statusStr === "action_planned") {
                      step = 2;
                    } else if (statusStr === "in_progress" || statusStr === "assigned") {
                      step = 3;
                    } else if (statusStr === "resolved") {
                      step = 4;
                    }

                    const STEPS = [
                      { label: "Detected", desc: "AI triggered" },
                      { label: "Analyzed", desc: "Plan created" },
                      { label: "Dispatched", desc: "Work active" },
                      { label: "Resolved", desc: "Completed" }
                    ];

                    return (
                      <div className="p-5 bg-white border border-orange-200 rounded-2xl space-y-4 shadow-inner">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <ShieldAlert className="h-4.5 w-4.5 text-orange-600 animate-pulse" />
                            <p className="text-xs font-bold text-stone-800 tracking-wide">
                              Escalated to Operations Incident
                            </p>
                          </div>
                          <span className="text-[10px] uppercase px-2 py-0.5 rounded bg-orange-50 text-orange-600 font-mono border border-orange-200">
                            {inc.status.replace(/_/g, " ")}
                          </span>
                        </div>

                        {/* Progress Stepper */}
                        <div className="grid grid-cols-4 gap-2 pt-2 relative">
                          {STEPS.map((s, idx) => {
                            const stepIdx = idx + 1;
                            const isActive = stepIdx <= step;
                            const isCurrent = stepIdx === step;
                            return (
                              <div key={idx} className="flex flex-col items-center text-center space-y-2 relative z-10">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center border text-xs font-semibold font-mono transition-all ${
                                  isCurrent
                                    ? "bg-orange-500 text-stone-800 border-orange-400 shadow-lg shadow-orange-500/30 scale-110"
                                    : isActive
                                      ? "bg-emerald-50 text-emerald-600 border-emerald-200"
                                      : "bg-stone-100 text-stone-400 border-stone-200"
                                }`}>
                                  {isActive && stepIdx < step ? "✓" : stepIdx}
                                </div>
                                <div>
                                  <p className={`text-[10px] font-bold ${isActive ? "text-stone-800" : "text-stone-400"}`}>{s.label}</p>
                                  <p className="text-[8px] text-stone-400 mt-0.5">{s.desc}</p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Resolution Notes */}
                  {c.resolution_notes && (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl space-y-1">
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600" />
                        <p className="text-xs font-semibold text-stone-800">Resolution Summary</p>
                      </div>
                      <p className="text-xs text-stone-500 mt-1 leading-relaxed">
                        {c.resolution_notes}
                      </p>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-stone-400 border-t border-stone-200 pt-3">
                    <p>Complaint ID: {c.id}</p>
                    <p>Filed at: {new Date(c.created_at).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
