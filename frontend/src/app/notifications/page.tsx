"use client";

import { useEffect, useState } from "react";
import { notificationsApi, type NotificationOut } from "@/lib/api";
import { Mail, MessageSquare, Bell, CheckCircle2, Clock, XCircle } from "lucide-react";

const TOKEN = "demo-token";

const MOCK_NOTIFICATIONS: NotificationOut[] = [
  { id: "1", incident_id: "1", channel: "email", subject: "🚨 Critical: Water Pressure Drop — Tower A", content: "Dear Resident,\n\nWe have detected a critical water pressure drop in Tower A. Our AI operations team has dispatched AquaFix Pro. Estimated restoration: 5 hours.\n\nWe sincerely apologize for the inconvenience.\n\nASIP Operations Team", status: "sent", sent_at: new Date().toISOString() },
  { id: "2", incident_id: "2", channel: "sms", subject: "", content: "ASIP Alert: Power outage detected in Tower B. DG backup active. Estimated restoration: 3hrs. Team working on it.", status: "sent", sent_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "3", incident_id: "3", channel: "email", subject: "⚠️ Tank Overflow Alert — Tower C", content: "Dear Management,\n\nA tank overflow was detected and resolved in Tower C. Root cause: Float valve malfunction. Action taken: Valve replaced. No resident impact.\n\nFull report available in ASIP dashboard.", status: "sent" },
  { id: "4", incident_id: "4", channel: "push", subject: "Power Overload Warning", content: "Monitoring high power consumption in Tower A. Recommended: Reduce AC usage. AI team is monitoring.", status: "draft" },
  { id: "5", incident_id: "5", channel: "email", subject: "🔴 ESCALATED: Critical Water Shortage — Tower B", content: "URGENT: Water shortage has been escalated to Society Committee. Emergency tankers arranged. ETA: 2 hours.", status: "failed" },
];

const CHANNEL_ICON: Record<string, React.ElementType> = {
  email: Mail,
  sms: MessageSquare,
  push: Bell,
};

const CHANNEL_STYLE: Record<string, string> = {
  email: "bg-blue-500/20 text-blue-400 border-blue-500/20",
  sms: "bg-green-500/20 text-green-400 border-green-500/20",
  push: "bg-purple-500/20 text-purple-400 border-purple-500/20",
};

const STATUS_CONFIG: Record<string, { icon: React.ElementType; cls: string; label: string }> = {
  sent: { icon: CheckCircle2, cls: "text-green-400 bg-green-500/10", label: "Sent" },
  draft: { icon: Clock, cls: "text-yellow-400 bg-yellow-500/10", label: "Draft" },
  failed: { icon: XCircle, cls: "text-red-400 bg-red-500/10", label: "Failed" },
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationOut[]>(MOCK_NOTIFICATIONS);
  const [selected, setSelected] = useState<NotificationOut | null>(null);

  useEffect(() => {
    notificationsApi.list(TOKEN).then(setNotifications).catch(() => setNotifications(MOCK_NOTIFICATIONS));
  }, []);

  const counts = { sent: notifications.filter(n => n.status === "sent").length, draft: notifications.filter(n => n.status === "draft").length, failed: notifications.filter(n => n.status === "failed").length };

  return (
    <div className="flex h-screen">
      {/* Left */}
      <div className="w-96 flex-shrink-0 border-r border-white/5 flex flex-col">
        <div className="px-5 py-4 border-b border-white/5">
          <h1 className="text-lg font-bold text-white mb-3">Notifications</h1>
          <div className="grid grid-cols-3 gap-2">
            {[["Sent", counts.sent, "text-green-400"], ["Draft", counts.draft, "text-yellow-400"], ["Failed", counts.failed, "text-red-400"]].map(([label, count, cls]) => (
              <div key={label as string} className="rounded-xl bg-white/3 border border-white/5 p-2 text-center">
                <p className={`text-xl font-bold ${cls}`}>{count}</p>
                <p className="text-[10px] text-gray-500">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-white/5">
          {notifications.map((n) => {
            const Icon = CHANNEL_ICON[n.channel] || Bell;
            const status = STATUS_CONFIG[n.status];
            const StatusIcon = status.icon;
            return (
              <button key={n.id} onClick={() => setSelected(n)}
                className={`w-full text-left px-5 py-4 hover:bg-white/3 transition-colors ${selected?.id === n.id ? "bg-blue-600/10 border-l-2 border-blue-500" : ""}`}>
                <div className="flex items-start gap-3">
                  <span className={`mt-0.5 flex-shrink-0 inline-flex items-center rounded-lg border p-1.5 ${CHANNEL_STYLE[n.channel]}`}>
                    <Icon className="w-3 h-3" />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5">
                      <p className="text-xs font-medium text-white capitalize">{n.channel}</p>
                      <span className={`inline-flex items-center gap-1 text-[10px] rounded-full px-2 py-0.5 ${status.cls}`}>
                        <StatusIcon className="w-2.5 h-2.5" />{status.label}
                      </span>
                    </div>
                    {n.subject && <p className="text-xs text-gray-300 truncate">{n.subject}</p>}
                    <p className="text-[10px] text-gray-500 mt-1 line-clamp-2">{n.content}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right */}
      <div className="flex-1 overflow-y-auto p-6">
        {selected ? (
          <div className="max-w-2xl space-y-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  {(() => { const Icon = CHANNEL_ICON[selected.channel] || Bell; return <span className={`inline-flex items-center gap-1.5 border px-3 py-1 rounded-full text-xs font-medium capitalize ${CHANNEL_STYLE[selected.channel]}`}><Icon className="w-3 h-3" />{selected.channel}</span>; })()}
                  {(() => { const s = STATUS_CONFIG[selected.status]; const Icon = s.icon; return <span className={`inline-flex items-center gap-1 text-xs rounded-full px-3 py-1 font-medium ${s.cls}`}><Icon className="w-3 h-3" />{s.label}</span>; })()}
                </div>
                {selected.subject && <h2 className="text-xl font-bold text-white">{selected.subject}</h2>}
              </div>
            </div>

            <div className="rounded-2xl bg-white/3 border border-white/5 p-5">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Message Content</p>
              <p className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{selected.content}</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-white/3 border border-white/5 p-3">
                <p className="text-[10px] text-gray-500">Incident ID</p>
                <p className="text-xs text-white font-mono mt-1">{selected.incident_id}</p>
              </div>
              {selected.sent_at && (
                <div className="rounded-xl bg-white/3 border border-white/5 p-3">
                  <p className="text-[10px] text-gray-500">Sent At</p>
                  <p className="text-xs text-white mt-1">{new Date(selected.sent_at).toLocaleString()}</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Bell className="w-12 h-12 text-gray-600 mb-3" />
            <p className="text-gray-400 font-medium">Select a notification to preview</p>
          </div>
        )}
      </div>
    </div>
  );
}
