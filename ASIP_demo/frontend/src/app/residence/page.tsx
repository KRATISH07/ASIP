"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { complaintsApi, incidentsApi } from "@/lib/api";
import {
  FileText, Plus, CheckCircle2, AlertTriangle, AlertCircle, Info, Home, ShieldAlert, Clock, Send
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
  { value: "high", label: "High (Urgent)" },
  { value: "urgent", label: "Urgent (Immediate)" },
];

const MOCK_COMPLAINTS: Complaint[] = [
  {
    id: "CMP-1042", resident_id: "r1", title: "Water leakage from ceiling in bathroom",
    description: "There is consistent water dripping from the bathroom ceiling, especially during evenings. Seems to be from the flat above.",
    category: "plumbing", priority: "high", status: "under_review",
    created_at: new Date(Date.now() - 86400000).toISOString(), updated_at: new Date(Date.now() - 43200000).toISOString(),
  },
  {
    id: "CMP-1038", resident_id: "r1", title: "Elevator #2 makes grinding noise",
    description: "Tower A elevator #2 has been making a grinding/squeaking noise when moving between floors 4-6.",
    category: "lift", priority: "medium", status: "converted_to_incident", linked_incident_id: "inc-mock",
    created_at: new Date(Date.now() - 259200000).toISOString(), updated_at: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: "CMP-1031", resident_id: "r1", title: "Parking spot occupied by unknown vehicle",
    description: "My reserved parking spot B-14 has been occupied by an unregistered white sedan for the past 2 days.",
    category: "parking", priority: "low", status: "resolved", resolution_notes: "Security team identified and contacted the vehicle owner. Vehicle has been moved.",
    created_at: new Date(Date.now() - 604800000).toISOString(), updated_at: new Date(Date.now() - 518400000).toISOString(),
  },
];

const STATUS_STYLES: Record<string, string> = {
  submitted: "bg-violet-500/20 text-violet-400 ring-1 ring-violet-500/30",
  under_review: "bg-sky-500/20 text-sky-400 ring-1 ring-sky-500/30",
  converted_to_incident: "bg-orange-500/20 text-orange-400 ring-1 ring-orange-500/30",
  assigned: "bg-cyan-500/20 text-cyan-400 ring-1 ring-cyan-500/30",
  resolved: "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30",
  rejected: "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30",
};

