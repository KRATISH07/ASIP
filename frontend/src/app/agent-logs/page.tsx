"use client";
import { useEffect, useState } from "react";
import { agentLogsApi, type AgentLogOut } from "@/lib/api";
import { Bot, Clock, Zap, AlertCircle } from "lucide-react";

const TOKEN = "demo-token";

const MOCK_LOGS: AgentLogOut[] = [
  { id: "1", incident_id: "inc-001", agent_name: "MonitoringAgent", execution_time_ms: 12, tokens_used: 0, status: "success", created_at: new Date().toISOString(), output_payload: { incident_detected: true, type: "water_pressure_drop", severity: "critical" } },
  { id: "2", incident_id: "inc-001", agent_name: "InfrastructureAgent", execution_time_ms: 2340, tokens_used: 820, status: "success", created_at: new Date(Date.now() - 2000).toISOString(), output_payload: { probable_cause: "Booster pump motor burnout", confidence: 0.92 } },
  { id: "3", incident_id: "inc-001", agent_name: "ImpactAnalysisAgent", execution_time_ms: 145, tokens_used: 0, status: "success", created_at: new Date(Date.now() - 4000).toISOString(), output_payload: { estimated_residents: 350, priority: "critical" } },
  { id: "4", incident_id: "inc-001", agent_name: "ContractorAgent", execution_time_ms: 1820, tokens_used: 650, status: "success", created_at: new Date(Date.now() - 6000).toISOString(), output_payload: { contractor_name: "AquaFix Pro", estimated_cost: 12500 } },
  { id: "5", incident_id: "inc-001", agent_name: "CommunicationAgent", execution_time_ms: 2100, tokens_used: 940, status: "success", created_at: new Date(Date.now() - 8000).toISOString(), output_payload: { notifications_generated: 3 } },
  { id: "6", incident_id: "inc-001", agent_name: "SupervisorAgent", execution_time_ms: 1950, tokens_used: 1100, status: "success", created_at: new Date(Date.now() - 10000).toISOString(), output_payload: { priority: "critical", estimated_resolution_hrs: 5 } },
];

const AGENT_COLORS: Record<string, string> = {
  MonitoringAgent: "from-blue-500/20 to-blue-600/10 border-blue-500/20 text-blue-400",
  InfrastructureAgent: "from-violet-500/20 to-violet-600/10 border-violet-500/20 text-violet-400",
  ImpactAnalysisAgent: "from-cyan-500/20 to-cyan-600/10 border-cyan-500/20 text-cyan-400",
  ContractorAgent: "from-amber-500/20 to-amber-600/10 border-amber-500/20 text-amber-400",
  CommunicationAgent: "from-pink-500/20 to-pink-600/10 border-pink-500/20 text-pink-400",
  SupervisorAgent: "from-green-500/20 to-green-600/10 border-green-500/20 text-green-400",
};

export default function AgentLogsPage() {
  const [logs, setLogs] = useState<AgentLogOut[]>(MOCK_LOGS);
  const [selected, setSelected] = useState<AgentLogOut | null>(null);

  useEffect(() => {
    agentLogsApi.list(TOKEN).then(setLogs).catch(() => setLogs(MOCK_LOGS));
  }, []);

  return (
    <div className="flex h-screen">
      <div className="w-96 flex-shrink-0 border-r border-white/5 flex flex-col">
        <div className="px-5 py-4 border-b border-white/5">
          <h1 className="text-lg font-bold text-white">Agent Logs</h1>
          <p className="text-xs text-gray-400 mt-0.5">Observability into every agent execution</p>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-white/5">
          {logs.map((log) => {
            const style = AGENT_COLORS[log.agent_name] || "from-gray-500/20 to-gray-600/10 border-gray-500/20 text-gray-400";
            return (
              <button key={log.id} onClick={() => setSelected(log)}
                className={`w-full text-left px-5 py-3.5 hover:bg-white/3 transition-colors ${selected?.id === log.id ? "bg-blue-600/10 border-l-2 border-blue-500" : ""}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className={`flex items-center gap-1.5 text-xs font-medium border rounded-lg px-2 py-0.5 bg-gradient-to-br ${style}`}>
                    <Bot className="w-3 h-3" />{log.agent_name}
                  </div>
                  {log.status === "success"
                    ? <span className="text-[10px] text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">Success</span>
                    : <span className="text-[10px] text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full">Failed</span>}
                </div>
                <div className="flex items-center gap-3 text-[10px] text-gray-500">
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{log.execution_time_ms}ms</span>
                  {log.tokens_used ? <span className="flex items-center gap-1"><Zap className="w-3 h-3" />{log.tokens_used} tokens</span> : null}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {selected ? (
          <div className="space-y-5 max-w-2xl">
            <div>
              <h2 className="text-xl font-bold text-white">{selected.agent_name}</h2>
              <p className="text-xs text-gray-400 mt-1">Incident: {selected.incident_id} · {new Date(selected.created_at).toLocaleString()}</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[["Execution Time", `${selected.execution_time_ms}ms`], ["Tokens Used", selected.tokens_used || "N/A"], ["Status", selected.status]].map(([k, v]) => (
                <div key={k as string} className="rounded-xl bg-white/3 border border-white/5 p-3">
                  <p className="text-[10px] text-gray-500">{k}</p>
                  <p className="text-sm font-semibold text-white mt-1 capitalize">{v}</p>
                </div>
              ))}
            </div>
            {selected.output_payload && (
              <div className="rounded-xl bg-green-500/5 border border-green-500/20 p-4">
                <p className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-2">Output Payload</p>
                <pre className="text-xs text-gray-300 whitespace-pre-wrap">{JSON.stringify(selected.output_payload, null, 2)}</pre>
              </div>
            )}
            {selected.error && (
              <div className="rounded-xl bg-red-500/5 border border-red-500/20 p-4 flex gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-red-300">{selected.error}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Bot className="w-12 h-12 text-gray-600 mb-3" />
            <p className="text-gray-400 font-medium">Select a log to inspect</p>
          </div>
        )}
      </div>
    </div>
  );
}
