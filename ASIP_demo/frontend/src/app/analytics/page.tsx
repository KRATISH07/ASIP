"use client";

import { AlertTriangle, TrendingUp, BarChart3, Clock, CheckCircle2, ShieldAlert } from "lucide-react";

export default function AnalyticsPage() {
  // Demo analytics data representing actual ASIP metrics
  const stats = [
    { label: "AI Prediction Accuracy", value: "94.2%", change: "+2.4% vs last week", desc: "Outage Duration & Cost Models" },
    { label: "LLM Judge Score", value: "4.82/5.0", change: "100% consistent", desc: "Based on 145 resolved reports" },
    { label: "Avg Resolution Time", value: "2.4 hrs", change: "-1.1 hrs faster", desc: "Autonomous contractor dispatch" },
    { label: "SLA Compliance Rate", value: "98.7%", change: "Zero breaches", desc: "Under 4-hour critical limit" },
  ];

  return (
    <div className="min-h-screen bg-[#09090b] p-5 lg:p-7 animate-fade-in space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Operational Analytics</h1>
        <p className="text-sm text-zinc-400">Core intelligence performance metrics and self-learning loop rolling status.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((s, idx) => (
          <div key={idx} className="glass-card p-5 flex flex-col justify-between space-y-4">
            <div>
              <p className="text-xs text-zinc-400 uppercase tracking-wider font-semibold">{s.label}</p>
              <h2 className="text-3xl font-extrabold text-white mt-2">{s.value}</h2>
            </div>
            <div>
              <p className="text-xs text-emerald-400 font-medium">{s.change}</p>
              <p className="text-[10px] text-zinc-500 mt-1">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Detail grids */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* ML Self-Retraining Pipeline Status */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-violet-400" />
              ML Self-Learning Loop
            </h3>
            <span className="inline-flex items-center rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 ring-1 ring-emerald-500/30">
              Active / Healthy
            </span>
          </div>

          <div className="space-y-3 pt-2">
            {[
              { label: "Current Outage Duration MAE", value: "1.08 hours", target: "Target < 2.50 hours", status: "pass" },
              { label: "Current Cost Estimation MAE", value: "₹480", target: "Target < ₹1,200", status: "pass" },
              { label: "Feedback Samples Registered", value: "245 resolved events", target: "Min required for retrain: 50", status: "pass" },
              { label: "Last Auto-Retrain Execution", value: "3 days ago", target: "Triggered by MAE Threshold Breach", status: "info" },
            ].map((m, i) => (
              <div key={i} className="flex justify-between items-center bg-white/[0.04] p-3 rounded-xl border border-white/[0.08]">
                <div>
                  <p className="text-sm font-medium text-zinc-200">{m.label}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{m.target}</p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-white">{m.value}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* LLM-as-Judge Quality Audit Audit */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-400" />
              LLM Judge Audit Rubric
            </h3>
            <span className="inline-flex items-center rounded-full bg-violet-500/20 px-2.5 py-0.5 text-xs font-semibold text-violet-400 ring-1 ring-violet-500/30">
              Score: 4.82/5.00
            </span>
          </div>

          <div className="space-y-3 pt-2">
            {[
              { rubric: "Factual Consistency", score: "4.92 / 5.00", desc: "No ground-truth hallucinations" },
              { rubric: "Root Cause Specificity", score: "4.78 / 5.00", desc: "Vague explanations avoided" },
              { rubric: "Action Plan Completeness", score: "4.85 / 5.00", desc: "Numbered, actionable sequences" },
              { rubric: "Priority Label Correctness", score: "4.74 / 5.00", desc: "Perfect severity correlation" },
            ].map((r, i) => (
              <div key={i} className="flex items-center justify-between bg-white/[0.04] p-3 rounded-xl border border-white/[0.08]">
                <div>
                  <p className="text-sm font-medium text-zinc-200">{r.rubric}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{r.desc}</p>
                </div>
                <span className="text-xs font-bold bg-white/[0.06] text-zinc-300 px-2.5 py-1 rounded-lg border border-white/[0.08]">{r.score}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
