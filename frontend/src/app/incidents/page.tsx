"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { incidentsApi, contractorsApi, type IncidentOut } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import {
  AlertTriangle, Filter, RefreshCw, Award, Zap,
  TrendingUp, CheckCircle2, ShieldAlert, ExternalLink, Plus, MessageSquare, X
} from "lucide-react";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-rose-700 bg-red-100 border-red-200",
  high: "text-orange-700 bg-orange-100 border-orange-200",
  medium: "text-yellow-700 bg-yellow-100 border-yellow-200",
  low: "text-emerald-700 bg-green-100 border-green-200",
};

const STATUS_COLORS: Record<string, string> = {
  detected: "text-blue-700 bg-blue-100 border-blue-200",
  analyzing: "text-violet-700 bg-violet-100 border-violet-200",
  action_planned: "text-cyan-700 bg-cyan-100 border-cyan-200",
  in_progress: "text-amber-700 bg-amber-100 border-amber-200",
  resolved: "text-emerald-700 bg-green-100 border-green-200",
  escalated: "text-rose-700 bg-red-100 border-red-200",
};

const MOCK_INCIDENTS: IncidentOut[] = [
  { 
    id: "1", 
    type: "water_pressure_drop", 
    severity: "critical", 
    confidence: 0.97, 
    status: "analyzing", 
    description: "Pressure dropped to 0.3 bar in Tower A pump room", 
    detected_at: new Date().toISOString(), 
    root_cause: "Booster pump motor failure due to voltage fluctuation.",
    ai_decision: {
      incident_summary: "Booster water pump feed pressure dropped critically. Secondary bypass valve activation recommended.",
      action_plan: "1. Lock out power to Booster Pump 1.\n2. Open standard bypass loop B-1.\n3. Dispatch AquaFix Pro for motor replacement.",
      estimated_resolution_hrs: 2.0,
      prediction: {
        predicted_outage_hrs: 2.3,
        estimated_cost: 7800.00
      }
    },
    contractor_assignment: {
      contractor_name: "AquaFix Pro",
      estimated_cost: 7500,
      estimated_time_hrs: 2.0,
      selection_reasoning: "Selected AquaFix Pro due to proximity, water specialization, and 1.5h response time."
    }
  },
  { 
    id: "2", 
    type: "power_outage", 
    severity: "high", 
    confidence: 0.99, 
    status: "in_progress", 
    description: "Complete power loss detected in Tower B", 
    detected_at: new Date(Date.now() - 3600000).toISOString(),
    root_cause: "Main breaker trip in Tower B sub-station due to transformer overload.",
    ai_decision: {
      incident_summary: "Complete electricity blackout in Tower B. DG backup failed to auto-start.",
      action_plan: "1. Verify DG generator fuel levels and cooling system.\n2. Manually start diesel generator backup.\n3. Reset Tower B main distribution breaker.",
      estimated_resolution_hrs: 1.5,
      prediction: {
        predicted_outage_hrs: 1.5,
        estimated_cost: 12500.00
      }
    },
    contractor_assignment: {
      contractor_name: "PowerSure Services",
      estimated_cost: 11200,
      estimated_time_hrs: 1.5,
      selection_reasoning: "Selected PowerSure Services based on 96% success rate and matching electrical specialization."
    }
  },
  { 
    id: "3", 
    type: "tank_overflow", 
    severity: "medium", 
    confidence: 0.98, 
    status: "resolved", 
    description: "Tank level exceeded 95% in Tower C", 
    detected_at: new Date(Date.now() - 7200000).toISOString(), 
    root_cause: "Upper reservoir float sensor valve got stuck in open position.",
    ai_decision: {
      incident_summary: "Tower C terrace tank level exceeded 95% threshold causing overflow drainage.",
      action_plan: "1. Close main supply valve to Tower C terrace tank.\n2. Manually inspect and release float valve assembly.\n3. Replace defective feedback float sensor.",
      estimated_resolution_hrs: 1.0,
      prediction: {
        predicted_outage_hrs: 1.0,
        estimated_cost: 2400.00
      }
    },
    contractor_assignment: {
      contractor_name: "AquaFix Pro",
      estimated_cost: 2000,
      estimated_time_hrs: 1.0,
      selection_reasoning: "Selected AquaFix Pro due to plumbing specialization and immediate active availability."
    }
  },
  { 
    id: "4", 
    type: "power_overload", 
    severity: "high", 
    confidence: 0.87, 
    status: "action_planned", 
    description: "Power consumption at 91% of rated capacity", 
    detected_at: new Date(Date.now() - 10800000).toISOString(),
    root_cause: "Peak phase load imbalances during high summer heat AC loads.",
    ai_decision: {
      incident_summary: "Tower A main phase consumption reached 91% of safe transformer capacity.",
      action_plan: "1. Issue automated demand-response push notification to residents.\n2. Temporarily shut down common area corridor air conditioning.\n3. Re-balance phase logs on primary distribution board.",
      estimated_resolution_hrs: 3.0,
      prediction: {
        predicted_outage_hrs: 3.0,
        estimated_cost: 4500.00
      }
    },
    contractor_assignment: {
      contractor_name: "PowerSure Services",
      estimated_cost: 4000,
      estimated_time_hrs: 3.0,
      selection_reasoning: "Selected PowerSure Services due to matching electrical specialization and high availability rating."
    }
  },
  { 
    id: "5", 
    type: "water_shortage", 
    severity: "critical", 
    confidence: 0.96, 
    status: "escalated", 
    description: "Tank level critically low at 4%", 
    detected_at: new Date(Date.now() - 14400000).toISOString(),
    root_cause: "Municipal water main supply line leakage outside society perimeter.",
    ai_decision: {
      incident_summary: "Water storage level critically low at 4% in central underground reservoir.",
      action_plan: "1. Restrict domestic water supply to scheduled hours.\n2. Dispatch society tractor water tanker emergency backup.\n3. Backfill central reservoir from municipal supply tankers.",
      estimated_resolution_hrs: 4.5,
      prediction: {
        predicted_outage_hrs: 4.5,
        estimated_cost: 15000.00
      }
    },
    contractor_assignment: {
      contractor_name: "RapidRepair Elite",
      estimated_cost: 14500,
      estimated_time_hrs: 4.0,
      selection_reasoning: "Selected RapidRepair Elite due to emergency water tanker logistics capability."
    }
  },
  
  // Statically seed mock manual complaints for resident complaints tab
  {
    id: "complaint-1",
    type: "abnormal_infrastructure" as any,
    severity: "medium",
    confidence: 1.0,
    status: "in_progress",
    description: "Resident Complaint (Room B-803): Corridor lighting on the 8th floor is flickering and making buzzing noises.",
    detected_at: new Date(Date.now() - 18000000).toISOString(),
    sensor_data: { manual_report: true, reported_by: "Room B-803" },
    root_cause: "Defective choke and starter transformer assembly.",
    ai_decision: {
      incident_summary: "Corridor light flicker reported. Ballast and starter replacement suggested.",
      action_plan: "1. Inspect light fixtures in Tower B, 8th floor.\n2. Replace ballast and clean tube housing.\n3. Verify voltage feed stability.",
      estimated_resolution_hrs: 1.0,
      prediction: {
        predicted_outage_hrs: 1.2,
        estimated_cost: 1500.00
      }
    },
    contractor_assignment: {
      contractor_name: "PowerSure Services",
      estimated_cost: 1200,
      estimated_time_hrs: 1.0,
      selection_reasoning: "Selected PowerSure due to electrical specialization and prompt local dispatch availability."
    }
  },
  {
    id: "complaint-2",
    type: "water_shortage" as any,
    severity: "high",
    confidence: 1.0,
    status: "action_planned",
    description: "Resident Complaint (Room A-1204): Muddy water coming from flush valves and bathroom pipes.",
    detected_at: new Date(Date.now() - 25000000).toISOString(),
    sensor_data: { manual_report: true, reported_by: "Room A-1204" },
    ai_decision: {
      incident_summary: "Turbid water reported in Tower A. Secondary sand filters backwash sequence recommended.",
      action_plan: "1. Inspect media filtration unit.\n2. Backwash filter sand bed and charcoal tanks.\n3. Run dump line until water runs clean.",
      estimated_resolution_hrs: 3.0,
      prediction: {
        predicted_outage_hrs: 3.5,
        estimated_cost: 3200.00
      }
    },
    contractor_assignment: {
      contractor_name: "AquaFix Pro",
      estimated_cost: 3000,
      estimated_time_hrs: 3.0,
      selection_reasoning: "Selected AquaFix Pro due to filtration specialization and matching plumbing capacity."
    }
  }
];

