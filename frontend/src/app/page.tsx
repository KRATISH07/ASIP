"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import { dashboardApi, type DashboardOut } from "@/lib/api";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  TrendingUp, Bot, ArrowRight, HardHat, Check,
  ArrowUpRight, Zap, ExternalLink
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
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

const SEV: Record<string, string> = {
  critical: "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/30",
  high: "bg-orange-500/20 text-orange-400 ring-1 ring-orange-500/30",
  medium: "bg-violet-500/20 text-violet-400 ring-1 ring-violet-500/30",
  low: "bg-sky-500/20 text-sky-400 ring-1 ring-sky-500/30",
};
const STAT: Record<string, string> = {
  detected: "text-sky-400",
  analyzing: "text-violet-400",
  action_planned: "text-cyan-400",
  in_progress: "text-amber-400",
  resolved: "text-emerald-400",
  escalated: "text-rose-400",
};

export default function Dashboard() {
  const { token, user } = useAuth();
  const [data, setData] = useState<DashboardOut>(MOCK);
  const [resolved, setResolved] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!token) return;
    dashboardApi.getSummary(token).then(setData).catch(() => setData(MOCK));
  }, [token]);

  const greeting = new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening";

  return (
    <div className="min-h-screen bg-[#09090b] p-5 lg:p-7 animate-fade-in space-y-6">

      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <p className="text-zinc-500 text-xs font-medium mb-1">Good {greeting}</p>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            {user?.full_name?.split(" ")[0] || "Admin"}&apos;s Dashboard
          </h1>
        </div>
        <div className="flex gap-2">
          <Link href="/incidents"
            className="px-3.5 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold transition flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" /> New Incident
          </Link>
          <Link href="/notifications"
            className="px-3.5 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-zinc-300 text-xs font-medium border border-white/[0.06] transition flex items-center gap-1.5">
            Broadcast Alert
          </Link>
        </div>
      </div>

      {/* ── KPI Row (All Clickable) ──────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {([
          { label: "Total Incidents", value: data.kpi.total_incidents, delta: "+12%", deltaUp: true, href: "/incidents", icon: Activity, color: "text-violet-400", glow: "violet" },
          { label: "Active Now", value: data.kpi.active_incidents, delta: "In pipeline", deltaUp: false, href: "/incidents", icon: Flame, color: "text-orange-400", glow: "orange" },
          { label: "Critical", value: data.kpi.critical_incidents, delta: "Needs action", deltaUp: false, href: "/incidents", icon: AlertTriangle, color: "text-rose-400", glow: "rose" },
          { label: "Resolved Today", value: data.kpi.resolved_today, delta: "Avg 42min", deltaUp: false, href: "/analytics", icon: CheckCircle2, color: "text-emerald-400", glow: "emerald" },
        ] as const).map((k) => (
          <Link key={k.label} href={k.href} className="glass-card-clickable p-4 group block">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">{k.label}</span>
              <k.icon className={`w-4 h-4 ${k.color} opacity-60 group-hover:opacity-100 transition`} />
            </div>
            <p className="text-2xl font-bold text-white tabular-nums">{k.value}</p>
            <p className="text-[10px] text-zinc-500 mt-1 flex items-center gap-1">
              {k.deltaUp && <TrendingUp className="w-3 h-3 text-emerald-500" />}
              {k.delta}
            </p>
          </Link>
        ))}
      </div>

      {/* ── Chart + Severity (Side by Side) ──────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
        
        {/* Chart - 3 cols */}
        <Link href="/analytics" className="lg:col-span-3 glass-card-clickable p-5 block group">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-zinc-200">Incident Trend</h2>
              <p className="text-[10px] text-zinc-500 mt-0.5">7-day velocity curve</p>
            </div>
            <ArrowUpRight className="w-4 h-4 text-zinc-600 group-hover:text-violet-400 transition" />
          </div>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.incident_trend}>
                <defs>
                  <linearGradient id="grd" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#3f3f46" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#3f3f46" fontSize={10} tickLine={false} axisLine={false} width={24} />
                <Tooltip contentStyle={{ background: "#18181b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#e4e4e7", fontSize: 11 }} />
                <Area type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2.5} fill="url(#grd)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Link>

        {/* Severity - 2 cols */}
        <Link href="/analytics" className="lg:col-span-2 glass-card-clickable p-5 block group">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-zinc-200">Severity</h2>
            <ArrowUpRight className="w-4 h-4 text-zinc-600 group-hover:text-violet-400 transition" />
          </div>
          <div className="space-y-3">
            {Object.entries(data.severity_distribution).map(([sev, count]) => {
              const total = Object.values(data.severity_distribution).reduce((a, b) => a + b, 0);
              const pct = Math.round((count / total) * 100);
              const bar: Record<string, string> = { critical: "bg-rose-500", high: "bg-orange-500", medium: "bg-violet-500", low: "bg-sky-500" };
              return (
                <div key={sev}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-medium text-zinc-400 capitalize">{sev}</span>
                    <span className="text-[11px] font-semibold text-zinc-300">{count} <span className="text-zinc-600">({pct}%)</span></span>
                  </div>
                  <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${bar[sev]} transition-all duration-700`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Link>
      </div>

      {/* ── Incidents + Right Col ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">

        {/* Incidents List */}
        <div className="lg:col-span-2 glass-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
              Active Incidents
            </h2>
            <Link href="/incidents" className="text-[11px] font-medium text-violet-400 hover:text-violet-300 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-1">
            {data.recent_incidents.map((inc) => {
              const done = resolved[inc.id] || inc.status === "resolved";
              return (
                <div key={inc.id}
                  className="flex items-center justify-between gap-3 p-3 rounded-lg hover:bg-white/[0.03] transition group">
                  <Link href="/incidents" className="min-w-0 flex-1 space-y-1 block">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[12px] font-semibold text-zinc-200 group-hover:text-white transition truncate">
                        {inc.type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                      </span>
                      <span className="text-[9px] font-medium text-zinc-600 bg-white/[0.05] px-1.5 py-0.5 rounded">{inc.tower_name}</span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${SEV[inc.severity]}`}>{inc.severity}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px]">
                      <span className={`font-medium capitalize ${STAT[done ? "resolved" : inc.status] || "text-zinc-500"}`}>
                        {(done ? "resolved" : inc.status).replace(/_/g, " ")}
                      </span>
                      <span className="text-zinc-700">•</span>
                      <span className="text-zinc-600">{new Date(inc.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </Link>
                  {!done && (
                    <button onClick={(e) => { e.preventDefault(); setResolved(p => ({ ...p, [inc.id]: true })); }}
                      className="px-2.5 py-1 rounded-md bg-white/[0.06] hover:bg-violet-500/20 text-[10px] font-semibold text-zinc-400 hover:text-violet-300 border border-white/[0.06] hover:border-violet-500/30 transition cursor-pointer flex-shrink-0">
                      Resolve
                    </button>
                  )}
                  {done && (
                    <span className="text-[10px] font-medium text-emerald-500 flex items-center gap-1 flex-shrink-0">
                      <Check className="w-3 h-3" /> Done
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Agents + Contractors */}
        <div className="space-y-3">

          {/* Agent Metrics */}
          <Link href="/agent-logs" className="glass-card-clickable p-5 block group space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
                <Bot className="w-4 h-4 text-violet-400" /> Agents
              </h2>
              <ArrowUpRight className="w-4 h-4 text-zinc-600 group-hover:text-violet-400 transition" />
            </div>
            <div className="space-y-2">
              {data.agent_activity.slice(0, 4).map((ag) => (
                <div key={ag.agent_name} className="flex items-center justify-between">
                  <span className="text-[11px] text-zinc-400 truncate flex-1">{ag.agent_name.replace("Agent", "")}</span>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-[10px] font-mono text-violet-400">{ag.avg_execution_time_ms}ms</span>
                    <span className={`text-[10px] font-semibold ${ag.success_rate >= 1 ? "text-emerald-400" : "text-amber-400"}`}>
                      {(ag.success_rate * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-zinc-600 pt-1 border-t border-white/[0.04]">
              +{data.agent_activity.length - 4} more agents →
            </p>
          </Link>

          {/* Top Contractors */}
          <Link href="/contractors" className="glass-card-clickable p-5 block group space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
                <HardHat className="w-4 h-4 text-orange-400" /> Contractors
              </h2>
              <ArrowUpRight className="w-4 h-4 text-zinc-600 group-hover:text-violet-400 transition" />
            </div>
            {[
              { name: "Apex Plumbing", spec: "Hydraulics", r: 4.9, c: "from-sky-500 to-cyan-500" },
              { name: "Voltaic Power", spec: "Electrical", r: 4.8, c: "from-amber-500 to-orange-500" },
              { name: "RapidRepair", spec: "Emergency", r: 4.7, c: "from-violet-500 to-fuchsia-500" },
            ].map((ct, i) => (
              <div key={ct.name} className="flex items-center gap-2.5">
                <div className={`w-6 h-6 rounded-md bg-gradient-to-br ${ct.c} flex items-center justify-center text-[9px] font-bold text-white`}>
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-medium text-zinc-300 truncate">{ct.name}</p>
                  <p className="text-[9px] text-zinc-600">{ct.spec}</p>
                </div>
                <span className="text-[11px] font-semibold text-amber-400">★ {ct.r}</span>
              </div>
            ))}
          </Link>

          {/* Quick Nav */}
          <div className="glass-card p-4 space-y-1">
            {[
              { label: "Sensor Telemetry", href: "/sensor-buffer" },
              { label: "Resident Complaints", href: "/complaints" },
              { label: "System Settings", href: "/settings" },
            ].map((lk) => (
              <Link key={lk.href} href={lk.href}
                className="flex items-center justify-between py-2 px-2 rounded-md hover:bg-white/[0.04] transition text-[11px] font-medium text-zinc-500 hover:text-zinc-300 group">
                {lk.label}
                <ArrowRight className="w-3 h-3 text-zinc-700 group-hover:text-violet-400 transition" />
              </Link>
            ))}
          </div>

        </div>
      </div>

    </div>
  );
}
