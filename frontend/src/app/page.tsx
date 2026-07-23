"use client";

import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import {
  AlertTriangle, CheckCircle2, Flame, Activity,
  Zap, Droplets, TrendingUp, Bot, ArrowRight,
  ShieldCheck, Wrench, Building2, Bell, Sparkles,
  Users, RefreshCw, ChevronRight, PlusCircle, Check,
  HardHat
} from "lucide-react";

// Mock Management Data (Runs 100% Client-Side with 0 DB overhead)
const TOWERS = [
  { id: "A", name: "Tower A (Orchid)", residents: 120, status: "warning", issue: "Water Pressure Drop (3.1 bar)", health: 92 },
  { id: "B", name: "Tower B (Lotus)", residents: 145, status: "healthy", issue: "All Systems Normal", health: 98 },
  { id: "C", name: "Tower C (Jasmine)", residents: 110, status: "healthy", issue: "All Systems Normal", health: 100 },
  { id: "D", name: "Tower D (Tulip)", residents: 130, status: "healthy", issue: "All Systems Normal", health: 96 },
];

const RECENT_INCIDENTS = [
  {
    id: "INC-8492",
    title: "Water Pressure Drop on Upper Floors",
    tower: "Tower A (Orchid)",
    severity: "high",
    status: "in_progress",
    category: "Plumbing & Hydraulics",
    ai_summary: "Infrastructure Agent identified booster pump #2 pressure regulator failure. Auto-assigned to Apex Plumbing.",
    contractor: "Apex Plumbing & Pumps",
    cost_est: "$450 - $600",
    time_est: "1.5 hrs",
    time_ago: "14 mins ago"
  },
  {
    id: "INC-8490",
    title: "Transformer Phase B Voltage Spike",
    tower: "Tower D (Tulip)",
    severity: "medium",
    status: "analyzing",
    category: "Electrical Substation",
    ai_summary: "Monitoring Agent detected 435V surge. Decision Agent recommended automated load balancing check.",
    contractor: "Voltaic Power Solutions",
    cost_est: "$200 - $350",
    time_est: "45 mins",
    time_ago: "42 mins ago"
  },
  {
    id: "INC-8488",
    title: "Elevator #2 Emergency Brake Sensor Alert",
    tower: "Tower B (Lotus)",
    severity: "low",
    status: "resolved",
    category: "Elevator Systems",
    ai_summary: "Routine sensor check passed. Reset command issued via IoT Edge Gateway successfully.",
    contractor: "ElevateX Maintenance",
    cost_est: "$0 (Covered under AMC)",
    time_est: "Resolved",
    time_ago: "2 hrs ago"
  }
];

const TOP_CONTRACTORS = [
  { name: "Apex Plumbing & Pumps", specialty: "Hydraulic & Water Systems", rating: 4.9, jobs: 42, speed: "Fast (< 1 hr)" },
  { name: "Voltaic Power Solutions", specialty: "High Voltage Electrical", rating: 4.8, jobs: 38, speed: "24/7 Priority" },
  { name: "RapidRepair Elite", specialty: "Civil & Emergency Repair", rating: 4.7, jobs: 55, speed: "Same-Day" },
];

const AI_AGENT_LOGS = [
  { time: "14 mins ago", agent: "InfrastructureAgent", action: "Diagnosed Booster Pump #2 regulator anomaly in Tower A." },
  { time: "18 mins ago", agent: "ContractorAgent", action: "Ranked Apex Plumbing #1 using Thompson Sampling (Confidence: 94%)." },
  { time: "22 mins ago", agent: "CommunicationAgent", action: "Sent push notification to 120 residents of Tower A." },
  { time: "45 mins ago", agent: "DecisionAgent", action: "Auto-dispatched voltage stabilizer check for Substation D." },
];

