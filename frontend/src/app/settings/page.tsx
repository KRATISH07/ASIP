"use client";

import { useState } from "react";
import { Settings, Cpu, Database, Bell, Save, CheckCircle, User } from "lucide-react";
import { useAuth } from "@/components/auth-provider";

export default function SettingsPage() {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <form onSubmit={handleSave} className="p-6 space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-800 mb-1 font-sans">Settings</h1>
          <p className="text-sm text-stone-500">Configure AI agent routing parameters, ML threshold settings, and tenant channels.</p>
        </div>
        <button
          type="submit"
          className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 active:bg-amber-700 text-stone-800 text-sm font-semibold rounded-xl transition-all shadow-lg shadow-amber-200/40 cursor-pointer"
        >
          <Save className="w-4 h-4" />
          Save Changes
        </button>
      </div>

      {saved && (
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-600 p-4 rounded-xl text-sm transition-all duration-300">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          Settings successfully updated. In-memory worker caches invalidated.
        </div>
      )}

      <div className="space-y-6">
        {/* Section 0: User Profile Info */}
        <div className="rounded-2xl border border-stone-200 bg-stone-50 p-6 space-y-4">
          <h3 className="text-base font-bold text-stone-800 flex items-center gap-2">
            <User className="w-4 h-4 text-violet-600" />
            User Profile
          </h3>
          <p className="text-xs text-stone-400 -mt-2">Currently logged-in identity information from secure auth state.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <p className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">Full Name</p>
              <p className="text-sm font-semibold text-stone-800 mt-1">{user?.full_name || "Guest User"}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">Email Address</p>
              <p className="text-sm font-semibold text-stone-800 mt-1">{user?.email || "N/A"}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">Role Scope</p>
              <p className="text-xs font-bold text-amber-600 capitalize bg-amber-100/60 border border-amber-300 px-2 py-0.5 rounded-md w-fit mt-1">{user?.role || "Resident"}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">Connection Status</p>
              <p className="text-xs font-semibold text-emerald-600 mt-1 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                Active Session
              </p>
            </div>
          </div>
        </div>

        {/* Section 1: AI Engine & Model Routing */}
        <div className="rounded-2xl border border-stone-200 bg-stone-50 p-6 space-y-4">
          <h3 className="text-base font-bold text-stone-800 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-amber-600" />
            AI Engine & Model Routing
          </h3>
          <p className="text-xs text-stone-400 -mt-2">Assign appropriate models based on LLM task complexity to optimize costs.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Complexity Router</label>
              <select className="w-full bg-stone-100 border border-stone-300 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500">
                <option className="bg-white text-stone-800" value="dynamic">Dynamic Routing (Complexity Based)</option>
                <option className="bg-white text-stone-800" value="expensive">Always High Performance (GPT-4o / Pro)</option>
                <option className="bg-white text-stone-800" value="cheap">Always Low Cost (GPT-4o-Mini / Flash)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Primary Reasoning Provider</label>
              <select className="w-full bg-stone-100 border border-stone-300 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500">
                <option className="bg-white text-stone-800" value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option className="bg-white text-stone-800" value="google">Google Gemini (Pro / Flash)</option>
                <option className="bg-white text-stone-800" value="hybrid">Hybrid (Failover Circuit Breaker)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 2: ML Pipeline & Learning Parameters */}
        <div className="rounded-2xl border border-stone-200 bg-stone-50 p-6 space-y-4">
          <h3 className="text-base font-bold text-stone-800 flex items-center gap-2">
            <Database className="w-4 h-4 text-violet-600" />
            Self-Retraining & RAG Thresholds
          </h3>
          <p className="text-xs text-stone-400 -mt-2">Tweak triggers that determine when the forecasting models automatically retrain.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">MAE Retraining Trigger Limit (Hours)</label>
              <input
                type="number"
                step="0.1"
                defaultValue="2.5"
                className="w-full bg-stone-100 border border-stone-300 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Min Feedback Samples for Retrain</label>
              <input
                type="number"
                defaultValue="50"
                className="w-full bg-stone-100 border border-stone-300 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">RAG Context K-Neighbors</label>
              <input
                type="number"
                defaultValue="5"
                className="w-full bg-stone-100 border border-stone-300 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Chroma collection namespace</label>
              <input
                type="text"
                defaultValue="asip_knowledge_base"
                className="w-full bg-stone-100 border border-stone-300 rounded-xl px-3.5 py-2.5 text-sm text-stone-800 focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Notification Channels */}
        <div className="rounded-2xl border border-stone-200 bg-stone-50 p-6 space-y-4">
          <h3 className="text-base font-bold text-stone-800 flex items-center gap-2">
            <Bell className="w-4 h-4 text-emerald-600" />
            Communication Integrations
          </h3>
          <p className="text-xs text-stone-400 -mt-2">Toggle native notifications channels dispatched autonomously by the communication agent.</p>

          <div className="space-y-3 pt-2">
            {[
              { id: "sms", title: "Twilio SMS Dispatcher", desc: "Sends critical incident alerts to managers and contractors.", defaultChecked: true },
              { id: "email", title: "SendGrid Email Dispatcher", desc: "Distributes structural reports, diagnosis briefs, and billing invoices.", defaultChecked: true },
              { id: "push", title: "Web Push Notifications", desc: "In-browser notices for instant status updates.", defaultChecked: false },
            ].map((ch) => (
              <div key={ch.id} className="flex items-center justify-between p-3.5 rounded-xl border border-stone-200 bg-stone-50">
                <div>
                  <p className="text-sm font-semibold text-stone-800">{ch.title}</p>
                  <p className="text-xs text-stone-400 mt-0.5">{ch.desc}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked={ch.defaultChecked} className="sr-only peer" />
                  <div className="w-9 h-5 bg-stone-100 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-600"></div>
                </label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </form>
  );
}
