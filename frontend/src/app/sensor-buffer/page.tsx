"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { sensorBufferApi } from "@/lib/api";
import {
  Cpu, RotateCw, CheckCircle2, AlertTriangle, Play, RefreshCw, BarChart2, Plus, Terminal
} from "lucide-react";

interface BufferStats {
  total_events: number;
  pending_events: number;
  synced_events: number;
  failed_events: number;
  oldest_pending_age_sec?: number;
  success_rate: number;
}

export default function SensorBufferPage() {
  const { token } = useAuth();
  
  const [stats, setStats] = useState<BufferStats>({
    total_events: 0, pending_events: 0, synced_events: 0, failed_events: 0, success_rate: 1.0
  });
  const [loading, setLoading] = useState(true);
  const [replaySubmitting, setReplaySubmitting] = useState(false);
  const [replayResult, setReplayResult] = useState<string | null>(null);
  
  // Simulator states
  const [sensorId, setSensorId] = useState("flow-meter-A1");
  const [value, setValue] = useState("1.8");
  const [unit, setUnit] = useState("bar");
  const [simulatorResult, setSimulatorResult] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);

  const fetchStats = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await sensorBufferApi.getStats(token);
      setStats(res);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [token]);

  const triggerReplay = async () => {
    if (!token) return;
    setReplaySubmitting(true);
    setReplayResult(null);
    try {
      const res = await sensorBufferApi.replay(token, 20);
      setReplayResult(`Replayed: ${res.replayed} events. Succeeded: ${res.succeeded}. Failed: ${res.failed}.`);
      fetchStats();
    } catch (err: any) {
      setReplayResult(`Error replaying: ${err.message}`);
    } finally {
      setReplaySubmitting(false);
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSimulating(true);
    setSimulatorResult(null);

    const event = {
      sensor_id: sensorId,
      idempotency_key: `sim-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      payload: {
        tower_id: "df7163dc-c593-42a6-9993-ecc1acc2002b", // default seeded Tower A ID
        sensor_type: "water_pressure",
        value: parseFloat(value),
        unit: unit,
        timestamp: new Date().toISOString(),
      },
      event_timestamp: new Date().toISOString(),
    };

    try {
      const res = await sensorBufferApi.upload(token, [event]);
      setSimulatorResult(`Uploaded 1 event to durable buffer. Total received: ${res.total_received}, duplicates skipped: ${res.duplicate_skipped}.`);
      fetchStats();
    } catch (err: any) {
      setSimulatorResult(`Failed to simulate upload: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-gradient-to-r from-cyan-100 to-amber-50 border border-cyan-200 rounded-3xl p-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-cyan-100 text-cyan-600 flex items-center justify-center shadow-inner">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-stone-800 tracking-tight">IoT Edge Gateway Portal</h1>
            <p className="text-xs text-stone-500 mt-1">
              Durable Store-and-Forward ingestion diagnostics &bull; Gateway ID: <span className="font-mono text-stone-800">gw-gate-3092</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-xl">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
          <p className="text-xs font-semibold text-emerald-600">Connected</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Metric Cards */}
        <div className="bg-white border border-stone-200 rounded-2xl p-5 space-y-2">
          <p className="text-xs text-stone-500 uppercase tracking-wider">Total Buffer Uploads</p>
          <p className="text-3xl font-bold text-stone-800 tabular-nums">{stats.total_events}</p>
          <p className="text-[10px] text-stone-400">Cumulative historical uploads</p>
        </div>
        <div className="bg-white border border-stone-200 rounded-2xl p-5 space-y-2">
          <p className="text-xs text-stone-500 uppercase tracking-wider">Unsynced Pending</p>
          <p className="text-3xl font-bold text-amber-600 tabular-nums">{stats.pending_events}</p>
          <p className="text-[10px] text-stone-400">Awaiting automatic loop upload</p>
        </div>
        <div className="bg-white border border-stone-200 rounded-2xl p-5 space-y-2">
          <p className="text-xs text-stone-500 uppercase tracking-wider">Failed / Retrying</p>
          <p className="text-3xl font-bold text-rose-600 tabular-nums">{stats.failed_events}</p>
          <p className="text-[10px] text-stone-400">Requires manual replay review</p>
        </div>
        <div className="bg-white border border-stone-200 rounded-2xl p-5 space-y-2">
          <p className="text-xs text-stone-500 uppercase tracking-wider">Ingestion Success Rate</p>
          <p className="text-3xl font-bold text-emerald-600 tabular-nums">{(stats.success_rate * 100).toFixed(1)}%</p>
          <p className="text-[10px] text-stone-400">Replay compilation success</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Replay Controls (Left) */}
        <div className="lg:col-span-1 bg-white border border-stone-200 rounded-3xl p-6 space-y-6 shadow-xl">
          <div>
            <div className="flex items-center gap-2">
              <RotateCw className="h-5 w-5 text-amber-600" />
              <h2 className="text-lg font-bold text-stone-800 tracking-tight">Manual Replay Trigger</h2>
            </div>
            <p className="text-xs text-stone-500 mt-1">Force compile and process failed buffer records into active incidents.</p>
          </div>

          <div className="p-4 bg-stone-100 border border-stone-200 rounded-2xl space-y-3">
            <p className="text-xs text-stone-600">
              When edge sensors experience network failures, events accumulate locally. If automatic loops stall, trigger a manual replay here.
            </p>
            <button
              onClick={triggerReplay}
              disabled={replaySubmitting || stats.failed_events === 0}
              className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:bg-stone-100 disabled:text-stone-400 disabled:border-stone-200 text-white text-sm font-semibold transition flex items-center justify-center gap-2 shadow-lg shadow-amber-200/40"
            >
              {replaySubmitting ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {replaySubmitting ? "Running Replay..." : "Trigger Replay"}
            </button>
          </div>

          {replayResult && (
            <div className="p-4 bg-stone-100 rounded-2xl border border-stone-200 flex items-start gap-2 text-xs font-mono text-stone-600 leading-snug">
              <Terminal className="h-4.5 w-4.5 text-amber-600 flex-shrink-0 mt-0.5" />
              <span>{replayResult}</span>
            </div>
          )}
        </div>

        {/* Telemetry Simulator Form (Right) */}
        <div className="lg:col-span-2 bg-white border border-stone-200 rounded-3xl p-6 space-y-6 shadow-xl">
          <div>
            <div className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-cyan-600" />
              <h2 className="text-lg font-bold text-stone-800 tracking-tight">Durable Buffer Ingestion Simulator</h2>
            </div>
            <p className="text-xs text-stone-500 mt-1">Simulate network drop uploads. Telemetry is saved with idempotency keys.</p>
          </div>

          <form onSubmit={handleSimulate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Sensor Identifier
              </label>
              <input
                type="text"
                value={sensorId}
                onChange={(e) => setSensorId(e.target.value)}
                placeholder="flow-meter-A1"
                className="w-full px-4 py-3 rounded-xl bg-stone-100 border border-stone-200 text-sm text-stone-800 focus:outline-none focus:border-cyan-500 focus:bg-stone-100 transition"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Telemetry Value
              </label>
              <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="1.8"
                className="w-full px-4 py-3 rounded-xl bg-stone-100 border border-stone-200 text-sm text-stone-800 focus:outline-none focus:border-cyan-500 focus:bg-stone-100 transition"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Unit of Measure
              </label>
              <input
                type="text"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                placeholder="bar"
                className="w-full px-4 py-3 rounded-xl bg-stone-100 border border-stone-200 text-sm text-stone-800 focus:outline-none focus:border-cyan-500 focus:bg-stone-100 transition"
                required
              />
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={simulating}
                className="w-full py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-600/50 text-white text-sm font-semibold transition shadow-lg shadow-cyan-500/10"
              >
                {simulating ? "Uploading..." : "Inject Simulated Telemetry"}
              </button>
            </div>
          </form>

          {simulatorResult && (
            <div className="p-4 bg-stone-100 rounded-2xl border border-stone-200 flex items-start gap-2 text-xs font-mono text-stone-600 leading-snug">
              <Terminal className="h-4.5 w-4.5 text-cyan-600 flex-shrink-0 mt-0.5" />
              <span>{simulatorResult}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