export default function OperationsDashboard() {
  const { user } = useAuth();
  const [incidents, setIncidents] = useState(RECENT_INCIDENTS);
  const [resolvedCount, setResolvedCount] = useState(1);
  const [actionDone, setActionDone] = useState<Record<string, boolean>>({});

  const handleResolve = (id: string) => {
    setActionDone(prev => ({ ...prev, [id]: true }));
    setIncidents(prev => prev.map(inc => inc.id === id ? { ...inc, status: "resolved" } : inc));
    setResolvedCount(c => c + 1);
  };

  return (
    <div className="min-h-screen bg-[#faf4e8] p-6 lg:p-8 animate-fade-in space-y-8">
      
      {/* ── Top Header & Live Society Health Bar ──────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-amber-200/80 rounded-3xl p-6 shadow-xl shadow-amber-900/5">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300/70">
              🏛️ Greenwood Heights Society
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
              Live AI Operations Center
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-black text-stone-900 tracking-tight mt-2">
            Welcome back, {user?.full_name || "Society Administrator"} 👋
          </h1>
          <p className="text-xs lg:text-sm text-stone-500 mt-1 font-medium">
            Autonomous multi-agent system monitoring 4 towers, 505 apartments, and 12 IoT sensor gateways.
          </p>
        </div>

        {/* Quick Action Button */}
        <div className="flex items-center gap-3">
          <Link
            href="/incidents"
            className="px-4 py-2.5 rounded-2xl bg-gradient-to-r from-amber-500 to-yellow-600 hover:from-amber-600 hover:to-yellow-700 text-white font-bold text-xs shadow-md shadow-amber-500/20 transition flex items-center gap-2 cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            Report Issue
          </Link>
          <Link
            href="/notifications"
            className="px-4 py-2.5 rounded-2xl bg-stone-100 hover:bg-stone-200 text-stone-800 font-bold text-xs border border-stone-300/70 transition flex items-center gap-2"
          >
            <Bell className="w-4 h-4 text-amber-600" />
            Broadcast Alert
          </Link>
        </div>
      </div>

      {/* ── Live Society Utility Status Bar ───────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="mgmt-card p-4 flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-blue-50 text-blue-600 border border-blue-200">
            <Droplets className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Water Supply</p>
            <p className="text-base font-extrabold text-stone-900 mt-0.5">4.2 bar <span className="text-[10px] font-semibold text-emerald-600">(Normal)</span></p>
          </div>
        </div>

        <div className="mgmt-card p-4 flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Power Grid</p>
            <p className="text-base font-extrabold text-stone-900 mt-0.5">415V <span className="text-[10px] font-semibold text-emerald-600">(3-Phase Stable)</span></p>
          </div>
        </div>

        <div className="mgmt-card p-4 flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Security Gates</p>
            <p className="text-base font-extrabold text-stone-900 mt-0.5">2/2 Active <span className="text-[10px] font-semibold text-emerald-600">(Online)</span></p>
          </div>
        </div>

        <div className="mgmt-card p-4 flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-violet-50 text-violet-600 border border-violet-200">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">AI Operations</p>
            <p className="text-base font-extrabold text-stone-900 mt-0.5">6 Agents <span className="text-[10px] font-semibold text-emerald-600">(Autonomous)</span></p>
          </div>
        </div>
      </div>

      {/* ── Main Content Grid: Active Maintenance + Towers & Contractors ───────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Columns: Active Maintenance & Infrastructure Incidents */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-black text-stone-900 tracking-tight flex items-center gap-2">
                <Wrench className="w-5 h-5 text-amber-600" />
                Active Property Maintenance & Incident Triage
              </h2>
              <p className="text-xs text-stone-500 mt-0.5 font-medium">
                Live AI-triaged complaints and infrastructure sensor diagnostics.
              </p>
            </div>
            <Link
              href="/incidents"
              className="text-xs font-bold text-amber-700 hover:text-amber-800 flex items-center gap-1 group"
            >
              View All <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          {/* Incident Cards */}
          <div className="space-y-4">
            {incidents.map((inc) => (
              <div key={inc.id} className="mgmt-card p-5 space-y-4">
                {/* Header row */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-stone-100 text-stone-700 border border-stone-200">
                        {inc.id}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300/80">
                        📍 {inc.tower}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider border ${
                        inc.severity === "critical" ? "bg-red-50 text-red-700 border-red-200" :
                        inc.severity === "high" ? "bg-amber-100 text-amber-800 border-amber-300" :
                        "bg-emerald-50 text-emerald-700 border-emerald-200"
                      }`}>
                        {inc.severity} priority
                      </span>
                    </div>
                    <h3 className="text-base font-extrabold text-stone-900 mt-2">{inc.title}</h3>
                  </div>
                  <span className="text-[11px] font-medium text-stone-400 flex-shrink-0">{inc.time_ago}</span>
                </div>

                {/* AI Summary Box */}
                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-200/80 flex items-start gap-3">
                  <div className="p-1.5 rounded-lg bg-amber-500 text-white flex-shrink-0 mt-0.5">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <p className="text-xs font-medium text-stone-800 leading-relaxed">
                    <strong className="font-bold text-amber-900">AI Diagnostic Summary:</strong> {inc.ai_summary}
                  </p>
                </div>

                {/* Footer Meta & Actions */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-stone-100 text-xs text-stone-600">
                  <div className="flex items-center gap-4">
                    <div>
                      <span className="text-[10px] font-bold text-stone-400 block uppercase">Recommended Contractor</span>
                      <span className="font-bold text-stone-800">{inc.contractor}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-stone-400 block uppercase">Cost Estimate</span>
                      <span className="font-semibold text-emerald-700">{inc.cost_est}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {inc.status === "resolved" || actionDone[inc.id] ? (
                      <span className="px-3 py-1.5 rounded-xl bg-emerald-100 text-emerald-800 font-bold text-xs border border-emerald-300 flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-emerald-600" /> Resolved
                      </span>
                    ) : (
                      <button
                        onClick={() => handleResolve(inc.id)}
                        className="px-3.5 py-1.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-white font-bold text-xs transition flex items-center gap-1.5 cursor-pointer shadow-xs"
                      >
                        Approve & Mark Resolved
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* ── Society Towers Health Grid ────────────────────────────────────── */}
          <div className="space-y-4 pt-4">
            <h2 className="text-lg font-black text-stone-900 tracking-tight flex items-center gap-2">
              <Building2 className="w-5 h-5 text-amber-600" />
              Society Towers Infrastructure Health
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {TOWERS.map((t) => (
                <div key={t.id} className="mgmt-card p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-2xl flex items-center justify-center font-black text-sm ${
                      t.status === "warning" ? "bg-amber-100 text-amber-900 border border-amber-300" : "bg-emerald-100 text-emerald-900 border border-emerald-300"
                    }`}>
                      {t.id}
                    </div>
                    <div>
                      <h4 className="font-extrabold text-sm text-stone-900">{t.name}</h4>
                      <p className="text-[11px] text-stone-500 font-medium">{t.residents} Residents • {t.issue}</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-base font-black text-stone-900">{t.health}%</span>
                    <span className="block text-[9px] font-bold text-stone-400 uppercase">Health Score</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Top Contractors & Live AI Log Stream ───────────────── */}
        <div className="space-y-6">
          
          {/* Top Ranked Contractors */}
          <div className="mgmt-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <h3 className="font-black text-base text-stone-900 flex items-center gap-2">
                <HardHat className="w-4 h-4 text-amber-600" />
                Ranked Contractors (Thompson Sampling)
              </h3>
              <Link href="/contractors" className="text-[11px] font-bold text-amber-700 hover:text-amber-800">
                View All
              </Link>
            </div>

            <div className="space-y-3">
              {TOP_CONTRACTORS.map((c, i) => (
                <div key={c.name} className="p-3 rounded-xl bg-stone-50 border border-stone-200/80 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded-full bg-amber-500 text-white font-bold text-[9px] flex items-center justify-center">
                        #{i + 1}
                      </span>
                      <p className="font-extrabold text-xs text-stone-900">{c.name}</p>
                    </div>
                    <p className="text-[10px] text-stone-500 mt-0.5 font-medium">{c.specialty} • {c.speed}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-black text-amber-800">★ {c.rating}</span>
                    <span className="block text-[9px] text-stone-400">{c.jobs} Jobs</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Live AI Operations Execution Feed */}
          <div className="mgmt-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <h3 className="font-black text-base text-stone-900 flex items-center gap-2">
                <Bot className="w-4 h-4 text-amber-600" />
                Live Autonomous AI Agent Log
              </h3>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            </div>

            <div className="space-y-3">
              {AI_AGENT_LOGS.map((log, i) => (
                <div key={i} className="p-3 rounded-xl bg-[#fffef9] border border-amber-200/60 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded-md text-[9px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                      {log.agent}
                    </span>
                    <span className="text-[9px] font-medium text-stone-400">{log.time}</span>
                  </div>
                  <p className="text-[11px] font-medium text-stone-700 leading-snug pt-1">
                    {log.action}
                  </p>
                </div>
              ))}
            </div>

            <Link
              href="/agent-logs"
              className="w-full py-2 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-900 font-bold text-xs border border-amber-200/80 transition flex items-center justify-center gap-1"
            >
              Inspect Agent Logs Stream <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

        </div>

      </div>

    </div>
  );
}
