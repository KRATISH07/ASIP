"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import { dashboardApi, type DashboardOut } from "@/lib/api";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  TrendingUp, Bot, ArrowRight, HardHat, Check,
  ArrowUpRight, Zap, Shield
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";

const MOCK: DashboardOut = {
  kpi: { total_incidents: 47, active_incidents: 8, critical_incidents: 3, resolved_today: 5 },
  recent_incidents: [
    { id: "1", type: "water_pressure_drop", severity: "critical", status: "analyzing", tower_name: "Tower A", detected_at: new Date().toISOString() },
    { id: "2", type: "power_outage", severity: "high", status: "in_progress", tower_name: "Tower B", detected_at: new Date(Date.now() - 3600000).toISOString() },
    { id: "3", type: "tank_overflow", severity: "medium", status: "resolved", tower_name: "Tower C", detected_at: new Date(Date.now() - 7200000).toISOString() },
    { id: "4", type: "power_overload", severity: "high", status: "action_planned", tower_name: "Tower A", detected_at: new Date(Date.now() - 10800000).toISOString() },
    { id: "5", type: "water_shortage", severity: "critical", status: "escalated", tower_name: "Tower B", detected_at: new Date(Date.now() - 14400000).toISOString() },
  ],
  incident_trend: [
    { date: "Mon", count: 4 }, { date: "Tue", count: 9 }, { date: "Wed", count: 6 },
    { date: "Thu", count: 14 }, { date: "Fri", count: 10 }, { date: "Sat", count: 5 }, { date: "Sun", count: 3 },
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

const SEV_COLORS: Record<string, string> = {
  critical: "bg-rose-500 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-violet-500 text-white",
  low: "bg-sky-500 text-white",
};
const STATUS_COLORS: Record<string, string> = {
  detected: "bg-sky-100 text-sky-700 border border-sky-200",
  analyzing: "bg-violet-100 text-violet-700 border border-violet-200",
  action_planned: "bg-cyan-100 text-cyan-700 border border-cyan-200",
  in_progress: "bg-orange-100 text-orange-700 border border-orange-200",
  resolved: "bg-emerald-100 text-emerald-700 border border-emerald-200",
  escalated: "bg-rose-100 text-rose-700 border border-rose-200",
};

export default function Dashboard() {
  const { token, user } = useAuth();
  const [data, setData] = useState<DashboardOut>(MOCK);
  const [resolved, setResolved] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!token) return;
    dashboardApi.getSummary(token).then(setData).catch(() => setData(MOCK));
  }, [token]);

  const kpis = [
    { label: "Total Incidents", value: data.kpi.total_incidents, sub: "This month", icon: Activity, gradient: "from-violet-600 to-indigo-600", shadow: "shadow-violet-500/25" },
    { label: "Active Now", value: data.kpi.active_incidents, sub: "In pipeline", icon: Flame, gradient: "from-orange-500 to-rose-500", shadow: "shadow-orange-500/25" },
    { label: "Critical", value: data.kpi.critical_incidents, sub: "Needs action", icon: AlertTriangle, gradient: "from-rose-500 to-pink-600", shadow: "shadow-rose-500/25" },
    { label: "Resolved Today", value: data.kpi.resolved_today, sub: "Avg 42m", icon: CheckCircle2, gradient: "from-emerald-500 to-teal-500", shadow: "shadow-emerald-500/25" },
  ];

  return (
    <div className="min-h-screen bg-[#f5f5f7] p-6 lg:p-8 animate-fade-in space-y-7">

      {/* ── Hero Header ──────────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#1e1b4b] via-[#312e81] to-[#1e3a5f] p-7 text-white">
        {/* Decorative circles */}
        <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-violet-500/20 blur-3xl" />
        <div className="absolute -bottom-16 -left-10 w-56 h-56 rounded-full bg-sky-400/15 blur-3xl" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div>
            <p className="text-violet-300 text-xs font-semibold tracking-wider uppercase mb-1">AI Society Operations Center</p>
            <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight">
              Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening"}, {user?.full_name?.split(" ")[0] || "Admin"} 👋
            </h1>
            <p className="text-sm text-violet-200/70 mt-1 max-w-xl">
              Real-time autonomous incident triage across 4 towers, 505 apartments.
            </p>
          </div>
          <div className="flex gap-2.5">
            <Link href="/incidents"
              className="px-4 py-2.5 rounded-xl bg-white text-[#1e1b4b] font-bold text-xs hover:bg-violet-50 transition flex items-center gap-2 shadow-lg">
              <Zap className="w-4 h-4 text-violet-600" /> View Incidents
            </Link>
            <Link href="/analytics"
              className="px-4 py-2.5 rounded-xl bg-white/10 backdrop-blur border border-white/10 text-white font-bold text-xs hover:bg-white/20 transition flex items-center gap-2">
              <TrendingUp className="w-4 h-4" /> Analytics
            </Link>
          </div>
        </div>
      </div>

      {/* ── KPI Row ──────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((k) => (
          <div key={k.label} className="premium-card p-5 flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{k.label}</p>
              <p className="text-3xl font-extrabold text-slate-900 tabular-nums">{k.value}</p>
              <p className="text-[11px] text-slate-400 font-medium">{k.sub}</p>
            </div>
            <div className={`p-2.5 rounded-xl bg-gradient-to-br ${k.gradient} shadow-lg ${k.shadow}`}>
              <k.icon className="w-5 h-5 text-white" />
            </div>
          </div>
        ))}
      </div>

      {/* ── Wave Chart ───────────────────────────────────────────────────────── */}
      <div className="premium-card p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-bold text-slate-900">Incident Trend</h2>
            <p className="text-xs text-slate-400 mt-0.5">Weekly velocity curve</p>
          </div>
          <span className="text-[10px] font-bold text-violet-600 bg-violet-50 px-2.5 py-1 rounded-lg border border-violet-100">Live Data</span>
        </div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.incident_trend}>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f2" vertical={false} />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "#1e1b4b", border: "none", borderRadius: 12, color: "#fff", fontSize: 12 }} />
              <Area type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={3} fill="url(#grad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Main Grid ────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left: Incidents + Agent Table */}
        <div className="lg:col-span-2 space-y-6">

          {/* Active Incidents */}
          <div className="premium-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                Active Incidents
              </h2>
              <Link href="/incidents" className="text-xs font-semibold text-violet-600 hover:text-violet-800 flex items-center gap-1">
                All <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-slate-100">
              {data.recent_incidents.map((inc) => {
                const isResolved = resolved[inc.id] || inc.status === "resolved";
                return (
                  <div key={inc.id} className="py-3.5 flex items-center justify-between gap-3 first:pt-0 last:pb-0">
                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[13px] font-bold text-slate-900 truncate">
                          {inc.type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                        </span>
                        <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                          {inc.tower_name}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${SEV_COLORS[inc.severity] || "bg-slate-400 text-white"}`}>
                          {inc.severity}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {new Date(inc.detected_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md capitalize ${STATUS_COLORS[isResolved ? "resolved" : inc.status] || ""}`}>
                        {(isResolved ? "resolved" : inc.status).replace(/_/g, " ")}
                      </span>
                      {!isResolved && (
                        <button onClick={() => setResolved(p => ({ ...p, [inc.id]: true }))}
                          className="px-3 py-1.5 rounded-lg bg-[#1e1b4b] hover:bg-[#312e81] text-white text-[11px] font-bold transition cursor-pointer">
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Agent Execution */}
          <div className="premium-card p-6 space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Bot className="w-4 h-4 text-violet-600" />
              Agent Execution Metrics
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[12px]">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                    <th className="pb-2.5">Agent</th><th className="pb-2.5">Runs</th><th className="pb-2.5">Latency</th><th className="pb-2.5">Success</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {data.agent_activity.map((ag) => (
                    <tr key={ag.agent_name} className="hover:bg-slate-50/50">
                      <td className="py-2.5 font-semibold text-slate-800">{ag.agent_name}</td>
                      <td className="py-2.5 text-slate-600">{ag.executions_today}</td>
                      <td className="py-2.5 font-mono text-violet-600 font-semibold">{ag.avg_execution_time_ms}ms</td>
                      <td className="py-2.5">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${ag.success_rate >= 1 ? "bg-emerald-100 text-emerald-700" : "bg-orange-100 text-orange-700"}`}>
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

        {/* Right Column */}
        <div className="space-y-6">

          {/* Severity */}
          <div className="premium-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Severity Breakdown</h3>
            {Object.entries(data.severity_distribution).map(([sev, count]) => {
              const total = Object.values(data.severity_distribution).reduce((a, b) => a + b, 0);
              const pct = Math.round((count / total) * 100);
              const barColor: Record<string, string> = { critical: "bg-rose-500", high: "bg-orange-500", medium: "bg-violet-500", low: "bg-sky-500" };
              return (
                <div key={sev} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] font-semibold text-slate-700 capitalize">{sev}</span>
                    <span className="text-[12px] font-bold text-slate-900">{count} <span className="text-slate-400 font-normal">({pct}%)</span></span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${barColor[sev] || "bg-slate-400"} transition-all duration-500`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Contractors */}
          <div className="premium-card p-6 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Top Contractors</h3>
              <Link href="/contractors" className="text-[11px] font-semibold text-violet-600">View All</Link>
            </div>
            {[
              { name: "Apex Plumbing", specialty: "Hydraulics", rating: 4.9, color: "from-sky-500 to-cyan-500" },
              { name: "Voltaic Power", specialty: "Electrical", rating: 4.8, color: "from-amber-500 to-orange-500" },
              { name: "RapidRepair", specialty: "Emergency", rating: 4.7, color: "from-violet-500 to-indigo-500" },
            ].map((c, i) => (
              <div key={c.name} className="flex items-center gap-3 py-2">
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${c.color} flex items-center justify-center text-white text-[11px] font-bold shadow-sm`}>
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] font-semibold text-slate-900 truncate">{c.name}</p>
                  <p className="text-[10px] text-slate-400">{c.specialty}</p>
                </div>
                <span className="text-[12px] font-bold text-amber-500">★ {c.rating}</span>
              </div>
            ))}
          </div>

          {/* Quick Links */}
          <div className="premium-card p-5 space-y-2">
            <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Quick Links</h3>
            {[
              { label: "Sensor Telemetry", href: "/sensor-buffer", color: "text-sky-600 bg-sky-50" },
              { label: "LLM Judge Rubric", href: "/analytics", color: "text-violet-600 bg-violet-50" },
              { label: "System Settings", href: "/settings", color: "text-slate-600 bg-slate-100" },
            ].map((lk) => (
              <Link key={lk.href} href={lk.href}
                className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-50 transition text-[12px] font-semibold text-slate-700 group">
                <span className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${lk.color.includes("sky") ? "bg-sky-500" : lk.color.includes("violet") ? "bg-violet-500" : "bg-slate-400"}`} />
                  {lk.label}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-violet-500 transition" />
              </Link>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}
