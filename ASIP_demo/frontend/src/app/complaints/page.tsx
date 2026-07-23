"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { complaintsApi } from "@/lib/api";
import {
  FileText, CheckCircle2, AlertTriangle, AlertCircle, Play, ArrowRight, ShieldAlert
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
  assigned_manager_id?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

const STATUS_BADGES: Record<string, string> = {
  submitted: "bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/30",
  under_review: "bg-violet-500/20 text-violet-400 ring-1 ring-violet-500/30",
  converted_to_incident: "bg-orange-500/20 text-orange-400 ring-1 ring-orange-500/30",
  assigned: "bg-sky-500/20 text-sky-400 ring-1 ring-sky-500/30",
  resolved: "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30",
  rejected: "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30",
};

export default function AdminComplaintsPage() {
  const { token } = useAuth();
  
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionStatus, setActionStatus] = useState<Record<string, string>>({});

  const fetchAllComplaints = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await complaintsApi.listAll(token);
      setComplaints(res.items || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load complaints.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllComplaints();
  }, [token]);

  const handleConvert = async (complaintId: string, category: string) => {
    if (!token) return;
    setActionStatus((prev) => ({ ...prev, [complaintId]: "converting" }));
    
    // Map categories to backend incident types
    let incidentType = "water_pressure_drop";
    if (category === "electrical" || category === "elevator") {
      incidentType = "power_outage";
    }
    
    try {
      await complaintsApi.convert(token, complaintId, { incident_type: incidentType });
      setActionStatus((prev) => ({ ...prev, [complaintId]: "converted" }));
      fetchAllComplaints();
    } catch (err: any) {
      setActionStatus((prev) => ({ ...prev, [complaintId]: `error: ${err.message}` }));
    }
  };

  const handleReject = async (complaintId: string) => {
    if (!token) return;
    setActionStatus((prev) => ({ ...prev, [complaintId]: "rejecting" }));
    try {
      await complaintsApi.update(token, complaintId, { status: "rejected" });
      setActionStatus((prev) => ({ ...prev, [complaintId]: "rejected" }));
      fetchAllComplaints();
    } catch (err: any) {
      setActionStatus((prev) => ({ ...prev, [complaintId]: `error: ${err.message}` }));
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] p-5 lg:p-7 animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <FileText className="h-6 w-6 text-amber-400" />
          Resident Complaints Management
        </h1>
        <p className="text-xs text-zinc-400 mt-1">Review issues filed by residents, trace AI diagnostics, and trigger incident response workflows.</p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-2 text-xs text-rose-400">
          <AlertCircle className="h-4.5 w-4.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-white/10 border-t-amber-400"></div>
        </div>
      ) : complaints.length === 0 ? (
        <div className="glass-card border-dashed p-12 text-center text-zinc-500">
          <FileText className="mx-auto h-12 w-12 text-zinc-600 mb-3" />
          <p className="text-sm font-medium text-zinc-300">No complaints active in database</p>
          <p className="text-xs text-zinc-500 mt-1">Complaints filed by residents will appear here for manager review.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {complaints.map((c) => (
            <div key={c.id} className="glass-card p-5 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-amber-400 font-mono tracking-wider">
                      Category: {c.category} &bull; {c.priority} Priority
                    </span>
                    <h3 className="text-base font-bold text-white tracking-tight mt-1">{c.title}</h3>
                  </div>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_BADGES[c.status] || "bg-zinc-500/20 text-zinc-400 ring-1 ring-zinc-500/30"}`}>
                    {c.status.replace(/_/g, " ")}
                  </span>
                </div>

                <p className="text-sm text-zinc-200 leading-relaxed bg-white/[0.03] p-3 rounded-xl border border-white/[0.06]">
                  {c.description}
                </p>
                
                <div className="text-[10px] text-zinc-400">
                  <p>Resident ID: {c.resident_id || "Anonymous"}</p>
                  <p className="mt-0.5">Filed at: {new Date(c.created_at).toLocaleString()}</p>
                </div>
              </div>

              <div className="border-t border-white/[0.06] pt-4 mt-2 flex flex-col gap-2">
                {c.status === "submitted" && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleConvert(c.id, c.category)}
                      disabled={actionStatus[c.id] === "converting" || actionStatus[c.id] === "rejecting"}
                      className="flex-1 py-2.5 px-4 rounded-xl bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-orange-500/10 cursor-pointer"
                    >
                      <Play className="h-3.5 w-3.5" />
                      {actionStatus[c.id] === "converting" ? "Converting..." : "Accept & Launch AI"}
                    </button>
                    <button
                      onClick={() => handleReject(c.id)}
                      disabled={actionStatus[c.id] === "converting" || actionStatus[c.id] === "rejecting"}
                      className="py-2.5 px-4 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.06] disabled:opacity-50 text-rose-400 hover:text-rose-300 text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      Reject
                    </button>
                  </div>
                )}

                {c.linked_incident_id && (
                  <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-center justify-between text-xs text-orange-400 font-mono">
                    <div className="flex items-center gap-1.5">
                      <ShieldAlert className="h-4 w-4" />
                      <span>Incident Active</span>
                    </div>
                    <span className="text-[10px] text-zinc-400">ID: {c.linked_incident_id.substring(0, 8)}...</span>
                  </div>
                )}

                {actionStatus[c.id] && actionStatus[c.id].startsWith("error") && (
                  <p className="text-[11px] text-rose-400 font-medium">{actionStatus[c.id]}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
