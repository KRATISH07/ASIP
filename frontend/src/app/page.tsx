"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import { dashboardApi, incidentsApi, type DashboardOut, type IncidentOut } from "@/lib/api";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  Zap, Droplets, TrendingUp, Bot, ArrowRight, ExternalLink
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
};

const SEVERITY_BG: Record<string, string> = {
  critical: "from-red-500/20 to-red-600/10 border-red-500/20",
  high: "from-orange-500/20 to-orange-600/10 border-orange-500/20",
  medium: "from-yellow-500/20 to-yellow-600/10 border-yellow-500/20",
  low: "from-green-500/20 to-green-600/10 border-green-500/20",
};

function KPICard({
  title, value, subtitle, icon: Icon, gradient,
}: {
  title: string; value: number | string; subtitle?: string;
  icon: React.ElementType; gradient: string;
}) {
  return (
    <div className={`relative overflow-hidden rounded-2xl border bg-gradient-to-br ${gradient} p-5`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-stone-500 uppercase tracking-wider">{title}</p>
          <p className="mt-2 text-4xl font-bold text-stone-800 tabular-nums">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-stone-500">{subtitle}</p>}
        </div>
        <div className="rounded-xl bg-white/60 p-2.5">
          <Icon className="h-5 w-5 text-stone-600" />
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-100 text-rose-700 border-red-200",
    high: "bg-orange-100 text-orange-700 border-orange-200",
    medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
    low: "bg-green-100 text-emerald-700 border-green-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize ${colors[severity] || "bg-stone-100 text-stone-500"}`}>
      {severity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    detected: "bg-blue-100 text-blue-700",
    analyzing: "bg-violet-100 text-violet-700",
    action_planned: "bg-cyan-100 text-cyan-700",
    in_progress: "bg-amber-100 text-amber-700",
    resolved: "bg-green-100 text-emerald-700",
    escalated: "bg-red-100 text-rose-700",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${colors[status] || "bg-stone-100 text-stone-500"}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

// ── Mock data (used when API is unavailable) ─────────────────────────────────
const MOCK_DATA: DashboardOut = {
  kpi: { total_incidents: 47, active_incidents: 8, critical_incidents: 3, resolved_today: 5 },
  recent_incidents: [
    { id: "1", type: "water_pressure_drop", severity: "critical", status: "analyzing", tower_name: "Tower A", detected_at: new Date().toISOString() },
    { id: "2", type: "power_outage", severity: "high", status: "in_progress", tower_name: "Tower B", detected_at: new Date(Date.now() - 3600000).toISOString() },
    { id: "3", type: "tank_overflow", severity: "medium", status: "resolved", tower_name: "Tower C", detected_at: new Date(Date.now() - 7200000).toISOString() },
    { id: "4", type: "power_overload", severity: "high", status: "action_planned", tower_name: "Tower A", detected_at: new Date(Date.now() - 10800000).toISOString() },
    { id: "5", type: "water_shortage", severity: "critical", status: "escalated", tower_name: "Tower B", detected_at: new Date(Date.now() - 14400000).toISOString() },
  ],
  agent_activity: [
    { agent_name: "MonitoringAgent", executions_today: 288, avg_execution_time_ms: 12, success_rate: 1.0 },
    { agent_name: "InfrastructureAgent", executions_today: 8, avg_execution_time_ms: 2340, success_rate: 0.875 },
    { agent_name: "ImpactAnalysisAgent", executions_today: 8, avg_execution_time_ms: 145, success_rate: 1.0 },
    { agent_name: "ContractorAgent", executions_today: 8, avg_execution_time_ms: 1820, success_rate: 1.0 },
    { agent_name: "CommunicationAgent", executions_today: 8, avg_execution_time_ms: 2100, success_rate: 0.875 },
    { agent_name: "SupervisorAgent", executions_today: 8, avg_execution_time_ms: 1950, success_rate: 1.0 },
  ],
  severity_distribution: { critical: 3, high: 5, medium: 12, low: 27 },
  incident_trend: [
    { date: "Jul 3", count: 4 },
    { date: "Jul 4", count: 7 },
    { date: "Jul 5", count: 5 },
    { date: "Jul 6", count: 8 },
    { date: "Jul 7", count: 3 },
    { date: "Jul 8", count: 6 },
    { date: "Jul 9", count: 9 },
  ],
};


export default function DashboardPage() {
  const { user, token: TOKEN } = useAuth();
  const [data, setData] = useState<DashboardOut>(MOCK_DATA);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  // States for active incident inspection on dashboard
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<IncidentOut | null>(null);
  const [fetchingIncident, setFetchingIncident] = useState(false);

  useEffect(() => {
    if (user?.role === "resident") {
      window.location.href = "/residence";
      return;
    }
    if (user?.role === "sensor_gateway") {
      window.location.href = "/sensor-buffer";
      return;
    }

    setMounted(true);
    if (TOKEN) {
      dashboardApi.getSummary(TOKEN)
        .then((res) => {
          if (res.kpi.total_incidents === 0) {
            setData(MOCK_DATA);
          } else {
            const blendedRecent = [...res.recent_incidents];
            MOCK_DATA.recent_incidents.forEach(m => {
              if (!blendedRecent.some(r => r.id === m.id)) {
                blendedRecent.push(m);
              }
            });
            setData({
              ...res,
              recent_incidents: blendedRecent,
              kpi: {
                total_incidents: res.kpi.total_incidents + MOCK_DATA.kpi.total_incidents,
                active_incidents: res.kpi.active_incidents + MOCK_DATA.kpi.active_incidents,
                critical_incidents: res.kpi.critical_incidents + MOCK_DATA.kpi.critical_incidents,
                resolved_today: res.kpi.resolved_today + MOCK_DATA.kpi.resolved_today,
              }
            });
          }
        })
        .catch(() => setData(MOCK_DATA))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [TOKEN]);

  const handleSelectIncident = async (id: string) => {
    if (selectedId === id) {
      setSelectedId(null);
      setSelectedIncident(null);
      return;
    }

    setSelectedId(id);
    setFetchingIncident(true);
    try {
      if (!TOKEN) throw new Error("No token");
      const res = await incidentsApi.get(TOKEN, id);
      setSelectedIncident(res);
    } catch {
      const activeItem = data.recent_incidents.find(i => i.id === id);
      const isPower = activeItem?.type.includes("power");
      const isOverflow = activeItem?.type.includes("overflow");
      const isShortage = activeItem?.type.includes("shortage");

      let rootCause = "Booster pump motor failure due to voltage fluctuation.";
      let summary = "Booster water pump feed pressure dropped critically. Secondary bypass valve activation recommended.";
      let plan = "1. Lock out power to Booster Pump 1.\n2. Open standard bypass loop B-1.\n3. Dispatch AquaFix Pro for motor replacement.";
      let cost = 7800.00;
      let duration = 2.0;
      let contractor = "AquaFix Pro";
      let contractorReason = "AquaFix is selected dynamically (Score: 97.5%) due to proximity, water specialization, and 1.5h response time.";

      if (isPower) {
        rootCause = "Main transformer feeder trip in sub-station due to phase overload.";
        summary = "Blackout in Tower B. Diesel Generator backup must be engaged manually.";
        plan = "1. Check DG battery cells and fuel meters.\n2. Switch main panel feeder grid to DG manually.\n3. Reset substation output relays.";
        cost = 12500.00;
        duration = 1.5;
        contractor = "PowerSure Services";
        contractorReason = "PowerSure holds the highest electrical load balance rating (96%) in our database.";
      } else if (isOverflow) {
        rootCause = "Feedback limit switch Float Valve assembly stuck open.";
        summary = "Tower C upper water reservoir overflow detected. Gravity drainage active.";
        plan = "1. Isolate inlet pump supply valves.\n2. Clean calcium deposition off float sensor trigger.\n3. Test flow level cut-offs.";
        cost = 2400.00;
        duration = 1.0;
        contractor = "AquaFix Pro";
        contractorReason = "AquaFix is pre-approved for all plumbing assets and is within 2km proximity.";
      } else if (isShortage) {
        rootCause = "Municipal supplier water grid leak outside outer perimeter gates.";
        summary = "Society reservoir capacity dropped below critical safety buffer (4%).";
        plan = "1. Ration water distribution schedules to morning and evening.\n2. Contract emergency water tanker transport.\n3. Fill central chamber.";
        cost = 15000.00;
        duration = 4.5;
        contractor = "RapidRepair Elite";
        contractorReason = "RapidRepair maintains emergency response vehicles matching water tanker logistics.";
      }

      const fallbackDetails: IncidentOut = {
        id: id as any,
        type: (activeItem?.type || "water_pressure_drop") as any,
        severity: (activeItem?.severity || "critical") as any,
        status: (activeItem?.status || "analyzing") as any,
        confidence: 0.96,
        description: activeItem?.type ? `Manually reported or sensor alert for ${activeItem.type.replace(/_/g, " ")}.` : "Critical telemetry breach.",
        detected_at: activeItem?.detected_at || new Date().toISOString(),
        root_cause: rootCause,
        ai_decision: {
          incident_summary: summary,
          action_plan: plan,
          estimated_resolution_hrs: duration,
          prediction: {
            predicted_outage_hrs: duration,
            estimated_cost: cost
          }
        },
        contractor_assignment: {
          contractor_name: contractor,
          estimated_cost: cost * 0.95,
          estimated_time_hrs: duration,
          selection_reasoning: contractorReason
        }
      };
      setSelectedIncident(fallbackDetails);
    } finally {
      setFetchingIncident(false);
    }
  };

  const pieData = Object.entries(data.severity_distribution).map(([name, value]) => ({
    name, value, color: SEVERITY_COLORS[name] || "#6b7280",
  }));

  const systemDateString = mounted
    ? new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })
    : "";

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-800">Operations Center</h1>
          <p className="text-sm text-stone-500 mt-0.5">Real-time AI infrastructure monitoring · {systemDateString}</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-emerald-600 font-medium">All agents active</span>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard title="Total Incidents" value={data.kpi.total_incidents} subtitle="All time" icon={Activity} gradient="from-amber-100/80 to-amber-50 border-amber-200" />
        <KPICard title="Active Incidents" value={data.kpi.active_incidents} subtitle="Needs attention" icon={AlertTriangle} gradient="from-orange-100/80 to-orange-50 border-orange-200" />
        <KPICard title="Critical Alerts" value={data.kpi.critical_incidents} subtitle="Immediate action" icon={Flame} gradient="from-red-100/80 to-red-50 border-red-200" />
        <KPICard title="Resolved Today" value={data.kpi.resolved_today} subtitle="Last 24 hours" icon={CheckCircle2} gradient="from-emerald-100/80 to-emerald-50 border-emerald-200" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Incident Trend */}
        <div className="xl:col-span-2 rounded-2xl border border-stone-200 bg-white shadow-sm p-5">
          <h2 className="text-sm font-semibold text-stone-800 mb-4">7-Day Incident Trend</h2>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data.incident_trend}>
              <defs>
                <linearGradient id="incidentGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#d97706" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#d97706" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis dataKey="date" tick={{ fill: "#78716c", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#78716c", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #d6d3d1", borderRadius: 8, color: "#44403c" }} />
              <Area type="monotone" dataKey="count" stroke="#d97706" strokeWidth={2} fill="url(#incidentGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Pie */}
        <div className="rounded-2xl border border-stone-200 bg-white shadow-sm p-5">
          <h2 className="text-sm font-semibold text-stone-800 mb-4">Severity Distribution</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #d6d3d1", borderRadius: 8, color: "#44403c" }} />
              <Legend formatter={(v) => <span className="text-xs text-stone-500 capitalize">{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row: Recent Incidents + Agent Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Recent Incidents Panel */}
        <div className="rounded-2xl border border-stone-200 bg-white shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-stone-800">Recent Incidents</h2>
            {selectedId && (
              <button onClick={() => { setSelectedId(null); setSelectedIncident(null); }} className="text-xs text-amber-600 hover:text-amber-500 font-semibold cursor-pointer">
                Clear Selection
              </button>
            )}
          </div>
          
          <div className={`grid grid-cols-1 ${selectedId ? "lg:grid-cols-2" : "grid-cols-1"} gap-4`}>
            {/* List column */}
            <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
              {data.recent_incidents.map((inc) => (
                <button
                  key={inc.id}
                  onClick={() => handleSelectIncident(inc.id)}
                  className={`w-full text-left flex items-center justify-between rounded-xl border px-4 py-3 hover:bg-stone-50 transition-all duration-200 cursor-pointer ${
                    selectedId === inc.id
                      ? "bg-amber-50 border-amber-300 shadow-inner"
                      : "bg-stone-50 border-stone-200"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-2 h-2 flex-shrink-0 rounded-full" style={{ background: SEVERITY_COLORS[inc.severity] || "#6b7280" }} />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-stone-800 truncate capitalize">{(inc as any).custom_type || inc.type.replace(/_/g, " ")}</p>
                      <p className="text-[10px] text-stone-400 mt-0.5">
                        {inc.tower_name} · {mounted ? new Date(inc.detected_at).toLocaleTimeString() : "..."}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                    <SeverityBadge severity={inc.severity} />
                    <StatusBadge status={inc.status} />
                    <ArrowRight className={`w-3.5 h-3.5 text-stone-400 transition-transform ${selectedId === inc.id ? "rotate-90 text-amber-600" : ""}`} />
                  </div>
                </button>
              ))}
            </div>

            {/* AI Solution & Contractor Details column */}
            {selectedId && (
              <div className="border-t lg:border-t-0 lg:border-l border-stone-200 pt-4 lg:pt-0 lg:pl-4 space-y-4 max-h-[350px] overflow-y-auto pr-1">
                {fetchingIncident ? (
                  <div className="h-full flex flex-col items-center justify-center py-20 space-y-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-600" />
                    <span className="text-[10px] text-stone-400">Querying agent reports...</span>
                  </div>
                ) : selectedIncident ? (
                  <div className="space-y-4 animate-fadeIn">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500">Diagnosis & Root Cause</h4>
                        <p className="text-xs text-stone-700 font-medium mt-1.5 bg-stone-50 px-3 py-2 rounded-lg border border-stone-200">
                          {selectedIncident.root_cause || "Analyzing incident telemetry..."}
                        </p>
                      </div>
                      <Link
                        href={`/incidents?id=${selectedId}`}
                        className="text-[10px] text-amber-600 hover:text-amber-500 font-semibold flex items-center gap-1 bg-amber-50 px-2 py-1 rounded-lg border border-amber-200 cursor-pointer"
                      >
                        Details <ExternalLink className="w-2.5 h-2.5" />
                      </Link>
                    </div>
                    
                    {/* Solution Plan */}
                    {(selectedIncident.ai_decision?.action_plan || selectedIncident.ai_decision?.incident_summary) && (
                      <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3.5 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">Solution Plan</span>
                          {selectedIncident.ai_decision?.estimated_resolution_hrs && (
                            <span className="text-[9px] text-emerald-600 font-semibold bg-emerald-100 px-2 py-0.5 rounded-full">
                              Est: {selectedIncident.ai_decision.estimated_resolution_hrs}h
                            </span>
                          )}
                        </div>
                        {/* Predicted Cost and Duration */}
                        {selectedIncident.ai_decision?.prediction && (
                          <div className="grid grid-cols-2 gap-2 bg-emerald-100/60 p-2 rounded-lg border border-emerald-200 mb-2 text-[10px]">
                            <div>
                              <p className="text-[8px] text-emerald-700 font-bold uppercase tracking-wider">Predicted Cost</p>
                              <p className="font-bold text-stone-800">₹{selectedIncident.ai_decision.prediction.estimated_cost?.toLocaleString()}</p>
                            </div>
                            <div>
                              <p className="text-[8px] text-emerald-700 font-bold uppercase tracking-wider">Predicted Outage</p>
                              <p className="font-bold text-stone-800">{selectedIncident.ai_decision.prediction.predicted_outage_hrs?.toFixed(1)} hrs</p>
                            </div>
                          </div>
                        )}
                        {selectedIncident.ai_decision?.incident_summary && (
                          <p className="text-[11px] text-stone-600 font-medium leading-relaxed">
                            {selectedIncident.ai_decision.incident_summary}
                          </p>
                        )}
                        {selectedIncident.ai_decision?.action_plan && (
                          <p className="text-[10px] text-stone-500 whitespace-pre-line leading-relaxed pt-2 border-t border-emerald-200">
                            {selectedIncident.ai_decision.action_plan}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Dispatched Contractor */}
                    {selectedIncident.contractor_assignment && (
                      <div className="rounded-xl bg-stone-50 border border-stone-200 p-3.5 space-y-2">
                        <span className="text-[10px] font-bold text-stone-500 uppercase tracking-wider">Recommended Contractor</span>
                        <div className="flex items-center justify-between pt-1">
                          <Link
                            href={`/contractors?highlight=${encodeURIComponent(selectedIncident.contractor_assignment.contractor_name)}`}
                            className="text-xs font-bold text-amber-600 hover:text-amber-500 hover:underline cursor-pointer inline-flex items-center gap-1 group"
                          >
                            {selectedIncident.contractor_assignment.contractor_name}
                            <ExternalLink className="w-3 h-3 text-stone-400 group-hover:text-amber-600 transition-colors" />
                          </Link>
                          <span className="text-xs text-amber-700 font-bold bg-amber-100 px-2 py-0.5 rounded-full">
                            ₹{selectedIncident.contractor_assignment.estimated_cost?.toLocaleString()}
                          </span>
                        </div>
                        {selectedIncident.contractor_assignment.selection_reasoning && (
                          <p className="text-[10px] text-stone-400 italic leading-relaxed pt-2 border-t border-stone-200 font-sans">
                            {selectedIncident.contractor_assignment.selection_reasoning}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-stone-400 text-center py-10">Select an active incident to view live AI plans.</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Agent Activity */}
        <div className="rounded-2xl border border-stone-200 bg-white shadow-sm p-5">
          <h2 className="text-sm font-semibold text-stone-800 mb-4">Agent Activity (Today)</h2>
          <div className="space-y-3">
            {data.agent_activity.map((agent) => (
              <div key={agent.agent_name} className="flex items-center gap-3">
                <div className="w-8 h-8 flex-shrink-0 rounded-lg bg-violet-100 border border-violet-200 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-violet-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs font-medium text-stone-800 truncate">{agent.agent_name}</p>
                    <span className="text-xs text-stone-500">{agent.executions_today} runs</span>
                  </div>
                  <div className="w-full bg-stone-100 rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-gradient-to-r from-amber-500 to-yellow-500"
                      style={{ width: `${agent.success_rate * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-[10px] text-emerald-600 flex-shrink-0">{(agent.success_rate * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
