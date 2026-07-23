"use client";

import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import Link from "next/link";
import {
  AlertTriangle, CheckCircle2, Activity, Zap,
  Bot, ArrowRight, ShieldCheck, Wrench, Bell,
  ChevronRight, PlusCircle, Check, ArrowUpRight
} from "lucide-react";

// Clean Mock Incidents for Minimalist Operations View
const INITIAL_INCIDENTS = [
  {
    id: "INC-8492",
    title: "Water Pressure Drop — Tower A",
    category: "Plumbing",
    severity: "critical",
    status: "analyzing",
    ai_action: "Infrastructure Agent querying RAG memory. Auto-assigned Apex Plumbing.",
    time: "12 mins ago"
  },
  {
    id: "INC-8490",
    title: "Substation Voltage Spike — Tower D",
    category: "Electrical",
    severity: "high",
    status: "in_progress",
    ai_action: "Decision Agent scheduled automated load-balancing diagnostic.",
    time: "38 mins ago"
  },
  {
    id: "INC-8488",
    title: "Elevator #2 Brake Sensor Check — Tower B",
    category: "Elevator",
    severity: "low",
    status: "resolved",
    ai_action: "Reset command issued via IoT Edge Gateway successfully.",
    time: "2 hrs ago"
  }
];

export default function SpaciousOperationsDashboard() {
  const { user } = useAuth();
  const [incidents, setIncidents] = useState(INITIAL_INCIDENTS);
  const [resolvedMap, setResolvedMap] = useState<Record<string, boolean>>({});

  const handleResolve = (id: string) => {
    setResolvedMap(prev => ({ ...prev, [id]: true }));
    setIncidents(prev => prev.map(inc => inc.id === id ? { ...inc, status: "resolved" } : inc));
  };

  return (
    <div className="min-h-screen bg-[#faf4e8] px-8 py-10 lg:px-12 lg:py-12 animate-fade-in">
      <div className="max-w-7xl mx-auto space-y-10">

        {/* ── 1. Top Header (Spacious & Clean) ─────────────────────────────────── */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-amber-200/60">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100/80 text-emerald-800 border border-emerald-300/60">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                All Systems Operational
              </span>
              <span className="text-xs font-semibold text-stone-400">|</span>
              <span className="text-xs font-semibold text-stone-500">Autonomous Mode Active</span>
            </div>

            <h1 className="text-3xl lg:text-4xl font-extrabold text-stone-900 tracking-tight">
              AI Society Operations Center
            </h1>
            <p className="text-sm text-stone-500 mt-1.5 max-w-2xl leading-relaxed">
              Real-time multi-agent triage, predictive impact estimation, and autonomous contractor dispatch.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/incidents"
              className="px-5 py-3 rounded-2xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-md shadow-amber-500/20 transition flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              New Incident
            </Link>
            <Link
              href="/notifications"
              className="px-5 py-3 rounded-2xl bg-white hover:bg-stone-50 text-stone-800 font-bold text-xs border border-amber-200/80 transition flex items-center gap-2 shadow-xs"
            >
              <Bell className="w-4 h-4 text-amber-600" />
              Broadcast Alert
            </Link>
          </div>
        </div>

        {/* ── 2. Top KPI Metrics (4 Spacious Cards) ───────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <div className="bg-white border border-amber-200/70 rounded-3xl p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">Total Handled</span>
              <div className="p-2.5 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200/60">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <p className="text-4xl font-extrabold text-stone-900 tracking-tight">47</p>
            <p className="text-xs font-medium text-stone-500">Incidents logged this month</p>
          </div>

          <div className="bg-white border border-amber-200/70 rounded-3xl p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">Active Alerts</span>
              <div className="p-2.5 rounded-2xl bg-amber-100 text-amber-700 border border-amber-300/60">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <p className="text-4xl font-extrabold text-stone-900 tracking-tight">2</p>
            <p className="text-xs font-medium text-amber-700">Requires supervisor review</p>
          </div>

          <div className="bg-white border border-amber-200/70 rounded-3xl p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">AI Accuracy</span>
              <div className="p-2.5 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200/60">
                <Bot className="w-4 h-4" />
              </div>
            </div>
            <p className="text-4xl font-extrabold text-stone-900 tracking-tight">98.4%</p>
            <p className="text-xs font-medium text-emerald-700">LLM Judge rubric score</p>
          </div>

          <div className="bg-white border border-amber-200/70 rounded-3xl p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">Resolved Today</span>
              <div className="p-2.5 rounded-2xl bg-blue-50 text-blue-600 border border-blue-200/60">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <p className="text-4xl font-extrabold text-stone-900 tracking-tight">12</p>
            <p className="text-xs font-medium text-stone-500">Average resolution time: 42m</p>
          </div>

        </div>

        {/* ── 3. Active Incident Operations Triage (Spacious List) ───────────── */}
        <div className="bg-white border border-amber-200/80 rounded-3xl p-8 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-extrabold text-stone-900 tracking-tight">
                Live Incident Triage
              </h2>
              <p className="text-xs text-stone-500 mt-1">
                Real-time autonomous diagnostic stream and resolution status.
              </p>
            </div>
            <Link
              href="/incidents"
              className="text-xs font-bold text-amber-700 hover:text-amber-800 flex items-center gap-1"
            >
              View Full List <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="divide-y divide-stone-100">
            {incidents.map((inc) => (
              <div key={inc.id} className="py-5 flex flex-col md:flex-row md:items-center justify-between gap-4 first:pt-0 last:pb-0">
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xs font-bold font-mono text-amber-900 bg-amber-100 px-2.5 py-0.5 rounded-md border border-amber-200/60">
                      {inc.id}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                      inc.severity === "critical" ? "bg-red-50 text-red-700 border-red-200" :
                      inc.severity === "high" ? "bg-amber-100 text-amber-800 border-amber-300" :
                      "bg-emerald-50 text-emerald-700 border-emerald-200"
                    }`}>
                      {inc.severity}
                    </span>
                    <span className="text-xs font-medium text-stone-400">{inc.time}</span>
                  </div>

                  <h3 className="text-base font-extrabold text-stone-900">{inc.title}</h3>
                  <p className="text-xs text-stone-600 leading-relaxed font-medium">
                    <strong className="text-stone-800">AI Status:</strong> {inc.ai_action}
                  </p>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                  {inc.status === "resolved" || resolvedMap[inc.id] ? (
                    <span className="px-4 py-2 rounded-xl bg-emerald-50 text-emerald-700 font-bold text-xs border border-emerald-200 flex items-center gap-1.5">
                      <Check className="w-4 h-4" /> Resolved
                    </span>
                  ) : (
                    <button
                      onClick={() => handleResolve(inc.id)}
                      className="px-4 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-white font-bold text-xs transition cursor-pointer"
                    >
                      Resolve Incident
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── 4. AI Multi-Agent System Workflow Status (Clean Grid) ────────────── */}
        <div className="bg-white border border-amber-200/80 rounded-3xl p-8 shadow-xs space-y-6">
          <div>
            <h2 className="text-xl font-extrabold text-stone-900 tracking-tight">
              AI Multi-Agent Workflow Execution
            </h2>
            <p className="text-xs text-stone-500 mt-1">
              Active LangGraph autonomous agent execution nodes.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { name: "Monitoring", time: "12ms", status: "Active" },
              { name: "Infrastructure", time: "2.3s", status: "Active" },
              { name: "Impact Analysis", time: "145ms", status: "Active" },
              { name: "Contractor Bandit", time: "1.8s", status: "Active" },
              { name: "Communication", time: "2.1s", status: "Active" },
              { name: "Supervisor", time: "1.9s", status: "Active" },
            ].map((agent) => (
              <div key={agent.name} className="p-4 rounded-2xl bg-[#fffef9] border border-amber-200/60 text-center space-y-1">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 mb-1" />
                <h4 className="text-xs font-bold text-stone-800 truncate">{agent.name}</h4>
                <p className="text-[10px] text-stone-400 font-mono">{agent.time}</p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
