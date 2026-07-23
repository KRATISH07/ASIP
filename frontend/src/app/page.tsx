"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import { dashboardApi, type DashboardOut } from "@/lib/api";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  Zap, Droplets, TrendingUp, Bot, ArrowRight, ExternalLink,
  ShieldCheck, Wrench, Building2, Bell, Sparkles, HardHat, Check,
  Waves, ArrowUpRight, Sparkle
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

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-600 text-white font-extrabold shadow-sm",
    high: "bg-amber-500 text-white font-extrabold shadow-sm",
    medium: "bg-purple-600 text-white font-bold shadow-sm",
    low: "bg-emerald-600 text-white font-bold shadow-sm",
  };
  return (
    <span className={`inline-flex items-center rounded-lg px-2.5 py-0.5 text-[10px] uppercase tracking-wider ${colors[severity] || "bg-stone-600 text-white"}`}>
      {severity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    detected: "bg-blue-600 text-white font-bold shadow-sm",
    analyzing: "bg-indigo-600 text-white font-bold shadow-sm",
    action_planned: "bg-teal-600 text-white font-bold shadow-sm",
    in_progress: "bg-amber-500 text-white font-bold shadow-sm",
    resolved: "bg-emerald-600 text-white font-bold shadow-sm",
    escalated: "bg-rose-600 text-white font-bold shadow-sm",
  };
  return (
    <span className={`inline-flex items-center rounded-lg px-2.5 py-1 text-[10px] capitalize ${colors[status] || "bg-stone-600 text-white"}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

export default function VibrantPopDashboard() {
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
    <div className="min-h-screen bg-[#ecfdf5] p-6 lg:p-10 animate-fade-in space-y-8">
      
      {/* ── 1. Vibrant Gradient Header Banner ───────────────────────────────── */}
      <div className="relative overflow-hidden bg-gradient-to-r from-emerald-800 via-teal-800 to-indigo-900 rounded-3xl p-8 shadow-2xl text-white space-y-4">
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-96 h-96 bg-amber-400/20 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="px-3.5 py-1 rounded-full text-xs font-black bg-amber-400 text-slate-950 shadow-md uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-slate-950" />
                Vibrant AI Operations
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-400/20 text-emerald-200 border border-emerald-400/40">
                ● Live Hardware Telemetry
              </span>
            </div>
            <h1 className="text-3xl lg:text-4xl font-black tracking-tight text-white">
              AI Society Operations & Wave Analytics
            </h1>
            <p className="text-xs lg:text-sm text-emerald-100/90 font-medium max-w-2xl">
              Welcome back, <strong className="text-amber-300 font-bold">{user?.full_name || "Administrator"}</strong>. Autonomous LangGraph pipeline triaging incidents across 4 towers.
            </p>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <Link
              href="/incidents"
              className="px-5 py-3 rounded-2xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs shadow-lg transition flex items-center gap-2"
            >
              <Activity className="w-4 h-4" />
              Incidents Triage
            </Link>
            <Link
              href="/analytics"
              className="px-5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs border border-white/20 backdrop-blur-md transition flex items-center gap-2"
            >
              <TrendingUp className="w-4 h-4 text-emerald-300" />
              AI Analytics
            </Link>
          </div>
        </div>
      </div>

      {/* ── 2. High-Noticeability Solid Color KPI Cards ─────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Card 1: Vibrant Emerald */}
        <div className="rounded-3xl bg-gradient-to-br from-emerald-600 to-teal-700 p-6 shadow-xl text-white space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-emerald-100 uppercase tracking-wider">Total Handled</span>
            <div className="p-3 rounded-2xl bg-white/20 backdrop-blur-md">
              <Activity className="h-6 w-6 text-white" />
            </div>
          </div>
          <div>
            <p className="text-4xl font-black tracking-tight tabular-nums">{data.kpi.total_incidents}</p>
            <p className="mt-1 text-xs font-semibold text-emerald-100">All logged events this month</p>
          </div>
        </div>

        {/* Card 2: Sunset Amber Gold */}
        <div className="rounded-3xl bg-gradient-to-br from-amber-500 to-orange-600 p-6 shadow-xl text-white space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-amber-100 uppercase tracking-wider">Active Alerts</span>
            <div className="p-3 rounded-2xl bg-white/20 backdrop-blur-md">
              <Flame className="h-6 w-6 text-white" />
            </div>
          </div>
          <div>
            <p className="text-4xl font-black tracking-tight tabular-nums">{data.kpi.active_incidents}</p>
            <p className="mt-1 text-xs font-semibold text-amber-100">Currently in triage pipeline</p>
          </div>
        </div>

        {/* Card 3: Electric Coral Rose */}
        <div className="rounded-3xl bg-gradient-to-br from-rose-600 to-pink-700 p-6 shadow-xl text-white space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-rose-100 uppercase tracking-wider">Critical Alerts</span>
            <div className="p-3 rounded-2xl bg-white/20 backdrop-blur-md">
              <AlertTriangle className="h-6 w-6 text-white" />
            </div>
          </div>
          <div>
            <p className="text-4xl font-black tracking-tight tabular-nums">{data.kpi.critical_incidents}</p>
            <p className="mt-1 text-xs font-semibold text-rose-100">Immediate attention needed</p>
          </div>
        </div>

        {/* Card 4: Royal Sapphire Indigo */}
        <div className="rounded-3xl bg-gradient-to-br from-indigo-600 to-blue-700 p-6 shadow-xl text-white space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-indigo-100 uppercase tracking-wider">Resolved Today</span>
            <div className="p-3 rounded-2xl bg-white/20 backdrop-blur-md">
              <CheckCircle2 className="h-6 w-6 text-white" />
            </div>
          </div>
          <div>
            <p className="text-4xl font-black tracking-tight tabular-nums">{data.kpi.resolved_today}</p>
            <p className="mt-1 text-xs font-semibold text-indigo-100">Closed automatically</p>
          </div>
        </div>

      </div>

      {/* ── 3. High-Contrast Dynamic Wave Chart Card ────────────────────────── */}
      <div className="vibrant-card p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-black text-emerald-950 tracking-tight flex items-center gap-2.5">
              <TrendingUp className="w-6 h-6 text-emerald-600" />
              Weekly Incident Velocity Wave Curve
            </h2>
            <p className="text-xs font-medium text-emerald-800/80 mt-1">Real-time incident frequency wave distribution over time.</p>
          </div>
          <span className="px-3.5 py-1.5 rounded-xl text-xs font-black bg-emerald-600 text-white shadow-sm">
            High-Contrast Wave
          </span>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.incident_trend}>
              <defs>
                <linearGradient id="vibrantWaveGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#a7f3d0" vertical={false} />
              <XAxis dataKey="date" stroke="#065f46" fontSize={12} fontWeight="bold" tickLine={false} axisLine={false} />
              <YAxis stroke="#065f46" fontSize={12} fontWeight="bold" tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "#064e3b", borderRadius: "14px", border: "2px solid #34d399", color: "#fff", fontSize: "12px", fontWeight: "bold" }} />
              <Area type="monotone" dataKey="count" stroke="#059669" strokeWidth={4} fillOpacity={1} fill="url(#vibrantWaveGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── 4. Main Grid: Active Incidents & Agent Executions ───────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Columns */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Active Incidents List */}
          <div className="vibrant-card p-7 space-y-5">
            <div className="flex items-center justify-between border-b border-emerald-100 pb-4">
              <div>
                <h2 className="text-lg font-black text-emerald-950 tracking-tight flex items-center gap-2">
                  <Flame className="w-5 h-5 text-emerald-600" />
                  Recent Active Incidents Triage
                </h2>
                <p className="text-xs text-emerald-800/80 mt-0.5 font-medium">Live incidents being triaged by autonomous AI pipeline.</p>
              </div>
              <Link href="/incidents" className="text-xs font-black text-emerald-700 hover:text-emerald-900 flex items-center gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {data.recent_incidents.map((inc) => (
                <div key={inc.id} className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200/90 flex items-center justify-between gap-4">
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-black text-sm text-emerald-950 truncate">
                        {inc.type.replace(/_/g, " ").toUpperCase()}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-black bg-emerald-800 text-white">
                        {inc.tower_name}
                      </span>
                      <SeverityBadge severity={inc.severity} />
                    </div>
                    <p className="text-xs text-emerald-800/70 font-semibold">
                      Detected: {new Date(inc.detected_at).toLocaleTimeString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <StatusBadge status={resolvedMap[inc.id] ? "resolved" : inc.status} />
                    {!resolvedMap[inc.id] && inc.status !== "resolved" && (
                      <button
                        onClick={() => handleResolve(inc.id)}
                        className="px-3.5 py-1.5 rounded-xl bg-emerald-900 hover:bg-emerald-950 text-white font-extrabold text-xs transition cursor-pointer shadow-md"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* LangGraph Agent Execution Metrics */}
          <div className="vibrant-card p-7 space-y-5">
            <div className="border-b border-emerald-100 pb-4">
              <h2 className="text-lg font-black text-emerald-950 tracking-tight flex items-center gap-2">
                <Bot className="w-5 h-5 text-emerald-600" />
                LangGraph Multi-Agent Execution Metrics
              </h2>
              <p className="text-xs text-emerald-800/80 mt-0.5 font-medium">Execution stats across autonomous diagnostic nodes today.</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-emerald-200 text-emerald-900 font-black uppercase tracking-wider">
                    <th className="pb-3">Agent Node</th>
                    <th className="pb-3">Executions</th>
                    <th className="pb-3">Avg Latency</th>
                    <th className="pb-3">Success Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-emerald-100 text-emerald-950 font-bold">
                  {data.agent_activity.map((ag) => (
                    <tr key={ag.agent_name} className="hover:bg-emerald-50/80">
                      <td className="py-3 font-extrabold text-emerald-950">{ag.agent_name}</td>
                      <td className="py-3">{ag.executions_today}</td>
                      <td className="py-3 font-mono text-emerald-700 font-extrabold">{ag.avg_execution_time_ms} ms</td>
                      <td className="py-3">
                        <span className="px-2.5 py-1 rounded-lg text-[10px] font-black bg-emerald-700 text-white">
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
          <div className="vibrant-card p-6 space-y-4">
            <h3 className="font-black text-base text-emerald-950 flex items-center gap-2 border-b border-emerald-100 pb-3">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              Severity Breakdown
            </h3>

            <div className="space-y-3">
              {Object.entries(data.severity_distribution).map(([sev, count]) => (
                <div key={sev} className="flex items-center justify-between p-3 rounded-2xl bg-emerald-50/80 border border-emerald-200/90">
                  <SeverityBadge severity={sev} />
                  <span className="font-black text-sm text-emerald-950">{count} events</span>
                </div>
              ))}
            </div>
          </div>

          {/* Ranked Contractors Snapshot */}
          <div className="vibrant-card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-emerald-100 pb-3">
              <h3 className="font-black text-base text-emerald-950 flex items-center gap-2">
                <HardHat className="w-4 h-4 text-emerald-600" />
                Ranked Contractors
              </h3>
              <Link href="/contractors" className="text-xs font-black text-emerald-700 hover:text-emerald-900">
                View All
              </Link>
            </div>

            <div className="space-y-3">
              {[
                { name: "Apex Plumbing & Pumps", specialty: "Hydraulic Systems", rating: 4.9 },
                { name: "Voltaic Power Solutions", specialty: "Electrical Substation", rating: 4.8 },
                { name: "RapidRepair Elite", specialty: "Emergency Repair", rating: 4.7 },
              ].map((c, i) => (
                <div key={c.name} className="p-3 rounded-2xl bg-emerald-50/80 border border-emerald-200/90 flex items-center justify-between">
                  <div>
                    <p className="font-extrabold text-xs text-emerald-950">#{i + 1} {c.name}</p>
                    <p className="text-[10px] text-emerald-800 font-semibold mt-0.5">{c.specialty}</p>
                  </div>
                  <span className="text-xs font-black bg-amber-400 text-slate-950 px-2 py-0.5 rounded-lg shadow-xs">★ {c.rating}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
