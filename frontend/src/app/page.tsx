"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import { dashboardApi, incidentsApi, type DashboardOut, type IncidentOut } from "@/lib/api";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  Zap, Droplets, TrendingUp, Bot, ArrowRight, ExternalLink,
  ShieldCheck, Wrench, Building2, Bell, Sparkles, HardHat, Check
} from "lucide-react";

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
    { date: "Tue", count: 8 },
    { date: "Wed", count: 6 },
    { date: "Thu", count: 12 },
    { date: "Fri", count: 9 },
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
  title, value, subtitle, icon: Icon, badgeColor
}: {
  title: string; value: number | string; subtitle?: string;
  icon: React.ElementType; badgeColor: string;
}) {
  return (
    <div className="pearl-card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">{title}</p>
        <div className={`p-2.5 rounded-2xl border ${badgeColor}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div>
        <p className="text-4xl font-extrabold text-slate-900 tracking-tight tabular-nums">{value}</p>
        {subtitle && <p className="mt-1 text-xs font-medium text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-rose-100 text-rose-800 border-rose-200 font-bold",
    high: "bg-amber-100 text-amber-900 border-amber-300 font-bold",
    medium: "bg-yellow-100 text-yellow-900 border-yellow-300 font-semibold",
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
    analyzing: "bg-violet-100 text-violet-800 font-bold border border-violet-200",
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

export default function OriginalDashboardRestored() {
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
    <div className="min-h-screen bg-[#f4f6f8] p-6 lg:p-8 animate-fade-in space-y-8">
      
      {/* Top Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 rounded-3xl p-6 shadow-md shadow-slate-200/50">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-900 border border-teal-300">
              🏛️ ASIP Operations Center
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
              System Active
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight mt-2">
            Operations & AI Society Intelligence
          </h1>
          <p className="text-xs lg:text-sm text-slate-500 mt-1 font-medium">
            Welcome back, <strong className="text-slate-800">{user?.full_name || "Administrator"}</strong>. Real-time autonomous triage & predictive analysis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/incidents"
            className="px-4 py-2.5 rounded-2xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-md shadow-teal-600/20 transition flex items-center gap-2"
          >
            <Activity className="w-4 h-4" />
            Incidents Triage
          </Link>
          <Link
            href="/contractors"
            className="px-4 py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs border border-slate-300 transition flex items-center gap-2"
          >
            <HardHat className="w-4 h-4 text-teal-600" />
            Contractors
          </Link>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          title="Total Incidents"
          value={data.kpi.total_incidents}
          subtitle="All logged events"
          icon={Activity}
          badgeColor="bg-teal-50 text-teal-600 border-teal-200"
        />
        <KPICard
          title="Active Incidents"
          value={data.kpi.active_incidents}
          subtitle="In triage / progress"
          icon={Flame}
          badgeColor="bg-amber-50 text-amber-600 border-amber-200"
        />
        <KPICard
          title="Critical Alerts"
          value={data.kpi.critical_incidents}
          subtitle="Requires immediate action"
          icon={AlertTriangle}
          badgeColor="bg-rose-50 text-rose-600 border-rose-200"
        />
        <KPICard
          title="Resolved Today"
          value={data.kpi.resolved_today}
          subtitle="Successfully closed"
          icon={CheckCircle2}
          badgeColor="bg-emerald-50 text-emerald-600 border-emerald-200"
        />
      </div>

      {/* Main Grid: Incidents & Agent Executions (Left) + Distribution & Contractors (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Recent Incidents Card */}
          <div className="pearl-card p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                  <Flame className="w-5 h-5 text-teal-600" />
                  Recent Active Incidents
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">Live events being processed by autonomous agent pipeline.</p>
              </div>
              <Link href="/incidents" className="text-xs font-bold text-teal-600 hover:text-teal-700 flex items-center gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {data.recent_incidents.map((inc) => (
                <div key={inc.id} className="p-4 rounded-2xl bg-slate-50/70 border border-slate-200/80 flex items-center justify-between gap-4">
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-sm text-slate-900 truncate">
                        {inc.type.replace(/_/g, " ").toUpperCase()}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-200 text-slate-700">
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
                        className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition cursor-pointer"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Agent Activity Table */}
          <div className="pearl-card p-6 space-y-5">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="text-lg font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <Bot className="w-5 h-5 text-teal-600" />
                LangGraph Multi-Agent Execution Metrics
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">Execution stats across autonomous diagnostic nodes today.</p>
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
                    <tr key={ag.agent_name} className="hover:bg-slate-50">
                      <td className="py-3 font-bold text-slate-900">{ag.agent_name}</td>
                      <td className="py-3">{ag.executions_today}</td>
                      <td className="py-3 font-mono">{ag.avg_execution_time_ms} ms</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
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
          
          {/* Severity Distribution */}
          <div className="pearl-card p-6 space-y-4">
            <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
              <TrendingUp className="w-4 h-4 text-teal-600" />
              Incident Severity Distribution
            </h3>

            <div className="space-y-3">
              {Object.entries(data.severity_distribution).map(([sev, count]) => (
                <div key={sev} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={sev} />
                  </div>
                  <span className="font-extrabold text-sm text-slate-900">{count} events</span>
                </div>
              ))}
            </div>
          </div>

          {/* Ranked Contractors Snapshot */}
          <div className="pearl-card p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
                <HardHat className="w-4 h-4 text-teal-600" />
                Ranked Contractors
              </h3>
              <Link href="/contractors" className="text-xs font-bold text-teal-600 hover:text-teal-700">
                View All
              </Link>
            </div>

            <div className="space-y-3">
              {[
                { name: "Apex Plumbing & Pumps", specialty: "Hydraulic Systems", rating: 4.9 },
                { name: "Voltaic Power Solutions", specialty: "Electrical Substation", rating: 4.8 },
                { name: "RapidRepair Elite", specialty: "Emergency Repair", rating: 4.7 },
              ].map((c, i) => (
                <div key={c.name} className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-xs text-slate-900">#{i + 1} {c.name}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{c.specialty}</p>
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
