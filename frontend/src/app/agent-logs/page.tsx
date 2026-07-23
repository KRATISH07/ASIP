"use client";
import { useEffect, useState } from "react";
import { agentLogsApi, type AgentLogOut } from "@/lib/api";
import { Bot, Clock, Zap, AlertCircle } from "lucide-react";
import { useAuth } from "@/components/auth-provider";

const MOCK_LOGS: AgentLogOut[] = [
  { id: "1", incident_id: "inc-001", agent_name: "MonitoringAgent", execution_time_ms: 12, tokens_used: 0, status: "success", created_at: new Date().toISOString(), output_payload: { incident_detected: true, type: "water_pressure_drop", severity: "critical" } },
  { id: "2", incident_id: "inc-001", agent_name: "InfrastructureAgent", execution_time_ms: 2340, tokens_used: 820, status: "success", created_at: new Date(Date.now() - 2000).toISOString(), output_payload: { probable_cause: "Booster pump motor burnout", confidence: 0.92 } },
  { id: "3", incident_id: "inc-001", agent_name: "ImpactAnalysisAgent", execution_time_ms: 145, tokens_used: 0, status: "success", created_at: new Date(Date.now() - 4000).toISOString(), output_payload: { estimated_residents: 350, priority: "critical" } },
  { id: "4", incident_id: "inc-001", agent_name: "ContractorAgent", execution_time_ms: 1820, tokens_used: 650, status: "success", created_at: new Date(Date.now() - 6000).toISOString(), output_payload: { contractor_name: "AquaFix Pro", estimated_cost: 12500 } },
  { id: "5", incident_id: "inc-001", agent_name: "CommunicationAgent", execution_time_ms: 2100, tokens_used: 940, status: "success", created_at: new Date(Date.now() - 8000).toISOString(), output_payload: { notifications_generated: 3 } },
  { id: "6", incident_id: "inc-001", agent_name: "SupervisorAgent", execution_time_ms: 1950, tokens_used: 1100, status: "success", created_at: new Date(Date.now() - 10000).toISOString(), output_payload: { priority: "critical", estimated_resolution_hrs: 5 } },
];

const AGENT_COLORS: Record<string, string> = {
  MonitoringAgent: "from-amber-500/20 to-amber-600/10 border-amber-300 text-amber-600",
  InfrastructureAgent: "from-violet-500/20 to-violet-600/10 border-violet-500/30 text-violet-600",
  ImpactAnalysisAgent: "from-cyan-500/20 to-cyan-600/10 border-cyan-500/30 text-cyan-600",
  ContractorAgent: "from-amber-500/20 to-amber-600/10 border-amber-500/30 text-amber-600",
  CommunicationAgent: "from-pink-500/20 to-pink-600/10 border-pink-500/30 text-pink-600",
  SupervisorAgent: "from-emerald-500/20 to-emerald-600/10 border-emerald-200 text-emerald-600",
};

export default function AgentLogsPage() {
  const { token: TOKEN } = useAuth();
  const [mounted, setMounted] = useState(false);
  const [logs, setLogs] = useState<AgentLogOut[]>(MOCK_LOGS);
  const [selected, setSelected] = useState<AgentLogOut | null>(null);

  useEffect(() => {
    setMounted(true);
    if (TOKEN) {
      agentLogsApi.list(TOKEN)
        .then((res) => {
          const blended = [...res];
          MOCK_LOGS.forEach(m => {
            if (!blended.some(n => n.id === m.id)) {
              blended.push(m);
            }
          });
          setLogs(blended);
        })
        .catch(() => setLogs(MOCK_LOGS));
    }
  }, [TOKEN]);

  return (
    <div className="flex h-screen">
      <div className="w-96 flex-shrink-0 border-r border-stone-200 flex flex-col">
        <div className="px-5 py-4 border-b border-stone-200">
          <h1 className="text-lg font-bold text-stone-800">Agent Logs</h1>
          <p className="text-xs text-stone-500 mt-0.5">Observability into every agent execution</p>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-stone-200">
          {logs.map((log) => {
            const style = AGENT_COLORS[log.agent_name] || "from-stone-500/20 to-stone-600/10 border-stone-500/20 text-stone-500";
            return (
              <button key={log.id} onClick={() => setSelected(log)}
                className={`w-full text-left px-5 py-3.5 hover:bg-stone-50 transition-colors ${selected?.id === log.id ? "bg-amber-50 border-l-2 border-amber-500" : ""}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className={`flex items-center gap-1.5 text-xs font-medium border rounded-lg px-2 py-0.5 bg-gradient-to-br ${style}`}>
                    <Bot className="w-3 h-3" />{log.agent_name}
                  </div>
                  {log.status === "success"
                    ? <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Success</span>
                    : <span className="text-[10px] text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full">Failed</span>}
                </div>
                <div className="flex items-center gap-3 text-[10px] text-stone-400">
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
              <h2 className="text-xl font-bold text-stone-800">{selected.agent_name}</h2>
              <p className="text-xs text-stone-500 mt-1">Incident: {selected.incident_id} · {mounted ? new Date(selected.created_at).toLocaleString() : ""}</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[["Execution Time", `${selected.execution_time_ms}ms`], ["Tokens Used", selected.tokens_used || "N/A"], ["Status", selected.status]].map(([k, v]) => (
                <div key={k as string} className="rounded-xl bg-stone-50 border border-stone-200 p-3">
                  <p className="text-[10px] text-stone-400">{k}</p>
                  <p className="text-sm font-semibold text-stone-800 mt-1 capitalize">{v}</p>
                </div>
              ))}
            </div>
            {selected.output_payload && (
              <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4">
                <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-2">Output Payload</p>
                <pre className="text-xs text-stone-600 whitespace-pre-wrap">{JSON.stringify(selected.output_payload, null, 2)}</pre>
              </div>
            )}
            {selected.error && (
              <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 flex gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-red-300">{selected.error}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Bot className="w-12 h-12 text-stone-400 mb-3" />
            <p className="text-stone-500 font-medium">Select a log to inspect</p>
          </div>
        )}
      </div>
    </div>
  );
}
