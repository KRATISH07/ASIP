"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import { dashboardApi, type DashboardOut } from "@/lib/api";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  Zap, Droplets, TrendingUp, Bot, ArrowRight, ExternalLink,
  ShieldCheck, Wrench, Building2, Bell, Sparkles, HardHat, Check,
  Waves, ArrowUpRight
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";

const MOCK_DATA: DashboardOut = {
  kpi: { total_incidents: 47, active_incidents: 8, critical_incidents: 3, resolved_today: 5 },
  recent_incidents: [
    { id: "1", type: "water_pressure_drop", severity: "critical", status: "analyzing", tower_name: "Tower A", detected_at: new Date().toISOString() },
    { id: "2", type: "power_outage", severity: "high", status: "in_progress", tower_name: "Tower B", detected_at: new Date(Date.now() - 3600000).toISOString() },
    { id: "3", type: "tank_overflow", severity: "medium", status: "resolved", tower_name: "Tower C", detected_at: new Date(Date.now() - 7200000).toISOString() },
    { id: "4", type: "power_overload", severity: "high", status: "action_planned", tower_name: "Tower A", detected_at: new Date(Date.now() - 10800000).toISOString() },
    { id: "5", type: "water_shortage", severity: "critical", status: "escalated", tower_name: "Tower B", detected_at: new Date(Date.now() - 14400000).toISOString() },
  ],
  incident_trend: [
    { date: "Mon", count: 4 },
    { date: "Tue", count: 9 },
    { date: "Wed", count: 6 },
    { date: "Thu", count: 14 },
    { date: "Fri", count: 10 },
    { date: "Sat", count: 5 },
    { date: "Sun", count: 3 },
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
};

function KPICard({
  title, value, subtitle, icon: Icon, badgeBg
}: {
  title: string; value: number | string; subtitle?: string;
  icon: React.ElementType; badgeBg: string;
}) {
  return (
    <div className="frost-card p-6 space-y-4 wave-glow-bg">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{title}</p>
        <div className={`p-3 rounded-2xl border ${badgeBg}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div>
        <p className="text-4xl font-extrabold text-slate-900 tracking-tight tabular-nums">{value}</p>
        {subtitle && <p className="mt-1.5 text-xs font-medium text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-rose-100 text-rose-800 border-rose-200 font-bold",
    high: "bg-amber-100 text-amber-900 border-amber-300 font-bold",
    medium: "bg-purple-100 text-purple-900 border-purple-300 font-semibold",
    low: "bg-emerald-100 text-emerald-900 border-emerald-300 font-medium",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] uppercase tracking-wider ${colors[severity] || "bg-slate-100 text-slate-600"}`}>
      {severity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    detected: "bg-blue-100 text-blue-800 font-bold border border-blue-200",
    analyzing: "bg-indigo-100 text-indigo-800 font-bold border border-indigo-200",
    action_planned: "bg-cyan-100 text-cyan-800 font-bold border border-cyan-200",
    in_progress: "bg-amber-100 text-amber-800 font-bold border border-amber-200",
    resolved: "bg-emerald-100 text-emerald-800 font-bold border border-emerald-200",
    escalated: "bg-rose-100 text-rose-800 font-bold border border-rose-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] capitalize ${colors[status] || "bg-slate-100 text-slate-600"}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

export default function WavePatternDashboard() {
  const { token, user } = useAuth();
  const [data, setData] = useState<DashboardOut>(MOCK_DATA);
  const [resolvedMap, setResolvedMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!token) return;
    dashboardApi.getSummary(token)
      .then((res) => setData(res))
      .catch(() => setData(MOCK_DATA));
  }, [token]);

  const handleResolve = (id: string) => {
    setResolvedMap(prev => ({ ...prev, [id]: true }));
  };

  return (
    <div className="min-h-screen bg-[#fafafc] p-6 lg:p-10 animate-fade-in space-y-8">
      
      {/* ── Top Hero Banner (Nordic Frost & Electric Wave) ──────────────────── */}
      <div className="relative overflow-hidden bg-white border border-indigo-100 rounded-3xl p-8 shadow-xl shadow-indigo-950/5 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-cyan-400/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-2">
          <div className="flex items-center gap-2.5">
            <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-indigo-100 text-indigo-900 border border-indigo-200/80 flex items-center gap-1.5">
              <Waves className="w-3.5 h-3.5 text-indigo-600 animate-wave-float" />
              AI Operations Center
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              ● Live Dynamic Stream
            </span>
          </div>
          <h1 className="text-3xl lg:text-4xl font-extrabold text-slate-900 tracking-tight">
            Real-Time Society Intelligence & Wave Analytics
          </h1>
          <p className="text-xs lg:text-sm text-slate-500 font-medium max-w-2xl">
            Welcome back, <strong className="text-slate-800">{user?.full_name || "Administrator"}</strong>. Autonomous multi-agent pipeline monitoring live telemetry and resident incidents.
          </p>
        </div>

        <div className="relative z-10 flex items-center gap-3">
          <Link
            href="/incidents"
            className="px-5 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-lg shadow-indigo-600/25 transition flex items-center gap-2"
          >
            <Activity className="w-4 h-4" />
            Incidents Triage
          </Link>
          <Link
            href="/analytics"
            className="px-5 py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs border border-slate-300 transition flex items-center gap-2"
          >
            <TrendingUp className="w-4 h-4 text-indigo-600" />
            AI Analytics
          </Link>
        </div>
      </div>

      {/* ── KPI Metric Cards ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Incidents"
          value={data.kpi.total_incidents}
          subtitle="Processed this month"
          icon={Activity}
          badgeBg="bg-indigo-50 text-indigo-600 border-indigo-200"
        />
        <KPICard
          title="Active Alerts"
          value={data.kpi.active_incidents}
          subtitle="Currently in pipeline"
          icon={Flame}
          badgeBg="bg-amber-50 text-amber-600 border-amber-200"
        />
        <KPICard
          title="Critical Incidents"
          value={data.kpi.critical_incidents}
          subtitle="Immediate attention"
          icon={AlertTriangle}
          badgeBg="bg-rose-50 text-rose-600 border-rose-200"
        />
        <KPICard
          title="Resolved Today"
          value={data.kpi.resolved_today}
          subtitle="Auto & manual closed"
          icon={CheckCircle2}
          badgeBg="bg-emerald-50 text-emerald-600 border-emerald-200"
        />
      </div>

      {/* ── Dynamic Wave Pattern Chart Card ──────────────────────────────────── */}
      <div className="frost-card p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
              Weekly Incident Velocity & Resolution Wave Pattern
            </h2>
            <p className="text-xs text-slate-500 mt-1 font-medium">Dynamic incident frequency curve and autonomous triage distribution over time.</p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-indigo-50 text-indigo-700 border border-indigo-200/80">
            Dynamic Monotone Wave
          </span>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.incident_trend}>
              <defs>
                <linearGradient id="waveGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderRadius: "14px", border: "none", color: "#fff", fontSize: "12px", boxShadow: "0 10px 25px -5px rgba(15, 23, 42, 0.3)" }} />
              <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={3.5} fillOpacity={1} fill="url(#waveGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Main Content Grid: Recent Active Incidents & Agent Executions ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Columns */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Active Incidents Triage List */}
          <div className="frost-card p-7 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                  <Flame className="w-5 h-5 text-indigo-600" />
                  Recent Active Incidents Triage
                </h2>
                <p className="text-xs text-slate-500 mt-0.5 font-medium">Real-time incident feed being triaged by autonomous agents.</p>
              </div>
              <Link href="/incidents" className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {data.recent_incidents.map((inc) => (
                <div key={inc.id} className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/70 flex items-center justify-between gap-4 hover:border-indigo-200 transition">
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-sm text-slate-900 truncate">
                        {inc.type.replace(/_/g, " ").toUpperCase()}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-indigo-100 text-indigo-900 border border-indigo-200">
                        {inc.tower_name}
                      </span>
                      <SeverityBadge severity={inc.severity} />
                    </div>
                    <p className="text-xs text-slate-500 font-medium">
                      Detected: {new Date(inc.detected_at).toLocaleTimeString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <StatusBadge status={resolvedMap[inc.id] ? "resolved" : inc.status} />
                    {!resolvedMap[inc.id] && inc.status !== "resolved" && (
                      <button
                        onClick={() => handleResolve(inc.id)}
                        className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition cursor-pointer"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* LangGraph Agent Execution Table */}
          <div className="frost-card p-7 space-y-5">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <Bot className="w-5 h-5 text-indigo-600" />
                LangGraph Multi-Agent Execution Metrics
              </h2>
              <p className="text-xs text-slate-500 mt-0.5 font-medium">Execution stats across autonomous diagnostic nodes today.</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider">
                    <th className="pb-3">Agent Node</th>
                    <th className="pb-3">Executions</th>
                    <th className="pb-3">Avg Latency</th>
                    <th className="pb-3">Success Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800 font-medium">
                  {data.agent_activity.map((ag) => (
                    <tr key={ag.agent_name} className="hover:bg-slate-50/80">
                      <td className="py-3 font-bold text-slate-900">{ag.agent_name}</td>
                      <td className="py-3">{ag.executions_today}</td>
                      <td className="py-3 font-mono text-indigo-600 font-semibold">{ag.avg_execution_time_ms} ms</td>
                      <td className="py-3">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          {(ag.success_rate * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>

        {/* Right Column (1 Col) */}
        <div className="space-y-6">
          
          {/* Incident Severity Distribution */}
          <div className="frost-card p-6 space-y-4">
            <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              Severity Breakdown
            </h3>

            <div className="space-y-3">
              {Object.entries(data.severity_distribution).map(([sev, count]) => (
                <div key={sev} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/70">
                  <SeverityBadge severity={sev} />
                  <span className="font-extrabold text-sm text-slate-900">{count} events</span>
                </div>
              ))}
            </div>
          </div>

          {/* Ranked Contractors Snapshot */}
          <div className="frost-card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                <HardHat className="w-4 h-4 text-indigo-600" />
                Ranked Contractors
              </h3>
              <Link href="/contractors" className="text-xs font-bold text-indigo-600 hover:text-indigo-700">
                View All
              </Link>
            </div>

            <div className="space-y-3">
              {[
                { name: "Apex Plumbing & Pumps", specialty: "Hydraulic Systems", rating: 4.9 },
                { name: "Voltaic Power Solutions", specialty: "Electrical Substation", rating: 4.8 },
                { name: "RapidRepair Elite", specialty: "Emergency Repair", rating: 4.7 },
              ].map((c, i) => (
                <div key={c.name} className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-xs text-slate-900">#{i + 1} {c.name}</p>
                    <p className="text-[10px] text-slate-500 font-medium mt-0.5">{c.specialty}</p>
                  </div>
                  <span className="text-xs font-extrabold text-amber-600">★ {c.rating}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
