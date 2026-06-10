"use client";

import { useEffect, useState } from "react";
import { dashboardApi, type DashboardOut } from "@/lib/api";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  Zap, Droplets, TrendingUp, Bot,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";

const TOKEN = "demo-token"; // replace with real auth context

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
    <div className={`relative overflow-hidden rounded-2xl border bg-gradient-to-br ${gradient} p-5 backdrop-blur-xl`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{title}</p>
          <p className="mt-2 text-4xl font-bold text-white tabular-nums">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
        </div>
        <div className="rounded-xl bg-white/10 p-2.5">
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    low: "bg-green-500/20 text-green-400 border-green-500/30",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${colors[severity] || "bg-gray-500/20 text-gray-400"}`}>
      {severity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    detected: "bg-blue-500/20 text-blue-400",
    analyzing: "bg-violet-500/20 text-violet-400",
    action_planned: "bg-cyan-500/20 text-cyan-400",
    in_progress: "bg-amber-500/20 text-amber-400",
    resolved: "bg-green-500/20 text-green-400",
    escalated: "bg-red-500/20 text-red-400",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${colors[status] || "bg-gray-500/20 text-gray-400"}`}>
      {status.replace("_", " ")}
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
  incident_trend: Array.from({ length: 7 }, (_, i) => ({
    date: new Date(Date.now() - (6 - i) * 86400000).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    count: Math.floor(Math.random() * 8 + 2),
  })),
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardOut>(MOCK_DATA);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getSummary(TOKEN)
      .then(setData)
      .catch(() => setData(MOCK_DATA))
      .finally(() => setLoading(false));
  }, []);

  const pieData = Object.entries(data.severity_distribution).map(([name, value]) => ({
    name, value, color: SEVERITY_COLORS[name] || "#6b7280",
  }));

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Operations Center</h1>
          <p className="text-sm text-gray-400 mt-0.5">Real-time AI infrastructure monitoring · {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-green-400 font-medium">All agents active</span>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard title="Total Incidents" value={data.kpi.total_incidents} subtitle="All time" icon={Activity} gradient="from-blue-500/20 to-blue-600/10 border-blue-500/20" />
        <KPICard title="Active Incidents" value={data.kpi.active_incidents} subtitle="Needs attention" icon={AlertTriangle} gradient="from-amber-500/20 to-amber-600/10 border-amber-500/20" />
        <KPICard title="Critical Alerts" value={data.kpi.critical_incidents} subtitle="Immediate action" icon={Flame} gradient="from-red-500/20 to-red-600/10 border-red-500/20" />
        <KPICard title="Resolved Today" value={data.kpi.resolved_today} subtitle="Last 24 hours" icon={CheckCircle2} gradient="from-green-500/20 to-green-600/10 border-green-500/20" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Incident Trend */}
        <div className="xl:col-span-2 rounded-2xl border border-white/5 bg-white/3 backdrop-blur-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4">7-Day Incident Trend</h2>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data.incident_trend}>
              <defs>
                <linearGradient id="incidentGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
              <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "#1a2035", border: "1px solid #ffffff15", borderRadius: 8, color: "#fff" }} />
              <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} fill="url(#incidentGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Pie */}
        <div className="rounded-2xl border border-white/5 bg-white/3 backdrop-blur-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Severity Distribution</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#1a2035", border: "1px solid #ffffff15", borderRadius: 8, color: "#fff" }} />
              <Legend formatter={(v) => <span className="text-xs text-gray-400 capitalize">{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row: Recent Incidents + Agent Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Recent Incidents */}
        <div className="rounded-2xl border border-white/5 bg-white/3 backdrop-blur-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Recent Incidents</h2>
          <div className="space-y-2">
            {data.recent_incidents.map((inc) => (
              <div key={inc.id} className="flex items-center justify-between rounded-xl bg-white/3 border border-white/5 px-4 py-3 hover:bg-white/5 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-2 h-2 flex-shrink-0 rounded-full ${SEVERITY_COLORS[inc.severity] ? "" : ""}`} style={{ background: SEVERITY_COLORS[inc.severity] }} />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-white truncate">{inc.type.replace(/_/g, " ")}</p>
                    <p className="text-[10px] text-gray-500">{inc.tower_name} · {new Date(inc.detected_at).toLocaleTimeString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                  <SeverityBadge severity={inc.severity} />
                  <StatusBadge status={inc.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Activity */}
        <div className="rounded-2xl border border-white/5 bg-white/3 backdrop-blur-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Agent Activity (Today)</h2>
          <div className="space-y-3">
            {data.agent_activity.map((agent) => (
              <div key={agent.agent_name} className="flex items-center gap-3">
                <div className="w-8 h-8 flex-shrink-0 rounded-lg bg-violet-500/20 border border-violet-500/20 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-violet-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs font-medium text-white truncate">{agent.agent_name}</p>
                    <span className="text-xs text-gray-400">{agent.executions_today} runs</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-gradient-to-r from-violet-500 to-blue-500"
                      style={{ width: `${agent.success_rate * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-[10px] text-green-400 flex-shrink-0">{(agent.success_rate * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
