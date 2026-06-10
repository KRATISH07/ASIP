"use client";

import { useEffect, useState } from "react";
import { incidentsApi, type IncidentOut } from "@/lib/api";
import { AlertTriangle, Filter, RefreshCw } from "lucide-react";

const TOKEN = "demo-token";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-500/10 border-red-500/20",
  high: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  low: "text-green-400 bg-green-500/10 border-green-500/20",
};

const STATUS_COLORS: Record<string, string> = {
  detected: "text-blue-400 bg-blue-500/10",
  analyzing: "text-violet-400 bg-violet-500/10",
  action_planned: "text-cyan-400 bg-cyan-500/10",
  in_progress: "text-amber-400 bg-amber-500/10",
  resolved: "text-green-400 bg-green-500/10",
  escalated: "text-red-400 bg-red-500/10",
};

const MOCK_INCIDENTS: IncidentOut[] = [
  { id: "1", type: "water_pressure_drop", severity: "critical", confidence: 0.97, status: "analyzing", description: "Pressure dropped to 0.3 bar in Tower A pump room", detected_at: new Date().toISOString(), root_cause: "Booster pump motor failure" },
  { id: "2", type: "power_outage", severity: "high", confidence: 0.99, status: "in_progress", description: "Complete power loss detected in Tower B", detected_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "3", type: "tank_overflow", severity: "medium", confidence: 0.98, status: "resolved", description: "Tank level exceeded 95% in Tower C", detected_at: new Date(Date.now() - 7200000).toISOString(), root_cause: "Float valve malfunction" },
  { id: "4", type: "power_overload", severity: "high", confidence: 0.87, status: "action_planned", description: "Power consumption at 91% of rated capacity", detected_at: new Date(Date.now() - 10800000).toISOString() },
  { id: "5", type: "water_shortage", severity: "critical", confidence: 0.96, status: "escalated", description: "Tank level critically low at 4%", detected_at: new Date(Date.now() - 14400000).toISOString() },
];

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentOut[]>(MOCK_INCIDENTS);
  const [selected, setSelected] = useState<IncidentOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    incidentsApi.list(TOKEN)
      .then((res) => setIncidents(res.items))
      .catch(() => setIncidents(MOCK_INCIDENTS))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex h-screen">
      {/* Left panel */}
      <div className="w-96 flex-shrink-0 border-r border-white/5 flex flex-col">
        <div className="px-5 py-4 border-b border-white/5">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-bold text-white">Incidents</h1>
            <button className="p-1.5 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/5">
            <Filter className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-xs text-gray-500">Filter incidents…</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-white/5">
          {incidents.map((inc) => (
            <button
              key={inc.id}
              onClick={() => setSelected(inc)}
              className={`w-full text-left px-5 py-4 hover:bg-white/3 transition-colors ${selected?.id === inc.id ? "bg-blue-600/10 border-l-2 border-blue-500" : ""}`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize ${SEVERITY_COLORS[inc.severity]}`}>
                  {inc.severity}
                </span>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${STATUS_COLORS[inc.status]}`}>
                  {inc.status.replace(/_/g, " ")}
                </span>
              </div>
              <p className="text-sm font-medium text-white capitalize">{inc.type.replace(/_/g, " ")}</p>
              <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{inc.description}</p>
              <p className="text-[10px] text-gray-600 mt-2">{new Date(inc.detected_at).toLocaleString()}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-y-auto p-6">
        {selected ? (
          <div className="space-y-5 max-w-2xl">
            <div>
              <h2 className="text-2xl font-bold text-white capitalize">{selected.type.replace(/_/g, " ")}</h2>
              <p className="text-sm text-gray-400 mt-1">{selected.description}</p>
            </div>

            {/* Meta grid */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Severity", value: selected.severity, cls: SEVERITY_COLORS[selected.severity] },
                { label: "Status", value: selected.status.replace(/_/g, " "), cls: STATUS_COLORS[selected.status] },
                { label: "Confidence", value: `${(selected.confidence * 100).toFixed(0)}%`, cls: "text-white bg-white/5" },
              ].map(({ label, value, cls }) => (
                <div key={label} className="rounded-xl bg-white/3 border border-white/5 p-3">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize border border-white/10 ${cls}`}>{value}</span>
                </div>
              ))}
            </div>

            {/* Root cause */}
            {selected.root_cause && (
              <div className="rounded-xl bg-white/3 border border-white/5 p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Root Cause Analysis</p>
                <p className="text-sm text-white">{selected.root_cause}</p>
              </div>
            )}

            {/* AI Decision */}
            {selected.ai_decision && (
              <div className="rounded-xl bg-violet-500/5 border border-violet-500/20 p-4">
                <p className="text-xs font-semibold text-violet-400 uppercase tracking-wider mb-2">AI Decision Report</p>
                <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-auto max-h-48">
                  {JSON.stringify(selected.ai_decision, null, 2)}
                </pre>
              </div>
            )}

            {/* Contractor */}
            {selected.contractor_assignment && (
              <div className="rounded-xl bg-white/3 border border-white/5 p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Assigned Contractor</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-[10px] text-gray-500">Name</p>
                    <p className="text-sm text-white font-medium">{selected.contractor_assignment.contractor_name}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">Estimated Cost</p>
                    <p className="text-sm text-white font-medium">₹{selected.contractor_assignment.estimated_cost?.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500">Estimated Time</p>
                    <p className="text-sm text-white font-medium">{selected.contractor_assignment.estimated_time_hrs}h</p>
                  </div>
                </div>
                {selected.contractor_assignment.selection_reasoning && (
                  <p className="mt-3 text-xs text-gray-400 italic">{selected.contractor_assignment.selection_reasoning}</p>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <AlertTriangle className="w-12 h-12 text-gray-600 mb-3" />
            <p className="text-gray-400 font-medium">Select an incident to view details</p>
            <p className="text-xs text-gray-600 mt-1">{incidents.length} incidents in the system</p>
          </div>
        )}
      </div>
    </div>
  );
}
