const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string;
};

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token } = opts;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || "Request failed");
  }

  return res.json() as Promise<T>;
}

// ── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>(
      "/auth/login",
      { method: "POST", body: { email, password } }
    ),
  me: (token: string) =>
    request<{ id: string; email: string; role: string; full_name: string }>(
      "/auth/me",
      { token }
    ),
};

// ── Dashboard ────────────────────────────────────────────────────────────────
export const dashboardApi = {
  getSummary: (token: string) =>
    request<DashboardOut>("/dashboard", { token }),
  getAnalytics: (token: string) =>
    request<AnalyticsOut>("/dashboard/analytics", { token }),
};

// ── Incidents ────────────────────────────────────────────────────────────────
export const incidentsApi = {
  list: (token: string, params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<IncidentListOut>(`/incidents${qs}`, { token });
  },
  get: (token: string, id: string) =>
    request<IncidentOut>(`/incidents/${id}`, { token }),
  ingestSensor: (token: string, data: SensorDataPayload) =>
    request<{ message: string; incident_id?: string }>("/incidents/sensor-data", {
      method: "POST", body: data, token,
    }),
};

// ── Contractors ───────────────────────────────────────────────────────────────
export const contractorsApi = {
  list: (token: string) =>
    request<ContractorOut[]>("/contractors", { token }),
  get: (token: string, id: string) =>
    request<ContractorOut>(`/contractors/${id}`, { token }),
};

// ── Notifications ─────────────────────────────────────────────────────────────
export const notificationsApi = {
  list: (token: string) =>
    request<NotificationOut[]>("/notifications", { token }),
};

// ── Agent Logs ────────────────────────────────────────────────────────────────
export const agentLogsApi = {
  list: (token: string) =>
    request<AgentLogOut[]>("/agent-logs", { token }),
  byIncident: (token: string, incidentId: string) =>
    request<AgentLogOut[]>(`/agent-logs/${incidentId}`, { token }),
};

// ── Types ─────────────────────────────────────────────────────────────────────
export interface DashboardOut {
  kpi: { total_incidents: number; active_incidents: number; critical_incidents: number; resolved_today: number; avg_resolution_time_hrs?: number };
  recent_incidents: RecentIncident[];
  agent_activity: AgentActivity[];
  severity_distribution: Record<string, number>;
  incident_trend: { date: string; count: number }[];
}
export interface AnalyticsOut {
  incident_trend: { date: string; count: number }[];
  severity_distribution: Record<string, number>;
  incident_type_distribution: Record<string, number>;
  resolution_time_trend: { date: string; avg_hours: number }[];
  contractor_performance: { name: string; jobs: number; rating: number }[];
}
export interface RecentIncident { id: string; type: string; severity: string; status: string; tower_name?: string; detected_at: string; }
export interface AgentActivity { agent_name: string; executions_today: number; avg_execution_time_ms?: number; success_rate: number; }
export interface IncidentOut { id: string; type: string; severity: string; confidence: number; status: string; tower_id?: string; description?: string; root_cause?: string; ai_decision?: Record<string, unknown>; detected_at: string; resolved_at?: string; contractor_assignment?: ContractorAssignmentOut; }
export interface IncidentListOut { items: IncidentOut[]; total: number; page: number; page_size: number; }
export interface ContractorAssignmentOut { contractor_id: string; contractor_name: string; estimated_cost?: number; estimated_time_hrs?: number; selection_reasoning?: string; }
export interface ContractorOut { id: string; name: string; specializations: string[]; rating: number; avg_response_time_hrs: number; total_jobs: number; success_rate: number; contact_info: Record<string, string>; is_active: boolean; }
export interface NotificationOut { id: string; incident_id: string; channel: string; subject?: string; content: string; status: string; sent_at?: string; }
export interface AgentLogOut { id: string; incident_id: string; agent_name: string; execution_time_ms?: number; tokens_used?: number; status: string; error?: string; input_payload?: Record<string, unknown>; output_payload?: Record<string, unknown>; created_at: string; }
export interface SensorDataPayload { tower_id: string; sensor_type: string; value: number; unit: string; timestamp: string; }