export default function ResidencePage() {
  const { token, user } = useAuth();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [incidents, setIncidents] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("plumbing");
  const [priority, setPriority] = useState("medium");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  const isSandbox = typeof window !== "undefined" && sessionStorage.getItem("asip_token") === "demo-sandbox-token";

  const fetchComplaints = async () => {
    if (!token) return;
    try {
      setLoading(true);
      if (isSandbox) {
        setComplaints(MOCK_COMPLAINTS);
        setError(null);
        setLoading(false);
        return;
      }
      const res = await complaintsApi.listMine(token);
      const items = res.items || [];
      setComplaints(items);
      setError(null);

      const linkedIds = items.map((c: any) => c.linked_incident_id).filter((id: any) => !!id) as string[];
      if (linkedIds.length > 0) {
        const uniqueIds = Array.from(new Set(linkedIds));
        const fetchedMap: Record<string, any> = {};
        await Promise.all(uniqueIds.map(async (id) => { try { const incident = await incidentsApi.get(token, id); fetchedMap[id] = incident; } catch {} }));
        setIncidents((prev) => ({ ...prev, ...fetchedMap }));
      }
    } catch (err: any) {
      // Fallback to mock data on any fetch error (e.g. no backend running)
      setComplaints(MOCK_COMPLAINTS);
      setError(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
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
      if (isSandbox) {
        // Simulate submission in sandbox mode
        const newComplaint: Complaint = {
          id: `CMP-${Math.floor(1000 + Math.random() * 9000)}`,
          resident_id: "r1", title, description, category, priority,
          status: "submitted",
          created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
        };
        setComplaints(prev => [newComplaint, ...prev]);
        setSuccessMsg("Complaint submitted successfully! Our AI system will triage it shortly.");
        setTitle(""); setDescription("");
      } else {
        await complaintsApi.create(token, { title, description, category, priority });
        setSuccessMsg("Complaint submitted successfully!");
        setTitle(""); setDescription("");
        fetchComplaints();
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit complaint.");
    } finally {
      setFormSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] p-5 lg:p-7 animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-zinc-500 text-xs font-medium mb-1">Resident Portal</p>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Welcome, {user?.full_name || "Resident"} 🏠
          </h1>
          <p className="text-sm text-zinc-500 mt-0.5">Flat 302, Tower A • Greenwood Heights Society</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[11px] font-medium text-emerald-400">
            ● Apartment Active
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">

        {/* Left: Submit Complaint Form */}
        <div className="lg:col-span-2 glass-card p-6 space-y-5 h-fit">
          <div>
            <h2 className="text-base font-semibold text-zinc-200 flex items-center gap-2">
              <Plus className="w-4 h-4 text-violet-400" /> File a Complaint
            </h2>
            <p className="text-[11px] text-zinc-500 mt-0.5">Submit issues to society operators and AI triage system.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[10px] font-medium text-zinc-500 uppercase tracking-wider mb-1.5">Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 focus:outline-none focus:border-violet-500/50 transition">
                {CATEGORIES.map((c) => (<option key={c.value} value={c.value} className="bg-zinc-900 text-zinc-200">{c.label}</option>))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-medium text-zinc-500 uppercase tracking-wider mb-1.5">Priority</label>
              <select value={priority} onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 focus:outline-none focus:border-violet-500/50 transition">
                {PRIORITIES.map((p) => (<option key={p.value} value={p.value} className="bg-zinc-900 text-zinc-200">{p.label}</option>))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-medium text-zinc-500 uppercase tracking-wider mb-1.5">Title</label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Pipe leakage in kitchen"
                className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 transition"
                required />
            </div>

            <div>
              <label className="block text-[10px] font-medium text-zinc-500 uppercase tracking-wider mb-1.5">Description</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3}
                placeholder="Describe the issue in detail..."
                className="w-full px-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 transition resize-none"
                required />
            </div>

            {successMsg && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-2 text-xs text-emerald-400">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" /><span>{successMsg}</span>
              </div>
            )}
            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-start gap-2 text-xs text-rose-400">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" /><span>{error}</span>
              </div>
            )}

            <button type="submit" disabled={formSubmitting}
              className="w-full py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white text-xs font-semibold transition flex items-center justify-center gap-2 cursor-pointer">
              <Send className="w-3.5 h-3.5" />
              {formSubmitting ? "Submitting..." : "Submit Complaint"}
            </button>
          </form>
        </div>

        {/* Right: Complaint History */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-zinc-200">Complaint History</h2>
            <span className="text-[10px] text-zinc-600">{complaints.length} total</span>
          </div>

          {loading ? (
            <div className="flex justify-center py-16">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-700 border-t-violet-500"></div>
            </div>
          ) : complaints.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <FileText className="mx-auto h-10 w-10 text-zinc-700 mb-3" />
              <p className="text-sm font-medium text-zinc-400">No complaints filed yet</p>
              <p className="text-xs text-zinc-600 mt-1">Use the form to submit your first issue.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {complaints.map((c) => (
                <div key={c.id} className="glass-card p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[9px] font-mono font-medium text-zinc-600">{c.id}</span>
                        <span className="text-[9px] font-medium text-zinc-600 bg-white/[0.04] px-1.5 py-0.5 rounded capitalize">{c.category}</span>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded capitalize ${
                          c.priority === "urgent" || c.priority === "high" ? "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30" :
                          c.priority === "medium" ? "bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/30" :
                          "bg-sky-500/20 text-sky-400 ring-1 ring-sky-500/30"
                        }`}>{c.priority}</span>
                      </div>
                      <h3 className="text-[13px] font-semibold text-zinc-200">{c.title}</h3>
                    </div>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md capitalize flex-shrink-0 ${STATUS_STYLES[c.status] || "bg-zinc-500/20 text-zinc-400"}`}>
                      {c.status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <p className="text-[12px] text-zinc-400 leading-relaxed p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    {c.description}
                  </p>

                  {/* Escalation Stepper (if linked to incident) */}
                  {c.linked_incident_id && (
                    <div className="p-4 rounded-lg bg-orange-500/5 border border-orange-500/15 space-y-3">
                      <div className="flex items-center gap-2">
                        <ShieldAlert className="h-3.5 w-3.5 text-orange-400" />
                        <span className="text-[11px] font-semibold text-orange-400">Escalated to Operations Incident</span>
                      </div>
                      <div className="grid grid-cols-4 gap-2">
                        {["Detected", "Analyzed", "Dispatched", "Resolved"].map((step, idx) => (
                          <div key={step} className="flex flex-col items-center text-center gap-1.5">
                            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold ${
                              idx <= 1 ? "bg-orange-500/20 text-orange-400 ring-1 ring-orange-500/30" : "bg-white/[0.04] text-zinc-600 ring-1 ring-white/[0.06]"
                            }`}>{idx <= 1 ? "✓" : idx + 1}</div>
                            <span className={`text-[9px] font-medium ${idx <= 1 ? "text-zinc-300" : "text-zinc-600"}`}>{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resolution Notes */}
                  {c.resolution_notes && (
                    <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/15 space-y-1">
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        <span className="text-[11px] font-semibold text-emerald-400">Resolution</span>
                      </div>
                      <p className="text-[11px] text-zinc-400 leading-relaxed">{c.resolution_notes}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[9px] text-zinc-600 border-t border-white/[0.04] pt-2">
                    <span>Filed: {new Date(c.created_at).toLocaleDateString()}</span>
                    <span>Updated: {new Date(c.updated_at).toLocaleDateString()}</span>
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
