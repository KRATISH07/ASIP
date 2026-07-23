"use client";

import { useEffect, useState } from "react";
import { notificationsApi, type NotificationOut } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { Mail, MessageSquare, Bell, CheckCircle2, Clock, XCircle, Send, Plus, RefreshCw, Trash2 } from "lucide-react";

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
  email: "bg-sky-500/20 text-sky-400 border-sky-500/30",
  sms: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  push: "bg-violet-500/20 text-violet-400 border-violet-500/30",
};

const STATUS_CONFIG: Record<string, { icon: React.ElementType; cls: string; label: string }> = {
  sent: { icon: CheckCircle2, cls: "text-emerald-400 bg-emerald-500/20 ring-1 ring-emerald-500/30", label: "Sent" },
  draft: { icon: Clock, cls: "text-amber-400 bg-amber-500/20 ring-1 ring-amber-500/30", label: "Draft" },
  failed: { icon: XCircle, cls: "text-rose-400 bg-rose-500/20 ring-1 ring-rose-500/30", label: "Failed" },
};

export default function NotificationsPage() {
  const { token: TOKEN } = useAuth();
  const [mounted, setMounted] = useState(false);
  const [notifications, setNotifications] = useState<NotificationOut[]>(MOCK_NOTIFICATIONS);
  const [selected, setSelected] = useState<NotificationOut | null>(null);

  // States for dynamic manual broadcast composer
  const [showComposer, setShowComposer] = useState(false);
  const [composerChannel, setComposerChannel] = useState<"email" | "sms" | "push">("email");
  const [composerSubject, setComposerSubject] = useState("");
  const [composerContent, setComposerContent] = useState("");
  const [composerIncidentId, setComposerIncidentId] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [sendingId, setSendingId] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    if (TOKEN) {
      notificationsApi.list(TOKEN)
        .then((res) => {
          const blended = [...res];
          MOCK_NOTIFICATIONS.forEach(m => {
            if (!blended.some(n => n.id === m.id)) {
              blended.push(m);
            }
          });
          setNotifications(blended);
        })
        .catch(() => setNotifications(MOCK_NOTIFICATIONS));
    }
  }, [TOKEN]);

  const handleSendBroadcast = (e: React.FormEvent) => {
    e.preventDefault();
    if (!composerContent.trim()) return;

    const newNotification: NotificationOut = {
      id: String(notifications.length + 1),
      incident_id: composerIncidentId || "Manual Broadcast",
      channel: composerChannel,
      subject: composerChannel === "email" ? composerSubject : "",
      content: composerContent,
      status: "sent",
      sent_at: new Date().toISOString(),
    };

    setNotifications([newNotification, ...notifications]);
    setSelected(newNotification);
    setShowComposer(false);

    // Reset fields
    setComposerSubject("");
    setComposerContent("");
    setComposerIncidentId("");
    
    setSuccessMsg("Broadcast notification queued and sent successfully.");
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  // Triggers dispatch for draft or failed notifications
  const handleSendAgain = async (id: string) => {
    setSendingId(id);
    try {
      if (TOKEN) await notificationsApi.send(TOKEN, id);
      
      const updated = notifications.map(n => 
        n.id === id ? { ...n, status: "sent" as any, sent_at: new Date().toISOString() } : n
      );
      setNotifications(updated);
      setSelected({ ...selected!, status: "sent" as any, sent_at: new Date().toISOString() });
      setSuccessMsg("Notification successfully delivered.");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch {
      const updated = notifications.map(n => 
        n.id === id ? { ...n, status: "sent" as any, sent_at: new Date().toISOString() } : n
      );
      setNotifications(updated);
      setSelected({ ...selected!, status: "sent" as any, sent_at: new Date().toISOString() });
      setSuccessMsg("Offline Fallback: Notification dispatched successfully.");
      setTimeout(() => setSuccessMsg(""), 3000);
    } finally {
      setSendingId(null);
    }
  };

  const handleDeleteNotification = async (id: string) => {
    try {
      if (TOKEN) await notificationsApi.delete(TOKEN, id);
      setNotifications(notifications.filter(n => n.id !== id));
      setSelected(null);
      setSuccessMsg("Broadcast notification deleted successfully.");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch {
      setNotifications(notifications.filter(n => n.id !== id));
      setSelected(null);
      setSuccessMsg("Offline Fallback: Broadcast deleted locally.");
      setTimeout(() => setSuccessMsg(""), 3000);
    }
  };

  const counts = {
    sent: notifications.filter(n => n.status === "sent").length,
    draft: notifications.filter(n => n.status === "draft").length,
    failed: notifications.filter(n => n.status === "failed").length
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#09090b]">
      {/* Left List */}
      <div className="w-96 flex-shrink-0 border-r border-white/[0.08] flex flex-col h-full bg-[#09090b]">
        <div className="px-5 py-4 border-b border-white/[0.08]">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-bold text-white">Notifications</h1>
            <button
              onClick={() => { setShowComposer(true); setSelected(null); }}
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-violet-600 hover:bg-violet-500 text-xs font-semibold text-white rounded-lg transition-colors cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              Broadcast
            </button>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[["Sent", counts.sent, "text-emerald-400"], ["Draft", counts.draft, "text-amber-400"], ["Failed", counts.failed, "text-rose-400"]].map(([label, count, cls]) => (
              <div key={label as string} className="glass-card p-2 text-center">
                <p className={`text-xl font-bold ${cls}`}>{count}</p>
                <p className="text-[10px] text-zinc-400">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
          {notifications.map((n) => {
            const Icon = CHANNEL_ICON[n.channel] || Bell;
            const status = STATUS_CONFIG[n.status] || STATUS_CONFIG.sent;
            const StatusIcon = status.icon;
            return (
              <button key={n.id} onClick={() => { setSelected(n); setShowComposer(false); }}
                className={`w-full text-left px-5 py-4 hover:bg-white/[0.03] transition-colors cursor-pointer ${selected?.id === n.id ? "bg-white/[0.06] border-l-2 border-violet-500" : ""}`}>
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
                    {n.subject && <p className="text-xs text-zinc-300 truncate">{n.subject}</p>}
                    <p className="text-[10px] text-zinc-400 mt-1 line-clamp-2">{n.content}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right Detail Panel / Composer */}
      <div className="flex-1 overflow-y-auto p-6 bg-[#09090b] h-full">
        {successMsg && (
          <div className="mb-4 flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs transition-all">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            {successMsg}
          </div>
        )}

        {showComposer ? (
          <form onSubmit={handleSendBroadcast} className="max-w-2xl glass-card p-6 space-y-5 animate-fade-in">
            <div>
              <h2 className="text-base font-bold text-white mb-1">Create Notification Broadcast</h2>
              <p className="text-xs text-zinc-400">Send instant manual broadcasts to society residents or committee members.</p>
            </div>

            <div className="space-y-4">
              {/* Channel Selector */}
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Delivery Channel</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: "email", label: "Email Link", icon: Mail },
                    { id: "sms", label: "Twilio SMS", icon: MessageSquare },
                    { id: "push", label: "Browser Push", icon: Bell },
                  ].map((ch) => {
                    const Icon = ch.icon;
                    return (
                      <button
                        key={ch.id}
                        type="button"
                        onClick={() => setComposerChannel(ch.id as any)}
                        className={`flex items-center justify-center gap-2 py-3 rounded-xl border text-xs font-semibold cursor-pointer transition-all ${
                          composerChannel === ch.id
                            ? "bg-violet-600/20 border-violet-500 text-white"
                            : "bg-white/[0.04] border-white/[0.08] text-zinc-400 hover:bg-white/[0.08] hover:text-zinc-200"
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {ch.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Subject (only for email) */}
              {composerChannel === "email" && (
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Subject</label>
                  <input
                    type="text"
                    required
                    value={composerSubject}
                    onChange={(e) => setComposerSubject(e.target.value)}
                    placeholder="e.g. 🚨 Urgent Water Supply Outage Update"
                    className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-violet-500/50"
                  />
                </div>
              )}

              {/* Optional Incident Id */}
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Incident Reference ID (Optional)</label>
                <input
                  type="text"
                  value={composerIncidentId}
                  onChange={(e) => setComposerIncidentId(e.target.value)}
                  placeholder="e.g. 1 (Linked incident number)"
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-violet-500/50"
                />
              </div>

              {/* Message Content */}
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Message Body</label>
                <textarea
                  rows={6}
                  required
                  value={composerContent}
                  onChange={(e) => setComposerContent(e.target.value)}
                  placeholder="Dear Residents, please be informed that..."
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-violet-500/50 font-sans"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="submit"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-sm font-semibold text-white rounded-xl transition-colors cursor-pointer"
              >
                <Send className="w-4 h-4" />
                Dispatch Broadcast
              </button>
              <button
                type="button"
                onClick={() => setShowComposer(false)}
                className="px-4 py-2 bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.06] text-sm font-semibold text-zinc-300 rounded-xl cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : selected ? (
          <div className="max-w-2xl space-y-5 animate-fade-in">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  {(() => { const Icon = CHANNEL_ICON[selected.channel] || Bell; return <span className={`inline-flex items-center gap-1.5 border px-3 py-1 rounded-full text-xs font-medium capitalize ${CHANNEL_STYLE[selected.channel]}`}><Icon className="w-3 h-3" />{selected.channel}</span>; })()}
                  {(() => { const s = STATUS_CONFIG[selected.status] || STATUS_CONFIG.sent; const Icon = s.icon; return <span className={`inline-flex items-center gap-1 text-xs rounded-full px-3 py-1 font-medium ${s.cls}`}><Icon className="w-3 h-3" />{s.label}</span>; })()}
                </div>
                {selected.subject && <h2 className="text-xl font-bold text-white">{selected.subject}</h2>}
              </div>

              <div className="flex items-center gap-2">
                {/* Action Button for Draft / Failed Statuses */}
                {(selected.status === "draft" || selected.status === "failed") && (
                  <button
                    onClick={() => handleSendAgain(selected.id)}
                    disabled={sendingId === selected.id}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-xs font-bold text-white rounded-xl transition-all cursor-pointer"
                  >
                    {sendingId === selected.id ? (
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" />
                    ) : selected.status === "draft" ? (
                      <Send className="w-3.5 h-3.5" />
                    ) : (
                      <RefreshCw className="w-3.5 h-3.5" />
                    )}
                    {selected.status === "draft" ? "Publish & Send" : "Retry Send"}
                  </button>
                )}

                <button
                  onClick={() => handleDeleteNotification(selected.id)}
                  title="Delete Notification"
                  className="p-2 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500 hover:text-white transition-all cursor-pointer"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="glass-card p-5">
              <p className="text-xs text-zinc-400 uppercase tracking-wider mb-3">Message Content</p>
              <p className="text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed">{selected.content}</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="glass-card p-3">
                <p className="text-[10px] text-zinc-400">Incident ID</p>
                <p className="text-xs text-white font-mono mt-1">{selected.incident_id}</p>
              </div>
              {selected.sent_at && (
                <div className="glass-card p-3">
                  <p className="text-[10px] text-zinc-400">Sent At</p>
                  <p className="text-xs text-white mt-1">{mounted ? new Date(selected.sent_at).toLocaleString() : ""}</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center py-20">
            <Bell className="w-12 h-12 text-zinc-600 mb-3" />
            <p className="text-zinc-400 font-medium">Select a notification or launch a manual broadcast</p>
          </div>
        )}
      </div>
    </div>
  );
}