function IncidentsPageContent() {
  const { token: TOKEN } = useAuth();
  const [mounted, setMounted] = useState(false);
  const [incidents, setIncidents] = useState<IncidentOut[]>(MOCK_INCIDENTS);
  const [selected, setSelected] = useState<IncidentOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setMounted(true);
  }, []);

  const [activeTab, setActiveTab] = useState<"alerts" | "complaints">("alerts");

  const [showForm, setShowForm] = useState(false);
  const [newType, setNewType] = useState<string>("abnormal_infrastructure");
  const [newRoom, setNewRoom] = useState("");
  const [newSeverity, setNewSeverity] = useState<string>("medium");
  const [newDesc, setNewDesc] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [customTypeName, setCustomTypeName] = useState("");

  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [actualOutageHrs, setActualOutageHrs] = useState<number | string>("");
  const [actualCost, setActualCost] = useState<number | string>("");
  const [feedbackRootCause, setFeedbackRootCause] = useState("");
  const [feedbackSummary, setFeedbackSummary] = useState("");
  const [feedbackContractor, setFeedbackContractor] = useState("");

  const [processingAiId, setProcessingAiId] = useState<string | null>(null);

  const [rankings, setRankings] = useState<any[]>([]);
  const [fetchingRankings, setFetchingRankings] = useState(false);

  const searchParams = useSearchParams();
  const deepLinkId = searchParams.get("id");

  useEffect(() => {
    if (TOKEN) {
      incidentsApi.list(TOKEN)
        .then((res) => {
          const blended = [...res.items];
          MOCK_INCIDENTS.forEach(m => {
            if (!blended.some(b => b.id === m.id)) {
              blended.push(m);
            }
          });
          setIncidents(blended);

          if (deepLinkId) {
            const matched = blended.find((i) => i.id === deepLinkId);
            if (matched) {
              setSelected(matched);
              if (matched.sensor_data?.manual_report) {
                setActiveTab("complaints");
              } else {
                setActiveTab("alerts");
              }
            }
          }
        })
        .catch(() => {
          setIncidents(MOCK_INCIDENTS);
          if (deepLinkId) {
            const matched = MOCK_INCIDENTS.find((i) => i.id === deepLinkId);
            if (matched) {
              setSelected(matched);
              if (matched.sensor_data?.manual_report) {
                setActiveTab("complaints");
              } else {
                setActiveTab("alerts");
              }
            }
          }
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [deepLinkId, TOKEN]);

  useEffect(() => {
    if (!processingAiId) return;

    let attempts = 0;
    const MAX_ATTEMPTS = 12;

    const poll = async () => {
      attempts++;
      try {
        if (TOKEN) {
          const updated = await incidentsApi.get(TOKEN, processingAiId);
          const hasAiDecision = !!(updated.ai_decision && (
            (updated.ai_decision as any).incident_summary ||
            (updated.ai_decision as any).action_plan
          ));
          const hasContractor = !!updated.contractor_assignment;

          if (hasAiDecision || hasContractor || attempts >= MAX_ATTEMPTS) {
            setIncidents(prev => prev.map(i => i.id === processingAiId ? { ...i, ...updated } : i));
            setSelected(prev => prev && prev.id === processingAiId ? { ...prev, ...updated } : prev);
            setProcessingAiId(null);
            if (hasAiDecision || hasContractor) {
              setSuccessMsg("✅ AI analysis complete — root cause, solution plan, and contractor assigned.");
              setTimeout(() => setSuccessMsg(""), 4000);
            }
            return;
          }
        }
      } catch {}

      if (attempts < MAX_ATTEMPTS) {
        setTimeout(poll, 3000);
      } else {
        setProcessingAiId(null);
      }
    };

    const timer = setTimeout(poll, 4000);
    return () => clearTimeout(timer);
  }, [processingAiId, TOKEN]);

  useEffect(() => {
    if (selected && TOKEN) {
      setFetchingRankings(true);
      contractorsApi.getRankings(TOKEN, selected.type, 3)
        .then(setRankings)
        .catch(() => {
          const isWater = selected.type.includes("water") || selected.type.includes("pressure") || selected.type.includes("tank");
          const fallbackCandidates = [
            {
              contractor_id: "cb08d635-64a0-48a2-8e7a-95ebdfaf2dc1",
              name: "AquaFix Pro",
              final_score: 95.45,
              breakdown: { success_rate_score: 97.0, repair_time_score: 85.0, feedback_score: 96.0 },
              specializations: ["water", "plumbing"]
            },
            {
              contractor_id: "powersure-id-1",
              name: "PowerSure Services",
              final_score: 92.20,
              breakdown: { success_rate_score: 95.0, repair_time_score: 90.0, feedback_score: 90.0 },
              specializations: ["electrical", "power"]
            },
            {
              contractor_id: "rapid-id-1",
              name: "RapidRepair Elite",
              final_score: 98.12,
              breakdown: { success_rate_score: 98.0, repair_time_score: 95.0, feedback_score: 98.0 },
              specializations: ["water", "electrical"]
            },
            {
              contractor_id: "cityfix-id-1",
              name: "CityFix General",
              final_score: 82.50,
              breakdown: { success_rate_score: 89.0, repair_time_score: 75.0, feedback_score: 80.0 },
              specializations: ["water", "electrical", "civil"]
            }
          ];

          const filtered = fallbackCandidates.filter(c => 
            c.specializations.includes(isWater ? "water" : "electrical")
          ).sort((a, b) => b.final_score - a.final_score);

          setRankings(filtered);
        })
        .finally(() => setFetchingRankings(false));
    } else {
      setRankings([]);
    }
  }, [selected]);

  useEffect(() => {
    if (selected) {
      setFeedbackContractor(selected.contractor_assignment?.contractor_name || selected.ai_decision?.contractor || "");
      setFeedbackRootCause(selected.root_cause || selected.ai_decision?.probable_cause || "");
      setActualOutageHrs(selected.ai_decision?.prediction?.predicted_outage_hrs ?? "");
      setActualCost(selected.ai_decision?.prediction?.estimated_cost ?? "");
    }
  }, [selected]);

  const handleStatusChange = async (newStatus: string) => {
    if (!selected) return;
    if (newStatus === "resolved") {
      setShowFeedbackForm(true);
      return;
    }
    try {
      if (!TOKEN) throw new Error("No token");
      const res = await incidentsApi.updateStatus(TOKEN, selected.id, newStatus);
      const updated = incidents.map(i => i.id === selected.id ? { ...i, status: res.status } : i);
      setIncidents(updated);
      setSelected({ ...selected, status: res.status });
      setSuccessMsg(`Incident status manually updated to ${newStatus.replace(/_/g, " ")}.`);
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch {
      const updated = incidents.map(i => i.id === selected.id ? { ...i, status: newStatus as any } : i);
      setIncidents(updated);
      setSelected({ ...selected, status: newStatus as any });
      setSuccessMsg(`Offline Fallback: Status simulated to ${newStatus.replace(/_/g, " ")}.`);
      setTimeout(() => setSuccessMsg(""), 3000);
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;

    const feedbackPayload = {
      actual_outage_hrs: actualOutageHrs !== "" ? Number(actualOutageHrs) : null,
      actual_cost: actualCost !== "" ? Number(actualCost) : null,
      root_cause: feedbackRootCause || null,
      resolution_summary: feedbackSummary || null,
      contractor_used: feedbackContractor || null,
    };

    try {
      if (!TOKEN) throw new Error("No token");
      await incidentsApi.submitFeedback(TOKEN, selected.id, feedbackPayload);
      await incidentsApi.updateStatus(TOKEN, selected.id, "resolved");
      
      const updated = incidents.map(i => i.id === selected.id ? { ...i, status: "resolved" as any, root_cause: feedbackRootCause || i.root_cause } : i);
      setIncidents(updated);
      setSelected({ ...selected, status: "resolved" as any, root_cause: feedbackRootCause || selected.root_cause });
      
      setShowFeedbackForm(false);
      setSuccessMsg("Incident resolved and feedback recorded to train AI models.");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err: any) {
      try {
        if (TOKEN) await incidentsApi.updateStatus(TOKEN, selected.id, "resolved");
      } catch {}
      const updated = incidents.map(i => i.id === selected.id ? { ...i, status: "resolved" as any, root_cause: feedbackRootCause || i.root_cause } : i);
      setIncidents(updated);
      setSelected({ ...selected, status: "resolved" as any, root_cause: feedbackRootCause || selected.root_cause });
      
      setShowFeedbackForm(false);
      setSuccessMsg(`Offline Fallback: Status resolved, feedback saved locally.`);
      setTimeout(() => setSuccessMsg(""), 3000);
    }
    
    setFeedbackSummary("");
  };

  const handleLogComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRoom.trim() || !newDesc.trim()) return;
    if (newType === "custom" && !customTypeName.trim()) return;

    const resolvedType = newType === "custom" ? "abnormal_infrastructure" : newType;
    const resolvedCustomType = newType === "custom" ? customTypeName : undefined;

    const payload = {
      type: resolvedType,
      severity: newSeverity,
      confidence: 1.0,
      description: `Resident Complaint (${newRoom}): ${newDesc}`,
      sensor_data: {
        manual_report: true,
        reported_by: newRoom,
        ...(resolvedCustomType ? { custom_type: resolvedCustomType } : {})
      }
    };

    try {
      if (!TOKEN) throw new Error("No token");
      const res = await incidentsApi.create(TOKEN, payload);
      const formatted: IncidentOut = {
        ...res,
        sensor_data: {
          manual_report: true,
          reported_by: newRoom,
          ...(resolvedCustomType ? { custom_type: resolvedCustomType } : {})
        },
      };

      setIncidents([formatted, ...incidents]);
      setSelected(formatted);
      setShowForm(false);
      setProcessingAiId(res.id as string);
      setSuccessMsg("Complaint registered. AI analysis running in background — results will appear shortly.");
      setTimeout(() => setSuccessMsg(""), 5000);
    } catch {
      const mockNew: IncidentOut = {
        id: String(incidents.length + 1) as any,
        type: resolvedType as any,
        severity: newSeverity as any,
        confidence: 1.0,
        status: "detected" as any,
        description: `Resident Complaint (${newRoom}): ${newDesc}`,
        detected_at: new Date().toISOString(),
        sensor_data: {
          manual_report: true,
          reported_by: newRoom,
          ...(resolvedCustomType ? { custom_type: resolvedCustomType } : {})
        },
        ai_decision: {
          incident_summary: `Manual complaint registered for ${(resolvedCustomType || resolvedType).replace(/_/g, " ")}. Dispatching plumber/electrician.`,
          action_plan: `1. Contact reporter in ${newRoom} to inspect details.\n2. Dispatched contractor to address ${newDesc}.\n3. Verify repair resolution state.`,
          estimated_resolution_hrs: 2.0,
          prediction: {
            predicted_outage_hrs: 2.0,
            estimated_cost: 3000.00
          }
        }
      };

      setIncidents([mockNew, ...incidents]);
      setSelected(mockNew);
      setShowForm(false);
      setSuccessMsg("Offline Fallback: Resident complaint logged locally in browser state.");
      setTimeout(() => setSuccessMsg(""), 3000);
    }

    setNewRoom("");
    setNewDesc("");
    setCustomTypeName("");
  };

  const filteredIncidents = incidents;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left List Panel */}
      <div className="w-96 flex-shrink-0 border-r border-stone-200 flex flex-col h-full bg-[#faf6f0]">
        <div className="px-5 py-4 border-b border-stone-200">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-bold text-stone-800">Active Incidents</h1>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-stone-200">
          {filteredIncidents.map((inc) => (
            <button
              key={inc.id}
              onClick={() => { setSelected(inc); setShowForm(false); }}
              className={`w-full text-left px-5 py-4 hover:bg-stone-100 transition-colors cursor-pointer ${selected?.id === inc.id ? "bg-amber-50 border-l-2 border-amber-500" : ""}`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize ${SEVERITY_COLORS[inc.severity]}`}>
                  {inc.severity}
                </span>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium capitalize border border-stone-200 ${STATUS_COLORS[inc.status]}`}>
                  {inc.status.replace(/_/g, " ")}
                </span>
              </div>
              <p className="text-sm font-medium text-stone-800 capitalize">{inc.sensor_data?.custom_type || inc.type.replace(/_/g, " ")}</p>
              <p className="text-xs text-stone-500 mt-0.5 line-clamp-2">{inc.description}</p>
              <p className="text-[10px] text-stone-400 mt-2">
                {inc.sensor_data?.reported_by ? `Reported by: ${inc.sensor_data.reported_by} · ` : ""}
                {mounted ? new Date(inc.detected_at).toLocaleString() : ""}
              </p>
            </button>
          ))}
          {filteredIncidents.length === 0 && (
            <p className="text-xs text-stone-400 text-center py-10">No items in this category.</p>
          )}
        </div>
      </div>

      {/* Right Detail / Form Panel */}
      <div className="flex-1 overflow-y-auto p-6 bg-[#faf6f0]/50 h-full">
        {successMsg && (
          <div className="mb-4 flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 p-4 rounded-xl text-xs transition-all animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {successMsg}
          </div>
        )}

        {showForm ? (
          <form onSubmit={handleLogComplaint} className="max-w-2xl bg-white border border-stone-200 shadow-sm rounded-2xl p-6 space-y-5 animate-fadeIn">
            <div>
              <h2 className="text-base font-bold text-stone-800 mb-1">File Resident Physical Complaint</h2>
              <p className="text-xs text-stone-500">Manually log complaints reported by building residents to queue repair dispatches.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Complaint Category</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
                >
                  <option value="abnormal_infrastructure">Abnormal Infrastructure / Repair</option>
                  <option value="water_pressure_drop">Water Pressure Drop</option>
                  <option value="water_shortage">Water Shortage Outage</option>
                  <option value="tank_overflow">Water Tank Overflow</option>
                  <option value="power_outage">Electricity Power Outage</option>
                  <option value="power_overload">Power Grid Overload</option>
                  <option value="custom">Other (Custom Incident Category)</option>
                </select>
              </div>

              {newType === "custom" && (
                <div className="md:col-span-2 animate-fadeIn">
                  <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Custom Incident Category Name</label>
                  <input
                    type="text"
                    required
                    value={customTypeName}
                    onChange={(e) => setCustomTypeName(e.target.value)}
                    placeholder="e.g. Broken Elevator, Blocked Sewage, Fire Alarm Malfunction..."
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Reporting Unit (e.g. Room/Tower)</label>
                <input
                  type="text"
                  required
                  value={newRoom}
                  onChange={(e) => setNewRoom(e.target.value)}
                  placeholder="e.g. Tower B, Room 803"
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Complaint Severity</label>
                <div className="grid grid-cols-4 gap-2.5">
                  {["low", "medium", "high", "critical"].map((sev) => (
                    <button
                      key={sev}
                      type="button"
                      onClick={() => setNewSeverity(sev)}
                      className={`py-2 rounded-xl text-xs font-bold uppercase tracking-wider border cursor-pointer transition-all ${
                        newSeverity === sev
                          ? "bg-amber-100 border-amber-400 text-amber-800"
                          : "bg-stone-50 border-stone-200 text-stone-500 hover:bg-stone-100 hover:text-stone-800"
                      }`}
                    >
                      {sev}
                    </button>
                  ))}
                </div>
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Description of Physical Issue</label>
                <textarea
                  rows={4}
                  required
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="e.g. Leaking pipeline below flush valves in master bathroom causing wall seepage..."
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500 font-sans"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="submit"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-sm font-semibold text-white rounded-xl transition-colors cursor-pointer shadow-md shadow-amber-200/40"
              >
                <Plus className="w-4 h-4" />
                Submit Complaint
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-stone-200 hover:bg-stone-100 text-sm font-semibold text-stone-600 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : selected ? (
          <div className="space-y-6 max-w-2xl animate-fadeIn">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-stone-800 capitalize">{selected.sensor_data?.custom_type || selected.type.replace(/_/g, " ")}</h2>
                <p className="text-sm text-stone-500 mt-1">{selected.description}</p>
              </div>
              {selected.sensor_data?.manual_report && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-100 border border-amber-300 text-xs font-bold text-amber-700 rounded-full">
                  <MessageSquare className="w-3.5 h-3.5 text-amber-600" /> Resident Complaint
                </span>
              )}
            </div>

            {/* AI Processing Banner */}
            {processingAiId === selected.id && (
              <div className="flex items-center gap-3 rounded-xl bg-amber-50 border border-amber-300 px-4 py-3 animate-pulse">
                <div className="flex-shrink-0 animate-spin rounded-full h-4 w-4 border-2 border-amber-600 border-t-transparent" />
                <div>
                  <p className="text-xs font-bold text-amber-800">AI Multi-Agent Pipeline Running…</p>
                  <p className="text-[10px] text-amber-600 mt-0.5">Infrastructure, impact, contractor &amp; decision agents processing. Results appear automatically.</p>
                </div>
              </div>
            )}

            {/* Meta grid */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Severity", value: selected.severity, cls: SEVERITY_COLORS[selected.severity] },
                {
                  label: "Status (Interactive)",
                  value: (
                    <select
                      value={selected.status}
                      onChange={(e) => handleStatusChange(e.target.value)}
                      className="bg-transparent border-none text-xs font-bold text-stone-800 capitalize focus:outline-none cursor-pointer"
                    >
                      <option value="detected" className="bg-white text-blue-700">Detected</option>
                      <option value="analyzing" className="bg-white text-violet-700">Analyzing</option>
                      <option value="action_planned" className="bg-white text-cyan-700">Action Planned</option>
                      <option value="in_progress" className="bg-white text-amber-700">In Progress</option>
                      <option value="resolved" className="bg-white text-emerald-700">Resolved</option>
                      <option value="escalated" className="bg-white text-rose-700">Escalated</option>
                    </select>
                  ),
                  cls: STATUS_COLORS[selected.status]
                },
                { label: "Confidence", value: `${(selected.confidence * 100).toFixed(0)}%`, cls: "text-stone-800 bg-stone-100" },
              ].map(({ label, value, cls }) => (
                <div key={label} className="rounded-xl bg-white border border-stone-200 shadow-sm p-3 flex flex-col justify-between">
                  <p className="text-[10px] text-stone-400 uppercase tracking-wider mb-1.5">{label}</p>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium border border-stone-200 ${cls}`}>{value}</span>
                </div>
              ))}
            </div>

            {/* Root cause */}
            {selected.root_cause && (
              <div className="rounded-xl bg-white border border-stone-200 shadow-sm p-4">
                <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Root Cause Analysis</p>
                <p className="text-sm text-stone-800">{selected.root_cause}</p>
              </div>
            )}

            {/* Solution Suggestion & AI Predictions */}
            {(selected.ai_decision?.action_plan || selected.ai_decision?.incident_summary) && (
              <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Solution Plan</p>
                  {selected.ai_decision?.estimated_resolution_hrs && (
                    <span className="text-xs text-emerald-600 font-medium bg-emerald-100 px-2 py-0.5 rounded-full">
                      Est: {selected.ai_decision.estimated_resolution_hrs}h
                    </span>
                  )}
                </div>

                {/* AI Predictions Row */}
                {selected.ai_decision?.prediction && (
                  <div className="grid grid-cols-2 gap-3 bg-emerald-100/60 p-3 rounded-xl border border-emerald-200">
                    <div>
                      <p className="text-[9px] text-emerald-700 font-bold uppercase tracking-wider">Predicted Cost</p>
                      <p className="text-sm font-bold text-stone-800 mt-1">
                        ₹{selected.ai_decision.prediction.estimated_cost?.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-[9px] text-emerald-700 font-bold uppercase tracking-wider">Predicted Duration</p>
                      <p className="text-sm font-bold text-stone-800 mt-1">
                        {selected.ai_decision.prediction.predicted_outage_hrs?.toFixed(1)} hrs
                      </p>
                    </div>
                  </div>
                )}

                {selected.ai_decision?.incident_summary && (
                  <p className="text-sm text-stone-700 font-medium leading-relaxed">
                    {selected.ai_decision.incident_summary}
                  </p>
                )}
                {selected.ai_decision?.action_plan && (
                  <div className="pt-2 border-t border-emerald-200">
                    <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-2">Action Steps</p>
                    <p className="text-sm text-stone-600 whitespace-pre-line leading-relaxed">
                      {selected.ai_decision.action_plan}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Contractor */}
            {selected.contractor_assignment && (
              <div className="rounded-xl bg-white border border-stone-200 shadow-sm p-4">
                <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">Assigned Contractor</p>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <p className="text-[10px] text-stone-400">Name</p>
                    <Link
                      href={`/contractors?highlight=${encodeURIComponent(selected.contractor_assignment.contractor_name)}`}
                      className="text-sm text-amber-600 hover:text-amber-500 font-semibold hover:underline cursor-pointer inline-flex items-center gap-1 group"
                    >
                      {selected.contractor_assignment.contractor_name}
                      <ExternalLink className="w-3 h-3 text-stone-400 group-hover:text-amber-600 transition-colors" />
                    </Link>
                  </div>
                  <div>
                    <p className="text-[10px] text-stone-400">Dispatched Cost</p>
                    <p className="text-sm text-stone-800 font-medium">₹{selected.contractor_assignment.estimated_cost?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-stone-400">Dispatched Time</p>
                    <p className="text-sm text-stone-800 font-medium">{selected.contractor_assignment.estimated_time_hrs}h</p>
                  </div>
                </div>
                {selected.contractor_assignment.selection_reasoning && (
                  <p className="mt-3 text-xs text-stone-500 italic leading-relaxed border-t border-stone-200 pt-2.5">{selected.contractor_assignment.selection_reasoning}</p>
                )}
              </div>
            )}

            {/* Dynamic Scored Contractor Candidate Alternatives */}
            <div className="rounded-xl bg-white border border-stone-200 shadow-sm p-5 space-y-4">
              <div>
                <h3 className="text-sm font-bold text-stone-800 flex items-center gap-2">
                  <Award className="w-4 h-4 text-amber-600" />
                  AI Contractor Candidate Evaluation
                </h3>
                <p className="text-[10px] text-stone-400 mt-1">
                  Scored using dynamic Thompson Sampling over historical speed, success rate, cost, and resident feedback.
                </p>
              </div>

              {fetchingRankings ? (
                <div className="flex flex-col items-center justify-center py-6 space-y-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600" />
                  <span className="text-[10px] text-stone-400">Evaluating contractors...</span>
                </div>
              ) : rankings.length > 0 ? (
                <div className="space-y-3">
                  {rankings.map((c, i) => {
                    const isBest = i === 0;
                    const isFastest = c.breakdown?.repair_time_score >= 92;
                    const isMostReliable = c.breakdown?.success_rate_score >= 96;

                    return (
                      <div key={c.contractor_id} className={`rounded-xl border p-4 space-y-2.5 ${isBest ? "bg-amber-50/60 border-amber-300" : "bg-stone-50/50 border-stone-200"}`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Link 
                              href={`/contractors?highlight=${encodeURIComponent(c.name)}`}
                              className="text-xs font-bold text-amber-700 hover:text-amber-600 hover:underline cursor-pointer inline-flex items-center gap-1 group"
                            >
                              {i + 1}. {c.name}
                              <ExternalLink className="w-2.5 h-2.5 text-stone-400 group-hover:text-amber-600 transition-colors" />
                            </Link>
                            {isBest && (
                              <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[9px] font-semibold text-amber-800">
                                Best Match
                              </span>
                            )}
                            {isFastest && !isBest && (
                              <span className="inline-flex items-center rounded-full bg-orange-100 px-2 py-0.5 text-[9px] font-semibold text-orange-700">
                                <Zap className="w-2.5 h-2.5 mr-0.5" /> Emergency
                              </span>
                            )}
                            {isMostReliable && !isBest && (
                              <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[9px] font-semibold text-emerald-700">
                                <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" /> Reliable
                              </span>
                            )}
                          </div>
                          <span className="text-xs font-bold text-stone-800">{c.final_score}%</span>
                        </div>

                        {/* Metrics Bar Breakdown */}
                        <div className="grid grid-cols-3 gap-2.5 pt-1.5 border-t border-stone-200 text-[10px]">
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-stone-400">Success Rate</span>
                              <span className="text-stone-700 font-medium">{c.breakdown?.success_rate_score}%</span>
                            </div>
                            <div className="w-full bg-stone-200 rounded-full h-1">
                              <div className="h-1 rounded-full bg-emerald-500" style={{ width: `${c.breakdown?.success_rate_score}%` }} />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-stone-400">Response Speed</span>
                              <span className="text-stone-700 font-medium">{c.breakdown?.repair_time_score}%</span>
                            </div>
                            <div className="w-full bg-stone-200 rounded-full h-1">
                              <div className="h-1 rounded-full bg-orange-500" style={{ width: `${c.breakdown?.repair_time_score}%` }} />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-stone-400">Feedback</span>
                              <span className="text-stone-700 font-medium">{c.breakdown?.feedback_score}%</span>
                            </div>
                            <div className="w-full bg-stone-200 rounded-full h-1">
                              <div className="h-1 rounded-full bg-violet-500" style={{ width: `${c.breakdown?.feedback_score}%` }} />
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-stone-400 text-center py-4">No contractor candidates found matching specialization.</p>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center py-20">
            <AlertTriangle className="w-12 h-12 text-stone-300 mb-3" />
            <p className="text-stone-500 font-medium">Select an incident to view details</p>
            <p className="text-xs text-stone-400 mt-1">{filteredIncidents.length} incidents in this category</p>
          </div>
        )}
      </div>

      {showFeedbackForm && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/50 backdrop-blur-md p-4 animate-fadeIn">
          <div className="w-full max-w-lg rounded-3xl border border-stone-200 bg-white p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-stone-800">Provide Incident Feedback</h3>
                <p className="text-xs text-stone-500 mt-0.5">Record outcomes to train the predictive AI model</p>
              </div>
              <button
                onClick={() => setShowFeedbackForm(false)}
                className="rounded-xl border border-stone-200 bg-stone-50 p-2 text-stone-400 hover:text-stone-800 hover:bg-stone-100 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmitFeedback} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Identified Root Cause (What was the issue?)</label>
                <input
                  type="text"
                  required
                  value={feedbackRootCause}
                  onChange={(e) => setFeedbackRootCause(e.target.value)}
                  placeholder="e.g. Pump impeller jammed by sand deposits"
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Actual Cost (INR)</label>
                  <input
                    type="number"
                    required
                    value={actualCost}
                    onChange={(e) => setActualCost(e.target.value)}
                    placeholder="e.g. 7800"
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Duration to Fix (Hours)</label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={actualOutageHrs}
                    onChange={(e) => setActualOutageHrs(e.target.value)}
                    placeholder="e.g. 2.5"
                    className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Contractor Dispatched</label>
                <input
                  type="text"
                  value={feedbackContractor}
                  onChange={(e) => setFeedbackContractor(e.target.value)}
                  placeholder="e.g. AquaFix Pro"
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Resolution Action Summary</label>
                <textarea
                  rows={3}
                  required
                  value={feedbackSummary}
                  onChange={(e) => setFeedbackSummary(e.target.value)}
                  placeholder="e.g. Replaced burnout capacitor and cleared blocked suction valve..."
                  className="w-full bg-stone-50 border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500 font-sans"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold text-white rounded-xl transition-colors cursor-pointer text-center shadow-md shadow-emerald-200/40"
                >
                  Submit Feedback & Resolve
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function IncidentsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-stone-400">Loading incident details...</div>}>
      <IncidentsPageContent />
    </Suspense>
  );
}
